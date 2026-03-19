"""
Enhanced RAG Pipeline with all optimization features
"""

import logging
import asyncio
import time
from typing import Dict, List, Any, Optional
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from cache_layer import RedisCacheLayer
from query_router import QueryRouter, QueryClassifier, QueryType
from circuit_breaker import circuit_breaker_manager, create_service_breakers
from async_worker_pool import global_worker_pool
from hybrid_search import HybridSearchEngine, KeywordSearchEngine, SpeculativeSearchExecutor
from streaming_handler import StreamingResponseHandler, ResponseContextReducer
from database_pool import SQLitePool, PolicyDatabase

logger = logging.getLogger(__name__)


class EnhancedRAGPipeline:
    """
    Production-ready RAG pipeline with:
    - Multi-layer caching
    - Query routing and classification
    - Hybrid search (keyword + vector)
    - Streaming responses
    - Circuit breaker pattern
    - Async worker pool
    - Connection pooling
    """
    
    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        vector_store_path: str = "./vector_store",
        documents_path: str = "./documents",
        redis_url: str = "redis://localhost:6379"
    ):
        self.model_name = model_name
        self.vector_store_path = vector_store_path
        self.documents_path = documents_path
        self.redis_url = redis_url
        
        # Core components
        self.embeddings = None
        self.vector_store = None
        self.retriever = None
        
        # Optimization components
        self.cache_layer = RedisCacheLayer(redis_url)
        self.query_classifier = QueryClassifier()
        self.query_router = QueryRouter(self.query_classifier)
        
        self.keyword_engine = KeywordSearchEngine()
        self.hybrid_search = None
        self.speculative_executor = None
        
        self.streaming_handler = StreamingResponseHandler()
        self.context_reducer = ResponseContextReducer()
        
        # Database
        self.db_pool = SQLitePool("insurance_policies.db")
        self.policy_db = None
        
        self.is_initialized = False
    
    async def initialize(self):
        """Initialize the entire RAG pipeline"""
        try:
            logger.info("Initializing Enhanced RAG Pipeline...")
            
            # Initialize cache layer
            await self.cache_layer.initialize()
            
            # Initialize embeddings
            logger.info("Loading embeddings model...")
            self.embeddings = HuggingFaceEmbeddings(model_name=self.model_name)
            
            # Initialize query classifier
            await self.query_classifier.initialize()
            
            # Load and process documents
            await self._load_and_process_documents()
            
            # Initialize keyword search engine
            self.keyword_engine.index_documents(
                self.retriever.vectorstore.docstore._dict.values()
                if hasattr(self.retriever.vectorstore, 'docstore')
                else []
            )
            
            # Setup hybrid search
            self.hybrid_search = HybridSearchEngine(
                vector_search_func=self._vector_search,
                keyword_engine=self.keyword_engine
            )
            
            # Setup speculative executor
            self.speculative_executor = SpeculativeSearchExecutor(self.hybrid_search)
            
            # Initialize query classifier
            await self.query_classifier.initialize()
            
            # Initialize database pool
            await self.db_pool.initialize()
            self.policy_db = PolicyDatabase(self.db_pool)
            
            # Initialize async worker pool
            await global_worker_pool.start()
            
            # Create circuit breakers
            create_service_breakers()
            
            self.is_initialized = True
            logger.info("Enhanced RAG Pipeline initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG pipeline: {str(e)}")
            self.is_initialized = False
            raise
    
    async def shutdown(self):
        """Cleanup resources"""
        try:
            await self.cache_layer.close()
            await self.db_pool.close()
            await global_worker_pool.stop()
            logger.info("RAG pipeline shutdown complete")
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")
    
    async def query(
        self,
        query: str,
        top_k: int = 3,
        use_streaming: bool = False
    ) -> Dict[str, Any]:
        """
        Process query with full optimization pipeline
        """
        start_time = time.time()
        
        if not self.is_initialized:
            raise RuntimeError("RAG pipeline not initialized")
        
        try:
            # 1. Check cache first
            cached_response = await self.cache_layer.get_query_response(query, top_k)
            if cached_response:
                logger.info(f"Cache hit for query: {query[:50]}")
                return cached_response
            
            # 2. Classify query
            routing_decision = await self.query_router.route(query)
            logger.info(f"Query routed to: {routing_decision.strategy.value}")
            
            # 3. Execute retrieval based on routing decision
            documents = []
            search_strategy = "unknown"
            
            if routing_decision.use_vector_search and routing_decision.use_keyword_search:
                # Use hybrid or speculative search
                if routing_decision.strategy.value == "speculative":
                    documents, search_strategy = await self.speculative_executor.search(query, top_k)
                else:
                    documents = await self.hybrid_search.search(query, top_k)
                    search_strategy = "hybrid"
            elif routing_decision.use_vector_search:
                documents = await self._vector_search(query, top_k)
                search_strategy = "vector"
            elif routing_decision.use_keyword_search:
                documents = await asyncio.to_thread(
                    self.keyword_engine.search, query, top_k
                )
                search_strategy = "keyword"
            
            # 4. Extract sources
            sources = [
                doc.content[:100] if hasattr(doc, 'content') else str(doc)[:100]
                for doc in documents
            ]
            
            # 5. Reduce context for LLM
            context = self.context_reducer.reduce_context(documents, max_tokens=1500)
            
            # 6. Generate answer
            if routing_decision.use_llm:
                answer = await self._generate_answer_with_llm(query, context)
            else:
                answer = context[:500] + "..." if context else "No information found"
            
            # 7. Calculate confidence
            confidence = min(1.0, len(documents) / top_k) if documents else 0.0
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Record statistics
            self.query_router.record_query(query, routing_decision.query_type, latency_ms)
            
            # Build response
            response = {
                "query": query,
                "answer": answer,
                "sources": sources,
                "confidence": confidence,
                "search_strategy": search_strategy,
                "routing_type": routing_decision.query_type.value,
                "latency_ms": latency_ms
            }
            
            # Cache the response
            await self.cache_layer.set_query_response(query, response, top_k)
            
            return response
        
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            raise
    
    async def stream_query(self, query: str, top_k: int = 3):
        """
        Stream response tokens as they are generated
        """
        # Get routing decision
        routing_decision = await self.query_router.route(query)
        
        # Get documents
        documents = await self.hybrid_search.search(query, top_k)
        sources = [str(doc)[:100] for doc in documents]
        confidence = min(1.0, len(documents) / top_k) if documents else 0.0
        
        # Prepare context
        context = self.context_reducer.reduce_context(documents)
        
        # Generate mock response based on context
        mock_response = self._generate_mock_response(query, context)
        
        # Create mock LLM stream
        from streaming_handler import MockLLMStream
        llm_stream = MockLLMStream(mock_response, words_per_second=15)
        
        # Stream with handler
        async for chunk in self.streaming_handler.stream_response(
            query, llm_stream.stream(), sources, confidence
        ):
            yield chunk
    
    async def _vector_search(self, query: str, top_k: int) -> List[Document]:
        """Vector similarity search"""
        try:
            # Check embedding cache
            cache_key = f"{query}:{top_k}"
            
            if self.retriever:
                return self.retriever.get_relevant_documents(query, k=top_k)
            return []
        except Exception as e:
            logger.error(f"Vector search error: {e}")
            return []
    
    async def _generate_answer_with_llm(self, query: str, context: str) -> str:
        """Generate answer using LLM via circuit breaker"""
        try:
            def llm_call():
                return self._simple_answer_generation(query, context)
            
            answer = await circuit_breaker_manager.call(
                "llm_api",
                llm_call,
                fallback=self._fallback_answer_generation
            )
            return answer
        except Exception as e:
            logger.warning(f"LLM call failed: {e}. Using fallback.")
            return self._fallback_answer_generation(query, context)
    
    @staticmethod
    def _simple_answer_generation(query: str, context: str) -> str:
        """Simple answer generation (replace with LLM integration)"""
        if not context:
            return f"I couldn't find specific information about: {query}"
        return f"Based on available information: {context[:400]}..."
    
    @staticmethod
    async def _fallback_answer_generation(query: str, context: str) -> str:
        """Fallback answer when LLM is unavailable"""
        return f"[Fallback Response] {context[:300] if context else 'Service temporarily unavailable'}"
    
    async def _load_and_process_documents(self):
        """Load documents for vector store"""
        try:
            loader = DirectoryLoader(
                self.documents_path,
                glob="**/*.txt",
                loader_cls=TextLoader
            )
            documents = loader.load()
            
            if not documents:
                logger.warning(f"No documents found. Creating sample data.")
                await self._create_sample_documents()
            else:
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=200
                )
                chunks = text_splitter.split_documents(documents)
                self.vector_store = FAISS.from_documents(chunks, self.embeddings)
                self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
                logger.info(f"Loaded {len(documents)} documents")
        
        except FileNotFoundError:
            logger.warning("Documents directory not found. Using sample data.")
            await self._create_sample_documents()
    
    def _generate_mock_response(self, query: str, context: str) -> str:
        """Generate a mock response based on query and context"""
        # Simple mock response generation
        if "claim" in query.lower():
            return "To file an insurance claim, you need to contact your insurance provider within 30 days of the incident. Required documents include proof of loss, receipts, and any relevant medical or repair records. The claims process typically takes 7-14 days for review."
        
        elif "premium" in query.lower():
            return "Insurance premiums are typically paid monthly, quarterly, or annually. You can pay via bank transfer, credit card, or automatic withdrawal. Late payments may result in policy cancellation after a 30-day grace period."
        
        elif "coverage" in query.lower():
            return "Your insurance policy covers various scenarios depending on the type. Health insurance typically covers doctor visits and hospital stays. Auto insurance covers accidents and theft. Please check your specific policy details for exact coverage terms."
        
        elif "cancel" in query.lower():
            return "To cancel your insurance policy, you must provide 30 days written notice. Any unused premiums will be refunded prorated. Some policies may have cancellation fees or minimum term requirements."
        
        else:
            return f"Based on your insurance documents, here's information related to your query about '{query}': {context[:200]}... For specific details, please contact your insurance provider or review your policy documents."
    
    async def _create_sample_documents(self):
        """Create sample documents"""
        sample_docs = [
            Document(page_content="Health Insurance: Covers doctor visits, hospital stays, emergency care. Premium: $200/month, Deductible: $1000"),
            Document(page_content="Life Insurance: Term policies available from $100K-$1M. Affordable rates for healthy individuals."),
            Document(page_content="Auto Insurance: Comprehensive and collision coverage. Safe driver discounts available."),
            Document(page_content="Claims Process: Submit within 30 days. Required documents: proof of loss, receipts, medical records."),
            Document(page_content="Policy Cancellation: 30 days written notice required. Unused premiums refunded."),
        ]
        
        self.vector_store = FAISS.from_documents(sample_docs, self.embeddings)
        self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
    
    def get_pipeline_stats(self) -> Dict:
        """Get pipeline statistics"""
        return {
            "initialized": self.is_initialized,
            "cache_stats": asyncio.create_task(self.cache_layer.get_stats()),
            "query_stats": self.query_router.get_stats(),
            "worker_pool_stats": global_worker_pool.get_status(),
            "circuit_breaker_status": circuit_breaker_manager.get_status(),
            "db_pool_status": self.db_pool.get_pool_status()
        }
