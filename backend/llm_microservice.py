"""
LLM Microservice
Separate service for LLM inference to enable independent scaling
Can be deployed as a separate service and called via API
"""

import logging
import asyncio
from typing import AsyncGenerator, Optional, Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json

logger = logging.getLogger(__name__)


class LLMRequest(BaseModel):
    """LLM inference request"""
    query: str
    context: str
    max_tokens: int = 500
    temperature: float = 0.7
    stream: bool = False


class LLMResponse(BaseModel):
    """LLM inference response"""
    query: str
    answer: str
    tokens_used: int
    latency_ms: float


class LLMStreamResponse(BaseModel):
    """Streaming LLM response chunk"""
    chunk: str
    is_final: bool = False


class LLMService:
    """LLM Inference Service"""
    
    def __init__(self, model_name: str = "gpt2"):
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.is_initialized = False
    
    async def initialize(self):
        """Initialize the LLM model"""
        try:
            from transformers import pipeline
            
            logger.info(f"Loading LLM model: {self.model_name}")
            self.model = pipeline(
                "text-generation",
                model=self.model_name,
                device=-1  # CPU
            )
            self.is_initialized = True
            logger.info(f"LLM model {self.model_name} loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load LLM model: {e}")
            self.is_initialized = False
            raise
    
    async def generate(
        self,
        query: str,
        context: str,
        max_tokens: int = 500,
        temperature: float = 0.7
    ) -> str:
        """Generate response synchronously"""
        if not self.is_initialized:
            raise RuntimeError("LLM service not initialized")
        
        try:
            # Prepare prompt with context
            prompt = self._prepare_prompt(query, context)
            
            # Generate response
            result = await asyncio.to_thread(
                self.model,
                prompt,
                max_length=max_tokens,
                temperature=temperature,
                do_sample=True,
                num_return_sequences=1
            )
            
            answer = result[0]['generated_text'][len(prompt):].strip()
            return answer
        
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            raise
    
    async def stream_generate(
        self,
        query: str,
        context: str,
        max_tokens: int = 500,
        temperature: float = 0.7
    ) -> AsyncGenerator:
        """Generate response with streaming"""
        if not self.is_initialized:
            raise RuntimeError("LLM service not initialized")
        
        try:
            prompt = self._prepare_prompt(query, context)
            
            # Mock streaming (in production, use actual streaming LLM)
            response = await self.generate(query, context, max_tokens, temperature)
            
            # Split into words and stream
            words = response.split()
            for word in words:
                yield word + " "
                await asyncio.sleep(0.05)  # Simulate generation delay
        
        except Exception as e:
            logger.error(f"LLM streaming error: {e}")
            raise
    
    @staticmethod
    def _prepare_prompt(query: str, context: str) -> str:
        """Prepare prompt for the model"""
        return f"""Based on the following context, answer the question.

Context:
{context}

Question: {query}

Answer:"""
    
    def get_model_info(self) -> Dict:
        """Get information about loaded model"""
        return {
            "model_name": self.model_name,
            "is_initialized": self.is_initialized,
            "device": "CPU"
        }


class LLMMicroserviceApp:
    """FastAPI app for LLM microservice"""
    
    def __init__(self):
        self.app = FastAPI(
            title="LLM Inference Microservice",
            description="Separate microservice for LLM inference",
            version="1.0.0"
        )
        self.llm_service = LLMService()
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.app.on_event("startup")
        async def startup():
            """Initialize LLM on startup"""
            await self.llm_service.initialize()
        
        @self.app.post("/generate", response_model=LLMResponse)
        async def generate(request: LLMRequest):
            """Generate response from LLM"""
            import time
            start_time = time.time()
            
            try:
                answer = await self.llm_service.generate(
                    query=request.query,
                    context=request.context,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature
                )
                
                latency_ms = (time.time() - start_time) * 1000
                
                return LLMResponse(
                    query=request.query,
                    answer=answer,
                    tokens_used=len(answer.split()),  # Rough estimate
                    latency_ms=latency_ms
                )
            
            except Exception as e:
                logger.error(f"Generation error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/stream")
        async def stream(request: LLMRequest):
            """Stream response from LLM"""
            from fastapi.responses import StreamingResponse
            
            async def generate_stream():
                try:
                    async for chunk in self.llm_service.stream_generate(
                        query=request.query,
                        context=request.context,
                        max_tokens=request.max_tokens,
                        temperature=request.temperature
                    ):
                        yield chunk.encode() + b'\n'
                except Exception as e:
                    logger.error(f"Streaming error: {e}")
                    yield f"Error: {str(e)}".encode()
            
            return StreamingResponse(
                generate_stream(),
                media_type="text/event-stream"
            )
        
        @self.app.get("/health")
        async def health():
            """Health check"""
            return {
                "status": "healthy",
                "model_initialized": self.llm_service.is_initialized,
                "model_info": self.llm_service.get_model_info()
            }
        
        @self.app.post("/batch")
        async def batch_generate(requests: list[LLMRequest]):
            """Process multiple requests in batch"""
            results = []
            
            for request in requests:
                try:
                    answer = await self.llm_service.generate(
                        query=request.query,
                        context=request.context,
                        max_tokens=request.max_tokens,
                        temperature=request.temperature
                    )
                    
                    results.append({
                        "query": request.query,
                        "answer": answer,
                        "success": True
                    })
                except Exception as e:
                    results.append({
                        "query": request.query,
                        "error": str(e),
                        "success": False
                    })
            
            return results
    
    def get_app(self):
        """Get FastAPI app instance"""
        return self.app


# Standalone microservice runner
if __name__ == "__main__":
    import uvicorn
    
    microservice = LLMMicroserviceApp()
    uvicorn.run(
        microservice.get_app(),
        host="0.0.0.0",
        port=8001
    )
