import os
from fastapi import APIRouter
from app.core.config import settings
from app.schemas.analytics import ProcessingAnalytics, HealthStatus
from app.services.vector_store_service import vector_store_service
from app.api.routes.documents import _load_registry

router = APIRouter(tags=["Health & Analytics"])

@router.get("/health", response_model=HealthStatus)
async def health_check():
    """
    Health check endpoint.
    """
    try:
        vector_count = vector_store_service.get_total_chunks()
        vs_status = f"healthy ({vector_count} chunks indexed)"
    except Exception as e:
        vs_status = f"unhealthy: {str(e)}"

    return HealthStatus(
        status="healthy",
        version=settings.VERSION,
        vector_store_status=vs_status,
        llm_provider_status=f"configured ({settings.LLM_PROVIDER} / {settings.LLM_MODEL})"
    )

@router.get("/analytics", response_model=ProcessingAnalytics)
async def get_analytics():
    """
    Returns session-level RAG analytics and document statistics.
    """
    registry = _load_registry()
    docs = list(registry.values())

    total_docs = len(docs)
    total_pages = sum(d.get("total_pages", 0) for d in docs)
    total_chunks = vector_store_service.get_total_chunks()
    indexed_docs = sum(1 for d in docs if d.get("status") == "Indexed")
    
    # Calculate storage size
    total_storage = sum(d.get("file_size_bytes", 0) for d in docs)

    return ProcessingAnalytics(
        total_documents=total_docs,
        total_pages=total_pages,
        total_chunks=total_chunks,
        indexed_documents=indexed_docs,
        storage_size_bytes=total_storage,
        active_llm_provider=settings.LLM_PROVIDER,
        active_llm_model=settings.LLM_MODEL,
        active_embedding_model=settings.EMBEDDING_MODEL
    )
