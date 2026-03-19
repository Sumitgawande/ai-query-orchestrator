@echo off
echo 🚀 Starting Insurance Portal RAG Application
echo ===========================================

REM Start backend in background
echo Starting backend...
cd backend
call ..\venv\Scripts\activate.bat
start "Backend" python main.py
cd ..

REM Wait for backend to start
timeout /t 5 /nobreak

REM Start frontend
echo Starting frontend...
cd frontend
start "Frontend" cmd /k npm start
cd ..

echo.
echo ✅ Application started!
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo.
echo Close the command windows to stop the application
