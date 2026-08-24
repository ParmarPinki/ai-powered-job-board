import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


MODELS_URL = "https://generativelanguage.googleapis.com/v1beta/models"
GENERATE_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
PREFERRED_MODELS = (
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-flash-latest",
)


def get_supported_model(api_key: str) -> str:
    request = Request(MODELS_URL, headers={"x-goog-api-key": api_key})

    try:
        with urlopen(request, timeout=15) as response:
            models = json.load(response).get("models", [])
    except HTTPError as error:
        if error.code in {400, 401, 403}:
            raise ValueError("Gemini rejected this API key.") from error
        raise ValueError("Could not retrieve the models available to this API key.") from error
    except URLError as error:
        raise ValueError("Could not reach Gemini. Check your internet connection.") from error

    available_models = {
        model.get("name", "").removeprefix("models/")
        for model in models
        if "generateContent" in model.get("supportedGenerationMethods", [])
    }
    for model in PREFERRED_MODELS:
        if model in available_models:
            return model

    raise ValueError("This API key has no supported Gemini text-generation model.")


def generate_text(api_key: str, prompt: str) -> str:
    model = get_supported_model(api_key)
    payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
    request = Request(
        GENERATE_URL_TEMPLATE.format(model=model),
        data=payload,
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        method="POST",
    )

    try:
        with urlopen(request, timeout=30) as response:
            response_data = json.load(response)
    except HTTPError as error:
        try:
            error_data = json.loads(error.read().decode("utf-8"))
            provider_message = error_data.get("error", {}).get("message", "")
        except (json.JSONDecodeError, UnicodeDecodeError):
            provider_message = ""

        if error.code in {400, 401, 403}:
            raise ValueError(
                provider_message or "Gemini rejected the API key or request."
            ) from error
        if error.code == 429:
            raise ValueError(
                "Gemini quota limit was reached. Wait a moment or check the API key's quota and billing."
            ) from error
        if error.code == 404:
            raise ValueError(
                "The configured Gemini model is unavailable for this API key."
            ) from error
        raise ValueError(
            provider_message or f"Gemini returned HTTP {error.code}. Please try again."
        ) from error
    except URLError as error:
        raise ValueError("Could not reach Gemini. Check your internet connection.") from error

    candidates = response_data.get("candidates", [])
    if not candidates:
        raise ValueError("Gemini did not return an answer for this request.")

    parts = candidates[0].get("content", {}).get("parts", [])
    answer = "".join(part.get("text", "") for part in parts).strip()
    if not answer:
        raise ValueError("Gemini returned an empty answer.")
    return answer


def ask_gemini(api_key: str, question: str, resume_skills: list[str], jobs: list[dict]) -> str:
    job_context = "\n".join(
        f"- {job['title']} at {job['company']} | {job['location']} | "
        f"Skills: {', '.join(job['skills'])}"
        for job in jobs
    ) or "No jobs were selected."
    profile_context = ", ".join(resume_skills) or "No resume skills were extracted."
    prompt = (
        "You are a practical job-search assistant. Use only the supplied job context "
        "and resume skills. Be concise, explain your reasoning, and do not claim the "
        "candidate is guaranteed to be selected.\n\n"
        f"Resume skills: {profile_context}\n"
        f"Available job context:\n{job_context}\n\n"
        f"User question: {question}"
    )
    return generate_text(api_key, prompt)


def classify_job(api_key: str, title: str, description: str) -> dict:
    prompt = (
        "Extract structured job tags from this job description. Return valid JSON only, "
        "with exactly these keys: skills (array of up to 12 concise technical skills), "
        "category (short role category based on daily responsibilities, such as 'Web Development', "
        "'Data Analysis', or 'Machine Learning'), domain (the business or industry context, such as "
        "'Cyber Security', 'Finance', or 'E-commerce'), experience (for example 'Fresher', "
        "'2-4 years', or 'Not specified'). Do not add markdown.\n\n"
        f"Title: {title}\nDescription: {description[:6000]}"
    )
    response_text = generate_text(api_key, prompt).strip()
    if response_text.startswith("```"):
        response_text = response_text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

    try:
        result = json.loads(response_text)
    except json.JSONDecodeError as error:
        raise ValueError("Gemini returned invalid enrichment data.") from error

    skills = result.get("skills", [])
    if not isinstance(skills, list):
        skills = []
    return {
        "skills": [str(skill).strip() for skill in skills if str(skill).strip()][:12],
        "category": str(result.get("category") or "Other").strip(),
        "domain": str(result.get("domain") or "Not specified").strip(),
        "experience": str(result.get("experience") or "Not specified").strip(),
    }
