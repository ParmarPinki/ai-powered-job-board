import io
import re
from pathlib import Path

from docx import Document
from pypdf import PdfReader


TECHNICAL_SKILLS = {
    "Python": ("python",),
    "Java": ("java",),
    "JavaScript": ("javascript", "js"),
    "TypeScript": ("typescript", "ts"),
    "C++": ("c++",),
    "C#": ("c#", "c sharp"),
    "R": ("r programming",),
    "SQL": ("sql",),
    "HTML": ("html", "html5"),
    "CSS": ("css", "css3"),
    "React": ("react", "react.js", "reactjs"),
    "Angular": ("angular", "angularjs"),
    "Vue.js": ("vue", "vue.js", "vuejs"),
    "Node.js": ("node", "node.js", "nodejs"),
    "Express": ("express", "express.js"),
    "Django": ("django",),
    "Flask": ("flask",),
    "FastAPI": ("fastapi",),
    "Spring Boot": ("spring boot",),
    ".NET": (".net", "dotnet"),
    "MongoDB": ("mongodb", "mongo db"),
    "MySQL": ("mysql",),
    "PostgreSQL": ("postgresql", "postgres"),
    "SQLite": ("sqlite",),
    "MariaDB": ("mariadb",),
    "Redis": ("redis",),
    "Git": ("git",),
    "GitHub": ("github",),
    "Docker": ("docker",),
    "Kubernetes": ("kubernetes", "k8s"),
    "AWS": ("aws", "amazon web services"),
    "Azure": ("azure",),
    "Google Cloud": ("google cloud", "gcp"),
    "REST APIs": ("rest api", "rest apis", "restful api"),
    "GraphQL": ("graphql",),
    "Postman": ("postman",),
    "Redux": ("redux", "redux toolkit"),
    "Tailwind CSS": ("tailwind", "tailwind css"),
    "Bootstrap": ("bootstrap",),
    "Pandas": ("pandas",),
    "NumPy": ("numpy",),
    "scikit-learn": ("scikit-learn", "scikit learn", "sklearn"),
    "TensorFlow": ("tensorflow",),
    "PyTorch": ("pytorch",),
    "Power BI": ("power bi", "powerbi"),
    "Tableau": ("tableau",),
    "Machine Learning": ("machine learning",),
    "Generative AI": ("generative ai", "genai"),
    "LLMs": ("llm", "llms", "large language models"),
}

ROLE_PATTERNS = {
    "Full Stack Developer": ("full stack developer", "full-stack developer", "full stack"),
    "Frontend Developer": ("frontend developer", "front-end developer"),
    "Backend Developer": ("backend developer", "back-end developer"),
    "Software Engineer": ("software engineer", "software developer"),
    "Data Analyst": ("data analyst",),
    "Data Scientist": ("data scientist",),
    "Machine Learning Engineer": ("machine learning engineer", "ml engineer"),
}


def extract_resume_text(filename: str, content: bytes) -> str:
    suffix = Path(filename).suffix.lower()

    if suffix == ".txt":
        return content.decode("utf-8", errors="ignore")
    if suffix == ".pdf":
        reader = PdfReader(io.BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if suffix == ".docx":
        document = Document(io.BytesIO(content))
        return "\n".join(paragraph.text for paragraph in document.paragraphs)

    raise ValueError("Upload a PDF, DOCX, or TXT resume.")


def extract_skills(resume_text: str) -> list[str]:
    normalized_text = resume_text.lower()
    matched_skills: list[str] = []

    for skill, aliases in TECHNICAL_SKILLS.items():
        if any(
            re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", normalized_text)
            for alias in aliases
        ):
            matched_skills.append(skill)

    return matched_skills


def canonicalize_skills(skills: list[str]) -> list[str]:
    canonical_skills: list[str] = []
    seen_skills: set[str] = set()

    for raw_skill in skills:
        normalized_skill = raw_skill.lower().strip().rstrip(".")
        for skill, aliases in TECHNICAL_SKILLS.items():
            if normalized_skill in aliases and skill not in seen_skills:
                canonical_skills.append(skill)
                seen_skills.add(skill)
                break

    return canonical_skills


def detect_roles(resume_text: str) -> list[str]:
    normalized_text = resume_text.lower()
    return [
        role
        for role, aliases in ROLE_PATTERNS.items()
        if any(
            re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", normalized_text)
            for alias in aliases
        )
    ]


def detect_experience(resume_text: str) -> str | None:
    matches = re.findall(r"\b(\d{1,2})\s*\+?\s*(?:years?|yrs?)\b", resume_text.lower())
    if not matches:
        return None
    return f"{max(map(int, matches))}+ years"


def detect_experience_years(resume_text: str) -> int | None:
    matches = re.findall(r"\b(\d{1,2})\s*\+?\s*(?:years?|yrs?)\b", resume_text.lower())
    return max(map(int, matches)) if matches else None
