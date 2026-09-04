from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import chat_service
from app.core.logging import logger

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    RAG Chat endpoint returning answer, source citations, confidence, and debug metrics.
    """
    try:
        response = await chat_service.answer_question(request)
        return response
    except Exception as e:
        logger.error(f"Error handling chat request: {e}")
        raise HTTPException(status_code=500, detail=f"Chat generation failed: {str(e)}")

@router.post("/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """
    Server-Sent Events (SSE) streaming chat endpoint for real-time typing and dynamic source attribution.
    """
    try:
        return StreamingResponse(
            chat_service.stream_chat(request),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    except Exception as e:
        logger.error(f"Error handling streaming chat request: {e}")
        raise HTTPException(status_code=500, detail=f"Streaming failed: {str(e)}")
