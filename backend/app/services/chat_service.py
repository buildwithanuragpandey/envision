import time
import json
from typing import List, Dict, Any, AsyncGenerator, Optional
from app.core.config import settings
from app.core.logging import logger
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    SourceCitation,
    DebugInfo
)
from app.services.retrieval_service import retrieval_service
from app.services.llm_service import llm_service

class ChatService:
    @staticmethod
    def contextualize_query(query: str, history: Optional[List[Any]]) -> str:
        """
        If follow-up question references previous turn (e.g. 'explain the second finding', 'what about the first one?'),
        enriches the query with context from previous assistant response.
        """
        if not history or len(history) < 2:
            return query

        last_user = ""
        last_assistant = ""
        for item in reversed(history):
            role = getattr(item, "role", item.get("role", "")) if not isinstance(item, dict) else item.get("role", "")
            content = getattr(item, "content", item.get("content", "")) if not isinstance(item, dict) else item.get("content", "")
            if role == "assistant" and not last_assistant:
                last_assistant = content
            elif role == "user" and not last_user:
                last_user = content

        # Check for pronouns or follow-up indicators
        follow_up_triggers = ["it", "this", "that", "the second", "the first", "explain more", "what about", "why", "elaborate"]
        query_lower = query.lower()
        
        if any(trigger in query_lower for trigger in follow_up_triggers) and last_user:
            # Combine previous topic with new query
            return f"{query} (Context: in reference to '{last_user[:100]}')"
        return query

    async def answer_question(self, request: ChatRequest) -> ChatResponse:
        """
        Standard non-streaming RAG query handler.
        """
        total_start = time.perf_counter()
        
        # 1. Query contextualization
        effective_query = self.contextualize_query(request.message, request.history)

        # 2. Retrieval
        chunks, citations, confidence, retrieval_latency_ms = retrieval_service.retrieve_context(
            query=effective_query,
            document_ids=request.document_ids,
            top_k=request.top_k
        )

        # 3. Anti-Hallucination Guardrail Check
        if not chunks or (confidence < settings.SIMILARITY_THRESHOLD and len(chunks) == 0):
            total_latency = (time.perf_counter() - total_start) * 1000.0
            return ChatResponse(
                answer="I couldn't find enough relevant information in the uploaded documents to answer that question. Try asking the question differently or upload a document containing this information.",
                sources=[],
                confidence=confidence,
                is_grounded=False,
                debug_info=DebugInfo(
                    retrieval_latency_ms=retrieval_latency_ms,
                    generation_latency_ms=0.0,
                    total_latency_ms=total_latency,
                    retrieved_chunks_count=0,
                    reformulated_query=effective_query if effective_query != request.message else None,
                    similarity_scores=[],
                    llm_provider=settings.LLM_PROVIDER,
                    llm_model=settings.LLM_MODEL
                )
            )

        # 4. Prompt Assembly & Generation
        prompt = llm_service.format_context_prompt(chunks, effective_query)
        gen_start = time.perf_counter()
        
        history_dicts = [
            {"role": h.role, "content": h.content}
            for h in (request.history or [])
        ]
        
        answer = await llm_service.generate_response(prompt, history=history_dicts)
        gen_latency_ms = (time.perf_counter() - gen_start) * 1000.0
        total_latency_ms = (time.perf_counter() - total_start) * 1000.0

        return ChatResponse(
            answer=answer,
            sources=citations,
            confidence=round(confidence, 3),
            is_grounded=True,
            debug_info=DebugInfo(
                retrieval_latency_ms=round(retrieval_latency_ms, 2),
                generation_latency_ms=round(gen_latency_ms, 2),
                total_latency_ms=round(total_latency_ms, 2),
                retrieved_chunks_count=len(chunks),
                reformulated_query=effective_query if effective_query != request.message else None,
                similarity_scores=[round(c.get("similarity", 0.0), 3) for c in chunks],
                llm_provider=settings.LLM_PROVIDER,
                llm_model=settings.LLM_MODEL
            )
        )

    async def stream_chat(self, request: ChatRequest) -> AsyncGenerator[str, None]:
        """
        Streams SSE events for real-time UI typing animation and source citations.
        Event types:
          - {"type": "debug", "data": {...}}
          - {"type": "token", "data": "..."}
          - {"type": "sources", "data": [...]}
          - {"type": "done", "data": {...}}
        """
        total_start = time.perf_counter()
        
        effective_query = self.contextualize_query(request.message, request.history)

        chunks, citations, confidence, retrieval_latency_ms = retrieval_service.retrieve_context(
            query=effective_query,
            document_ids=request.document_ids,
            top_k=request.top_k
        )

        # Emit citations early so UI source panel updates immediately
        citations_data = [c.model_dump() for c in citations]
        yield f"event: sources\ndata: {json.dumps(citations_data)}\n\n"

        if not chunks or (confidence < settings.SIMILARITY_THRESHOLD and len(chunks) == 0):
            msg = "I couldn't find enough relevant information in the uploaded documents to answer that question. Try asking the question differently or upload a document containing this information."
            for word in msg.split(" "):
                yield f"event: token\ndata: {json.dumps(word + ' ')}\n\n"
            
            total_latency = (time.perf_counter() - total_start) * 1000.0
            done_payload = {
                "confidence": confidence,
                "is_grounded": False,
                "debug_info": {
                    "retrieval_latency_ms": round(retrieval_latency_ms, 2),
                    "generation_latency_ms": 0.0,
                    "total_latency_ms": round(total_latency, 2),
                    "retrieved_chunks_count": 0,
                    "llm_provider": settings.LLM_PROVIDER,
                    "llm_model": settings.LLM_MODEL
                }
            }
            yield f"event: done\ndata: {json.dumps(done_payload)}\n\n"
            return

        # Prompt formatting & streaming tokens
        prompt = llm_service.format_context_prompt(chunks, effective_query)
        gen_start = time.perf_counter()
        
        history_dicts = [
            {"role": h.role, "content": h.content}
            for h in (request.history or [])
        ]

        async for token in llm_service.stream_response(prompt, history=history_dicts):
            yield f"event: token\ndata: {json.dumps(token)}\n\n"

        gen_latency_ms = (time.perf_counter() - gen_start) * 1000.0
        total_latency_ms = (time.perf_counter() - total_start) * 1000.0

        done_payload = {
            "confidence": round(confidence, 3),
            "is_grounded": True,
            "debug_info": {
                "retrieval_latency_ms": round(retrieval_latency_ms, 2),
                "generation_latency_ms": round(gen_latency_ms, 2),
                "total_latency_ms": round(total_latency_ms, 2),
                "retrieved_chunks_count": len(chunks),
                "reformulated_query": effective_query if effective_query != request.message else None,
                "similarity_scores": [round(c.get("similarity", 0.0), 3) for c in chunks],
                "llm_provider": settings.LLM_PROVIDER,
                "llm_model": settings.LLM_MODEL
            }
        }
        yield f"event: done\ndata: {json.dumps(done_payload)}\n\n"

chat_service = ChatService()
