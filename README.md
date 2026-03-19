# 🚀 AI Query Orchestrator (Insurance AI System)

A production-ready AI system that intelligently routes user queries to SQL, vector search, or LLM pipelines to optimize latency, cost, and accuracy.

Built using **FastAPI**, **React**, **RAG**, and **LLM orchestration** patterns, this system reflects real-world architectures used in modern AI applications.

---

## 🧠 Problem

Traditional LLM-based systems send every query directly to the model, which leads to:

- ❌ **High latency** (2–5 seconds per request)
- ❌ **Increased cost** (unnecessary LLM usage)
- ❌ **Poor scalability**

## ✅ Solution

This system introduces a **Query Routing Engine** that:

- Classifies user queries (pricing, claims, policy, FAQ, complex)
- Dynamically selects the optimal execution path:
  - **SQL** (structured queries)
  - **Vector search** (RAG)
  - **LLM** (only when required)
- Optimizes performance using caching, async processing, and streaming

---

## ⚡ Key Features

### 🧠 Intelligent Query Routing
- Hybrid classifier (keyword + lightweight ML model)
- Avoids unnecessary LLM calls
- Reduces latency significantly

### 🔍 Hybrid Retrieval (RAG)
- FAISS-based vector search
- Keyword-based retrieval
- Context-aware answer generation

### ⚡ Performance Optimizations
- Caching layer for repeated queries
- Async worker pool for heavy tasks
- Streaming responses for better UX
- Circuit breaker for fault tolerance
- Database connection pooling

### 🧩 Multi-Source Execution
- SQL database queries
- Vector search (document retrieval)
- LLM reasoning (fallback for complex queries)

---

## 🚀 Example Query Flow

### 🔹 Example 1: Fast Path

**User Query:**
```
What is the premium of policy X?
```

**Flow:**
- Routed to SQL
- No LLM call
- Response in **<200ms**

### 🔹 Example 2: RAG + LLM

**User Query:**
```
Explain claim rejection policy
```

**Flow:**
- Vector search retrieves relevant documents
- LLM generates contextual explanation
- Response in **~1–2 seconds**

### 🔹 Example 3: Complex Query

**User Query:**
```
Compare policies and suggest the best plan
```

**Flow:**
- Full pipeline execution
- SQL + Vector Search + LLM reasoning
- Response in **~2–3 seconds**

---

## 🏗️ Architecture

```
User
  ↓
Frontend (React)
  ↓
FastAPI Backend
  ↓
Query Router (Core Intelligence)
  ↓
Execution Layer
  ├── Cache Layer
  ├── SQL Database
  ├── Vector DB (FAISS)
  ├── LLM Service
  ↓
Response (Streaming)
```

---

## 📦 Tech Stack

### Backend
- **FastAPI** - Async API framework
- **Python** - Core language
- **FAISS** - Vector database
- **HuggingFace Transformers** - Model hub
- **LangChain** - LLM orchestration
- **SQLite** - Database (replaceable with production DB)

### Frontend
- **React.js** - UI framework
- **Axios** - HTTP client
- **CSS Modules** - Styling

### Architecture Concepts
- Query routing engine
- Retrieval-Augmented Generation (RAG)
- Async processing
- Circuit breaker pattern
- Worker pool architecture

---

## 📁 Project Structure

```
backend/
  ├── query_router.py
  ├── rag_pipeline.py
  ├── hybrid_search.py
  ├── cache_layer.py
  ├── circuit_breaker.py
  ├── async_worker_pool.py
  ├── database_pool.py
  ├── main.py
  └── requirements.txt

frontend/
  ├── components/
  │   ├── LoadingSpinner.js
  │   ├── QueryForm.js
  │   └── ResponseDisplay.js
  ├── styles/
  │   ├── LoadingSpinner.css
  │   ├── QueryForm.css
  │   └── ResponseDisplay.css
  ├── App.js
  ├── package.json
  └── public/
      └── index.html

docs/
  ├── ARCHITECTURE.md
  ├── DEPLOYMENT_GUIDE.md
  └── INTEGRATION_GUIDE.md
```
---

## 🚀 Getting Started

### Backend Setup

```bash
cd backend
python -m venv venv
# For Windows:
venv\Scripts\activate
# For macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
python main.py
```

Backend will run at:
- **URL:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

### Frontend Setup

```bash
cd frontend
npm install
npm start
```

Frontend will run at:
- **URL:** http://localhost:3000

---

## 🧪 API Example

### Request

```
POST /query
```

```json
{
  "query": "What insurance plans do you offer?",
  "top_k": 3
}
```

### Response

```json
{
  "answer": "Based on available policies...",
  "sources": ["policy_doc_1", "policy_doc_2"],
  "confidence": 0.87
}
```
---

## ⚡ Performance Highlights

- Query routing reduces unnecessary LLM calls
- Cached responses return in **milliseconds**
- Async processing improves throughput
- Reduced prompt size improves LLM response time

---

## 🎯 Key Engineering Highlights

- Built modular AI architecture
- Implemented hybrid query classification
- Designed multi-path execution engine
- Integrated SQL + RAG + LLM pipelines
- Applied production-grade patterns (caching, async, circuit breaker)

---

## 📸 Demo

- Query input UI
- Response output
- System workflow

*(Add screenshots or GIF here)*

---

## 🧭 Future Improvements

- [ ] Replace SQLite with PostgreSQL
- [ ] Add Redis for distributed caching
- [ ] Deploy on AWS (ECS / Kubernetes)
- [ ] Add monitoring (Prometheus + Grafana)

---

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

---

## 📧 Contact

- **LinkedIn:** [Sumit Gawande](https://www.linkedin.com/in/sumit-gawande-2a211437a)
- **GitHub:** [Sumitgawande](https://github.com/Sumitgawande)

---

## 🔥 Final Note

This README positions the project as:

- 👉 Production AI system (not demo)
- 👉 System design + engineering focused
- 👉 High-paying role ready