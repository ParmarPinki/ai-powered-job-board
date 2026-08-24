import json
from pathlib import Path

from database import get_connection
from services.job_cleaner import normalize_job


RAW_DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "jobs.json"


def import_jobs(limit: int, clear_existing: bool) -> dict:
    if not RAW_DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found at {RAW_DATA_PATH}")

    with RAW_DATA_PATH.open(encoding="utf-8") as source_file:
        raw_jobs = json.load(source_file)

    normalized_jobs = [normalize_job(raw_job) for raw_job in raw_jobs[:limit]]

    with get_connection() as connection:
        if clear_existing:
            connection.execute("DELETE FROM jobs")

        total_before = connection.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        connection.executemany(
            """
            INSERT INTO jobs (
                source_job_id, title, company, source, location, category,
                min_experience, max_experience, experience_label, description,
                posted_at, skills_json, duplicate_key
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(duplicate_key) DO NOTHING
            """,
            [
                (
                    job["source_job_id"], job["title"], job["company"], job["source"],
                    job["location"], job["category"], job["min_experience"],
                    job["max_experience"], job["experience_label"], job["description"],
                    job["posted_at"], json.dumps(job["skills"]), job["duplicate_key"],
                )
                for job in normalized_jobs
            ],
        )
        total_jobs = connection.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        inserted = total_jobs - total_before

    return {
        "processed": len(normalized_jobs),
        "inserted": inserted,
        "skipped_as_duplicates": len(normalized_jobs) - inserted,
        "total_jobs_in_database": total_jobs,
    }
