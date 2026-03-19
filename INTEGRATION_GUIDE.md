# Complete Integration Guide: Using All Optimization Features

## 🎯 Quick Start with All Features

### Step 1: Install Redis (Required for Caching)
```bash
# Windows (using WSL or separate Redis installation)
choco install redis

# Mac
brew install redis
brew services start redis

# Linux
sudo apt install redis-server
sudo systemctl start redis-server
```

### Step 2: Setup Backend with All Features
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install all dependencies including new optimizations
pip install -r requirements.txt

# Start the API server with all optimizations
python main_v2.py
```

API runs on `http://localhost:8000` with full optimization stack

### Step 3: Start LLM Microservice (Optional but Recommended)
```bash
# In a new terminal
cd backend
python llm_microservice.py
```

LLM service runs on `http://localhost:8001`

### Step 4: Start Frontend
```bash
cd frontend
npm install
npm start
```

Frontend runs on `http://localhost:3000`

## 📊 Feature Interaction Flow

```
User Query
    ↓
[1] Cache Layer
    ├─ Check In-Memory Cache → Hit? Return instantly
    ├─ Check Redis Cache → Hit? Return + update memory
    └─ Cache Miss → Continue
    ↓
[2] Query Classifier
    ├─ Analyze query type (PRICING, CLAIMS, POLICY, etc.)
    └─ Determine execution strategy
    ↓
[3] Routing Decision
    ├─ FAST_PATH → Vector + Keyword Search only
    ├─ BALANCED → Hybrid Search + Lightweight LLM
    ├─ FULL → Full LLM Reasoning
    └─ SPECULATIVE → Multiple parallel strategies
    ↓
[4] Parallel Execution
    ├─ Keyword Engine (Fast)
    ├─ Vector Store (Medium)
    ├─ Database Query (Medium)
    └─ Circuit Breaker (Fallback)
    ↓
[5] Hybrid Search (if needed)
    ├─ Speculative Executor runs fastest strategy
    └─ Returns results quickly
    ↓
[6] Context Reduction
    ├─ Select most relevant documents
    ├─ Limit to ~1500 tokens
    └─ Prepare for LLM
    ↓
[7] LLM Processing (if needed)
    ├─ Via Circuit Breaker
    ├─ Optional streaming
    └─ With fallback handling
    ↓
[8] Response Compression
    ├─ Gzip if requested
    └─ Stream or batch return
    ↓
[9] Cache Response
    ├─ Store in Redis
    ├─ Store in Memory
    └─ Set TTL
    ↓
Return Response to Client
```

## 🔧 Configuration Examples

### Example 1: High-Performance Configuration
Optimized for sub-second response times:

```python
# Create enhanced RAG pipeline
pipeline = EnhancedRAGPipeline(
    redis_url="redis://localhost:6379"
)

# Configure caching
cache_config = {
    "QUERY_TTL": 7200,  # 2 hours
    "RESPONSE_TTL": 3600,  # 1 hour
    "EMBEDDING_TTL": 86400,  # 24 hours
}

# Configure routing for speed
router_config = {
    "use_speculative": True,  # Multiple parallel strategies
    "timeout": 2.0,  # 2 second timeout for speculation
}

# Configure context reduction
context_config = {
    "max_tokens": 1500,
    "overlap": 100,
}
```

### Example 2: Balanced Configuration
Trade-off between speed and accuracy:

```python
pipeline = EnhancedRAGPipeline(
    redis_url="redis://localhost:6379"
)

# Configure for balance
config = {
    "cache": {
        "QUERY_TTL": 3600,
        "use_l2_cache": True,
    },
    "routing": {
        "use_hybrid_search": True,
        "llm_confidence_threshold": 0.7,
    },
    "performance": {
        "compression": "gzip",
        "worker_pool_size": 4,
    }
}
```

### Example 3: Maximum Accuracy Configuration
Best results, may be slower:

```python
pipeline = EnhancedRAGPipeline()

# Full pipeline, no shortcuts
config = {
    "cache": {
        "QUERY_TTL": 1800,  # Short TTL
        "skip_cache": False,
    },
    "routing": {
        "always_use_llm": True,
        "hybrid_search_depth": 10,  # More results
    },
    "context": {
        "max_tokens": 3000,  # More context
        "include_metadata": True,
    }
}
```

## 📈 Common Use Cases

### Use Case 1: FAQ Bot (High Cache Hit Rate)
```python
# Configuration
- Use heavy caching (TTL: 24 hours)
- Enable speculative search
- Skip LLM for simple questions
- Cache all FAQ responses

# Expected Results
- 95%+ cache hit rate
- <50ms average latency
- <10ms for cached queries
```

### Use Case 2: Real-Time Policy Updates (Low Cache)
```python
# Configuration
- Short cache TTL (30 minutes)
- Always verify with database
- Use hybrid search
- Full LLM reasoning

# Expected Results
- Always fresh data
- 200-500ms latency
- High accuracy
```

### Use Case 3: Mobile App (Streaming Enabled)
```python
# Configuration
- Enable streaming responses
- Aggressive compression
- Smaller context window
- Optimistic caching

# Expected Results
- Real-time token delivery
- Reduced bandwidth
- Sub-second TTFB
```

## 🎯 Optimization Scenarios

### Scenario 1: Improving Latency
```python
# 1. Enable speculative execution
routing.strategy = ExecutionStrategy.SPECULATIVE

# 2. Reduce context size
context_reducer.reduce_context(documents, max_tokens=1000)

# 3. Enable full caching
cache_layer.cache.RESPONSE_TTL = 7200

# 4. Use hybrid search with timeout
timeout = 1.5  # seconds
results = await speculative_executor.search(query, timeout=timeout)
```

### Scenario 2: Improving Accuracy
```python
# 1. Disable speculative, use full pipeline
routing.strategy = ExecutionStrategy.FULL

# 2. Increase context
context_reducer.reduce_context(documents, max_tokens=3000)

# 3. Use top-K expansion
top_k = 10  # Get more documents

# 4. Always use LLM
routing.use_llm = True
```

### Scenario 3: Reducing Costs
```python
# 1. Maximize cache hits
await cache_layer.set_query_response(query, response, ttl=86400)

# 2. Minimize LLM calls
routing.use_llm = False  # For FAQ-like queries

# 3. Reduce token processing
context_reducer.reduce_context(documents, max_tokens=800)

# 4. Use keyword search only for simple queries
routing.use_keyword_search = True
routing.use_vector_search = False
```

## 🧪 Testing All Features

### Unit Test Example
```python
import pytest
from enhanced_rag_pipeline import EnhancedRAGPipeline

@pytest.mark.asyncio
async def test_caching():
    pipeline = EnhancedRAGPipeline()
    await pipeline.initialize()
    
    # First call - cache miss
    result1 = await pipeline.query("test query")
    assert result1["latency_ms"] > 100
    
    # Second call - cache hit
    result2 = await pipeline.query("test query")
    assert result2["latency_ms"] < 50  # Much faster

@pytest.mark.asyncio
async def test_query_routing():
    pipeline = EnhancedRAGPipeline()
    await pipeline.initialize()
    
    # Pricing query should use database
    result = await pipeline.query("How much does policy cost?")
    assert result["routing_type"] in ["pricing", "policy"]
    
    # Claims query should use LLM
    result = await pipeline.query("How do I file a claim?")
    assert result["routing_type"] == "claims"

@pytest.mark.asyncio
async def test_streaming():
    pipeline = EnhancedRAGPipeline()
    
    # Test streaming response
    stream = await pipeline.stream_query("test query")
    chunks = []
    async for chunk in stream:
        chunks.append(chunk)
    
    assert len(chunks) > 0
    assert isinstance(chunks[0], str)
```

### Load Testing All Features
```python
from locust import HttpUser, task, between
import time

class OptimizedRAGUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(10)
    def cached_query(self):
        """Should get very fast responses"""
        query = "What insurance plans do you offer?"
        start = time.time()
        self.client.post("/query", json={"query": query})
        latency = time.time() - start
        
        # Assert sub-100ms latency due to caching
        assert latency < 0.1  # 100ms
    
    @task(5)
    def new_query(self):
        """More expensive queries"""
        query = f"Tell me about advanced feature X{int(time.time())}"
        self.client.post("/query", json={"query": query})
    
    @task(2)
    def streaming_query(self):
        """Test streaming"""
        query = "Explain the process"
        self.client.post(
            "/query",
            json={"query": query, "stream": True},
            stream=True
        )
    
    @task(1)
    def check_stats(self):
        """Monitor performance"""
        self.client.get("/stats")
        self.client.get("/cache/stats")
        self.client.get("/routing/stats")
```

Run with: `locust -f locustfile.py --host=http://localhost:8000`

## 📊 Monitoring Dashboard

Create a monitoring script to track all features:

```python
import asyncio
import json
from datetime import datetime

async def monitor_pipeline():
    """Monitor all optimization features"""
    
    while True:
        stats = {
            "timestamp": datetime.now().isoformat(),
            "cache": await pipeline.cache_layer.get_stats(),
            "routing": pipeline.query_router.get_stats(),
            "workers": global_worker_pool.get_status(),
            "circuit_breakers": circuit_breaker_manager.get_status(),
            "database": pipeline.db_pool.get_pool_status(),
        }
        
        print(json.dumps(stats, indent=2))
        await asyncio.sleep(5)  # Update every 5 seconds

# Run with: asyncio.run(monitor_pipeline())
```

## 🚀 Performance Tuning Checklist

- [ ] Redis cache is running and connected
- [ ] Worker pool size matches CPU cores
- [ ] Database connection pool is sized correctly
- [ ] Circuit breaker thresholds are appropriate
- [ ] Cache TTLs are set based on data freshness requirements
- [ ] Compression is enabled for large responses
- [ ] Context reduction is limiting tokens appropriately
- [ ] Hybrid search timeout is tuned for your data
- [ ] LLM microservice is running (if using LLM)
- [ ] Monitoring alerts are configured
- [ ] Load testing shows acceptable latencies
- [ ] Memory usage is within acceptable limits

## 🔄 Troubleshooting Integration

### Slow Despite All Optimizations
1. Check cache hit rate: `GET /cache/stats`
2. Verify routing decisions: `GET /routing/stats`
3. Monitor worker pool: `GET /worker-pool/status`
4. Check database: `SELECT * FROM pg_stat_activity;`

### High Memory Usage
1. Reduce in-memory cache size
2. Enable compression
3. Monitor Redis memory: `redis-cli INFO memory`
4. Clear old cache entries

### LLM Timeouts
1. Check LLM microservice: `curl http://localhost:8001/health`
2. Verify circuit breaker: `GET /circuit-breaker/status`
3. Reduce context size
4. Increase timeout values

