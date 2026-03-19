# 🚀 Quick Start Guide

Get your Insurance Portal RAG application running in minutes!

## ⚡ Fast Setup (Windows)

1. **Clone/Open the project**
   ```
   The project is ready in: d:\insurance_portal\agent
   ```

2. **Run the setup script**
   ```bash
   setup.bat
   ```
   This installs all dependencies for both backend and frontend.

3. **Start the application**
   ```bash
   start.bat
   ```
   This opens both backend and frontend in separate windows.

4. **Open in browser**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

---

## ⚡ Fast Setup (Mac/Linux)

1. **Make scripts executable**
   ```bash
   chmod +x setup.sh start.sh
   ```

2. **Run the setup script**
   ```bash
   ./setup.sh
   ```

3. **Start the application**
   ```bash
   ./start.sh
   ```

4. **Open in browser**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000

---

## 📖 Manual Setup (Step by Step)

### Backend Setup

1. **Navigate to backend**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # Mac/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the server**
   ```bash
   python main.py
   ```

Server runs on: `http://localhost:8000`

### Frontend Setup (in another terminal)

1. **Navigate to frontend**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start the application**
   ```bash
   npm start
   ```

Browser opens automatically at: `http://localhost:3000`

---

## 🐳 Using Docker (Optional)

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

2. **Access the application**
   - Frontend: http://localhost:3000
   - Backend: http://localhost:8000

---

## ✅ Verify Everything Works

### Backend Health Check
```bash
# In PowerShell or terminal
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "message": "RAG pipeline is ready"
}
```

### Test a Query
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What health insurance plans do you offer?", "top_k": 3}'
```

---

## 📚 Adding Your Documents

1. **Create documents folder**
   ```bash
   mkdir backend/documents
   ```

2. **Add your insurance documents** 
   - Supported formats: `.txt`, `.md`
   - Place them in `backend/documents/`
   - Examples:
     - `coverage_plans.txt`
     - `policies.txt`
     - `faqs.txt`

3. **Restart the backend**
   - Backend automatically loads documents on startup
   - New documents require restart

---

## 🔧 Troubleshooting

### Port Already in Use
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Mac/Linux
lsof -ti:8000 | xargs kill -9
```

### Backend Won't Start
- Ensure Python 3.8+ is installed: `python --version`
- Check all dependencies: `pip install -r backend/requirements.txt`
- Check console for error messages

### Frontend Won't Connect to Backend
- Verify backend is running: `curl http://localhost:8000/health`
- Check that CORS is enabled in backend
- Try hard-refreshing browser (Ctrl+Shift+R)

### Models Taking Too Long to Download
- First run downloads embedding model (~500MB)
- Subsequent runs use cache
- Ensure stable internet connection
- Models are cached in `~/.cache/huggingface`

---

## 📝 Project Structure

```
insurance_portal/
├── backend/
│   ├── main.py                 # FastAPI app
│   ├── rag_pipeline.py         # RAG implementation
│   ├── requirements.txt        # Python dependencies
│   └── documents/              # Add your docs here
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── App.js
│   │   ├── components/
│   │   └── styles/
│   └── package.json
├── README.md                   # Full documentation
├── setup.sh / setup.bat        # Automated setup
└── start.sh / start.bat        # Easy startup
```

---

## 🎯 Next Steps

1. **Customize the application**
   - Add your own insurance documents
   - Customize UI colors in `frontend/src/App.css`
   - Adjust RAG parameters in `backend/rag_pipeline.py`

2. **Integrate with LLM**
   - Update `_generate_answer()` in `rag_pipeline.py`
   - Add OpenAI, Anthropic, or local LLM integration
   - See README.md for LangChain integration examples

3. **Deploy**
   - Use Docker for containerization
   - Deploy frontend to Vercel/Netlify
   - Deploy backend to AWS/Google Cloud/Azure

---

## 📞 Support

For detailed documentation, see the main [README.md](README.md)

Common issues? Check the Troubleshooting section above.

---

**Happy coding! 🎉**
