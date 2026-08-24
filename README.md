# AI-Powered Job Board

- **Live prototype:** [https://ai-powered-job-board-gray.vercel.app/](https://ai-powered-job-board-gray.vercel.app/)
- **Backend API documentation:** [https://ai-powered-job-board-twyn.onrender.com/docs](https://ai-powered-job-board-twyn.onrender.com/docs)
- **Explanation video:** 

An AI-powered job board built with React, FastAPI, Supabase Postgres, and Gemini. It processes the supplied multi-platform job dataset, removes duplicate listings, supports filtered discovery, analyzes uploaded resumes, recommends relevant jobs, and provides a Gemini-powered job assistant.

## Features

- Imports the supplied JSON dataset into a persistent database.
- Normalizes incomplete job fields and removes duplicate listings using a normalized title, company, and location key.
- Filters by job source, skill, category, experience, and keyword search.
- Supports paginated job browsing.
- Extracts skills and experience from PDF, DOCX, and TXT resumes without storing uploaded files.
- Recommends jobs with matching skills and an explainable match score.
- Uses a caller-provided Gemini API key for a contextual job assistant without saving the key.
- Provides Gemini enrichment that extracts skills, role category, business domain, and experience tags while preserving original dataset tags for comparison.

## Architecture

```text
React + Vite frontend (Vercel)
        |
        | HTTP API
        v
FastAPI backend (Render)
  |-- JSON import + normalization + deduplication
  |-- Supabase Postgres database
  |-- resume parser + recommendation logic
  |-- Gemini assistant + AI job enrichment
```

The raw JSON file is an import source. The frontend never reads it directly. The backend loads it into the database, and the frontend queries the API for only the jobs it needs.

## Technology Stack

- Frontend: React, Vite, CSS
- Backend: FastAPI, Uvicorn, Python
- Production database: Supabase Postgres
- Local development fallback: SQLite
- Hosting: Vercel (frontend), Render (backend)
- Resume parsing: pypdf, python-docx
- LLM: Gemini `generateContent` API

## Local Setup

### 1. Dataset

Download the supplied assignment dataset and place it at:

```text
data/jobs.json
```

It is intentionally excluded from Git because it is too large for a normal GitHub repository.

### 2. Backend

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Open Swagger at `http://127.0.0.1:8000/docs`.

Use `POST /admin/jobs/import` to create the local database. Set `limit` to `56769` to import the whole supplied dataset.

To use Supabase locally, copy `backend/.env.example` to `backend/.env` and set a private `DATABASE_URL`. Never commit this file.

### 3. Frontend

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## API Overview

| Endpoint | Purpose |
| --- | --- |
| `GET /jobs` | Paginated filtered jobs |
| `GET /filters` | Available source/category/experience options |
| `GET /stats` | Database totals and source/category counts |
| `POST /resumes/analyze` | Extract skills from a resume file |
| `POST /recommendations` | Return explainable skill-based matches |
| `POST /assistant/chat` | Gemini-powered job assistant |
| `POST /admin/jobs/import` | JSON ingestion and deduplication |
| `POST /admin/jobs/enrich` | Gemini batch enrichment using a user-provided key |

## AI Components

### AI enrichment

In Swagger, call `POST /admin/jobs/enrich` with your Gemini API key and a small `batch_size`. Gemini returns structured skills, role category, business domain, and experience values. Those values are stored separately from the supplied raw fields and take priority in filters and recommendations. The UI shows an `AI enriched` badge and lets users view the original dataset tags.

### Resume recommendations

The backend extracts resume text locally, detects skills and role signals, then ranks matching opportunities using:

```text
skill coverage + matched-skill depth + role relevance + experience fit
```

This makes each recommendation explainable through its displayed matched skills, skill coverage, and recommendation score. The implementation streams database jobs and retains only the best matches to remain suitable for the deployed service.

### Security

- Gemini keys are received only for the active request and are never saved in the database, a file, or browser storage.
- Resume files are parsed in memory and are not persisted.
- `.env` files, the raw dataset, and local databases are excluded from Git.

## Limitations and Next Steps

- The deployed service uses Supabase Postgres; SQLite remains only as a local fallback when `DATABASE_URL` is not configured.
- AI enrichment intentionally runs in small batches to control API usage and cost.
- Text extraction may not work for image-only or password-protected PDFs.
- Job source detection uses the supplied `via` field; records from other providers are labelled `Other`.

## Submission Checklist

- [x] Add the deployed prototype URL.
- [x] Add the deployed API documentation URL.
- [x] Replace the explanation video URL above.
- [x] Verify the GitHub repository is public.
- [x] Verify the video is accessible to anyone with the link.
- [x] Verify no secrets, local SQLite databases, or raw dataset are committed.
