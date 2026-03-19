<<<<<<< HEAD
# AI-Powered Insurance Portal with RAG

A full-stack application featuring a React frontend and FastAPI backend with a Retrieval-Augmented Generation (RAG) pipeline for intelligent insurance query processing.

## 🎯 Features

- **RAG Pipeline**: Retrieves relevant information and generates contextual answers
- **FastAPI Backend**: High-performance REST API with async support
- **React Frontend**: Modern, responsive UI with real-time feedback
- **Vector Database**: FAISS for efficient document retrieval
- **Language Models**: Powered by Hugging Face embeddings and transformers
- **Health Monitoring**: Built-in API health checks
- **CORS Enabled**: Ready for cross-origin requests

## 📋 Project Structure

```
insurance_portal/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── rag_pipeline.py         # RAG pipeline implementation
│   ├── requirements.txt         # Python dependencies
│   ├── .env.example            # Environment variables template
│   └── documents/              # Place your documents here
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── styles/             # CSS modules
│   │   ├── App.js
│   │   └── index.js
│   └── package.json
├── README.md
└── .gitignore
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Node.js 16+
- Git

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file from the template:
   ```bash
   cp .env.example .env
   ```

5. Start the backend server:
   ```bash
   python main.py
   ```
   The API will be available at `http://localhost:8000`

6. Access API documentation at `http://localhost:8000/docs`

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```
   The frontend will open at `http://localhost:3000`

## 📚 Adding Documents

Place your insurance documents (PDF text, markdown, or plain text) in the `backend/documents/` directory:

```bash
mkdir -p backend/documents
# Add your document files here
```

The RAG pipeline will automatically load and process these documents.

## 🔗 API Endpoints

### Health Check
```
GET /health
```
Returns the current health status of the API.

### Process Query
```
POST /query
Content-Type: application/json

{
  "query": "What insurance plans do you offer?",
  "top_k": 3
}
```

Response:
```json
{
  "query": "What insurance plans do you offer?",
  "answer": "Based on available information...",
  "sources": ["Source 1...", "Source 2..."],
  "confidence": 0.85
}
```

## 🎨 Frontend Features

- **Query Input**: Natural language questions
- **Real-time Responses**: Instant feedback with loading indicators
- **Source Attribution**: See which documents were used
- **Confidence Indicator**: Visual representation of answer reliability
- **Responsive Design**: Works on desktop and mobile devices
- **API Status**: Live connection status indicator

## 🔧 Configuration

### Backend Environment Variables

Edit `backend/.env`:

```env
DATABASE_URL=sqlite:///./rag.db
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
LOG_LEVEL=INFO
VECTOR_STORE_PATH=./vector_store
```

### Frontend API URL

Update the API base URL in `frontend/src/App.js` if your backend is on a different host/port:

```javascript
const API_BASE_URL = 'http://localhost:8000';
```

## 📦 Dependencies

### Backend
- **FastAPI**: Web framework
- **LangChain**: LLM orchestration
- **FAISS**: Vector similarity search
- **sentence-transformers**: Embedding model
- **Pydantic**: Data validation

### Frontend
- **React 18**: UI library
- **Axios**: HTTP client
- **React Markdown**: Markdown rendering

## 🧪 Testing

### Test the API with curl

```bash
# Health check
curl http://localhost:8000/health

# Submit a query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What policies do you offer?", "top_k": 3}'
```

## 🐳 Docker Support (Optional)

Create `backend/Dockerfile`:

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Run with Docker:

```bash
docker build -t insurance-rag-api .
docker run -p 8000:8000 insurance-rag-api
```

## 🔍 Troubleshooting

### Backend won't start
- Check Python version (3.8+)
- Verify all dependencies installed: `pip install -r requirements.txt`
- Check port 8000 is not in use

### Frontend can't connect to backend
- Ensure backend is running on `http://localhost:8000`
- Check CORS configuration in `main.py`
- Review browser console for errors

### Missing embeddings model
- First run downloads the embedding model (requires internet)
- Subsequent runs use cached version
- Check disk space (model ~100MB)

## 📖 Learn More

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LangChain Documentation](https://python.langchain.com/)
- [React Documentation](https://react.dev/)
- [FAISS GitHub](https://github.com/facebookresearch/faiss)

## 📝 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Support

For issues and questions, please create an issue on GitHub or contact the development team.
=======
# ai-query-orchestrator
>>>>>>> 26ff19db2eb9a5fdd7d7f63a92b11ef847a1bfb3
