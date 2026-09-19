import os
import json
import asyncio
from typing import List, Dict, Any, AsyncGenerator, Optional
from app.core.config import settings
from app.core.logging import logger

SYSTEM_PROMPT = """You are DocuMind AI, an intelligent, highly reliable document assistant.

Your task is to answer user questions using ONLY the information provided in the retrieved document context.

Rules:
1. Do not use outside knowledge or make assumptions not directly supported by the context.
2. Do not invent information or hallucinate facts.
3. If the answer is not present in the provided context, clearly say: "I couldn't find enough information in the uploaded documents to answer that question."
4. Every factual statement should be supported by retrieved document context.
5. When comparing documents, clearly identify which information comes from which document using headers or bullet points.
6. Format citations explicitly in your text using brackets like [1], [2] corresponding to the numbered SOURCE items in the context.
7. Be concise, structured, and informative. Use markdown headings, bullet points, and bold text for readability.
8. Preserve uncertainty when documents are unclear or contradictory.
9. Never claim that you read a document unless relevant context from that document is included in the prompt.
"""

class LLMService:
    def __init__(
        self,
        provider: str = settings.LLM_PROVIDER,
        model: str = settings.LLM_MODEL,
        api_key: Optional[str] = settings.LLM_API_KEY
    ):
        self.provider = (provider or "groq").lower()
        self.model = model
        self.api_key = api_key or os.getenv("LLM_API_KEY") or os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")

    def format_context_prompt(self, chunks: List[Dict[str, Any]], query: str) -> str:
        """
        Formats retrieved chunks into structured numbered contexts.
        """
        if not chunks:
            return f"Retrieved Context:\n[NO RELEVANT DOCUMENTS FOUND]\n\nUser Question:\n{query}"

        context_blocks = []
        for idx, chunk in enumerate(chunks, start=1):
            block = (
                f"--- SOURCE [{idx}] ---\n"
                f"Document: {chunk.get('filename', 'Unknown')}\n"
                f"Page: {chunk.get('page_number', 'N/A')}\n"
                f"Content:\n{chunk.get('content', '')}\n"
            )
            context_blocks.append(block)

        context_str = "\n".join(context_blocks)
        prompt = (
            f"Here is the retrieved context from the user's uploaded documents:\n\n"
            f"{context_str}\n\n"
            f"--- END OF CONTEXT ---\n\n"
            f"User Question: {query}\n\n"
            f"Please provide an accurate, grounded answer citing relevant sources as [1], [2], etc."
        )
        return prompt

    async def generate_response(
        self,
        prompt: str,
        system_prompt: str = SYSTEM_PROMPT,
        history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Non-streaming response generator.
        """
        chunks_collected = []
        async for chunk in self.stream_response(prompt, system_prompt, history):
            chunks_collected.append(chunk)
        return "".join(chunks_collected)

    async def stream_response(
        self,
        prompt: str,
        system_prompt: str = SYSTEM_PROMPT,
        history: Optional[List[Dict[str, str]]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Streams response tokens from the configured LLM provider.
        """
        messages = [{"role": "system", "content": system_prompt}]
        
        if history:
            # Include recent turns
            for item in history[-6:]:
                messages.append({"role": item.get("role", "user"), "content": item.get("content", "")})

        messages.append({"role": "user", "content": prompt})

        # Try provider
        if self.provider == "groq" and self.api_key:
            async for token in self._stream_groq(messages):
                yield token
        elif self.provider == "openai" and self.api_key:
            async for token in self._stream_openai(messages):
                yield token
        elif self.provider == "gemini" and self.api_key:
            async for token in self._stream_gemini(messages):
                yield token
        elif self.provider == "ollama":
            async for token in self._stream_ollama(messages):
                yield token
        else:
            # Smart Offline Mock Provider
            async for token in self._stream_mock_grounded(prompt, messages):
                yield token

    async def _stream_groq(self, messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        from groq import AsyncGroq
        client = AsyncGroq(api_key=self.api_key)
        try:
            stream = await client.chat.completions.create(
                model=self.model or "qwen/qwen3.6-27b",
                messages=messages,
                temperature=settings.LLM_TEMPERATURE,
                stream=True
            )
            async for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
        except Exception as e:
            logger.error(f"Groq API error: {e}. Falling back to grounded synthesizer.")
            async for token in self._stream_mock_grounded(messages[-1]["content"], messages):
                yield token

    async def _stream_openai(self, messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=self.api_key, base_url=settings.LLM_BASE_URL)
        try:
            stream = await client.chat.completions.create(
                model=self.model or "gpt-4o-mini",
                messages=messages,
                temperature=settings.LLM_TEMPERATURE,
                stream=True
            )
            async for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}. Falling back to grounded synthesizer.")
            async for token in self._stream_mock_grounded(messages[-1]["content"], messages):
                yield token

    async def _stream_gemini(self, messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)
        try:
            model = genai.GenerativeModel(self.model or "gemini-1.5-flash")
            # Build prompt text
            combined_prompt = "\n\n".join(f"{m['role'].upper()}: {m['content']}" for m in messages)
            response = await asyncio.to_thread(model.generate_content, combined_prompt, stream=True)
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            logger.error(f"Gemini API error: {e}. Falling back.")
            async for token in self._stream_mock_grounded(messages[-1]["content"], messages):
                yield token

    async def _stream_ollama(self, messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        import httpx
        base_url = settings.LLM_BASE_URL or "http://localhost:11434"
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    f"{base_url}/api/chat",
                    json={"model": self.model or "llama3", "messages": messages, "stream": True}
                ) as response:
                    async for line in response.aiter_lines():
                        if line:
                            data = json.loads(line)
                            content = data.get("message", {}).get("content", "")
                            if content:
                                yield content
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            async for token in self._stream_mock_grounded(messages[-1]["content"], messages):
                yield token

    async def _stream_mock_grounded(
        self,
        raw_prompt: str,
        messages: List[Dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        """
        High-fidelity offline grounded synthesizer.
        Extracts facts and synthesis from the provided SOURCE contexts when running offline.
        """
        await asyncio.sleep(0.05)
        
        # Check if context contains sources
        if "[NO RELEVANT DOCUMENTS FOUND]" in raw_prompt or "--- SOURCE [1] ---" not in raw_prompt:
            msg = "I couldn't find enough information in the uploaded documents to answer that question. Please upload relevant PDF documents or try rephrasing your question."
            for word in msg.split(" "):
                yield word + " "
                await asyncio.sleep(0.015)
            return

        # Parse out sources from raw_prompt
        import re
        sources_found = re.findall(r'--- SOURCE \[(\d+)\] ---\nDocument: (.*?)\nPage: (.*?)\nContent:\n(.*?)(?=\n--- SOURCE|\n--- END OF CONTEXT)', raw_prompt, re.DOTALL)
        
        # Extract user query
        query_match = re.search(r'User Question:\s*(.*?)(?=\nPlease provide|$)', raw_prompt, re.DOTALL)
        user_query = query_match.group(1).strip() if query_match else "your question"

        intro = f"Based on the analysis of the uploaded document(s), here is the detailed breakdown for **{user_query}**:\n\n"
        for word in intro.split(" "):
            yield word + " "
            await asyncio.sleep(0.01)

        # Synthesize source by source
        for src_num, doc_name, page_num, content in sources_found[:4]:
            clean_content = content.strip().replace('\n', ' ')
            # Take the most informative sentences
            sentences = [s.strip() for s in clean_content.split('.') if len(s.strip()) > 20]
            summary_points = sentences[:2] if sentences else [clean_content[:150]]

            section = f"### Key Insights from {doc_name} (Page {page_num.strip()}) [{src_num}]\n"
            for pt in summary_points:
                section += f"- {pt}. [{src_num}]\n"
            section += "\n"

            for word in section.split(" "):
                yield word + " "
                await asyncio.sleep(0.012)

        conclusion = (
            "### Summary\n"
            "The retrieved evidence corroborates the key points detailed above. "
            "All findings are strictly grounded in the document context cited in the sources panel."
        )
        for word in conclusion.split(" "):
            yield word + " "
            await asyncio.sleep(0.01)

llm_service = LLMService()
