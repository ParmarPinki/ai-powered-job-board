import json

from database import get_connection
from services.gemini_service import classify_job


def enrich_jobs(api_key: str, batch_size: int, force: bool, job_ids: list[int]) -> dict:
    unique_job_ids = list(dict.fromkeys(job_ids))

    with get_connection() as connection:
        if unique_job_ids:
            placeholders = ", ".join("?" for _ in unique_job_ids)
            where_clause = f"id IN ({placeholders})"
            if not force:
                where_clause += " AND ai_category IS NULL"
            rows = connection.execute(
                f"SELECT id, title, description FROM jobs WHERE {where_clause}",
                unique_job_ids,
            ).fetchall()
        else:
            where_clause = "" if force else "WHERE ai_category IS NULL"
            rows = connection.execute(
                f"SELECT id, title, description FROM jobs {where_clause} ORDER BY id LIMIT ?",
                [batch_size],
            ).fetchall()

    enriched = 0
    failed = 0
    for row in rows:
        try:
            tags = classify_job(api_key, row["title"], row["description"])
            with get_connection() as connection:
                connection.execute(
                    """
                    UPDATE jobs
                    SET ai_skills_json = ?, ai_category = ?, ai_domain = ?, ai_experience = ?
                    WHERE id = ?
                    """,
                    [
                        json.dumps(tags["skills"]),
                        tags["category"],
                        tags["domain"],
                        tags["experience"],
                        row["id"],
                    ],
                )
            enriched += 1
        except ValueError:
            failed += 1

    return {"attempted": len(rows), "enriched": enriched, "failed": failed}
