from pydantic import BaseModel
from typing import List, Dict

class ProcessingAnalytics(BaseModel):
    total_documents: int
    total_pages: int
    total_chunks: int
    indexed_documents: int
    storage_size_bytes: int
    active_llm_provider: str
    active_llm_model: str
    active_embedding_model: str

class HealthStatus(BaseModel):
    status: str
    version: str
    vector_store_status: str
    llm_provider_status: str
