from pydantic import BaseModel, Field


class JobResponse(BaseModel):
    id: int
    source_job_id: str | None
    title: str
    company: str
    source: str
    location: str
    category: str
    domain: str | None
    min_experience: int | None
    max_experience: int | None
    experience: str
    description: str
    posted_at: str | None
    skills: list[str]
    is_ai_enriched: bool
    raw_category: str
    raw_experience: str
    raw_skills: list[str]


class JobListResponse(BaseModel):
    items: list[JobResponse]
    total: int
    offset: int
    limit: int


class ImportResponse(BaseModel):
    processed: int
    inserted: int
    skipped_as_duplicates: int
    total_jobs_in_database: int


class FilterOptionsResponse(BaseModel):
    sources: list[str]
    categories: list[str]
    experience_levels: list[str]


class JobStatsResponse(BaseModel):
    total_jobs: int
    jobs_by_source: dict[str, int]
    jobs_by_category: dict[str, int]


class RecommendationRequest(BaseModel):
    resume_skills: list[str] = Field(min_length=1)
    resume_roles: list[str] = Field(default_factory=list)
    experience_years: int | None = Field(default=None, ge=0, le=50)
    limit: int = Field(default=10, ge=1, le=20)


class RecommendedJob(JobResponse):
    matching_skills: list[str]
    skill_coverage: int
    recommendation_score: int


class RecommendationResponse(BaseModel):
    resume_skills: list[str]
    items: list[RecommendedJob]


class ResumeProfileResponse(BaseModel):
    filename: str
    skills: list[str]
    roles: list[str]
    detected_experience: str | None
    experience_years: int | None


class ResumeAnalysisResponse(BaseModel):
    profile: ResumeProfileResponse


class AssistantRequest(BaseModel):
    api_key: str = Field(min_length=1)
    question: str = Field(min_length=1, max_length=2000)
    resume_skills: list[str] = Field(default_factory=list)
    job_ids: list[int] = Field(default_factory=list, max_length=20)


class AssistantResponse(BaseModel):
    answer: str


class JobEnrichmentRequest(BaseModel):
    api_key: str = Field(min_length=1)
    batch_size: int = Field(default=5, ge=1, le=25)
    force: bool = False
    job_ids: list[int] = Field(default_factory=list, max_length=25)


class JobEnrichmentResponse(BaseModel):
    attempted: int
    enriched: int
    failed: int


class EnrichedJobPreview(BaseModel):
    id: int
    title: str
    ai_category: str
    ai_domain: str | None
    ai_experience: str
    ai_skills: list[str]


class EnrichmentStatusResponse(BaseModel):
    total_jobs: int
    enriched_jobs: int
    remaining_jobs: int
    sample_enriched_jobs: list[EnrichedJobPreview]
