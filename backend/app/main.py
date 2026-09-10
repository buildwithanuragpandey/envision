from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.logging import logger
from app.api.routes import documents, chat, health

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}...")
    logger.info(f"Active LLM Provider: {settings.LLM_PROVIDER} | Model: {settings.LLM_MODEL}")
    logger.info(f"Embedding Model: {settings.EMBEDDING_MODEL}")
    logger.info(f"Vector Store Directory: {settings.CHROMA_PERSIST_DIRECTORY}")
    try:
        from app.services.embedding_service import embedding_service
        embedding_service._get_model()
    except Exception as e:
        logger.warning(f"Could not pre-warm embedding model: {e}")
    yield
    logger.info("Shutting down DocuMind AI...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Multi-PDF RAG Intelligence Assistant API with ChromaDB, PyMuPDF, and Multi-LLM support.",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(documents.router, prefix=settings.API_PREFIX)
app.include_router(chat.router, prefix=settings.API_PREFIX)
app.include_router(health.router, prefix=settings.API_PREFIX)

@app.api_route("/", methods=["GET", "HEAD"])
def root():
    return {
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs_url": "/docs",
        "api_prefix": settings.API_PREFIX
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
