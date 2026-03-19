"""
Streaming Response Handler
Sends LLM tokens to client as they are generated in real-time
"""

import logging
import asyncio
from typing import AsyncGenerator, Optional
import json

logger = logging.getLogger(__name__)


class StreamingResponseHandler:
    """Handles streaming responses over HTTP"""
    
    def __init__(self):
        self.chunk_size = 50  # Characters per chunk
    
    async def stream_response(
        self,
        query: str,
        llm_generator: AsyncGenerator,
        sources: list,
        confidence: float
    ) -> AsyncGenerator:
        """
        Stream response tokens as they are generated
        Yields JSON chunks compatible with SSE (Server-Sent Events)
        """
        
        try:
            # Send initial metadata
            yield json.dumps({
                "type": "metadata",
                "query": query,
                "sources": sources,
                "confidence": confidence
            }) + "\n"
            
            # Stream the answer
            accumulated_text = ""
            
            async for token in llm_generator:
                accumulated_text += token
                
                # Send chunks of text
                if len(accumulated_text) >= self.chunk_size:
                    yield json.dumps({
                        "type": "content",
                        "chunk": accumulated_text[:self.chunk_size]
                    }) + "\n"
                    accumulated_text = accumulated_text[self.chunk_size:]
                
                # Yield control to allow other tasks to run
                await asyncio.sleep(0)
            
            # Send remaining text
            if accumulated_text:
                yield json.dumps({
                    "type": "content",
                    "chunk": accumulated_text
                }) + "\n"
            
            # Send completion signal
            yield json.dumps({
                "type": "end",
                "message": "Response complete"
            }) + "\n"
        
        except Exception as e:
            logger.error(f"Streaming error: {str(e)}")
            yield json.dumps({
                "type": "error",
                "error": str(e)
            }) + "\n"
    
    async def stream_file_response(self, file_path: str) -> AsyncGenerator:
        """Stream a file in chunks"""
        try:
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(1024 * 64)  # 64KB chunks
                    if not chunk:
                        break
                    yield chunk
                    await asyncio.sleep(0)
        except Exception as e:
            logger.error(f"File streaming error: {str(e)}")


class MockLLMStream:
    """Mock LLM stream generator for testing"""
    
    def __init__(self, text: str, words_per_second: int = 10):
        self.text = text
        self.words_per_second = words_per_second
    
    async def stream(self) -> AsyncGenerator:
        """Generate mock tokens"""
        words = self.text.split()
        delay = 1.0 / self.words_per_second
        
        for word in words:
            yield word + " "
            await asyncio.sleep(delay)


class ResponseCompressor:
    """Compress responses for faster transmission"""
    
    @staticmethod
    async def compress_response(response_data: dict, compression: str = "gzip") -> bytes:
        """Compress response using specified algorithm"""
        import gzip
        
        try:
            json_data = json.dumps(response_data).encode('utf-8')
            
            if compression == "gzip":
                compressed = gzip.compress(json_data, compresslevel=6)
                return compressed
            
            return json_data
        
        except Exception as e:
            logger.error(f"Compression error: {str(e)}")
            return json.dumps(response_data).encode('utf-8')


class ResponseContextReducer:
    """Reduce context size sent to LLM"""
    
    @staticmethod
    def reduce_context(
        documents: list,
        max_tokens: int = 2000,
        overlap: int = 100
    ) -> str:
        """
        Extract most relevant content from documents
        Respecting token limit
        """
        combined_content = ""
        token_count = 0
        
        # Sort documents by relevance score if available
        sorted_docs = sorted(
            documents,
            key=lambda x: getattr(x, 'score', 0),
            reverse=True
        )
        
        for doc in sorted_docs:
            content = doc.page_content if hasattr(doc, 'page_content') else str(doc)
            
            # Estimate tokens (roughly 4 chars per token)
            content_tokens = len(content) // 4
            
            if token_count + content_tokens <= max_tokens:
                combined_content += content + "\n\n"
                token_count += content_tokens
            else:
                # Add partial content to fit within limit
                remaining_tokens = max_tokens - token_count
                remaining_chars = remaining_tokens * 4
                combined_content += content[:remaining_chars]
                break
        
        return combined_content.strip()
    
    @staticmethod
    def chunk_context(
        context: str,
        chunk_size: int = 512,
        overlap: int = 100
    ) -> list:
        """Split context into overlapping chunks"""
        chunks = []
        start = 0
        
        while start < len(context):
            end = start + chunk_size
            chunk = context[start:end]
            chunks.append(chunk)
            start = end - overlap
        
        return chunks


class StreamingLLMHandler:
    """Handles streaming responses from LLM with proper formatting"""
    
    def __init__(self):
        self.compressor = ResponseCompressor()
        self.context_reducer = ResponseContextReducer()
    
    async def prepare_streaming_response(
        self,
        query: str,
        documents: list,
        confidence: float,
        include_sources: bool = True
    ) -> tuple:
        """
        Prepare streamed response with reduced context
        Returns metadata and reduced context
        """
        
        # Reduce context to most relevant parts
        reduced_context = self.context_reducer.reduce_context(
            documents,
            max_tokens=1500  # Limit context to 1500 tokens
        )
        
        metadata = {
            "query": query,
            "confidence": confidence,
            "context_size_chars": len(reduced_context),
            "num_sources": len(documents) if include_sources else 0
        }
        
        sources = []
        if include_sources:
            sources = [
                doc.page_content[:100] if hasattr(doc, 'page_content') else str(doc)[:100]
                for doc in documents
            ]
        
        return metadata, reduced_context, sources
