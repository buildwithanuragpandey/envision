from typing import List, Dict, Any
from app.core.config import settings
from app.core.logging import logger

class RerankingService:
    def __init__(self, model_name: str = settings.RERANKER_MODEL, enabled: bool = settings.ENABLE_RERANKING):
        self.model_name = model_name
        self.enabled = enabled
        self._model = None

    def _get_model(self):
        if self._model is None and self.enabled:
            try:
                from sentence_transformers import CrossEncoder
                logger.info(f"Loading CrossEncoder reranker model: {self.model_name}")
                self._model = CrossEncoder(self.model_name)
                logger.info("CrossEncoder model loaded successfully.")
            except Exception as e:
                logger.warning(f"Failed to load CrossEncoder reranker '{self.model_name}': {e}. Continuing without reranking.")
                self.enabled = False
        return self._model

    def rerank(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        top_n: int = settings.TOP_K
    ) -> List[Dict[str, Any]]:
        """
        Reranks retrieved candidate chunks using a cross-encoder scoring pairs of (query, chunk_text).
        """
        if not chunks or not self.enabled:
            return chunks[:top_n]

        model = self._get_model()
        if model is None:
            return chunks[:top_n]

        try:
            pairs = [[query, chunk["content"]] for chunk in chunks]
            scores = model.predict(pairs)

            # Assign rerank scores and sort
            for i, chunk in enumerate(chunks):
                chunk["rerank_score"] = float(scores[i])

            ranked_chunks = sorted(chunks, key=lambda x: x.get("rerank_score", 0.0), reverse=True)
            return ranked_chunks[:top_n]
        except Exception as e:
            logger.error(f"Error during cross-encoder reranking: {e}")
            return chunks[:top_n]

reranking_service = RerankingService()
