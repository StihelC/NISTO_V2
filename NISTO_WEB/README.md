# NISTO Web Migration

NISTO Web is the in-progress migration of the original PyQt5-based network topology tool into a modern web stack powered by FastAPI and React. The goal is to deliver a browser-friendly experience that maintains the core workflow of the desktop app while laying the groundwork for future collaboration features.

## MVP Scope
- Devices: create, list, edit, delete, basic configuration fields
- Connections: CRUD operations linking devices with typed properties
- Properties panel: edit properties for selected devices or connections
- Undo/Redo: client-side state history for CRUD and property edits
- Health check endpoint and basic logging
- Embed support: render safely inside Notion via CSP headers

## Stack Overview
- Backend: FastAPI, SQLAlchemy, Pydantic v2, SQLite (dev), pytest
- Frontend: React + Vite + TypeScript, Redux Toolkit, React Router, Vitest
- Tooling: Docker Compose with nginx proxy for unified dev/prod workflows

## Getting Started
1. **Backend setup**
   ```bash
   cd NISTO_WEB
   python -m venv .venv
   source .venv/bin/activate
   pip install -r backend/requirements.txt
   uvicorn app.main:app --reload --port 8000
   ```
2. **Frontend setup**
   ```bash
   cd NISTO_WEB/frontend
   pnpm install
   pnpm dev
   ```
3. **Docker Compose (optional)**
   ```bash
   cd NISTO_WEB
   docker compose -f deploy/docker-compose.yml up --build
   ```
   - `backend`: runs FastAPI on port 8000 with live code mounting
   - `frontend`: runs Vite dev server on port 5173 with hot reload
   - `nginx`: proxies http://localhost to frontend (/api routes → backend)

## Testing
- Backend: `pytest -q backend/tests`
- Frontend: `cd frontend && pnpm test`

## Development Scripts

A helper script is available to tear down and relaunch the dockerized stack:

```bash
./scripts/run_dev.sh
```

This script:
- Stops existing services defined in `deploy/docker-compose.yml`
- Removes orphaned containers
- Rebuilds images and brings the stack back up (frontend + backend + nginx)

## Project Structure
```
NISTO_WEB/
├── backend/
│   ├── app/
│   └── tests/
├── frontend/
│   ├── public/
│   └── src/
│       ├── api/
│       ├── components/
│       ├── pages/
│       └── store/
├── deploy/
└── README.md
```

## Next Steps
- Scaffold FastAPI backend modules (`main.py`, `models.py`, `schemas.py`, `crud.py`, `api.py`)
- Add backend tests covering device and connection CRUD flows
- Scaffold React frontend with Redux store and core components
- Implement undo/redo middleware and Notion embedding support

