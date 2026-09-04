from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
import datetime

class DocumentStatus(str, Enum):
    UPLOADED = "Uploaded"
    PROCESSING = "Processing"
    INDEXED = "Indexed"
    FAILED = "Failed"

class PageContent(BaseModel):
    filename: str
    page_number: int
    document_id: str
    text: str

class TextChunk(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    page_number: int
    chunk_index: int
    content: str
    document_hash: str

class DocumentMetadata(BaseModel):
    document_id: str
    filename: str
    file_size_bytes: int
    total_pages: int
    chunk_count: int = 0
    document_hash: str
    status: DocumentStatus = DocumentStatus.UPLOADED
    error_message: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

class DocumentUploadResponse(BaseModel):
    documents: List[DocumentMetadata]
    message: str
    duplicates_detected: int = 0
    total_documents: int

class DocumentDeleteResponse(BaseModel):
    document_id: str
    message: str
    chunks_removed: int
