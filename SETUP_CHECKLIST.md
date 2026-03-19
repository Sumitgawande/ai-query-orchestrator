# ✅ First-Time Setup Checklist

A step-by-step checklist to get your Insurance Portal RAG v2.0 running smoothly on your first attempt.

## 🎯 Pre-Setup (5 minutes)

- [ ] **Check System Requirements**
  - [ ] Windows 10/11, macOS 10.14+, or Linux
  - [ ] 4GB RAM minimum (8GB recommended)
  - [ ] 2GB free disk space
  - [ ] Internet connection

- [ ] **Install Prerequisites**
  - [ ] Python 3.8+ ([download](https://www.python.org/downloads/))
  - [ ] Node.js 14+ ([download](https://nodejs.org/))
  - [ ] Git ([download](https://git-scm.com/))
  - [ ] Redis (optional but recommended)

- [ ] **Clone Repository**
  ```bash
  git clone <repository-url>
  cd insurance_portal
  ```

## 🚀 Quick Setup (10-15 minutes)

### Option A: Automated Setup (Recommended for Windows/macOS)

- [ ] **Run Setup Script**
  ```bash
  # Windows
  setup.bat
  
  # macOS/Linux
  ./setup.sh
  ```
  
  Wait for completion (should take 3-5 minutes)

- [ ] **Verify Installation**
  ```bash
  # Check Python
  python --version          # Should be 3.8+
  
  # Check Node
  node --version           # Should be 14+
  
  # Check pip packages
  pip list | grep fastapi  # Should show fastapi
  ```

- [ ] **Start Services**
  ```bash
  # Windows
  start.bat
  
  # macOS/Linux
  ./start.sh
  ```
  
  Wait for message: "✅ All services started successfully"

### Option B: Manual Setup (For detailed control)

#### Backend Setup
- [ ] **Install Python Dependencies**
  ```bash
  cd backend
  python -m venv venv
  
  # Windows
  venv\Scripts\activate
  
  # macOS/Linux
  source venv/bin/activate
  
  pip install -r requirements.txt
  ```

- [ ] **Start Backend**
  ```bash
  python main_v2.py
  ```
  Wait for: "Uvicorn running on http://127.0.0.1:8000"

#### Frontend Setup (in new terminal)
- [ ] **Install Node Dependencies**
  ```bash
  cd frontend
  npm install
  ```

- [ ] **Start Frontend**
  ```bash
  npm start
  ```
  Wait for: "Compiled successfully" and browser opens to http://localhost:3000

## ✔️ Verification (5 minutes)

After starting services, verify everything works:

### Backend Health Check
- [ ] **Check API Response**
  ```bash
  curl http://localhost:8000/health
  ```
  Expected response: `{"status":"healthy"}`

- [ ] **Check Statistics Endpoint**
  ```bash
  curl http://localhost:8000/stats
  ```
  Expected response: JSON with stats

### Frontend Health Check
- [ ] **Open Browser**
  - [ ] Go to http://localhost:3000
  - [ ] Page loads without errors
  - [ ] "Connected" indicator shows green

- [ ] **Check Browser Console**
  - [ ] Press F12 to open developer tools
  - [ ] Go to Console tab
  - [ ] No red error messages

## 🎓 First Query Test (2 minutes)

### Try a Simple Query
- [ ] **Using Frontend**
  - [ ] Type query: "How do I file a claim?"
  - [ ] Click "Search"
  - [ ] Wait for response
  - [ ] See answer displayed
  - [ ] See confidence score
  - [ ] See response time

### Try Streaming Mode
- [ ] **Enable Streaming**
  - [ ] Check "Streaming Mode" checkbox
  - [ ] Type query: "What is insurance?"
  - [ ] Click "Search"
  - [ ] Watch tokens appear in real-time (slower network shows this better)

### Try Advanced Modes
- [ ] **Adjust Top K**
  - [ ] Change "Top K" dropdown to 10
  - [ ] Run another query
  - [ ] See more sources returned

## 🔍 Basic Diagnostics (5 minutes)

If something doesn't work, run these checks:

### API Issues
```bash
# Test endpoint directly
curl http://localhost:8000/query \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"query":"test"}'

# Check cache
curl http://localhost:8000/cache/stats

# Check circuit breaker
curl http://localhost:8000/circuit-breaker/status

# View logs
tail -f backend/app.log
```

### Frontend Issues
```bash
# Check if Node is running
netstat -ano | findstr :3000  # Windows
lsof -i :3000                 # macOS/Linux

# Check Node process
npm list

# Clear cache and rebuild
rm -rf node_modules package-lock.json
npm install
npm start
```

### Port Already in Use
```bash
# Windows - Kill process on port
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux - Kill process on port
lsof -i :8000
kill -9 <PID>
```

## 📚 Learning Path (30 minutes)

After successful setup, go through:

- [ ] **Understand the System (10 min)**
  - Read: [V2_SUMMARY.md](Documentation/V2_SUMMARY.md)
  - What: Overview of all 15 features

- [ ] **Learn Architecture (10 min)**
  - Read: [ARCHITECTURE.md](Documentation/ARCHITECTURE.md)
  - What: How system components interact

- [ ] **Try Examples (10 min)**
  - Read: [INTEGRATION_GUIDE.md](Documentation/INTEGRATION_GUIDE.md)
  - What: Practical usage examples

## 🎯 Common First-Time Issues & Fixes

### Issue: "ModuleNotFoundError: No module named 'fastapi'"
**Solution:**
```bash
pip install -r backend/requirements.txt
```

### Issue: "Port 8000 already in use"
**Solution:**
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :8000 | grep LISTEN
kill -9 <PID>
```

### Issue: "Backend won't start / crashes immediately"
**Solution:**
```bash
# Check Python version
python --version          # Needs 3.8+

# Check dependencies
pip install -r requirements.txt --upgrade

# Test if it's an import error
python -c "import fastapi; print('OK')"

# View detailed error
python main_v2.py --verbose
```

### Issue: "Frontend blank or not loading"
**Solution:**
```bash
# Check if Node process is running
netstat -ano | findstr :3000   # Windows
lsof -i :3000                  # macOS/Linux

# Rebuild
rm -rf frontend/node_modules
npm install --prefix frontend
npm start --prefix frontend
```

### Issue: "Can't connect to API"
**Solution:**
```bash
# Check backend is running
curl http://localhost:8000/health

# Check CORS is enabled (should be in main_v2.py)
# Check firewall isn't blocking port 8000
```

### Issue: "No documents loaded / Always gives generic answer"
**Solution:**
```bash
# Check documents folder has .txt files
ls backend/documents/

# If empty, download sample documents
# Or create a test document:
echo "Insurance Policy Details..." > backend/documents/test.txt

# Restart backend to index new documents
```

## 🚀 Next Steps After Setup

### Short Term (Today)
- [ ] Verify all tests pass
- [ ] Explore the UI
- [ ] Try a few queries
- [ ] Check monitoring endpoints

### Medium Term (This Week)
- [ ] Study feature documentation
- [ ] Add your own documents to `backend/documents/`
- [ ] Try streaming mode
- [ ] Monitor performance metrics
- [ ] Try load testing

### Long Term (This Month)
- [ ] Connect real LLM provider
- [ ] Set up Redis for caching
- [ ] Configure production database
- [ ] Plan deployment strategy
- [ ] Create monitoring dashboards

## 📋 Configuration Walkthrough (Optional)

### Edit Backend Configuration
Open `backend/main_v2.py` and adjust:
```python
# Around line 20
CACHE_TTL = 3600              # How long to cache queries (seconds)
WORKER_POOL_SIZE = 4          # Number of background workers
CIRCUIT_BREAKER_THRESHOLD = 5 # Failure threshold
STREAMING_CHUNK_SIZE = 50     # Size of streaming chunks
```

### Edit Frontend Configuration
Open `frontend/.env`:
```
REACT_APP_API_URL=http://localhost:8000
REACT_APP_DEBUG=true
```

## 🔐 Early Security Checks

Even for development, consider:

- [ ] **API Security**
  - [ ] API only accessible locally (default)
  - [ ] No sensitive data in logs
  - [ ] CORS configured properly

- [ ] **Data Safety**
  - [ ] Documents folder has expected files
  - [ ] Database file exists
  - [ ] Backups created

- [ ] **Performance**
  - [ ] Queries returning in <2 seconds
  - [ ] No memory errors
  - [ ] UI responsive

## 📊 Success Criteria

You're ready to use the system when:

- [x] Backend running on http://localhost:8000
- [x] Frontend running on http://localhost:3000
- [x] API /health endpoint returns 200
- [x] Frontend loads without errors
- [x] Can submit query and get response
- [x] Response includes answer, confidence, and sources
- [x] Streaming mode works (tokens appear one at a time)
- [x] Can see performance metrics in response

## 🎉 Congratulations!

You now have a production-grade RAG system with 15 optimization features running locally!

### What You Have
✅ Intelligent Query Router  
✅ Multi-layer Caching (50x faster for cached queries)  
✅ Hybrid Search (2-3x faster retrieval)  
✅ Streaming Responses (real-time tokens)  
✅ Circuit Breaker (fault tolerance)  
✅ Comprehensive Monitoring  
✅ Production-Ready API  
✅ Modern React Frontend  

### Next: Explore the Features
- Try streaming mode
- Run queries and check latency
- Monitor your cache hit rate
- Review performance statistics
- Test with different search modes

### Then: Prepare for Production
- Follow [DEPLOYMENT_GUIDE.md](Documentation/DEPLOYMENT_GUIDE.md)
- Set up monitoring
- Configure real LLM
- Performance tune
- Plan scaling

## 📞 Need Help?

### Stuck on Setup?
1. Check [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Common commands
2. Check relevant troubleshooting section above
3. Review [ADVANCED_FEATURES.md](Documentation/ADVANCED_FEATURES.md) - Troubleshooting section

### Want to Learn More?
- Start with [INDEX.md](INDEX.md) - Main documentation hub
- Each documentation file has a specific purpose
- Pick your learning path based on your goals

### Something Broken?
1. Check logs: `tail -f backend/app.log`
2. Check endpoints: `curl http://localhost:8000/health`
3. Check browser console: F12 → Console tab
4. See troubleshooting section above

---

**Version**: v2.0  
**Status**: ✅ First-time user ready  
**Estimated Total Time**: 30-45 minutes  

Good luck! You've got this! 🚀

