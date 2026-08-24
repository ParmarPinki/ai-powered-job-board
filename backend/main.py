import json
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from database import get_connection, initialize_database
from schemas import (
    AssistantRequest,
    AssistantResponse,
    EnrichedJobPreview,
    EnrichmentStatusResponse,
    FilterOptionsResponse,
    ImportResponse,
    JobListResponse,
    JobEnrichmentRequest,
    JobEnrichmentResponse,
    JobResponse,
    JobStatsResponse,
    RecommendedJob,
    RecommendationRequest,
    RecommendationResponse,
    ResumeAnalysisResponse,
    ResumeProfileResponse,
)
from services.gemini_service import ask_gemini
from services.job_enricher import enrich_jobs
from services.job_importer import import_jobs
from services.resume_parser import (
    canonicalize_skills,
    detect_experience,
    detect_experience_years,
    detect_roles,
    extract_resume_text,
    extract_skills,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="AI-Powered Job Board API",
    version="0.1.0",
    description="Job ingestion, filtering, recommendations, and data statistics.",
    lifespan=lifespan,
)

allowed_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def row_to_job(row) -> JobResponse:
    skills_json = row["ai_skills_json"] or row["skills_json"]
    category = row["ai_category"] or row["category"]
    experience = row["ai_experience"] or row["experience_label"]
    return JobResponse(
        id=row["id"],
        source_job_id=row["source_job_id"],
        title=row["title"],
        company=row["company"],
        source=row["source"],
        location=row["location"],
        category=category,
        domain=row["ai_domain"],
        min_experience=row["min_experience"],
        max_experience=row["max_experience"],
        experience=experience,
        description=row["description"],
        posted_at=row["posted_at"],
        skills=json.loads(skills_json),
        is_ai_enriched=row["ai_category"] is not None,
        raw_category=row["category"],
        raw_experience=row["experience_label"],
        raw_skills=json.loads(row["skills_json"]),
    )


def title_matches_resume_roles(title: str, resume_roles: list[str]) -> bool:
    normalized_title = title.lower()
    role_keywords = {
        "Full Stack Developer": ("full stack", "full-stack"),
        "Frontend Developer": ("frontend", "front-end"),
        "Backend Developer": ("backend", "back-end"),
        "Software Engineer": ("software engineer", "software developer"),
        "Data Analyst": ("data analyst",),
        "Data Scientist": ("data scientist",),
        "Machine Learning Engineer": ("machine learning", "ml engineer"),
    }
    return any(
        keyword in normalized_title
        for role in resume_roles
        for keyword in role_keywords.get(role, ())
    )


@app.get("/", tags=["Health"])
def read_root():
    return {"message": "AI-Powered Job Board API is running"}


@app.get("/health", tags=["Health"])
def health_check():
    with get_connection() as connection:
        total_jobs = connection.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    return {"status": "healthy", "database": "connected", "total_jobs": total_jobs}


@app.post("/admin/jobs/import", response_model=ImportResponse, tags=["Administration"])
def import_dataset(
    limit: int = Query(default=1000, ge=1, le=56769),
    clear_existing: bool = Query(default=False),
):
    """Import a bounded batch from the supplied JSON dataset into the configured database."""
    try:
        return import_jobs(limit=limit, clear_existing=clear_existing)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except json.JSONDecodeError as error:
        raise HTTPException(status_code=400, detail="The supplied jobs JSON is invalid.") from error


@app.post(
    "/admin/jobs/enrich",
    response_model=JobEnrichmentResponse,
    tags=["Administration"],
)
def enrich_dataset(request: JobEnrichmentRequest):
    """Use the caller's Gemini key to add AI-extracted tags to a small job batch."""
    return enrich_jobs(
        api_key=request.api_key,
        batch_size=request.batch_size,
        force=request.force,
        job_ids=request.job_ids,
    )


@app.get(
    "/admin/jobs/enrichment-status",
    response_model=EnrichmentStatusResponse,
    tags=["Administration"],
)
def get_enrichment_status():
    with get_connection() as connection:
        total_jobs = connection.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        enriched_jobs = connection.execute(
            "SELECT COUNT(*) FROM jobs WHERE ai_category IS NOT NULL"
        ).fetchone()[0]
        rows = connection.execute(
            """
            SELECT id, title, ai_category, ai_domain, ai_experience, ai_skills_json
            FROM jobs
            WHERE ai_category IS NOT NULL
            ORDER BY id DESC
            LIMIT 5
            """
        ).fetchall()

    return EnrichmentStatusResponse(
        total_jobs=total_jobs,
        enriched_jobs=enriched_jobs,
        remaining_jobs=total_jobs - enriched_jobs,
        sample_enriched_jobs=[
            EnrichedJobPreview(
                id=row["id"],
                title=row["title"],
                ai_category=row["ai_category"],
                ai_domain=row["ai_domain"],
                ai_experience=row["ai_experience"],
                ai_skills=json.loads(row["ai_skills_json"]),
            )
            for row in rows
        ],
    )


@app.get("/jobs", response_model=JobListResponse, tags=["Jobs"])
def get_jobs(
    source: str | None = None,
    skill: str | None = None,
    category: str | None = None,
    experience: str | None = None,
    search: str | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    conditions: list[str] = []
    parameters: list[object] = []

    filter_columns = {
        "source": "source",
        "category": "COALESCE(NULLIF(ai_category, ''), category)",
        "experience": "COALESCE(NULLIF(ai_experience, ''), experience_label)",
    }
    for filter_name, value in (
        ("source", source),
        ("category", category),
        ("experience", experience),
    ):
        if value and value.lower() != "all":
            conditions.append(f"LOWER({filter_columns[filter_name]}) = LOWER(?)")
            parameters.append(value)

    if skill:
        conditions.append("LOWER(COALESCE(ai_skills_json, skills_json)) LIKE LOWER(?)")
        parameters.append(f'%"{skill.strip()}"%')

    if search:
        conditions.append(
            "(LOWER(title) LIKE LOWER(?) OR LOWER(company) LIKE LOWER(?) OR LOWER(description) LIKE LOWER(?))"
        )
        search_term = f"%{search.strip()}%"
        parameters.extend([search_term, search_term, search_term])

    where_clause = f" WHERE {' AND '.join(conditions)}" if conditions else ""

    with get_connection() as connection:
        total = connection.execute(
            f"SELECT COUNT(*) FROM jobs{where_clause}", parameters
        ).fetchone()[0]
        rows = connection.execute(
            f"SELECT * FROM jobs{where_clause} ORDER BY id DESC LIMIT ? OFFSET ?",
            [*parameters, limit, offset],
        ).fetchall()

    return JobListResponse(
        items=[row_to_job(row) for row in rows], total=total, offset=offset, limit=limit
    )


@app.get("/jobs/{job_id}", response_model=JobResponse, tags=["Jobs"])
def get_job(job_id: int):
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM jobs WHERE id = ?", [job_id]).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return row_to_job(row)


@app.get("/filters", response_model=FilterOptionsResponse, tags=["Jobs"])
def get_filter_options():
    with get_connection() as connection:
        sources = [row[0] for row in connection.execute("SELECT DISTINCT source FROM jobs ORDER BY source")]
        categories = [
            row[0]
            for row in connection.execute(
                "SELECT DISTINCT COALESCE(NULLIF(ai_category, ''), category) FROM jobs ORDER BY 1"
            )
        ]
        experience_levels = [
            row[0]
            for row in connection.execute(
                "SELECT DISTINCT COALESCE(NULLIF(ai_experience, ''), experience_label) "
                "FROM jobs ORDER BY 1"
            )
        ]

    return FilterOptionsResponse(
        sources=sources, categories=categories, experience_levels=experience_levels
    )


@app.get("/stats", response_model=JobStatsResponse, tags=["Jobs"])
def get_job_stats():
    with get_connection() as connection:
        total_jobs = connection.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        source_rows = connection.execute(
            "SELECT source, COUNT(*) FROM jobs GROUP BY source ORDER BY COUNT(*) DESC"
        ).fetchall()
        category_rows = connection.execute(
            "SELECT COALESCE(NULLIF(ai_category, ''), category), COUNT(*) FROM jobs "
            "GROUP BY 1 ORDER BY COUNT(*) DESC"
        ).fetchall()

    return JobStatsResponse(
        total_jobs=total_jobs,
        jobs_by_source={row[0]: row[1] for row in source_rows},
        jobs_by_category={row[0]: row[1] for row in category_rows},
    )


@app.post("/recommendations", response_model=RecommendationResponse, tags=["Recommendations"])
def get_recommendations(request: RecommendationRequest):
    resume_skills = canonicalize_skills(request.resume_skills)
    normalized_resume_skills = set(resume_skills)

    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM jobs").fetchall()

    recommendations: list[RecommendedJob] = []
    for row in rows:
        job = row_to_job(row)
        job_skills = canonicalize_skills(job.skills)
        matching_skills = [skill for skill in job_skills if skill in normalized_resume_skills]
        if not matching_skills:
            continue

        skill_coverage = round((len(matching_skills) / len(job_skills)) * 100)
        skill_depth_bonus = min(len(matching_skills) / 5, 1) * 15
        role_bonus = 10 if title_matches_resume_roles(job.title, request.resume_roles) else 0
        experience_bonus = (
            5
            if request.experience_years is not None
            and (job.min_experience is None or job.min_experience <= request.experience_years)
            else 0
        )
        recommendation_score = round(skill_coverage * 0.7 + skill_depth_bonus + role_bonus + experience_bonus)
        job_payload = job.model_dump()
        job_payload["skills"] = job_skills
        recommendations.append(
            RecommendedJob(
                **job_payload,
                matching_skills=matching_skills,
                skill_coverage=skill_coverage,
                recommendation_score=recommendation_score,
            )
        )

    recommendations.sort(
        key=lambda job: (job.recommendation_score, job.skill_coverage, len(job.matching_skills)),
        reverse=True,
    )
    return RecommendationResponse(
        resume_skills=resume_skills,
        items=recommendations[: request.limit],
    )


@app.post("/resumes/analyze", response_model=ResumeAnalysisResponse, tags=["Resumes"])
async def analyze_resume(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="A resume file is required.")

    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Resume files must be 5 MB or smaller.")

    try:
        resume_text = extract_resume_text(file.filename, content)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=400, detail="The resume could not be read.") from error

    return ResumeAnalysisResponse(
        profile=ResumeProfileResponse(
            filename=file.filename,
            skills=extract_skills(resume_text),
            roles=detect_roles(resume_text),
            detected_experience=detect_experience(resume_text),
            experience_years=detect_experience_years(resume_text),
        )
    )


@app.post("/assistant/chat", response_model=AssistantResponse, tags=["AI Assistant"])
def chat_with_assistant(request: AssistantRequest):
    job_ids = list(dict.fromkeys(request.job_ids))
    with get_connection() as connection:
        if job_ids:
            placeholders = ", ".join("?" for _ in job_ids)
            rows = connection.execute(
                f"SELECT * FROM jobs WHERE id IN ({placeholders})", job_ids
            ).fetchall()
        else:
            rows = connection.execute("SELECT * FROM jobs ORDER BY id DESC LIMIT 10").fetchall()

    job_context = [row_to_job(row).model_dump() for row in rows]
    try:
        answer = ask_gemini(
            api_key=request.api_key,
            question=request.question,
            resume_skills=request.resume_skills,
            jobs=job_context,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return AssistantResponse(answer=answer)
