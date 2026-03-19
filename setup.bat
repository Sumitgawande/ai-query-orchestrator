@echo off
echo 🚀 Insurance Portal RAG Application Setup
echo ==========================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.8+
    exit /b 1
)

echo ✅ Python is installed

REM Setup backend
echo.
echo 📦 Setting up backend...
cd backend

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo Installing Python dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo ✅ Backend setup complete
cd ..

REM Setup frontend
echo.
echo 📦 Setting up frontend...
cd frontend

if not exist "node_modules" (
    echo Installing npm dependencies...
    call npm install
)

echo ✅ Frontend setup complete
cd ..

echo.
echo ✅ Setup complete!
echo.
echo To start the application:
echo 1. Backend:  cd backend ^&^& source venv\Scripts\activate.bat ^&^& python main.py
echo 2. Frontend: cd frontend ^&^& npm start
echo.
echo Then open http://localhost:3000 in your browser
