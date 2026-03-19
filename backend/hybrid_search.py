"""
Hybrid Search Implementation
Combines keyword search and vector similarity search for better results
"""

import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import asyncio
import json

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Result from search operation"""
    content: str
    score: float
    source: str
    search_type: str
    metadata: Dict = None


class KeywordSearchEngine:
    """Simple keyword-based search engine"""
    
    def __init__(self):
        self.documents: List[Document] = []
        self.inverted_index: Dict[str, List[Tuple[int, int]]] = {}  # word -> [(doc_idx, positions)]
    
    def index_documents(self, documents: List[Document]):
        """Build inverted index from documents"""
        self.documents = documents
        self.inverted_index = {}
        
        for doc_idx, doc in enumerate(documents):
            words = doc.page_content.lower().split()
            for pos, word in enumerate(words):
                # Normalize word (remove punctuation, etc)
                clean_word = ''.join(c for c in word if c.isalnum())
                
                if clean_word:
                    if clean_word not in self.inverted_index:
                        self.inverted_index[clean_word] = []
                    self.inverted_index[clean_word].append((doc_idx, pos))
    
    def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """Search documents using keywords"""
        query_words = [w.lower() for w in query.split()]
        query_words = [''.join(c for c in w if c.isalnum()) for w in query_words]
        query_words = [w for w in query_words if w]
        
        if not query_words or not self.documents:
            return []
        
        # Calculate relevance scores for each document
        doc_scores: Dict[int, float] = {}
        
        for word in query_words:
            if word in self.inverted_index:
                positions = self.inverted_index[word]
                for doc_idx, pos in positions:
                    if doc_idx not in doc_scores:
                        doc_scores[doc_idx] = 0
                    # Score based on word frequency (position closer to start = higher)
                    doc_scores[doc_idx] += 1.0 / (pos + 1)
        
        # Sort by score
        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        
        results = []
        for doc_idx, score in sorted_docs:
            doc = self.documents[doc_idx]
            results.append(SearchResult(
                content=doc.page_content,
                score=min(score / len(query_words), 1.0),  # Normalize score
                source=doc.metadata.get("source", "unknown") if doc.metadata else "unknown",
                search_type="keyword",
                metadata=doc.metadata
            ))
        
        return results


class HybridSearchEngine:
    """Combines keyword and vector search"""
    
    def __init__(self, vector_search_func, keyword_engine: KeywordSearchEngine):
        self.vector_search_func = vector_search_func
        self.keyword_engine = keyword_engine
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        keyword_weight: float = 0.3,
        vector_weight: float = 0.7
    ) -> List[SearchResult]:
        """
        Hybrid search combining keyword and vector search
        """
        
        # Run searches in parallel
        keyword_task = asyncio.to_thread(
            self.keyword_engine.search, query, top_k * 2
        )
        vector_task = asyncio.to_thread(
            self.vector_search_func, query, top_k * 2
        )
        
        keyword_results, vector_results = await asyncio.gather(
            keyword_task, vector_task,
            return_exceptions=True
        )
        
        # Handle errors gracefully
        if isinstance(keyword_results, Exception):
            logger.warning(f"Keyword search failed: {keyword_results}")
            keyword_results = []
        
        if isinstance(vector_results, Exception):
            logger.warning(f"Vector search failed: {vector_results}")
            vector_results = []
        
        # Combine and deduplicate results
        combined: Dict[str, SearchResult] = {}
        
        # Add keyword results
        for result in keyword_results:
            key = result.content[:100]  # Use content hash as key
            if key not in combined:
                combined[key] = result
                combined[key].score *= keyword_weight
            else:
                # Average scores if duplicate
                combined[key].score = (combined[key].score + result.score * keyword_weight) / 2
        
        # Add vector results
        for result in vector_results:
            key = result.content[:100]
            if key not in combined:
                combined[key] = result
                combined[key].score *= vector_weight
                combined[key].search_type = "hybrid"
            else:
                # Average scores if duplicate
                combined[key].score = (combined[key].score + result.score * vector_weight) / 2
                combined[key].search_type = "hybrid"
        
        # Sort by combined score
        results = sorted(combined.values(), key=lambda x: x.score, reverse=True)[:top_k]
        
        logger.info(f"Hybrid search returned {len(results)} results")
        return results
    
    def get_index_stats(self) -> Dict:
        """Get statistics about indexed documents"""
        return {
            "total_documents": len(self.keyword_engine.documents),
            "inverted_index_size": len(self.keyword_engine.inverted_index),
            "unique_terms": len(self.keyword_engine.inverted_index)
        }


class SpeculativeSearchExecutor:
    """Executes multiple search strategies in parallel and returns fastest result"""
    
    def __init__(self, hybrid_search_engine: HybridSearchEngine):
        self.hybrid_engine = hybrid_search_engine
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        timeout: int = 5
    ) -> Tuple[List[SearchResult], str]:
        """
        Execute multiple search strategies in parallel
        Returns results from the fastest one
        """
        
        # Strategy 1: Keyword-only (fastest)
        keyword_only = asyncio.create_task(
            asyncio.to_thread(
                self.hybrid_engine.keyword_engine.search, query, top_k
            )
        )
        
        # Strategy 2: Vector search
        vector_task = asyncio.create_task(
            asyncio.to_thread(
                self.hybrid_engine.vector_search_func, query, top_k
            )
        )
        
        # Strategy 3: Hybrid search
        hybrid_task = asyncio.create_task(
            self.hybrid_engine.search(query, top_k)
        )
        
        # Wait for any result
        done, pending = await asyncio.wait(
            [keyword_only, vector_task, hybrid_task],
            timeout=timeout,
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # Cancel pending tasks
        for task in pending:
            task.cancel()
        
        if done:
            result = done.pop().result()
            
            # Determine which strategy succeeded
            if result is vector_task.result():
                strategy = "vector"
            elif result is hybrid_task.result():
                strategy = "hybrid"
            else:
                strategy = "keyword"
            
            logger.info(f"Speculative search completed using {strategy} strategy")
            return result, strategy
        
        logger.warning("Speculative search timed out")
        # Fallback to hybrid search
        return await self.hybrid_engine.search(query, top_k), "fallback"
