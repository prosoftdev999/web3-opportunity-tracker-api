import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.opportunity import OpportunityResponse


class SavedOpportunityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    opportunity_id: uuid.UUID
    created_at: datetime
    opportunity: OpportunityResponse


class SavedOpportunityListResponse(BaseModel):
    items: list[SavedOpportunityResponse]
    total: int
