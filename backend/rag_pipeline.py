import logging
from typing import Dict, List, Any
from abc import ABC, abstractmethod
import asyncio
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain.chains import RetrievalQA

logger = logging.getLogger(__name__)

class RAGPipeline:
    """
    Retrieval-Augmented Generation Pipeline for processing queries
    """
    
    def __init__(self, 
                 model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
                 vector_store_path: str = "./vector_store",
                 documents_path: str = "./documents"):
        """
        Initialize RAG Pipeline
        
        Args:
            model_name: Name of the embedding model from HuggingFace
            vector_store_path: Path to store vector database
            documents_path: Path to source documents
        """
        self.model_name = model_name
        self.vector_store_path = vector_store_path
        self.documents_path = documents_path
        
        self.embeddings = None
        self.vector_store = None
        self.retriever = None
        self.qa_chain = None
        self.is_initialized = False
    
    async def initialize(self):
        """Initialize the RAG pipeline components"""
        try:
            logger.info("Initializing embeddings model...")
            self.embeddings = HuggingFaceEmbeddings(model_name=self.model_name)
            
            logger.info("Loading and processing documents...")
            await self._load_documents()
            
            self.is_initialized = True
            logger.info("RAG pipeline initialization complete")
        except Exception as e:
            logger.error(f"Failed to initialize RAG pipeline: {str(e)}")
            self.is_initialized = False
            raise
    
    async def _load_documents(self):
        """Load documents from the documents directory"""
        try:
            # Try to load from documents directory
            loader = DirectoryLoader(
                self.documents_path, 
                glob="**/*.txt",
                loader_cls=TextLoader
            )
            documents = loader.load()
            
            if not documents:
                logger.warning(f"No documents found in {self.documents_path}")
                # Create a sample vector store with dummy data
                await self._create_sample_vector_store()
            else:
                # Split documents into chunks
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=200
                )
                chunks = text_splitter.split_documents(documents)
                
                # Create vector store
                self.vector_store = FAISS.from_documents(chunks, self.embeddings)
                self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
                logger.info(f"Loaded {len(documents)} documents and created vector store")
        except FileNotFoundError:
            logger.warning(f"Documents directory not found at {self.documents_path}")
            await self._create_sample_vector_store()
        except Exception as e:
            logger.error(f"Error loading documents: {str(e)}")
            await self._create_sample_vector_store()
    
    async def _create_sample_vector_store(self):
        """Create a sample vector store with dummy insurance data"""
        from langchain.schema import Document
        
        sample_docs = [
            Document(page_content="Insurance Coverage: Our basic health insurance covers doctor visits, hospital stays, and emergency care. Premium is $200/month with a $1000 deductible."),
            Document(page_content="Life Insurance Options: We offer term life insurance with coverage from $100,000 to $1,000,000. Get a free quote today."),
            Document(page_content="Auto Insurance: Comprehensive and collision coverage available. Discounts for safe drivers and bundled policies."),
            Document(page_content="Claim Process: Submit claims within 30 days of incident. Required documents: proof of loss, receipts, and medical records for health claims."),
            Document(page_content="Policy Cancellation: You can cancel anytime with 30 days written notice. Unused premiums will be refunded."),
        ]
        
        self.vector_store = FAISS.from_documents(sample_docs, self.embeddings)
        self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
        logger.info("Created sample vector store with dummy insurance data")
    
    async def query(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        """
        Process a query through the RAG pipeline
        
        Args:
            query: User's query string
            top_k: Number of top documents to retrieve
            
        Returns:
            Dictionary containing answer, sources, and confidence
        """
        if not self.is_initialized:
            raise RuntimeError("RAG pipeline not initialized. Call initialize() first.")
        
        try:
            # Update retriever search parameters
            self.retriever.search_kwargs = {"k": top_k}
            
            # Retrieve relevant documents
            docs = self.retriever.get_relevant_documents(query)
            
            # Extract sources
            sources = [doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content 
                      for doc in docs]
            
            # Generate answer using RAG approach
            answer = await self._generate_answer(query, docs)
            
            # Calculate confidence based on retrieval scores
            confidence = min(1.0, len(docs) / top_k) if docs else 0.0
            
            return {
                "answer": answer,
                "sources": sources,
                "confidence": confidence
            }
        
        except Exception as e:
            logger.error(f"Error in query processing: {str(e)}")
            raise
    
    async def _generate_answer(self, query: str, documents: List) -> str:
        """
        Generate answer based on retrieved documents
        Use a simple approach - can be replaced with LLM integration
        """
        # For now, return a formatted response based on retrieved documents
        if not documents:
            return f"No relevant information found for: {query}"
        
        # Combine document contents
        context = "\n\n".join([doc.page_content for doc in documents])
        
        # Simple response generation (can be replaced with LLM)
        answer = f"Based on available information: {context[:500]}..."
        
        return answer
    
    def add_documents(self, documents: List[str]):
        """
        Add new documents to the vector store
        
        Args:
            documents: List of document strings
        """
        if not self.is_initialized:
            raise RuntimeError("RAG pipeline not initialized")
        
        try:
            from langchain.schema import Document
            
            doc_objects = [Document(page_content=doc) for doc in documents]
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            chunks = text_splitter.split_documents(doc_objects)
            
            # Add to existing vector store
            if hasattr(self.vector_store, 'add_documents'):
                self.vector_store.add_documents(chunks)
            else:
                self.vector_store = FAISS.from_documents(chunks, self.embeddings)
            
            self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
            logger.info(f"Added {len(documents)} new documents to vector store")
        except Exception as e:
            logger.error(f"Error adding documents: {str(e)}")
            raise
