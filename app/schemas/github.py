from pydantic import BaseModel, Field


class GitHubAnalyzeRequest(BaseModel):
    username: str = Field(min_length=1, max_length=39)


class GitHubRepositoryResponse(BaseModel):
    name: str
    url: str
    description: str | None
    primary_language: str | None
    topics: list[str]
    stars: int
    forks: int


class GitHubProfileResponse(BaseModel):
    username: str
    profile_url: str
    public_repositories: int
    followers: int
    total_stars: int
    total_forks: int
    languages: list[str]
    topics: list[str]
    repositories: list[GitHubRepositoryResponse]
    experience_score: int


class OpportunityMatchResponse(BaseModel):
    opportunity_id: str
    username: str
    match_score: int
    matched_skills: list[str]
    missing_skills: list[str]
    recommendation: str