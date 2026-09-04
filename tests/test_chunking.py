import pytest
from app.schemas.document import PageContent, DocumentMetadata, DocumentStatus
from app.services.chunking_service import ChunkingService

def test_chunking_with_metadata_preservation():
    service = ChunkingService(chunk_size=100, chunk_overlap=20)
    
    meta = DocumentMetadata(
        document_id="doc-123",
        filename="report.pdf",
        file_size_bytes=1024,
        total_pages=2,
        document_hash="abc123hash",
        status=DocumentStatus.PROCESSING
    )
    
    pages = [
        PageContent(
            filename="report.pdf",
            page_number=1,
            document_id="doc-123",
            text="Sentence one is here. Sentence two is very interesting and explains quantum computing algorithms in depth. Sentence three adds more details."
        ),
        PageContent(
            filename="report.pdf",
            page_number=2,
            document_id="doc-123",
            text="Second page content starts here. It discusses battery storage economics and grid scale efficiency metrics."
        )
    ]
    
    chunks = service.chunk_pages(pages, meta)
    
    assert len(chunks) >= 2
    for chunk in chunks:
        assert chunk.document_id == "doc-123"
        assert chunk.filename == "report.pdf"
        assert chunk.document_hash == "abc123hash"
        assert chunk.page_number in [1, 2]
        assert len(chunk.content) > 0
        assert chunk.chunk_id is not None
