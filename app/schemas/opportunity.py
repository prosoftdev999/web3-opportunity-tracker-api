import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


OpportunityType = Literal[
    "grant",
    "bounty",
    "hackathon",
    "job",
    "contest",
    "other",
]

DifficultyLevel = Literal[
    "beginner",
    "intermediate",
    "advanced",
]


class OpportunityBase(BaseModel):
    title: str = Field(
        min_length=3,
        max_length=255,
    )

    description: str = Field(
        min_length=10,
        max_length=50_000,
    )

    opportunity_type: OpportunityType

    platform: str = Field(
        min_length=2,
        max_length=100,
    )

    source_url: HttpUrl

    reward_amount: float | None = Field(
        default=None,
        ge=0,
    )

    reward_currency: str | None = Field(
        default=None,
        min_length=1,
        max_length=20,
    )

    required_skills: list[str] = Field(
        default_factory=list,
        max_length=50,
    )

    difficulty: DifficultyLevel = "intermediate"

    deadline: datetime | None = None

    is_active: bool = True


class OpportunityCreate(OpportunityBase):
    pass


class OpportunityUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=3,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        min_length=10,
        max_length=50_000,
    )

    opportunity_type: OpportunityType | None = None

    platform: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    source_url: HttpUrl | None = None

    reward_amount: float | None = Field(
        default=None,
        ge=0,
    )

    reward_currency: str | None = Field(
        default=None,
        min_length=1,
        max_length=20,
    )

    required_skills: list[str] | None = None

    difficulty: DifficultyLevel | None = None

    score: int | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    deadline: datetime | None = None

    is_active: bool | None = None


class OpportunityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str
    opportunity_type: str
    platform: str
    source_url: str
    reward_amount: float | None
    reward_currency: str | None
    required_skills: list[str]
    difficulty: str
    score: int
    deadline: datetime | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class OpportunityListResponse(BaseModel):
    items: list[OpportunityResponse]
    total: int
    offset: int
    limit: int