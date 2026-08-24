# Explanation Video Script

Target length: 6 to 8 minutes. Record in English. Keep Swagger, the frontend, and this project README ready before recording.

## Before Recording

1. Start the backend and frontend.
2. Confirm `GET /health` reports the full imported database.
3. In Swagger, run `POST /admin/jobs/enrich` with your own Gemini key and `batch_size` set to 5. This gives you real AI-enriched examples to show.
4. Keep one PDF, DOCX, or TXT resume ready for upload.
5. Never show your Gemini key on screen. Paste it with the recorder paused, or blur the field.

## Script

### 0:00 - 0:30: Introduction

“Hello, this is my AI-Powered Job Board. The goal is to help users discover job opportunities, understand job requirements, receive resume-based recommendations, and ask career questions with Gemini.”

### 0:30 - 1:30: Job Discovery

Show the home page.

“The frontend is built with React and Vite. Jobs are not hard-coded in the UI. The frontend requests paginated data from the FastAPI backend. I can filter by source, skill, role category, and experience level. The filter values are loaded dynamically from the database.”

Select a source, search a skill such as `Python`, and move to the next page.

### 1:30 - 2:30: Data Ingestion and Deduplication

Open Swagger and show `POST /admin/jobs/import`, then `GET /stats`.

“The supplied JSON file is the source dataset. The import service normalizes titles, companies, locations, skills, and experience fields before saving them into SQLite. To detect duplicates, I build a normalized key from title, company, and location. From 56,769 raw records, the import produced 45,853 unique jobs, so duplicate listings are not shown repeatedly.”

### 2:30 - 3:30: Architecture

Show the README architecture diagram.

“The React frontend calls FastAPI over HTTP. FastAPI handles data ingestion, filtering, resume analysis, recommendations, and Gemini integration. SQLite stores the cleaned jobs locally. For deployment, SQLite can be replaced with hosted PostgreSQL without changing the frontend API.”

### 3:30 - 4:20: AI Job Enrichment

Show Swagger `POST /admin/jobs/enrich` and the response from a small completed batch. Return to the frontend and show an enriched job.

“The enrichment endpoint sends a bounded batch of job titles and descriptions to Gemini. Gemini extracts structured skills, role category, and experience information. These AI-generated fields are stored separately from the original data, so the source data remains available and enriched values can be used for filters and recommendations.”

### 4:20 - 5:15: Resume and Recommendations

Upload your resume.

“The backend accepts PDF, DOCX, and TXT files. It extracts resume text in memory, finds matching skills from the jobs database, and does not store the uploaded file. Recommendations show both a match percentage and exact matching skills, so the result is explainable.”

### 5:15 - 6:15: Gemini Job Assistant

Enter your key off-camera. Choose a suggested question, such as “Which jobs should I apply for?”

“The user provides their own Gemini API key. It is sent only for the current request and is not stored. The backend gives Gemini the current visible job context and extracted resume skills, which allows the assistant to answer questions about job fit, missing skills, and preparation.”

### 6:15 - 7:00: Decisions, Limitations, and Closing

“I chose a backend-first data flow because the original JSON is large and should not be filtered directly in the browser. I use SQLite locally for simple persistent storage, and I would use PostgreSQL in deployment. AI enrichment runs in small batches to control cost. One limitation is that image-only PDFs may not produce readable text. Thank you for watching.”
