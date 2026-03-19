from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
from typing import List
from rag_pipeline import RAGPipeline

# Initialize FastAPI app
app = FastAPI(
    title="Insurance Portal RAG API",
    description="RAG-based AI application for insurance queries",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize RAG pipeline
rag_pipeline = RAGPipeline()

# Request/Response models
class QueryRequest(BaseModel):
    query: str
    top_k: int = 3

class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[str]
    confidence: float

class HealthResponse(BaseModel):
    status: str
    message: str

@app.on_event("startup")
async def startup_event():
    """Initialize RAG pipeline on startup"""
    try:
        logger.info("Initializing RAG pipeline...")
        await rag_pipeline.initialize()
        logger.info("RAG pipeline initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize RAG pipeline: {str(e)}")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        is_ready = rag_pipeline.is_initialized
        return HealthResponse(
            status="healthy" if is_ready else "initializing",
            message="RAG pipeline is ready" if is_ready else "RAG pipeline is being initialized"
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail=str(e))

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process user query through RAG pipeline
    
    Args:
        request: QueryRequest containing the user's query
        
    Returns:
        QueryResponse with answer, sources, and confidence score
    """
    try:
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        logger.info(f"Processing query: {request.query}")
        
        # Get response from RAG pipeline
        result = await rag_pipeline.query(
            query=request.query,
            top_k=request.top_k
        )
        
        return QueryResponse(
            query=request.query,
            answer=result["answer"],
            sources=result["sources"],
            confidence=result["confidence"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Insurance Portal RAG API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "query": "/query (POST)",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
