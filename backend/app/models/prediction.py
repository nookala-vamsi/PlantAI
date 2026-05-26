"""
Prediction model — stores every disease prediction result.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    image_url: Mapped[str] = mapped_column(
        String(500), nullable=False
    )
    selected_crop: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    disease_name: Mapped[str] = mapped_column(
        String(200), nullable=True  # Null if prediction failed
    )
    confidence: Mapped[float] = mapped_column(
        Float, nullable=True
    )
    severity: Mapped[str] = mapped_column(
        String(20), nullable=True  # Low / Medium / High
    )
    remedies: Mapped[dict] = mapped_column(
        JSON, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="predictions")

    def __repr__(self) -> str:
        return f"<Prediction {self.disease_name} ({self.confidence:.2f})>"
