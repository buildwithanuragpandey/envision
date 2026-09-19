import uuid
from typing import List, Callable, Optional
from app.core.config import settings
from app.core.logging import logger
from app.schemas.document import PageContent, TextChunk, DocumentMetadata

class RecursiveCharacterTextSplitter:
    """
    Lightweight, pure-Python recursive text splitter.
    Provides splitting behavior without importing LangChain, saving ~400MB of RAM.
    """
    def __init__(
        self,
        chunk_size: int = 800,
        chunk_overlap: int = 150,
        separators: Optional[List[str]] = None,
        length_function: Callable[[str], int] = len
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]
        self.length_function = length_function

    def split_text(self, text: str) -> List[str]:
        return self._split_text(text, self.separators)

    def _split_text(self, text: str, separators: List[str]) -> List[str]:
        final_chunks: List[str] = []
        separator = separators[-1]
        new_separators = []
        for i, _s in enumerate(separators):
            if _s == "":
                separator = _s
                break
            if _s in text:
                separator = _s
                new_separators = separators[i + 1:]
                break

        splits = text.split(separator) if separator else list(text)

        good_splits: List[str] = []
        _separator = "" if separator == "" else separator
        for s in splits:
            if self.length_function(s) < self.chunk_size:
                good_splits.append(s)
            else:
                if good_splits:
                    merged = self._merge_splits(good_splits, _separator)
                    final_chunks.extend(merged)
                    good_splits = []
                if not new_separators:
                    final_chunks.append(s)
                else:
                    other_info = self._split_text(s, new_separators)
                    final_chunks.extend(other_info)
        if good_splits:
            merged = self._merge_splits(good_splits, _separator)
            final_chunks.extend(merged)
        return final_chunks

    def _merge_splits(self, splits: List[str], separator: str) -> List[str]:
        docs: List[str] = []
        current_doc: List[str] = []
        total = 0
        for d in splits:
            _len = self.length_function(d)
            sep_len = self.length_function(separator) if len(current_doc) > 0 else 0
            if total + _len + sep_len > self.chunk_size:
                if total > 0:
                    doc = separator.join(current_doc).strip()
                    if doc:
                        docs.append(doc)
                    while total > self.chunk_overlap or (
                        total + _len + (self.length_function(separator) if len(current_doc) > 0 else 0) > self.chunk_size and total > 0
                    ):
                        total -= self.length_function(current_doc[0]) + (
                            self.length_function(separator) if len(current_doc) > 1 else 0
                        )
                        current_doc = current_doc[1:]
            current_doc.append(d)
            total += _len + (self.length_function(separator) if len(current_doc) > 1 else 0)
        doc = separator.join(current_doc).strip()
        if doc:
            docs.append(doc)
        return docs

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
