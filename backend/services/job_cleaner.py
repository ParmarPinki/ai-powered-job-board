import re


KNOWN_SOURCES = {
    "linkedin": "LinkedIn",
    "naukri": "Naukri",
    "indeed": "Indeed",
    "internshala": "Internshala",
}


def normalize_text(value: object) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def to_integer(value: object) -> int | None:
    text = normalize_text(value)
    if not text or text.lower() == "null":
        return None

    match = re.search(r"\d+", text)
    number = int(match.group()) if match else None
    return number if number is not None and number <= 30 else None


def normalize_skills(value: object) -> list[str]:
    raw_skills = value if isinstance(value, list) else normalize_text(value).split(",")
    unique_skills: list[str] = []
    seen_skills: set[str] = set()

    for skill in raw_skills:
        cleaned_skill = normalize_text(skill).rstrip(".")
        key = cleaned_skill.lower()
        if cleaned_skill and key not in seen_skills:
            unique_skills.append(cleaned_skill)
            seen_skills.add(key)

    return unique_skills


def detect_source(value: object) -> str:
    source_text = normalize_text(value).lower()
    for key, label in KNOWN_SOURCES.items():
        if key in source_text:
            return label
    return "Other"


def experience_label(minimum: int | None, maximum: int | None) -> str:
    if minimum is None and maximum is None:
        return "Not specified"
    if maximum is not None and minimum is not None and maximum < minimum:
        maximum = None
    effective_minimum = minimum if minimum is not None else maximum

    if effective_minimum is None:
        return "Not specified"
    if effective_minimum == 0 and (maximum is None or maximum <= 1):
        return "Fresher"
    if effective_minimum <= 2:
        return "0-2 years"
    if effective_minimum <= 5:
        return "3-5 years"
    if effective_minimum <= 10:
        return "6-10 years"
    return "10+ years"


def normalize_job(raw_job: dict) -> dict:
    title = normalize_text(raw_job.get("title")) or "Untitled role"
    company = normalize_text(raw_job.get("company_name")) or "Company not specified"
    location = normalize_text(raw_job.get("location")) or "Location not specified"
    minimum = to_integer(raw_job.get("minExperienceRequired"))
    maximum = to_integer(raw_job.get("maxExperienceRequired"))

    return {
        "source_job_id": normalize_text(raw_job.get("job_id")) or None,
        "title": title,
        "company": company,
        "source": detect_source(raw_job.get("via")),
        "location": location,
        "category": normalize_text(raw_job.get("domain")) or "Other",
        "min_experience": minimum,
        "max_experience": maximum,
        "experience_label": experience_label(minimum, maximum),
        "description": normalize_text(raw_job.get("description")) or "Description not available.",
        "posted_at": normalize_text(raw_job.get("posted_at")) or None,
        "skills": normalize_skills(raw_job.get("skills")),
        "duplicate_key": "|".join([title.lower(), company.lower(), location.lower()]),
    }
