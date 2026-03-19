# Architecture & Feature Map

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        React Frontend (v2)                          │
│                    - Streaming support                              │
│                    - Performance metrics display                    │
│                    - Cache-aware UI                                 │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              │ HTTP/WebSocket
                              │
┌─────────────────────────────▼───────────────────────────────────────┐
│                 FastAPI Main Service (main_v2.py)                   │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ Route: POST /query - Process user queries                      │ │
│  │ Route: GET /stats - Pipeline statistics                        │ │
│  │ Route: GET /cache/stats - Cache performance                    │ │
│  │ Route: GET /circuit-breaker/status - Service health            │ │
│  │ Route: GET /worker-pool/status - Background tasks              │ │
│  │ Route: GET /routing/stats - Query classification stats         │ │
│  └────────────────────────────────────────────────────────────────┘ │
└──────────┬──────────┬──────────┬──────────┬──────────┬───────────────┘
           │          │          │          │          │
      ┌────▼┐    ┌────▼┐    ┌────▼┐    ┌────▼┐   ┌────▼────┐
      │Cache│    │Query│    │Hybrid  │Circuit │Async  │
      │Layer│    │Router│    │Search  │Breaker│Worker │
      └────┬┘    └────┬┘    └────┬┘    └──┬───┘   └──┬───┘
           │          │          │        │          │
      ┌────▼──────────▼──────────▼────────▼──────────▼────┐
      │       Enhanced RAG Pipeline (enhanced_rag_...)    │
      │                                                    │
      │  ┌─────────────────────────────────────────────┐ │
      │  │  Vector Store (FAISS)                       │ │
      │  │  - Precomputed embeddings                   │ │
      │  │  - Semantic similarity search               │ │
      │  └─────────────────────────────────────────────┘ │
      │                                                    │
      │  ┌─────────────────────────────────────────────┐ │
      │  │  Keyword Search Engine                      │ │
      │  │  - Inverted index                           │ │
      │  │  - Fast exact matching                      │ │
      │  └─────────────────────────────────────────────┘ │
      │                                                    │
      │  ┌─────────────────────────────────────────────┐ │
      │  │  Database Layer (with Connection Pooling)   │ │
      │  │  - SQLite / PostgreSQL                      │ │
      │  │  - Policy & Claims data                     │ │
      │  └─────────────────────────────────────────────┘ │
      └────────────────────────────────────────────────────┘
           │                          │
      ┌────▼────┐         ┌──────────▼─────────┐
      │Redis    │         │LLM Microservice    │
      │Cache    │         │(llm_microservice.py)
      │- Query  │         │- Inference only    │
      │- Embed  │         │- Independent scale │
      │- Response         │- Batch processing  │
      │- TTL   │         │- Streaming support │
      └─────────┘         └────────────────────┘
```

## Feature Implementation Locations

### 1. **Multi-Layer Caching** 📦
**File**: `backend/cache_layer.py`

Components:
- `InMemoryCache` - LRU in-memory cache (1000 items)
- `RedisCacheLayer` - Distributed Redis cache
- `CacheConfig` - TTL configuration (1h query, 2h response, 24h embedding)

Methods:
```python
await cache.get_query_response(query, top_k)
await cache.set_query_response(query, response, top_k)
await cache.get_embeddings(doc_id)
await cache.invalidate_query_cache(query)
```

Performance: Cache hit → <10ms (50x improvement)

---

### 2. **Query Router & Classifier** 🎯
**File**: `backend/query_router.py`

Components:
- `QueryClassifier` - ML-based query classification
- `QueryRouter` - Routing decision maker
- `QueryType` - Enum of query classifications
- `ExecutionStrategy` - How to execute the query

Query Types:
- PRICING → Database + Keyword
- CLAIMS → Hybrid + LLM
- POLICY_DETAILS → Vector + Database
- FAQ → Keyword only
- GENERAL → Full LLM pipeline

Methods:
```python
await classifier.classify(query)  # → QueryType
await router.route(query)  # → RoutingDecision
router.record_query(query, type, latency)  # Statistics
```

Latency: <50ms classification

---

### 3. **Hybrid Search** 🔍
**File**: `backend/hybrid_search.py`

Components:
- `KeywordSearchEngine` - Inverted index search
- `HybridSearchEngine` - Combines keyword + vector
- `SpeculativeSearchExecutor` - Parallel multi-strategy

Features:
- Keyword weight: 30% (fast, exact)
- Vector weight: 70% (semantic, slow)
- Speculative: Multiple in parallel, returns fastest

Methods:
```python
await keyword_engine.search(query, top_k)  # Fast
await hybrid_search.search(query, top_k)   # Balanced
await speculative_executor.search(query, timeout)  # Fastest
```

Performance: 2-3x faster than vector-only

---

### 4. **Streaming Responses** 🌊
**File**: `backend/streaming_handler.py`

Components:
- `StreamingResponseHandler` - SSE streaming
- `ResponseCompressor` - gzip compression
- `ResponseContextReducer` - Token reduction
- `StreamingLLMHandler` - Streaming LLM integration

Features:
- Server-Sent Events (SSE)
- Automatic chunking
- Gzip compression (60-70% reduction)
- Context reduction (1500 token limit)

Methods:
```python
async for chunk in handler.stream_response(query, llm_gen, sources):
    yield chunk

compressed = await compressor.compress_response(data, "gzip")
reduced = reducer.reduce_context(documents, max_tokens=1500)
```

---

### 5. **Circuit Breaker Pattern** 🔌
**File**: `backend/circuit_breaker.py`

Components:
- `CircuitBreaker` - Individual breaker
- `CircuitBreakerManager` - Manage multiple breakers

States:
- CLOSED (normal operation)
- OPEN (service failing, block requests)
- HALF_OPEN (testing recovery)

Configuration:
```python
CircuitBreaker(
    name="llm_api",
    failure_threshold=3,  # Open after 3 failures
    recovery_timeout=30,  # Retry after 30s
)
```

Methods:
```python
await breaker.call(func, *args, fallback=fallback_fn)
await circuit_breaker_manager.call("llm_api", func, fallback=fallback)
```

---

### 6. **Async Worker Pool** 👥
**File**: `backend/async_worker_pool.py`

Components:
- `Task` - Unit of work with metadata
- `AsyncWorkerPool` - Pool of async workers (default: 4)
- `TaskStatus` - PENDING, RUNNING, COMPLETED, FAILED

Features:
- Configurable worker count
- Task priority (1=highest, 10=lowest)
- Background processing
- Result tracking

Methods:
```python
task_id = await pool.submit(func, *args, priority=5)
result = await pool.get_result(task_id, timeout=300)
status = pool.get_status()  # Get stats
```

---

### 7. **Database Connection Pooling** 🗄️
**File**: `backend/database_pool.py`

Components:
- `DatabasePool` - PostgreSQL with asyncpg
- `SQLitePool` - SQLite with aiosqlite
- `PolicyDatabase` - Data access layer

Features:
- Min/max connection pool size
- Connection reuse
- Async context manager
- WAL mode for SQLite

Methods:
```python
await pool.initialize()
async with pool.acquire() as conn:
    results = await conn.fetch(query)

await policy_db.search_policies(keywords)
await policy_db.search_claims_info(keywords)
```

Performance: 50% latency reduction vs new connections

---

### 8. **Response Compression** 🗜️
**File**: `backend/streaming_handler.py`  (ResponseCompressor class)

Features:
- gzip compression
- Adaptive threshold
- Automatic client decompression

Methods:
```python
compressed = await compressor.compress_response(data, "gzip")
```

Performance: 60-70% bandwidth reduction

---

### 9. **Context Reduction** 📄
**File**: `backend/streaming_handler.py`  (ResponseContextReducer class)

Features:
- Token counting & limiting (max 1500 tokens)
- Relevance-based selection
- Overlapping chunk generation

Methods:
```python
reduced = reducer.reduce_context(documents, max_tokens=1500)
chunks = reducer.chunk_context(context, chunk_size=512)
```

Performance: 30-50% token reduction, faster LLM processing

---

### 10. **Speculative Execution** ⚡
**File**: `backend/hybrid_search.py`  (SpeculativeSearchExecutor class)

Features:
- Parallel strategy execution
- Returns fastest result
- Configurable timeout

Strategies:
1. Keyword-only (fastest)
2. Vector search (medium)
3. Hybrid search (slowest, most accurate)

Methods:
```python
results, strategy = await executor.search(query, top_k, timeout=5)
```

---

### 11. **Precomputed Embeddings** 🧠
**File**: `backend/enhanced_rag_pipeline.py`

Features:
- Generated during document ingestion
- Cached in FAISS vector store
- Fast similarity lookup

Components:
- HuggingFace embeddings (sentence-transformers)
- FAISS vector database
- Embedding cache in Redis

Performance: <50ms vector search with precomputation

---

### 12. **Response Caching** 💾
**File**: `backend/cache_layer.py`

Features:
- Query hash for cache key
- TTL-based expiration (default 2h)
- Manual invalidation

Cache Levels:
1. Memory cache (instant, 1000 items)
2. Redis cache (distributed)

Performance: Cached queries <10ms

---

### 13. **LLM Microservice** 🤖
**File**: `backend/llm_microservice.py`

Features:
- Separate FastAPI service
- Independent scaling
- Batch processing support
- Streaming generation
- Health monitoring

Endpoints:
- POST `/generate` - Single query
- POST `/stream` - Streaming
- POST `/batch` - Multiple queries
- GET `/health` - Service health

Performance: Can scale independently from main API

---

### 14. **Small Model Router** 🎓
**File**: `backend/query_router.py`  (QueryClassifier class)

Features:
- Zero-shot BART classifier (or keyword fallback)
- <50ms latency
- Keyword-based fast path available

Models:
- Primary: facebook/bart-large-mnli (zero-shot)
- Fallback: Keyword pattern matching

---

### 15. **Advanced Monitoring** 📊
**File**: `backend/main_v2.py`

Endpoints:
- `GET /health` - Service health
- `GET /stats` - All statistics
- `GET /cache/stats` - Cache performance
- `GET /circuit-breaker/status` - Service health
- `GET /worker-pool/status` - Background tasks
- `GET /routing/stats` - Query classification stats

---

## Data Flow: From Query to Response

```
1. User Query
   ↓
2. Cache Check (cache_layer.py)
   ├─ Hit? → Return instantly
   └─ Miss? → Continue
   ↓
3. Query Classification (query_router.py)
   ├─ Classify query type
   └─ Determine strategy
   ↓
4. Routing Decision (query_router.py)
   ├─ FAST_PATH → Vector + Keyword
   ├─ BALANCED → Hybrid + Light LLM
   ├─ FULL → Full LLM reasoning
   └─ SPECULATIVE → Parallel strategies
   ↓
5. Document Retrieval (hybrid_search.py)
   ├─ Keyword search (fast)
   ├─ Vector search (semantic)
   └─ Speculative executor → fastest wins
   ↓
6. Context Reduction (streaming_handler.py)
   ├─ Select top-k relevant
   ├─ Limit to 1500 tokens
   └─ Order by relevance
   ↓
7. LLM Processing (with circuit_breaker.py)
   ├─ Call LLM with context
   ├─ On failure → Circuit breaker opens
   └─ Fallback → Use context directly
   ↓
8. Response Generation
   ├─ If streaming → Send tokens one by one
   └─ If batch → Compress & send
   ↓
9. Response Caching (cache_layer.py)
   ├─ Store in memory cache
   ├─ Store in Redis with TTL
   └─ Index for future hits
   ↓
10. Return to Frontend (with compression)
    ├─ Gzip if enabled
    └─ Send with latency metrics
```

## Integration Points

### External Services
- **Redis**: Cache layer
- **PostgreSQL/SQLite**: Policy database
- **LLM API**: Via microservice with circuit breaker
- **HuggingFace**: Embeddings download

### Internal Service Communication
```
main_v2.py
  ├─→ enhanced_rag_pipeline.py
  │    ├─→ cache_layer.py (Redis)
  │    ├─→ query_router.py (classification)
  │    ├─→ hybrid_search.py (retrieval)
  │    ├─→ streaming_handler.py (compression)
  │    ├─→ circuit_breaker.py (protection)
  │    ├─→ async_worker_pool.py (background tasks)
  │    └─→ database_pool.py (SQL queries)
  │
  └─→ llm_microservice.py (optional, separate port 8001)
```

## Configuration Dependencies

```
CacheConfig           → controls TTL values
CircuitBreaker config → failure thresholds, timeouts
Worker pool config    → worker count, task priority
Database config       → connection pool size
Streaming config      → chunk size, compression
Router config         → execution strategies
```

## Performance Characteristics

| Component | Latency | Memory | CPU | Network |
|-----------|---------|--------|-----|---------|
| Cache Hit | <10ms | Low | Minimal | 0 |
| Keyword Search | 10-30ms | Low | Low | 0 |
| Vector Search | 50-100ms | Medium | Medium | 0 |
| Hybrid Search | 80-150ms | Medium | Medium | 0 |
| LLM Call | 500-3000ms | High | High | Network |
| Caching Overhead | 1-5ms | Low | Low | 0 |
| Compression | 5-20ms | Low | Medium | 0 |
| Streaming | <50ms/token | Low | Medium | Network |

---

This architecture provides:
- ✅ **Speed**: Multiple optimization layers
- ✅ **Reliability**: Circuit breaker, fallbacks
- ✅ **Scalability**: Async, worker pool, microservices
- ✅ **Observability**: Comprehensive statistics
- ✅ **Flexibility**: Multiple execution paths

