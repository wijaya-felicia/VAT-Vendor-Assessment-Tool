# Complete Setup Guide - Vendor Assessment Tool

## 📋 Overview

This is a full-stack Bayesian vendor assessment application with:

- **Backend**: FastAPI (Python) on http://localhost:8000
- **Frontend**: Next.js (React) on http://localhost:3000
- **Database**: SQLite
- **Analytics**: Bayesian Hierarchical Model with PyMC

---

## 🔧 Backend Setup

### Prerequisites

- Python 3.9+
- Conda environment manager

### Step 1: Activate Backend Environment

```bash
# Navigate to backend
cd backend

# Activate conda environment (should already exist: "Thesis")
conda activate Thesis
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Run Backend Server

```bash
python main.py
```

**Expected output:**

```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

Access API docs: http://localhost:8000/docs

**Key Endpoints:**

- POST `/api/v1/auth/login` - Login
- POST `/api/v1/auth/register` - Register
- POST `/api/v1/upload` - Upload files
- GET `/api/v1/dashboard/metrics` - Dashboard metrics
- GET `/api/v1/bhm/rankings` - Vendor rankings
- POST `/api/v1/bhm/model/lock` - Lock model

---

## 🎨 Frontend Setup

### Prerequisites

- Node.js 18+ (v23.6.1 tested ✓)
- npm or yarn

### Step 1: Navigate to Frontend

```bash
cd frontend
```

### Step 2: Install Dependencies

```bash
npm install
```

**Install time:** ~2-3 minutes  
**Node version check:** `node --version`

### Step 3: Configure Environment

Create/verify `.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### Step 4: Run Development Server

```bash
npm run dev
```

**Expected output:**

```
> vendor-assessment-tool@1.0.0 dev
> next dev

  ▲ Next.js 14.0.0
  - Local:        http://localhost:3000
  - Environments: .env.local
```

Access the app: http://localhost:3000

---

## ✅ Verification Checklist

### Backend Ready

- [ ] `python main.py` running without errors
- [ ] http://localhost:8000/docs shows API documentation
- [ ] CORS headers present in responses

### Frontend Ready

- [ ] `npm run dev` running without errors
- [ ] http://localhost:3000 loads without errors
- [ ] Navbar shows "Login" link (unauthenticated)

### Integration Test

1. Go to http://localhost:3000/login
2. Register new user (any email/password)
3. Should redirect to dashboard
4. Upload test Excel files (from `backend/sample\ data/`)
5. Should see metrics cards and charts
6. Click "Rankings" to view vendor scores

---

## 📁 Project Structure

```
App_1/
├── backend/
│   ├── main.py                 # FastAPI server
│   ├── requirements.txt        # Python dependencies
│   ├── src/
│   │   ├── database/           # SQLAlchemy models
│   │   ├── routers/            # API endpoints
│   │   ├── services/           # Business logic (BHM)
│   │   └── modules/            # Data pipeline
│   └── sample\ data/           # Test Excel files
│
└── frontend/
    ├── package.json            # Node dependencies
    ├── .env.local             # API configuration
    ├── app/                   # Next.js app pages
    ├── components/            # React components
    ├── lib/                   # Utilities
    ├── hooks/                 # Custom hooks
    ├── store/                 # Zustand stores
    ├── types/                 # TypeScript types
    └── globals.css            # Global styles
```

---

## 🚀 Quick Start (Terminal Commands)

### Terminal 1: Backend

```bash
cd backend
conda activate Thesis
python main.py
```

### Terminal 2: Frontend

```bash
cd frontend
npm install  # First time only
npm run dev
```

### Terminal 3 (Optional): Tail Logs

```bash
# Watch for API calls in browser console
# (DevTools -> Console)
```

---

## 🔐 Authentication Flow

1. User visits http://localhost:3000
2. Redirects to `/login` (no session)
3. Register or login with credentials
4. Backend generates JWT token
5. Frontend stores token in localStorage
6. Token sent in `Authorization: Bearer <token>` for all requests
7. 401 errors redirect back to login

---

## 📊 Workflow

### First Time Users

1. **Register** at `/register`
2. **Dashboard** at `/dashboard`
    - Upload 3 Excel files (PO, OC, SHIP)
    - System validates and merges data
    - Session ID created
3. **Metrics** appear on dashboard
    - Total transactions
    - Vendor count
    - Price/delay statistics
4. **Rankings** at `/rankings`
    - Shows Bayesian vendor scores
    - 95% confidence intervals
    - MCMC diagnostics
5. **Vendor Detail** at `/rankings/[vendor-name]`
    - Individual performance metrics
    - Convergence diagnostics
6. **Admin** at `/admin`
    - Lock model for audit year
    - Enables Bayesian updating for next year

---

## 🛠️ Development

### Frontend Development

**Add new page:**

```bash
# Create file: app/newpage/page.tsx
'use client'
import { Container } from 'react-bootstrap'
export default function NewPage() {
  return <Container>New Page</Container>
}
```

**Use API:**

```typescript
import { api } from "@/lib/api";
import { API_ENDPOINTS } from "@/lib/constants";

const response = await api.get(API_ENDPOINTS.DASHBOARD.METRICS, {
    params: { session_id: sessionId },
});
```

**Use hooks:**

```typescript
import { useDashboardMetrics } from "@/hooks/useDashboard";

const { data, isLoading, error } = useDashboardMetrics(sessionId);
```

### Backend Development

**Add new endpoint:**

```python
# In src/routers/myrouter.py
from fastapi import APIRouter, Depends
from src.dependencies.auth import get_current_user

router = APIRouter(prefix="/my", tags=["my"])

@router.get("/endpoint")
async def my_endpoint(current_user: User = Depends(get_current_user)):
    return {"message": "Hello"}
```

---

## 📦 Build for Production

### Frontend

```bash
npm run build
npm start
```

### Backend

```bash
# Using Gunicorn with multiple workers
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

---

## 🐛 Troubleshooting

### Frontend won't connect to API

- [ ] Backend running? (http://localhost:8000/docs)
- [ ] .env.local has correct API URL?
- [ ] CORS enabled in backend?

### npm install hangs

```bash
# Clear npm cache and retry
npm cache clean --force
npm install
```

### Python dependencies conflict

```bash
# Rebuild environment
conda activate Thesis
pip install -r requirements.txt --upgrade --force-reinstall
```

### Port already in use

```bash
# Backend (change in main.py)
python main.py --port 8001

# Frontend (Next.js auto-fallback or)
PORT=3001 npm run dev
```

---

## 📞 Support

**API Documentation**: http://localhost:8000/docs  
**Frontend Dev Tools**: http://localhost:3000 -> DevTools (F12)  
**Console Logs**: Check browser console for API call debugging

Colors indicate:

- 🔵 Blue: API request sent
- ✅ Green: API success response
- ❌ Red: API error

---

## 📝 Notes

- First upload will take ~30-60s (MCMC sampling)
- Subsequent requests use cached results
- Model locking is irreversible
- Token expires after 24 hours (can be configured)
- Database is SQLite by default (portable, no server needed)
