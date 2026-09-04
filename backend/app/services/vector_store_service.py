import os
import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional, Tuple
from app.core.config import settings
from app.core.logging import logger
from app.schemas.document import TextChunk
from app.services.embedding_service import embedding_service

class VectorStoreService:
    COLLECTION_NAME = "documind_chunks"

    def __init__(self, persist_directory: str = settings.CHROMA_PERSIST_DIRECTORY):
        self.persist_directory = os.path.abspath(persist_directory)
        os.makedirs(self.persist_directory, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                is_persistent=True
            )
        )
        self.collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"description": "DocuMind multi-PDF knowledge chunks"}
        )
        logger.info(f"Initialized ChromaDB vector store at '{self.persist_directory}' (Collection count: {self.collection.count()})")

    def add_chunks(self, chunks: List[TextChunk]) -> int:
        """
        Embeds and indexes a list of TextChunks into ChromaDB.
        """
        if not chunks:
            return 0

        # Batch embed
        texts = [chunk.content for chunk in chunks]
        embeddings = embedding_service.embed_documents(texts)

        ids = [chunk.chunk_id for chunk in chunks]
        metadatas = [
            {
                "document_id": chunk.document_id,
                "filename": chunk.filename,
                "page_number": int(chunk.page_number),
                "chunk_index": int(chunk.chunk_index),
                "document_hash": chunk.document_hash,
            }
            for chunk in chunks
        ]

        # Insert into Chroma in batches of 100
        batch_size = 100
        for i in range(0, len(chunks), batch_size):
            end_idx = i + batch_size
            self.collection.upsert(
                ids=ids[i:end_idx],
                embeddings=embeddings[i:end_idx],
                documents=texts[i:end_idx],
                metadatas=metadatas[i:end_idx]
            )

        logger.info(f"Successfully added {len(chunks)} chunks to ChromaDB.")
        return len(chunks)

    def search(
        self,
        query_text: str,
        top_k: int = settings.TOP_K,
        document_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Performs vector similarity search against the collection.
        Returns a list of chunk dictionaries with similarity score and metadata.
        """
        if self.collection.count() == 0:
            return []

        query_embedding = embedding_service.embed_query(query_text)

        where_clause = None
        if document_ids:
            if len(document_ids) == 1:
                where_clause = {"document_id": document_ids[0]}
            elif len(document_ids) > 1:
                where_clause = {"document_id": {"$in": document_ids}}

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self.collection.count()),
            where=where_clause,
            include=["documents", "metadatas", "distances"]
        )

        matched_chunks = []
        if results and results["ids"] and len(results["ids"][0]) > 0:
            ids = results["ids"][0]
            docs = results["documents"][0]
            metadatas = results["metadatas"][0]
            distances = results["distances"][0]

            for i in range(len(ids)):
                # Chroma uses L2 distance or cosine distance by default.
                # Distance to similarity: 1 / (1 + distance) or max(0, 1 - distance/2)
                distance = distances[i]
                similarity = max(0.0, min(1.0, 1.0 - (distance / 2.0))) if distance >= 0 else 1.0

                matched_chunks.append({
                    "chunk_id": ids[i],
                    "content": docs[i],
                    "filename": metadatas[i].get("filename", "Unknown"),
                    "page_number": metadatas[i].get("page_number", 1),
                    "document_id": metadatas[i].get("document_id", ""),
                    "distance": distance,
                    "similarity": round(similarity, 4),
                    "document_hash": metadatas[i].get("document_hash", "")
                })

        return matched_chunks

    def delete_by_document_id(self, document_id: str) -> int:
        """
        Deletes all chunks associated with a specific document ID.
        """
        try:
            # Query existing IDs for this document
            existing = self.collection.get(
                where={"document_id": document_id},
                include=["metadatas"]
            )
            count = len(existing["ids"]) if existing and "ids" in existing else 0
            if count > 0:
                self.collection.delete(where={"document_id": document_id})
                logger.info(f"Deleted {count} chunks for document_id '{document_id}' from ChromaDB.")
            return count
        except Exception as e:
            logger.error(f"Error deleting chunks for document_id {document_id}: {e}")
            return 0

    def clear_all(self) -> int:
        """
        Clears the entire ChromaDB collection.
        """
        count = self.collection.count()
        self.client.delete_collection(self.COLLECTION_NAME)
        self.collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"description": "DocuMind multi-PDF knowledge chunks"}
        )
        logger.info(f"Cleared vector store. Removed {count} chunks.")
        return count

    def get_total_chunks(self) -> int:
        return self.collection.count()

    def get_all_document_ids(self) -> List[str]:
        results = self.collection.get(include=["metadatas"])
        if not results or not results["metadatas"]:
            return []
        return list(set(m.get("document_id") for m in results["metadatas"] if m.get("document_id")))

vector_store_service = VectorStoreService()
