import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.opportunity import Opportunity
from app.schemas.opportunity import (
    OpportunityCreate,
    OpportunityListResponse,
    OpportunityResponse,
    OpportunityUpdate,
)
from app.services.scoring import calculate_opportunity_score


router = APIRouter(
    prefix="/opportunities",
    tags=["Opportunities"],
)


async def get_opportunity_or_404(
    opportunity_id: uuid.UUID,
    db: AsyncSession,
) -> Opportunity:
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

    return opportunity


@router.post(
    "",
    response_model=OpportunityResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_opportunity(
    payload: OpportunityCreate,
    db: AsyncSession = Depends(get_db),
) -> Opportunity:
    opportunity = Opportunity(
        title=payload.title.strip(),
        description=payload.description.strip(),
        opportunity_type=payload.opportunity_type,
        platform=payload.platform.strip(),
        source_url=str(payload.source_url),
        reward_amount=payload.reward_amount,
        reward_currency=(
            payload.reward_currency.upper()
            if payload.reward_currency
            else None
        ),
        required_skills=[
            skill.strip().lower()
            for skill in payload.required_skills
            if skill.strip()
        ],
        difficulty=payload.difficulty,
        deadline=payload.deadline,
        is_active=payload.is_active,
    )

    opportunity.score = calculate_opportunity_score(
        reward_amount=opportunity.reward_amount,
        required_skills=opportunity.required_skills,
        difficulty=opportunity.difficulty,
        deadline=opportunity.deadline,
        is_active=opportunity.is_active,
    )

    db.add(opportunity)

    try:
        await db.commit()
        await db.refresh(opportunity)
    except IntegrityError as exc:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An opportunity with this source URL already exists.",
        ) from exc

    return opportunity


@router.get(
    "",
    response_model=OpportunityListResponse,
)
async def list_opportunities(
    search: str | None = Query(
        default=None,
        min_length=1,
        max_length=255,
    ),
    opportunity_type: str | None = Query(default=None),
    platform: str | None = Query(default=None),
    difficulty: str | None = Query(default=None),
    skill: str | None = Query(default=None),
    is_active: bool | None = Query(default=True),
    min_reward: float | None = Query(default=None, ge=0),
    minimum_score: int | None = Query(
        default=None,
        ge=0,
        le=100,
    ),
    deadline_after: datetime | None = Query(default=None),
    deadline_before: datetime | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> OpportunityListResponse:
    filters = []

    if search:
        pattern = f"%{search.strip()}%"

        filters.append(
            or_(
                Opportunity.title.ilike(pattern),
                Opportunity.description.ilike(pattern),
                Opportunity.platform.ilike(pattern),
            )
        )

    if opportunity_type:
        filters.append(
            Opportunity.opportunity_type == opportunity_type
        )

    if platform:
        filters.append(
            Opportunity.platform.ilike(platform.strip())
        )

    if difficulty:
        filters.append(
            Opportunity.difficulty == difficulty
        )

    if skill:
        filters.append(
            Opportunity.required_skills.any(skill.strip().lower())
        )

    if is_active is not None:
        filters.append(
            Opportunity.is_active == is_active
        )

    if min_reward is not None:
        filters.append(
            Opportunity.reward_amount >= min_reward
        )

    if minimum_score is not None:
        filters.append(
            Opportunity.score >= minimum_score
        )

    if deadline_after is not None:
        filters.append(
            Opportunity.deadline >= deadline_after
        )

    if deadline_before is not None:
        filters.append(
            Opportunity.deadline <= deadline_before
        )

    count_statement = select(func.count()).select_from(Opportunity)

    list_statement = select(Opportunity)

    if filters:
        count_statement = count_statement.where(*filters)
        list_statement = list_statement.where(*filters)

    total = (
        await db.execute(count_statement)
    ).scalar_one()

    result = await db.execute(
        list_statement
        .order_by(
            Opportunity.score.desc(),
            Opportunity.created_at.desc(),
        )
        .offset(offset)
        .limit(limit)
    )

    opportunities = list(result.scalars().all())

    return OpportunityListResponse(
        items=[
            OpportunityResponse.model_validate(opportunity)
            for opportunity in opportunities
        ],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{opportunity_id}",
    response_model=OpportunityResponse,
)
async def get_opportunity(
    opportunity_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Opportunity:
    return await get_opportunity_or_404(
        opportunity_id,
        db,
    )


@router.patch(
    "/{opportunity_id}",
    response_model=OpportunityResponse,
)
async def update_opportunity(
    opportunity_id: uuid.UUID,
    payload: OpportunityUpdate,
    db: AsyncSession = Depends(get_db),
) -> Opportunity:
    opportunity = await get_opportunity_or_404(
        opportunity_id,
        db,
    )

    update_data = payload.model_dump(
        exclude_unset=True,
    )

    if "source_url" in update_data:
        update_data["source_url"] = str(
            update_data["source_url"]
        )

    if "title" in update_data:
        update_data["title"] = update_data["title"].strip()

    if "description" in update_data:
        update_data["description"] = (
            update_data["description"].strip()
        )

    if "platform" in update_data:
        update_data["platform"] = (
            update_data["platform"].strip()
        )

    if "reward_currency" in update_data:
        reward_currency = update_data["reward_currency"]

        update_data["reward_currency"] = (
            reward_currency.upper()
            if reward_currency
            else None
        )

    if "required_skills" in update_data:
        update_data["required_skills"] = [
            skill.strip().lower()
            for skill in update_data["required_skills"]
            if skill.strip()
        ]

    for field, value in update_data.items():
        setattr(opportunity, field, value)

    opportunity.score = calculate_opportunity_score(
        reward_amount=opportunity.reward_amount,
        required_skills=opportunity.required_skills,
        difficulty=opportunity.difficulty,
        deadline=opportunity.deadline,
        is_active=opportunity.is_active,
    )

    opportunity.updated_at = datetime.now(timezone.utc)

    try:
        await db.commit()
        await db.refresh(opportunity)
    except IntegrityError as exc:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An opportunity with this source URL already exists.",
        ) from exc

    return opportunity


@router.delete(
    "/{opportunity_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_opportunity(
    opportunity_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Response:
    opportunity = await get_opportunity_or_404(
        opportunity_id,
        db,
    )

    await db.delete(opportunity)
    await db.commit()

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )