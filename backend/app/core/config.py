from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import Optional, List
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "DocuMind AI"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # LLM Settings
    LLM_PROVIDER: str = Field(default="groq", description="LLM provider: groq, openai, gemini, ollama, mock")
    LLM_MODEL: str = Field(default="qwen/qwen3.6-27b", description="Model name for provider (e.g. qwen/qwen3.6-27b, openai/gpt-oss-120b, openai/gpt-oss-20b)")
    LLM_API_KEY: Optional[str] = Field(default=None, description="API Key for the chosen provider")
    LLM_TEMPERATURE: float = Field(default=0.1, description="Sampling temperature")
    LLM_BASE_URL: Optional[str] = Field(default=None, description="Optional base URL for OpenAI-compatible or Ollama endpoints")
    
    # Embedding Settings
    EMBEDDING_MODEL: str = Field(default="BAAI/bge-small-en-v1.5", description="HuggingFace embedding model or sentence-transformers model")
    EMBEDDING_BATCH_SIZE: int = Field(default=8, description="Batch size for generating embeddings")
    
    # Storage Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    CHROMA_PERSIST_DIRECTORY: str = Field(default=os.path.join(BASE_DIR, "..", "data", "vector_store"))
    UPLOAD_DIRECTORY: str = Field(default=os.path.join(BASE_DIR, "..", "data", "uploads"))
    SAMPLE_DOCS_DIRECTORY: str = Field(default=os.path.join(BASE_DIR, "..", "data", "sample_docs"))
    
    # RAG Settings
    CHUNK_SIZE: int = Field(default=800, description="Target character length of text chunks")
    CHUNK_OVERLAP: int = Field(default=150, description="Overlap character length between chunks")
    TOP_K: int = Field(default=5, description="Number of top chunks to retrieve")
    SIMILARITY_THRESHOLD: float = Field(default=0.35, description="Minimum cosine similarity / normalized score to accept chunk")
    ENABLE_RERANKING: bool = Field(default=False, description="Enable cross-encoder reranker if true")
    RERANKER_MODEL: str = Field(default="cross-encoder/ms-marco-MiniLM-L-6-v2", description="Cross-encoder model for reranking")
    MAX_DOCUMENTS_PER_SESSION: int = Field(default=50, description="Maximum number of PDF documents allowed per session")
    MAX_FILE_SIZE_MB: int = Field(default=50, description="Maximum allowed PDF file size in MB")
    
    # CORS
    ALLOWED_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000",
            "https://documind-api-olive.vercel.app",
            "*"
        ]
    )
    
    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Ensure directories exist
os.makedirs(os.path.abspath(settings.CHROMA_PERSIST_DIRECTORY), exist_ok=True)
os.makedirs(os.path.abspath(settings.UPLOAD_DIRECTORY), exist_ok=True)
os.makedirs(os.path.abspath(settings.SAMPLE_DOCS_DIRECTORY), exist_ok=True)
