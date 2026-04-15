# EntryLens

EntryLens is a local development workspace for a face-recognition attendance and identity review system. The repository contains:

- `entrylens-api/`: FastAPI backend
- `entrylens-frontend/`: React + Vite frontend
- `scripts/dev.ps1`: root launcher that starts both apps together
- `runtime-data/`: local runtime storage for captured sample images

## Prerequisites

Install these before running the project:

- Node.js 20+ with `npm`
- Python 3.11+ with `pip`
- PowerShell
- A Supabase project

This project uses Supabase for identity, embedding, and detection-log data. Without valid Supabase credentials, the UI can start, but most of the core recognition and identity flows will not work correctly.

## Environment Setup

1. Copy the root environment template:

```powershell
Copy-Item .env.example .env
```

2. Update `.env` with your real values.

Minimum values you should review:

- `SENTINEL_API_KEY`
- `SENTINEL_ALLOWED_ORIGINS`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`
- `SUPABASE_DB_URL`
- `VITE_API_BASE_URL`
- `VITE_API_KEY`
- `VITE_WS_BASE_URL`

Notes:

- The backend reads the root `.env`.
- The frontend uses the `VITE_*` values from the same root `.env`.
- `SENTINEL_API_KEY` and `VITE_API_KEY` should match for local development.

## Supabase Setup

You need to create the database objects used by the app.

1. Open your Supabase project.
2. Go to the SQL Editor.
3. Run the SQL in `entrylens-api/setup_supabase.sql`.

That script creates the core extension, tables, and matching function needed by the app.

The repository also includes `entrylens-api/setup_supabase.py`, but it currently contains a hard-coded path from an older workspace, so `setup_supabase.sql` is the safer setup path.

## Install Dependencies

Install frontend dependencies:

```powershell
npm install --prefix entrylens-frontend
```

Install backend dependencies:

```powershell
python -m pip install -r entrylens-api/requirements.txt
```

## Run The Project

### Recommended: start both apps together

From the repository root:

```powershell
npm run dev
```

This starts:

- API: `http://127.0.0.1:8000`
- Frontend: `http://127.0.0.1:5173`

### Run services separately

Backend only:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --app-dir entrylens-api
```

Frontend only:

```powershell
npm run dev --prefix entrylens-frontend
```

## First Run Checklist

Before using the app, make sure:

1. `.env` exists at the repo root.
2. Supabase credentials are filled in.
3. `entrylens-api/setup_supabase.sql` has been run in Supabase.
4. Frontend dependencies are installed.
5. Backend Python dependencies are installed.
6. `npm run dev` starts both services without errors.

## Useful URLs

- Frontend app: `http://127.0.0.1:5173`
- API base: `http://127.0.0.1:8000`
- Health check: `http://127.0.0.1:8000/health`

## Project Structure

```text
.
|-- entrylens-api/
|-- entrylens-frontend/
|-- scripts/
|-- runtime-data/
|-- .env.example
|-- package.json
`-- README.md
```

## Troubleshooting

- If the frontend loads but API calls fail, check that `VITE_API_BASE_URL` points to the running backend.
- If requests return unauthorized errors, check that `SENTINEL_API_KEY` and `VITE_API_KEY` match.
- If identity or recognition features fail, verify your Supabase schema has been created and your service key is valid.
- If `npm run dev` fails to start the backend, confirm `python` is available in your shell and the backend dependencies were installed.
