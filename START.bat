@echo off
REM Vendor Assessment Tool - Quick Start Script
REM This script starts both backend and frontend

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║                                                                ║
echo ║         ⚡ VENDOR ASSESSMENT TOOL - QUICK START ⚡             ║
echo ║                                                                ║
echo ║    Bayesian Hierarchical Model for Vendor Performance         ║
echo ║                                                                ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

echo 📋 INSTRUCTIONS:
echo.
echo This script will guide you through starting the system.
echo You will need 2 terminal windows:
echo   1. Backend (FastAPI) - http://localhost:8000
echo   2. Frontend (Next.js) - http://localhost:3000
echo.
echo ========================================
echo.
echo 🔧 STEP 1: Start Backend
echo.
echo Open a NEW terminal and run:
echo.
echo   cd backend
echo   conda activate Thesis
echo   python main.py
echo.
echo Wait for: "Uvicorn running on http://0.0.0.0:8000"
echo.
echo ========================================
echo.
echo 🎨 STEP 2: Start Frontend
echo.
echo Open ANOTHER NEW terminal and run:
echo.
echo   cd frontend
echo   npm run dev
echo.
echo Wait for: "▲ Next.js 14.0.0"
echo.
echo ========================================
echo.
echo 🌐 STEP 3: Access the Application
echo.
echo Open your browser to:
echo   http://localhost:3000
echo.
echo Login/Register with any credentials
echo.
echo ========================================
echo.
echo 📊 TEST WORKFLOW:
echo.
echo 1. Upload PO, OC, SHIP files from: backend/sample\ data/
echo 2. View metrics on Dashboard
echo 3. Go to Rankings to see Bayesian scores
echo 4. Click vendor name to see details
echo 5. Admin panel to lock model
echo.
echo ========================================
echo.
echo 💡 TROUBLESHOOTING:
echo.
echo Backend won't start?
echo   - Check: conda activate Thesis
echo   - Check: Python 3.9+ installed
echo   - Check: Port 8000 not in use
echo.
echo Frontend won't start?
echo   - Check: npm install completed
echo   - Check: Node 18+ installed (node --version)
echo   - Check: .env.local has NEXT_PUBLIC_API_URL
echo.
echo Can't upload files?
echo   - Make sure backend is running first
echo   - Check browser console (F12) for API errors
echo   - Check backend logs
echo.
echo ========================================
echo.
echo Press any key to open the quick start guide...
pause

REM Open SETUP.md if it exists
if exist SETUP.md (
    start notepad SETUP.md
)

echo.
echo ✅ Ready to start! Follow the steps above in your terminals.
echo.
