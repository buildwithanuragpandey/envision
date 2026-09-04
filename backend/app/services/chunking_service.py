import uuid
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.config import settings
from app.core.logging import logger
from app.schemas.document import PageContent, TextChunk, DocumentMetadata

class ChunkingService:
    def __init__(
        self,
        chunk_size: int = settings.CHUNK_SIZE,
        chunk_overlap: int = settings.CHUNK_OVERLAP
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

    def chunk_pages(
        self,
        pages: List[PageContent],
        document_metadata: DocumentMetadata
    ) -> List[TextChunk]:
        """
        Splits text from individual pages into overlapping chunks while preserving rich metadata.
        """
        chunks: List[TextChunk] = []
        global_chunk_idx = 0

        for page in pages:
            if not page.text or len(page.text.strip()) == 0:
                continue

            page_splits = self.text_splitter.split_text(page.text)
            for split_idx, split_text in enumerate(page_splits):
                cleaned_split = split_text.strip()
                if not cleaned_split:
                    continue

                chunk = TextChunk(
                    chunk_id=str(uuid.uuid4()),
                    document_id=document_metadata.document_id,
                    filename=document_metadata.filename,
                    page_number=page.page_number,
                    chunk_index=global_chunk_idx,
                    content=cleaned_split,
                    document_hash=document_metadata.document_hash
                )
                chunks.append(chunk)
                global_chunk_idx += 1

        logger.info(
            f"Chunked document '{document_metadata.filename}' ({document_metadata.total_pages} pages) into {len(chunks)} chunks."
        )
        return chunks

chunking_service = ChunkingService()
