"""
DrugPrediction model — stores every drug classification result.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DrugPrediction(Base):
    __tablename__ = "drug_predictions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    smiles: Mapped[str] = mapped_column(
        String(1000), nullable=False
    )
    predicted_class: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    confidence: Mapped[dict] = mapped_column(
        JSON, nullable=False
    )
    note: Mapped[str] = mapped_column(
        String(500), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="drug_predictions")

    def __repr__(self) -> str:
        return f"<DrugPrediction {self.predicted_class} ({self.smiles})>"
