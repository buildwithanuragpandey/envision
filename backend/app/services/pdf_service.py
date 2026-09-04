import hashlib
import uuid
import re
import fitz  # PyMuPDF
from typing import List, Tuple, Optional
from app.core.logging import logger
from app.schemas.document import PageContent, DocumentMetadata, DocumentStatus

class PDFProcessingError(Exception):
    pass

class PDFService:
    def __init__(self, max_file_size_mb: int = 50):
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024

    @staticmethod
    def calculate_sha256(file_bytes: bytes) -> str:
        return hashlib.sha256(file_bytes).hexdigest()

    @staticmethod
    def clean_text(text: str) -> str:
        if not text:
            return ""
        # Normalize non-breaking spaces and tabs
        text = text.replace('\xa0', ' ').replace('\t', ' ')
        # Collapse multiple spaces while preserving paragraph breaks
        text = re.sub(r'[ ]{2,}', ' ', text)
        # Collapse 3 or more consecutive newlines to double newline
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Remove trailing/leading whitespaces on each line
        lines = [line.strip() for line in text.split('\n')]
        return '\n'.join(lines).strip()

    def validate_and_extract(
        self,
        file_bytes: bytes,
        filename: str,
        document_id: Optional[str] = None
    ) -> Tuple[DocumentMetadata, List[PageContent]]:
        """
        Validates the PDF bytes and extracts text page-by-page.
        """
        if len(file_bytes) > self.max_file_size_bytes:
            raise PDFProcessingError(
                f"File '{filename}' exceeds maximum allowed size of {self.max_file_size_bytes // (1024*1024)}MB."
            )
        
        if not filename.lower().endswith(".pdf"):
            raise PDFProcessingError(f"File '{filename}' is not a valid PDF document. Only .pdf files are supported.")

        doc_hash = self.calculate_sha256(file_bytes)
        doc_id = document_id or str(uuid.uuid4())
        
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
        except Exception as e:
            logger.error(f"Failed to open PDF stream for {filename}: {str(e)}")
            raise PDFProcessingError(
                f"This PDF could not be processed. The file may be corrupted or invalid."
            )

        if doc.is_encrypted:
            try:
                # Try empty password
                if not doc.authenticate(""):
                    raise PDFProcessingError(f"PDF '{filename}' is password-protected and cannot be read.")
            except Exception:
                raise PDFProcessingError(f"PDF '{filename}' is password-protected and cannot be read.")

        total_pages = doc.page_count
        if total_pages == 0:
            raise PDFProcessingError(f"PDF '{filename}' is empty (0 pages).")

        pages: List[PageContent] = []
        total_extracted_text_len = 0

        for page_idx in range(total_pages):
            try:
                page = doc.load_page(page_idx)
                raw_text = page.get_text("text") or ""
                cleaned_text = self.clean_text(raw_text)
                total_extracted_text_len += len(cleaned_text)

                pages.append(
                    PageContent(
                        filename=filename,
                        page_number=page_idx + 1,  # 1-indexed for human readability
                        document_id=doc_id,
                        text=cleaned_text
                    )
                )
            except Exception as e:
                logger.warning(f"Error reading page {page_idx + 1} of {filename}: {e}")
                pages.append(
                    PageContent(
                        filename=filename,
                        page_number=page_idx + 1,
                        document_id=doc_id,
                        text=""
                    )
                )

        doc.close()

        if total_extracted_text_len < 10:
            logger.warning(f"Extracted minimal text ({total_extracted_text_len} chars) from {filename}. Might be a scanned/image-only PDF.")

        metadata = DocumentMetadata(
            document_id=doc_id,
            filename=filename,
            file_size_bytes=len(file_bytes),
            total_pages=total_pages,
            document_hash=doc_hash,
            status=DocumentStatus.PROCESSING
        )

        return metadata, pages

pdf_service = PDFService()
