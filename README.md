# ArogyaGrid

ArogyaGrid is a federated AI platform for PHC (Primary Health Centre) supply-chain intelligence and patient prescription literacy. Built for the GDG India hackathon.

## Prerequisites
- **Python 3.12+**
- **Node.js 18+**
- A Gemini API Key (set in `.env`)

---

## How to Run the Project Locally

The project consists of a **FastAPI backend** (running on port 8000) and a **Next.js frontend** (running on port 3000). You need to run both simultaneously in two different terminal windows.

### 1. Start the Backend
Open a new terminal and run the following to start the FastAPI server:
```powershell
cd D:\ArogyaGrid
C:\Python312\python.exe -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
```
*The backend API will be available at `http://localhost:8000` (Swagger UI at `/docs`).*

### 2. Start the Frontend
Open a **second** terminal, navigate to the `frontend` folder, and run:
```powershell
cd frontend
npm install
npm run dev
```
*The web app will be available at `http://localhost:3000`.*

---

## Viewing the App

Currently, the frontend is available at the following URLs:
- **Officer Dashboard:** [http://localhost:3000/dho](http://localhost:3000/dho)
- **Patient App:** [http://localhost:3000/patient](http://localhost:3000/patient)
- **Main Agent Demo:** [http://localhost:3000/](http://localhost:3000/)

> **Note on Background Tasks:** Both the backend and frontend are actually **already running in the background right now** as part of this IDE session. You can view them immediately in your browser without running the commands above!
