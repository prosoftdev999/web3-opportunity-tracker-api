import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.opportunity import Opportunity
from app.models.saved_opportunity import SavedOpportunity
from app.schemas.saved_opportunity import (
    SavedOpportunityListResponse,
    SavedOpportunityResponse,
)


router = APIRouter(
    prefix="/saved-opportunities",
    tags=["Saved Opportunities"],
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
    "/{opportunity_id}",
    response_model=SavedOpportunityResponse,
    status_code=status.HTTP_201_CREATED,
)
async def save_opportunity(
    opportunity_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> SavedOpportunity:
    await get_opportunity_or_404(opportunity_id, db)

    saved = SavedOpportunity(
        opportunity_id=opportunity_id,
    )
    db.add(saved)

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This opportunity is already saved.",
        ) from exc

    result = await db.execute(
        select(SavedOpportunity)
        .options(
            selectinload(SavedOpportunity.opportunity)
        )
        .where(SavedOpportunity.id == saved.id)
    )

    return result.scalar_one()


@router.get(
    "",
    response_model=SavedOpportunityListResponse,
)
async def list_saved_opportunities(
    db: AsyncSession = Depends(get_db),
) -> SavedOpportunityListResponse:
    result = await db.execute(
        select(SavedOpportunity)
        .options(
            selectinload(SavedOpportunity.opportunity)
        )
        .order_by(SavedOpportunity.created_at.desc())
    )

    saved_items = list(result.scalars().all())

    return SavedOpportunityListResponse(
        items=[
            SavedOpportunityResponse.model_validate(item)
            for item in saved_items
        ],
        total=len(saved_items),
    )


@router.delete(
    "/{opportunity_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_saved_opportunity(
    opportunity_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Response:
    result = await db.execute(
        select(SavedOpportunity).where(
            SavedOpportunity.opportunity_id
            == opportunity_id
        )
    )
    saved = result.scalar_one_or_none()

    if saved is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved opportunity not found.",
        )

    await db.delete(saved)
    await db.commit()

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )
