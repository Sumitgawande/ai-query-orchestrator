# 🚀 Quick Reference Guide

A fast-lookup reference for developers and operators working with Insurance Portal RAG v2.0.

## ⚡ Common Commands

### Setup & Start
```bash
# Windows
setup.bat
start.bat
stop.bat

# Mac/Linux
./setup.sh
./start.sh
./stop.sh
```

### Check Status
```bash
curl http://localhost:8000/health
curl http://localhost:8000/stats
curl http://localhost:8000/cache/stats
```

### View Logs
```bash
# Backend logs
tail -f backend.log

# Frontend logs
# Check browser console (F12)
```

### Add Documents
```bash
# Place .txt files in backend/documents/
cp your_document.txt backend/documents/
# Restart backend to index
```

## 📡 API Endpoints

### Query Endpoint
```bash
# Regular query
POST /query
{
  "query": "How do I file a claim?",
  "top_k": 5,
  "use_streaming": false
}

# Streaming query (real-time tokens)
POST /query
{
  "query": "How do I file a claim?",
  "top_k": 5,
  "stream": true
}
```

### Monitoring Endpoints
```bash
GET /stats              # All statistics
GET /cache/stats        # Cache hit rate, size
GET /routing/stats      # Query classification stats
GET /circuit-breaker/status  # Health of services
GET /worker-pool/status      # Background task status
```

### Management Endpoints
```bash
POST /cache/invalidate  # Clear cache
POST /documents/add     # Background document indexing
POST /task/status/{id}  # Check task progress
```

## 🔧 Configuration

### Environment Variables
```bash
# Caching
REDIS_URL=redis://localhost:6379
CACHE_TTL=3600
MEMORY_CACHE_SIZE=1000

# LLM Service
LLM_SERVICE_URL=http://localhost:8001
LLM_MODEL=gpt-3.5-turbo

# Database
DATABASE_URL=sqlite:///insurance_policies.db
CONNECTION_POOL_MIN=5
CONNECTION_POOL_MAX=20

# Performance
WORKER_POOL_SIZE=4
CIRCUIT_BREAKER_THRESHOLD=5
STREAMING_CHUNK_SIZE=50
```

### Edit in Files
- **Backend config**: `backend/main_v2.py` (top section)
- **Frontend config**: `frontend/.env`

## 🎯 Feature Toggles

### Enable/Disable Features
```python
# In backend/enhanced_rag_pipeline.py
self.use_cache = True              # Enable caching
self.use_hybrid_search = True      # Enable hybrid search
self.use_streaming = True          # Enable streaming
self.use_compression = True        # Enable compression
self.use_worker_pool = True        # Enable background tasks
```

### Query-Level Overrides
```bash
# Disable cache for specific query
POST /query
{
  "query": "...",
  "bypass_cache": true
}

# Force specific routing
POST /query
{
  "query": "...",
  "force_routing": "simple_keyword"
}
```

## 🐛 Debugging

### Check Service Status
```bash
# All services
curl http://localhost:8000/health

# Circuit breaker status
curl http://localhost:8000/circuit-breaker/status

# Cache statistics
curl http://localhost:8000/cache/stats

# Worker pool status
curl http://localhost:8000/worker-pool/status
```

### View Logs
```bash
# Combined logs
tail -f app.log

# Filter by level
grep ERROR app.log
grep WARNING app.log
```

### Test Individual Components
```bash
# Test cache
curl -X POST http://localhost:8000/query -d '{"query":"test"}'
curl http://localhost:8000/cache/stats

# Test streaming
curl -X POST http://localhost:8000/query -d '{"query":"test","stream":true}'

# Test background task
curl -X POST http://localhost:8000/documents/add \
  -d '{"path":"documents/test.txt"}' \
  -H "Content-Type: application/json"
```

## 📊 Performance Metrics

### Key Metrics to Monitor
```bash
# Cache hit rate
curl http://localhost:8000/cache/stats
→ Look for: hit_rate, total_hits, total_misses

# Query latency
curl http://localhost:8000/stats
→ Look for: avg_query_time, p95_query_time

# Routing accuracy
curl http://localhost:8000/routing/stats
→ Look for: classification_accuracy, avg_classification_time

# Service health
curl http://localhost:8000/circuit-breaker/status
→ Look for: all states should be "CLOSED"
```

### Performance Expectations
```
Cached query:      <10ms
New query:         80-200ms
Complex query:     1000-2000ms
Streaming:         100-500ms
Cache hit rate:    Should be >70% after warmup
```

## 🔄 Development Workflow

### Adding a New Feature
1. Create new module in `backend/`
2. Add to `enhanced_rag_pipeline.py` initialization
3. Update `main_v2.py` endpoints if needed
4. Update `requirements.txt` dependencies
5. Test via API endpoints
6. Update documentation

### Testing
```bash
# Unit test a module
python -m pytest backend/cache_layer.py

# Test specific feature
python -c "from backend.cache_layer import InMemoryCache; c = InMemoryCache(); print(c)"

# Full integration test
curl http://localhost:8000/stats

# Load test
locust -f locustfile.py --host=http://localhost:8000
```

## 🐳 Docker

### Build and Run
```bash
# Build image
docker build -t insurance-portal:v2 .

# Run container
docker run -p 8000:8000 -p 3000:3000 insurance-portal:v2

# Run with Docker Compose
docker-compose up
```

### Cleanup
```bash
# Stop containers
docker-compose down

# Remove images
docker rmi insurance-portal:v2

# Prune unused
docker system prune
```

## 🚀 Deployment Shortcuts

### Single Server
```bash
# SSH to server
ssh user@server.com

# Clone repo
git clone <repo>
cd insurance_portal

# Run setup
./setup.sh
./start.sh

# Check status
curl http://localhost:8000/health
```

### Kubernetes
```bash
# Create namespace
kubectl create namespace insurance

# Deploy
kubectl apply -f k8s/deployment.yaml -n insurance

# Check pods
kubectl get pods -n insurance

# View logs
kubectl logs -n insurance pod/insurance-portal-xxxxx

# Expose service
kubectl expose pod insurance-portal-xxxxx \
  --port=8000 --type=LoadBalancer
```

### AWS (Manual)
```bash
# Start EC2 instance
aws ec2 start-instances --instance-ids i-xxxxx

# SSH and deploy
ssh -i key.pem ec2-user@instance-ip
./setup.sh
./start.sh

# Update security group
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxx \
  --protocol tcp \
  --port 8000 \
  --cidr 0.0.0.0/0
```

## 🔐 Security Checklist

Before deploying to production:

- [ ] Enable SSL/TLS certificates
- [ ] Configure firewall rules
- [ ] Set API authentication headers
- [ ] Rotate API keys
- [ ] Enable rate limiting
- [ ] Create database backups
- [ ] Run security audit
- [ ] Review logs for errors
- [ ] Load test with expected volume
- [ ] Test failover/recovery

See [DEPLOYMENT_GUIDE.md](../Documentation/DEPLOYMENT_GUIDE.md) for detailed security setup.

## 📈 Scaling Guide

### Vertical Scaling (Single Server)
```bash
# Increase worker pool
WORKER_POOL_SIZE=8

# Increase cache size
MEMORY_CACHE_SIZE=5000

# Increase connection pool
CONNECTION_POOL_MAX=50
```

### Horizontal Scaling (Multiple Servers)
```bash
# Setup load balancer (nginx)
# Point to multiple backend instances
# Use shared Redis for cache

# Run backend on multiple servers
# Each connects to same Redis
# Load balancer distributes traffic
```

### Microservice Scaling
```bash
# LLM service separate tier
# Deploy multiple LLM instances
# Main API load balanced across servers
# Shared Redis cache layer
# Shared database (PostgreSQL)
```

## 🆘 Troubleshooting Checklist

### Won't Start
- [ ] Python version 3.8+? → `python --version`
- [ ] Dependencies installed? → `pip install -r requirements.txt`
- [ ] Port available? → `lsof -i :8000`
- [ ] Redis running? → `redis-cli ping`
- [ ] Check logs → `tail -f app.log`

### Slow Performance
- [ ] Cache enabled? → `curl http://localhost:8000/cache/stats`
- [ ] Hybrid search enabled? → Check `main_v2.py`
- [ ] Circuit breaker healthy? → `curl .../circuit-breaker/status`
- [ ] Database connections good? → Check connection pool logs
- [ ] Server resources available? → `top`, `free -h`

### High Memory
- [ ] Reduce cache size → `MEMORY_CACHE_SIZE=500`
- [ ] Enable compression → `ENABLE_COMPRESSION=true`
- [ ] Monitor worker pool → `curl .../worker-pool/status`
- [ ] Check for memory leaks → `memory_profiler`

### No Cache Hits
- [ ] Redis running? → `redis-cli ping`
- [ ] Redis URL correct? → Check `REDIS_URL`
- [ ] Cache TTL set? → Check `CACHE_TTL`
- [ ] Same identical queries? → Cache uses query hash

## 🔄 Update & Maintenance

### Update Dependencies
```bash
pip install -r requirements.txt --upgrade
pip freeze > requirements.txt
```

### Backup Configuration
```bash
# Backup all documents
cp -r backend/documents backup/documents_$(date +%Y%m%d)

# Backup database
sqlite3 insurance_policies.db ".backup backup.db"

# Backup cache
redis-cli --rdb /backup/dump.rdb
```

### Version Control
```bash
git add backend/ frontend/ Documentation/
git commit -m "Production update - v2.1"
git push production main
```

## 📞 Quick Links

- **Full Docs**: See [INDEX.md](../INDEX.md)
- **Architecture**: See [ARCHITECTURE.md](../Documentation/ARCHITECTURE.md)
- **Features**: See [ADVANCED_FEATURES.md](../Documentation/ADVANCED_FEATURES.md)
- **Deployment**: See [DEPLOYMENT_GUIDE.md](../Documentation/DEPLOYMENT_GUIDE.md)
- **Integration**: See [INTEGRATION_GUIDE.md](../Documentation/INTEGRATION_GUIDE.md)

---

**Remember**: For detailed information, always check the full documentation files above.

**Last Updated**: March 10, 2026  
**Version**: v2.0

