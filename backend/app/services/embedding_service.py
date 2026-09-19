from typing import List
import numpy as np
from app.core.config import settings
from app.core.logging import logger

class EmbeddingService:
    def __init__(self, model_name: str = settings.EMBEDDING_MODEL):
        self.model_name = model_name
        self._model = None
        self._model_type = None  # "fastembed", "sentence_transformers", "fallback"
        self._dimension = 384  # default for bge-small-en / all-MiniLM-L6-v2

    def _get_model(self):
        if self._model is None:
            # 1. Try lightweight fastembed (ONNX runtime, ~40MB RAM, no PyTorch)
            try:
                from fastembed import TextEmbedding
                logger.info(f"Loading FastEmbed model: {self.model_name}")
                # Restrict threads=1 to prevent ONNX Runtime from allocating excessive thread pools on multi-core hosts (e.g. Render)
                self._model = TextEmbedding(model_name=self.model_name, threads=1)
                self._model_type = "fastembed"
                sample_emb = list(self._model.embed(["test"]))[0]
                self._dimension = len(sample_emb)
                logger.info(f"FastEmbed model loaded successfully (dimension={self._dimension}).")
                return self._model
            except Exception as e:
                logger.info(f"FastEmbed not available or failed to load: {e}")

            # 2. Try SentenceTransformer if installed
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading SentenceTransformer embedding model: {self.model_name}")
                self._model = SentenceTransformer(self.model_name)
                self._model_type = "sentence_transformers"
                sample_emb = self._model.encode(["test"])
                self._dimension = sample_emb.shape[1]
                logger.info(f"SentenceTransformer loaded successfully (dimension={self._dimension}).")
                return self._model
            except Exception as e:
                logger.warning(
                    f"Could not load SentenceTransformer '{self.model_name}': {e}. Using deterministic fallback embedder."
                )

            # 3. Deterministic fallback embedder
            self._model = "fallback"
            self._model_type = "fallback"

        return self._model

    def _fallback_embed(self, texts: List[str]) -> List[List[float]]:
        """
        Deterministic lightweight feature hash embedding fallback for zero-network/fallback setups.
        Produces 384-dimensional normalized vectors.
        """
        vectors = []
        dim = 384
        for text in texts:
            vec = np.zeros(dim, dtype=np.float32)
            words = text.lower().split()
            if not words:
                vectors.append(vec.tolist())
                continue
            for i, word in enumerate(words):
                h = hash(word) % dim
                weight = 1.0 / (1.0 + np.log1p(i))
                vec[h] += float(weight)
            # Add character n-gram hashing
            for i in range(len(text) - 3):
                h_ng = hash(text[i:i+3]) % dim
                vec[h_ng] += 0.25
            # L2 normalize
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            vectors.append(vec.tolist())
        return vectors

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generates embeddings for a batch of documents / chunks.
        """
        if not texts:
            return []
        
        model = self._get_model()
        if self._model_type == "fastembed":
            try:
                batch_size = min(settings.EMBEDDING_BATCH_SIZE, 16)
                embeddings = list(model.embed(texts, batch_size=batch_size))
                result = [e.tolist() if hasattr(e, "tolist") else list(e) for e in embeddings]
                import gc
                gc.collect()
                return result
            except Exception as e:
                logger.error(f"Error generating embeddings with fastembed: {e}. Falling back to deterministic embedder.")
                return self._fallback_embed(texts)

        if self._model_type == "sentence_transformers":
            try:
                embeddings = model.encode(
                    texts,
                    batch_size=settings.EMBEDDING_BATCH_SIZE,
                    show_progress_bar=False,
                    normalize_embeddings=True
                )
                return embeddings.tolist()
            except Exception as e:
                logger.error(f"Error generating embeddings with sentence_transformers: {e}. Falling back.")
                return self._fallback_embed(texts)

        return self._fallback_embed(texts)

    def embed_query(self, text: str) -> List[float]:
        """
        Generates an embedding vector for a single query.
        """
        embeddings = self.embed_documents([text])
        return embeddings[0] if embeddings else []

    @property
    def dimension(self) -> int:
        if self._model is None:
            self._get_model()
        return self._dimension

embedding_service = EmbeddingService()
