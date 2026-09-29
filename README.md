# ArogyaGrid 🏥

> **Federated AI Platform for PHC Supply-Chain Intelligence & Patient Prescription Literacy**
> Built for the GDG India Hackathon — powered entirely by Google AI & Google Cloud.

ArogyaGrid connects Primary Health Centres (PHCs) across India using a multi-agent AI system to predict drug stockouts, optimize redistribution, explain prescriptions to patients in local languages, and surface epidemiological signals — all while keeping patient data within state boundaries.

---

## 📋 Table of Contents

- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Environment Setup](#environment-setup)
- [Running the Backend](#running-the-backend)
- [Running the Frontend](#running-the-frontend)
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────┐
│                   Frontend                       │
│         Next.js PWA (port 3000)                  │
│   /dho  •  /patient  •  / (demo)                │
└─────────────────┬───────────────────────────────┘
                  │ HTTP / REST
┌─────────────────▼───────────────────────────────┐
│                  Backend                         │
│          FastAPI Server (port 8000)              │
│                                                  │
│  /api/stock   /api/alerts   /api/forecast        │
│  /api/redistribution        /api/prescription    │
│  /api/dashboard             /api/demo            │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│             AI Agent Layer                       │
│  Gemini 1.5 Flash • Document AI • Imagen 3       │
│  Vertex AI Forecasting • Cloud Translation       │
└─────────────────────────────────────────────────┘
```

---

## ✅ Prerequisites

Make sure the following are installed on your system:

| Tool | Version | Download |
|------|---------|----------|
| **Python** | 3.12+ | https://python.org/downloads |
| **Node.js** | 18+ | https://nodejs.org |
| **npm** | 9+ | Bundled with Node.js |
| **Git** | Any | https://git-scm.com |

You will also need:
- A **Google Gemini API Key** → get one at https://aistudio.google.com/app/apikey
- *(Optional)* A GCP Project ID if using real Vertex AI / Document AI services

---

## 📁 Project Structure

```
ArogyaGrid/
├── backend/                  # FastAPI Python backend
│   ├── api/
│   │   ├── main.py           # App entry point
│   │   └── routes/           # Route handlers
│   │       ├── stock.py      # Stock management endpoints
│   │       ├── alerts.py     # Early warning alerts
│   │       ├── forecast.py   # Demand forecasting
│   │       ├── redistribution.py  # Drug redistribution optimizer
│   │       ├── prescription.py    # Prescription explainer
│   │       ├── dashboard.py  # DHO/state dashboard
│   │       └── demo.py       # Demo & seed data
│   ├── agents/               # AI agent implementations
│   ├── providers/            # Service provider stubs/real impls
│   ├── data/                 # SQLite DB & data models
│   ├── config.py             # App configuration
│   └── requirements.txt      # Python dependencies
├── frontend/                 # Next.js frontend (PWA)
├── data/                     # Shared data & poster images
├── .env.example              # Environment variable template
├── arogya_grid.db            # SQLite database (dev)
└── README.md
```

---

## ⚙️ Environment Setup

### 1. Clone the repository
```bash
git clone https://github.com/your-org/ArogyaGrid.git
cd ArogyaGrid
```

### 2. Create your `.env` file
```powershell
# Windows
copy .env.example .env
```
```bash
# macOS / Linux
cp .env.example .env
```

### 3. Fill in your API keys
Open `.env` and update the following values:

```env
# ── Required ──────────────────────────────────────
GOOGLE_API_KEY=your-gemini-api-key-here     # Get from aistudio.google.com

# ── Optional (GCP) ────────────────────────────────
GOOGLE_PROJECT_ID=your-gcp-project-id
GOOGLE_REGION=us-central1

# ── Provider Switches (keep false for local demo) ─
USE_REAL_GEMINI=true        # Uses Gemini SDK with GOOGLE_API_KEY
USE_REAL_FORECAST=false     # false = local heuristic stub
USE_REAL_OCR=false          # false = Gemini multimodal stub
USE_REAL_IMAGEN=false       # false = Pillow image render stub
USE_REAL_TRANSLATE=false    # false = Gemini translation stub

# ── App Settings ──────────────────────────────────
GEMINI_MODEL=gemini-1.5-flash
DEMO_LANGUAGE=en
STOCKOUT_LEAD_DAYS=14
SAFETY_STOCK_DAYS=7
```

> **Tip:** For a local demo, you only **need** `GOOGLE_API_KEY`. All other switches can stay at their defaults.

---

## 🐍 Running the Backend

Open a terminal in the project root (`ArogyaGrid/`).

### Step 1 — Install Python dependencies
```powershell
C:\Python312\python.exe -m pip install -r backend\requirements.txt
```

### Step 2 — Start the FastAPI server
```powershell
C:\Python312\python.exe -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
```

> ⚠️ **Important:** Always run from the **project root** (`ArogyaGrid/`), not from inside `backend/`. The app uses root-relative imports.

**Expected output:**
```
INFO:     Will watch for changes in these directories: ['E:\ArogyaGrid']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process using WatchFiles
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Backend URLs

| URL | Description |
|-----|-------------|
| http://localhost:8000 | API root / health check |
| http://localhost:8000/docs | **Swagger UI** — interactive API explorer |
| http://localhost:8000/redoc | ReDoc API documentation |
| http://localhost:8000/posters | Static poster images |

---

## 🌐 Running the Frontend

Open a **second terminal** and navigate to the `frontend/` folder.

### Step 1 — Install Node dependencies
```powershell
cd frontend
npm install
```

### Step 2 — Start the dev server
```powershell
npm run dev
```

**Expected output:**
```
▲ Next.js 14.x
- Local:   http://localhost:3000
- Ready in Xs
```

### Frontend URLs

| URL | Who it's for |
|-----|--------------|
| http://localhost:3000/ | Main demo / Orchestrator agent |
| http://localhost:3000/dho | District Health Officer dashboard |
| http://localhost:3000/patient | Patient prescription explainer |

---

## 🚀 Running Both Together (Quick Reference)

**Terminal 1 — Backend:**
```powershell
cd ArogyaGrid
C:\Python312\python.exe -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 — Frontend:**
```powershell
cd ArogyaGrid\frontend
npm install
npm run dev
```

---

## 📡 API Reference

The backend exposes the following route groups (explore all at `/docs`):

| Route Prefix | Description |
|---|---|
| `GET /` | Health check |
| `/api/demo` | Demo data seeding & agent showcase |
| `/api/stock` | PHC stock levels — read & update |
| `/api/alerts` | Early warning stockout alerts |
| `/api/forecast` | Drug demand forecasting per PHC |
| `/api/redistribution` | Cross-PHC redistribution suggestions |
| `/api/prescription` | Prescription OCR + patient explanation |
| `/api/dashboard` | Aggregated DHO / state-level dashboards |

---

## 🔧 Troubleshooting

### `No module named uvicorn`
```powershell
C:\Python312\python.exe -m pip install -r backend\requirements.txt
```

### `ModuleNotFoundError` when starting backend
Make sure you are running the command **from the project root**, not from inside `backend/`:
```powershell
# ✅ Correct
cd ArogyaGrid
C:\Python312\python.exe -m uvicorn backend.api.main:app ...

# ❌ Wrong
cd ArogyaGrid\backend
python -m uvicorn api.main:app ...
```

### Port 8000 already in use
```powershell
# Find and kill the process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Frontend can't reach backend (CORS errors)
Ensure the backend is running on port 8000 **before** starting the frontend. The backend is configured with permissive CORS for local development.

### `.env` not being picked up
Confirm `.env` exists at the **project root** (same level as `backend/` and `frontend/`), not inside `backend/`.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.12, FastAPI, SQLAlchemy, Uvicorn |
| **Frontend** | Next.js (PWA), React |
| **AI / Agents** | Gemini 1.5 Flash, Google Generative AI SDK |
| **Database** | SQLite (dev) → BigQuery / Firestore (prod) |
| **OCR** | Gemini multimodal stub → Document AI (prod) |
| **Forecasting** | Local heuristic stub → BigQuery ML ARIMA_PLUS (prod) |
| **Image Gen** | Pillow stub → Imagen 3 via Vertex AI (prod) |
| **Translation** | Gemini stub → Cloud Translation API (prod) |

---

## 📄 License

Built for the GDG India Hackathon. See individual source files for license information.
