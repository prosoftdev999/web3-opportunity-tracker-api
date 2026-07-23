import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.opportunity import Opportunity
from app.schemas.github import (
    GitHubAnalyzeRequest,
    GitHubProfileResponse,
    OpportunityMatchResponse,
)
from app.services.github_matcher import (
    calculate_skill_match,
    github_service,
)


router = APIRouter(
    prefix="/github",
    tags=["GitHub Analysis"],
)


@router.post(
    "/analyze",
    response_model=GitHubProfileResponse,
)
async def analyze_github_profile(
    payload: GitHubAnalyzeRequest,
) -> GitHubProfileResponse:
    analysis = await github_service.analyze_user(
        payload.username.strip()
    )

    return GitHubProfileResponse.model_validate(analysis)


@router.get(
    "/{username}",
    response_model=GitHubProfileResponse,
)
async def get_github_profile(
    username: str,
) -> GitHubProfileResponse:
    analysis = await github_service.analyze_user(username.strip())
    return GitHubProfileResponse.model_validate(analysis)


@router.get(
    "/opportunities/{opportunity_id}/match/{username}",
    response_model=OpportunityMatchResponse,
)
async def match_opportunity_to_github_user(
    opportunity_id: uuid.UUID,
    username: str,
    db: AsyncSession = Depends(get_db),
) -> OpportunityMatchResponse:
    result = await db.execute(
        select(Opportunity).where(
            Opportunity.id == opportunity_id
        )
    )
    opportunity = result.scalar_one_or_none()

    if opportunity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found.",
        )

    profile = await github_service.analyze_user(username.strip())

    score, matched, missing, recommendation = (
        calculate_skill_match(
            opportunity.required_skills,
            profile["languages"],
            profile["topics"],
        )
    )

    return OpportunityMatchResponse(
        opportunity_id=str(opportunity.id),
        username=profile["username"],
        match_score=score,
        matched_skills=matched,
        missing_skills=missing,
        recommendation=recommendation,
    )