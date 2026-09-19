import os
import json
import uuid
import shutil
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from app.core.config import settings
from app.core.logging import logger
from app.schemas.document import (
    DocumentMetadata,
    DocumentStatus,
    DocumentUploadResponse,
    DocumentDeleteResponse
)
from app.services.pdf_service import pdf_service, PDFProcessingError
from app.services.chunking_service import chunking_service
from app.services.vector_store_service import vector_store_service

router = APIRouter(prefix="/documents", tags=["Documents"])

# In-memory / persistent metadata registry file
DOCUMENTS_STORE_FILE = os.path.join(settings.UPLOAD_DIRECTORY, "documents_registry.json")

def _load_registry() -> dict:
    if os.path.exists(DOCUMENTS_STORE_FILE):
        try:
            with open(DOCUMENTS_STORE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading document registry: {e}")
    return {}

def _save_registry(registry: dict):
    try:
        with open(DOCUMENTS_STORE_FILE, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving document registry: {e}")

@router.get("", response_model=List[DocumentMetadata])
async def list_documents():
    """
    Returns all uploaded and indexed documents in the current session.
    """
    registry = _load_registry()
    docs = [DocumentMetadata(**data) for data in registry.values()]
    return sorted(docs, key=lambda d: d.created_at, reverse=True)

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_documents(files: List[UploadFile] = File(...)):
    """
    Uploads up to 50 PDF files, extracts text page-by-page, chunks, and indexes into ChromaDB.
    Detects duplicate documents via SHA-256 hash.
    """
    registry = _load_registry()
    current_doc_count = len(registry)
    
    if current_doc_count + len(files) > settings.MAX_DOCUMENTS_PER_SESSION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Upload limit exceeded. Maximum of {settings.MAX_DOCUMENTS_PER_SESSION} documents allowed per session. (Currently {current_doc_count} indexed)."
        )

    processed_docs: List[DocumentMetadata] = []
    duplicates_detected = 0

    # Build map of existing hashes
    existing_hashes = {d["document_hash"]: d for d in registry.values()}

    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only PDF files are supported. File '{file.filename}' was rejected."
            )

        try:
            content = await file.read()
            if len(content) == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File '{file.filename}' is empty."
                )

            # Check duplicate hash
            doc_hash = pdf_service.calculate_sha256(content)
            if doc_hash in existing_hashes:
                duplicates_detected += 1
                logger.info(f"Duplicate detected for '{file.filename}' (hash: {doc_hash[:8]}). Reusing existing index.")
                processed_docs.append(DocumentMetadata(**existing_hashes[doc_hash]))
                continue

            # Save file to uploads folder
            doc_id = str(uuid.uuid4())
            safe_filename = f"{doc_id}_{file.filename}"
            file_path = os.path.join(settings.UPLOAD_DIRECTORY, safe_filename)
            with open(file_path, "wb") as f:
                f.write(content)

            # Step 1 & 2 & 3: Validate & Extract pages
            meta, pages = pdf_service.validate_and_extract(content, file.filename, document_id=doc_id)
            del content
            import gc
            gc.collect()

            # Step 4: Chunk pages
            chunks = chunking_service.chunk_pages(pages, meta)
            meta.chunk_count = len(chunks)
            del pages
            gc.collect()

            # Step 5: Embed & Index in Vector DB
            if chunks:
                vector_store_service.add_chunks(chunks)
                meta.status = DocumentStatus.INDEXED
            else:
                meta.status = DocumentStatus.FAILED
                meta.error_message = "No extractable text found in PDF."
            del chunks
            gc.collect()

            # Update registry
            registry[doc_id] = meta.model_dump()
            existing_hashes[doc_hash] = meta.model_dump()
            processed_docs.append(meta)

        except PDFProcessingError as e:
            logger.error(f"PDF processing error for {file.filename}: {e}")
            failed_meta = DocumentMetadata(
                document_id=str(uuid.uuid4()),
                filename=file.filename,
                file_size_bytes=len(content) if 'content' in locals() else 0,
                total_pages=0,
                document_hash="",
                status=DocumentStatus.FAILED,
                error_message=str(e)
            )
            processed_docs.append(failed_meta)
        except Exception as e:
            logger.error(f"Unexpected error processing {file.filename}: {e}")
            failed_meta = DocumentMetadata(
                document_id=str(uuid.uuid4()),
                filename=file.filename,
                file_size_bytes=len(content) if 'content' in locals() else 0,
                total_pages=0,
                document_hash="",
                status=DocumentStatus.FAILED,
                error_message=f"Processing failed: {str(e)}"
            )
            processed_docs.append(failed_meta)

    _save_registry(registry)

    msg = f"Processed {len(processed_docs)} document(s)."
    if duplicates_detected > 0:
        msg += f" {duplicates_detected} duplicate(s) recognized and reused."

    return DocumentUploadResponse(
        documents=processed_docs,
        message=msg,
        duplicates_detected=duplicates_detected,
        total_documents=len(registry)
    )

@router.delete("/{document_id}", response_model=DocumentDeleteResponse)
async def delete_document(document_id: str):
    """
    Deletes a document from the session, removing its chunks from ChromaDB and registry.
    """
    registry = _load_registry()
    if document_id not in registry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found."
        )

    # Remove chunks from ChromaDB
    chunks_removed = vector_store_service.delete_by_document_id(document_id)

    # Remove uploaded file if present
    doc_meta = registry.pop(document_id)
    safe_filename = f"{document_id}_{doc_meta.get('filename')}"
    file_path = os.path.join(settings.UPLOAD_DIRECTORY, safe_filename)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            logger.warning(f"Could not remove local file {file_path}: {e}")

    _save_registry(registry)

    return DocumentDeleteResponse(
        document_id=document_id,
        message=f"Document '{doc_meta.get('filename')}' successfully removed.",
        chunks_removed=chunks_removed
    )

@router.delete("", response_model=dict)
async def clear_all_documents():
    """
    Clears all documents, chunks, and vector store data for the session.
    """
    chunks_cleared = vector_store_service.clear_all()
    _save_registry({})

    # Clean uploads directory
    for f in os.listdir(settings.UPLOAD_DIRECTORY):
        if f != "documents_registry.json":
            file_path = os.path.join(settings.UPLOAD_DIRECTORY, f)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception as e:
                logger.warning(f"Error removing {file_path}: {e}")

    return {
        "message": "All documents and vector indexes cleared successfully.",
        "chunks_cleared": chunks_cleared
    }

@router.post("/seed_samples", response_model=DocumentUploadResponse)
async def seed_sample_documents():
    """
    Seeds three comprehensive sample research papers (Quantum Computing, Energy Storage, AI in Diagnostics)
    for immediate 1-click evaluation and demoing.
    """
    from evaluation.generate_sample_pdfs import generate_all_samples
    samples = generate_all_samples(settings.SAMPLE_DOCS_DIRECTORY)
    
    registry = _load_registry()
    existing_hashes = {d["document_hash"]: d for d in registry.values()}
    processed_docs: List[DocumentMetadata] = []

    for filename, filepath in samples.items():
        with open(filepath, "rb") as f:
            content = f.read()

        doc_hash = pdf_service.calculate_sha256(content)
        if doc_hash in existing_hashes:
            processed_docs.append(DocumentMetadata(**existing_hashes[doc_hash]))
            continue

        doc_id = str(uuid.uuid4())
        meta, pages = pdf_service.validate_and_extract(content, filename, document_id=doc_id)
        chunks = chunking_service.chunk_pages(pages, meta)
        meta.chunk_count = len(chunks)

        if chunks:
            vector_store_service.add_chunks(chunks)
            meta.status = DocumentStatus.INDEXED
        
        registry[doc_id] = meta.model_dump()
        existing_hashes[doc_hash] = meta.model_dump()
        processed_docs.append(meta)

    _save_registry(registry)

    return DocumentUploadResponse(
        documents=processed_docs,
        message="Sample research papers seeded successfully into DocuMind AI.",
        duplicates_detected=0,
        total_documents=len(registry)
    )
