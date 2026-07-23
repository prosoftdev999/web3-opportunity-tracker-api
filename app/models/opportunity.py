import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Opportunity(Base):
    __tablename__ = "opportunities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    opportunity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    platform: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    source_url: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
        unique=True,
    )

    reward_amount: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    reward_currency: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    required_skills: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        default=list,
        nullable=False,
    )

    difficulty: Mapped[str] = mapped_column(
        String(30),
        default="intermediate",
        nullable=False,
    )

    score: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        index=True,
    )

    deadline: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )