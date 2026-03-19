# Production Deployment Guide

## 🚀 Deployment Architectures

### Architecture 1: Single Server Deployment
```
┌─────────────────────────────────────┐
│         Single Server (VPS)          │
├─────────────────────────────────────┤
│  Nginx (Reverse Proxy)              │
│  ├─ Port 80/443 (SSL)               │
│  │                                  │
│  ├─→ FastAPI Main Service (8000)    │
│  │                                  │
│  ├─→ LLM Microservice (8001)        │
│  │                                  │
│  └─→ React Frontend (3000)          │
│                                     │
│  Redis Cache (6379)                 │
│  SQLite Database                    │
│  PostgreSQL Database (Optional)     │
└─────────────────────────────────────┘
```

**Requirements**:
- 4GB RAM minimum
- 2-4 CPU cores
- 20GB storage
- Latest Ubuntu/CentOS

**Setup**:
```bash
# Install dependencies
sudo apt update && sudo apt install -y \
  python3.10 python3-venv \
  nodejs npm \
  redis-server postgresql \
  nginx ssl-cert

# Clone repository
git clone <repo> /opt/insurance-portal
cd /opt/insurance-portal

# Setup backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start services
systemctl start redis-server postgresql

# Create systemd service for API
sudo tee /etc/systemd/system/rag-api.service <<EOF
[Unit]
Description=RAG API Service
After=network.target redis-server.service

[Service]
Type=notify
User=www-data
WorkingDirectory=/opt/insurance-portal/backend
ExecStart=/opt/insurance-portal/backend/venv/bin/python main_v2.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl start rag-api
sudo systemctl enable rag-api
```

### Architecture 2: Kubernetes Deployment
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: insurance-portal

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rag-api
  namespace: insurance-portal
spec:
  replicas: 3
  selector:
    matchLabels:
      app: rag-api
  template:
    metadata:
      labels:
        app: rag-api
    spec:
      containers:
      - name: api
        image: insurance-portal-api:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 8000
        env:
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: rag-config
              key: redis_url
        - name: LLM_SERVICE_URL
          value: "http://llm-service:8001"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: connection_string
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-service
  namespace: insurance-portal
spec:
  replicas: 2
  selector:
    matchLabels:
      app: llm-service
  template:
    metadata:
      labels:
        app: llm-service
    spec:
      containers:
      - name: llm
        image: insurance-portal-llm:latest
        ports:
        - containerPort: 8001
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"

---
apiVersion: v1
kind: Service
metadata:
  name: rag-api-service
  namespace: insurance-portal
spec:
  selector:
    app: rag-api
  ports:
  - protocol: TCP
    port: 8000
    targetPort: 8000
  type: LoadBalancer

---
apiVersion: v1
kind: Service
metadata:
  name: llm-service
  namespace: insurance-portal
spec:
  selector:
    app: llm-service
  ports:
  - protocol: TCP
    port: 8001
    targetPort: 8001
  type: ClusterIP

---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis
  namespace: insurance-portal
spec:
  serviceName: redis
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:latest
        ports:
        - containerPort: 6379
        volumeMounts:
        - name: data
          mountPath: /data
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
```

### Architecture 3: AWS Deployment
```bash
# Using Elastic Beanstalk
eb init -p docker insurance-portal
eb create insurance-portal-env

# RDS for PostgreSQL
aws rds create-db-instance \
  --db-instance-identifier insurance-db \
  --db-instance-class db.t3.micro \
  --engine postgres

# ElastiCache for Redis
aws elasticache create-cache-cluster \
  --cache-cluster-id insurance-cache \
  --engine redis \
  --cache-node-type cache.t3.micro

# S3 for embeddings/model cache
aws s3 mb s3://insurance-portal-cache
```

## 📊 Load Testing

```bash
# Using Apache Bench
ab -n 1000 -c 50 http://api.example.com/health

# Using wrk
wrk -t4 -c100 -d30s \
  -s load_test.lua \
  http://api.example.com/query

# Using locust
locust -f locustfile.py --host=http://api.example.com
```

Load Test Script (locustfile.py):
```python
from locust import HttpUser, task, between
import json

class InsurancePortalUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def simple_query(self):
        query = "What insurance plans do you offer?"
        self.client.post("/query", json={
            "query": query,
            "top_k": 3
        })
    
    @task(1)
    def streaming_query(self):
        query = "Explain claims process"
        self.client.post("/query", json={
            "query": query,
            "top_k": 5,
            "stream": True
        }, stream=True)
    
    def on_start(self):
        self.client.get("/health")
```

## 🔒 Security

### SSL/TLS Setup with Nginx
```nginx
server {
    listen 443 ssl http2;
    server_name api.example.com;

    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Rate limiting
        limit_req zone=api burst=100 nodelay;
    }
}

# Rate limiting zone
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
```

### API Authentication
```python
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from fastapi import Depends, HTTPException, status

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthCredentials = Depends(security)):
    token = credentials.credentials
    if not verify_jwt_token(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    return token

@app.post("/query")
async def process_query(
    request: QueryRequest,
    token: str = Depends(verify_token)
):
    # Process request
    pass
```

## 📈 Scaling Strategies

### Horizontal Scaling
```bash
# Docker Swarm
docker swarm init
docker stack deploy -c docker-compose.yml insurance

# Kubernetes autoscaling
kubectl autoscale deployment rag-api \
  --min 2 --max 10 \
  --cpu-percent 80 -n insurance-portal
```

### Vertical Scaling
- Increase instance size
- Add more workers
- Increase cache memory
- Scale database vertically

### Database Optimization
```python
# Connection pooling
sqlalchemy.pool.NullPool  # For serverless
sqlalchemy.pool.QueuePool  # For persistent

# Query optimization
CREATE INDEX ON policies(name, description);
CREATE INDEX ON claims(status, created_at);

# Read replicas
PRIMARY = postgresql://master/insurance
REPLICA = postgresql://replica/insurance
```

## 🔍 Monitoring & Logging

### Prometheus Metrics
```bash
pip install prometheus-client
```

```python
from prometheus_client import Counter, Histogram, generate_latest

query_counter = Counter('queries_total', 'Total queries processed')
query_latency = Histogram('query_latency_ms', 'Query latency in ms')
cache_hits = Counter('cache_hits_total', 'Cache hits')

@app.post("/query")
async def process_query(request: QueryRequest):
    with query_latency.time():
        result = await rag_pipeline.query(request.query)
        query_counter.inc()
        if cache_hit:
            cache_hits.inc()
    return result

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### DataDog Integration
```python
from ddtrace import patch_all, tracer

patch_all()

@tracer.wrap()
async def traced_query(query: str):
    with tracer.trace("rag.query") as span:
        span.set_tag("query.length", len(query))
        result = await rag_pipeline.query(query)
        span.set_tag("result.confidence", result["confidence"])
    return result
```

### ELK Stack Logging
```python
import logging
from pythonjsonlogger import jsonlogger

handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
handler.setFormatter(formatter)

logger = logging.getLogger()
logger.addHandler(handler)

# Now logs are JSON formatted for ELK
logger.info("Query processed", extra={
    "query": query,
    "latency": latency,
    "cache_hit": cache_hit
})
```

## 🚨 Disaster Recovery

### Backup Strategy
```bash
# Daily backup of databases
0 2 * * * /usr/bin/pg_dump insurance > /backups/insurance-$(date +\%Y\%m\%d).sql

# Redis persistence
appendonly yes
appendfsync everysec

# S3 backup of critical data
aws s3 sync /var/lib/postgresql s3://backup-bucket/postgresql/
```

### High Availability
```yaml
# PostgreSQL HA with Patroni
postgresql:
  parameters:
    wal_level: replica
    max_wal_senders: 10
    wal_keep_size: '1GB'
```

## 📋 Pre-Production Checklist

- [ ] All environment variables configured
- [ ] Database migrations run
- [ ] Redis cache operational
- [ ] SSL certificates valid
- [ ] Rate limiting configured
- [ ] Backup strategy in place
- [ ] Monitoring alerts configured
- [ ] Load testing completed
- [ ] Security audit passed
- [ ] Documentation updated
- [ ] Rollback plan in place
- [ ] On-call rotation established

