import time
from typing import List, Dict, Any, Optional, Tuple
from app.core.config import settings
from app.core.logging import logger
from app.schemas.chat import SourceCitation
from app.services.vector_store_service import vector_store_service
from app.services.reranking_service import reranking_service

class RetrievalService:
    def __init__(
        self,
        top_k: int = settings.TOP_K,
        similarity_threshold: float = settings.SIMILARITY_THRESHOLD
    ):
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold

    def retrieve_context(
        self,
        query: str,
        document_ids: Optional[List[str]] = None,
        top_k: Optional[int] = None
    ) -> Tuple[List[Dict[str, Any]], List[SourceCitation], float, float]:
        """
        Executes semantic search, reranking (if enabled), threshold checks, and formatting.
        Returns:
            - filtered_chunks: raw chunk data
            - citations: list of SourceCitation objects
            - max_confidence: float [0, 1]
            - latency_ms: float
        """
        start_time = time.perf_counter()
        effective_top_k = top_k or self.top_k

        # If reranking is enabled, fetch more candidate chunks initially
        fetch_k = effective_top_k * 2 if settings.ENABLE_RERANKING else effective_top_k
        
        raw_chunks = vector_store_service.search(
            query_text=query,
            top_k=fetch_k,
            document_ids=document_ids
        )

        if not raw_chunks:
            latency = (time.perf_counter() - start_time) * 1000.0
            return [], [], 0.0, latency

        # Optional Reranking
        if settings.ENABLE_RERANKING:
            ranked_chunks = reranking_service.rerank(query, raw_chunks, top_n=effective_top_k)
        else:
            ranked_chunks = raw_chunks[:effective_top_k]

        # Calculate max similarity confidence
        max_similarity = max((c.get("similarity", 0.0) for c in ranked_chunks), default=0.0)
        
        # Filter chunks by similarity threshold
        filtered_chunks = []
        for c in ranked_chunks:
            # We keep chunks that meet the minimum threshold or top 2 chunks if closest
            if c.get("similarity", 0.0) >= self.similarity_threshold or len(filtered_chunks) < 2:
                filtered_chunks.append(c)

        # Build Source Citations
        citations: List[SourceCitation] = []
        for idx, chunk in enumerate(filtered_chunks, start=1):
            snippet = chunk["content"]
            if len(snippet) > 280:
                snippet = snippet[:280].rstrip() + "..."

            citations.append(
                SourceCitation(
                    citation_id=idx,
                    filename=chunk["filename"],
                    page_number=chunk["page_number"],
                    chunk_id=chunk["chunk_id"],
                    relevance_score=round(chunk.get("similarity", 0.0), 3),
                    snippet=snippet
                )
            )

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        logger.info(
            f"Retrieved {len(filtered_chunks)} chunks for query '{query[:40]}...' in {latency_ms:.2f}ms (Confidence: {max_similarity:.2f})"
        )

        return filtered_chunks, citations, max_similarity, latency_ms

retrieval_service = RetrievalService()
