from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class MessageRole:
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ChatHistoryItem(BaseModel):
    role: str
    content: str

class SourceCitation(BaseModel):
    citation_id: int
    filename: str
    page_number: int
    chunk_id: str
    relevance_score: float
    snippet: str

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default-session"
    document_ids: Optional[List[str]] = Field(default=None, description="Optional list of specific document IDs to filter search")
    history: Optional[List[ChatHistoryItem]] = Field(default_factory=list, description="Recent conversation turns (5-10 max)")
    top_k: Optional[int] = Field(default=None, description="Override default TOP_K retrieval chunks")

class DebugInfo(BaseModel):
    retrieval_latency_ms: float
    generation_latency_ms: float
    total_latency_ms: float
    retrieved_chunks_count: int
    reformulated_query: Optional[str] = None
    similarity_scores: List[float] = Field(default_factory=list)
    llm_provider: str
    llm_model: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceCitation]
    confidence: float
    is_grounded: bool
    debug_info: Optional[DebugInfo] = None
