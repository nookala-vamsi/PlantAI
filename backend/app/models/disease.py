"""
Disease model — all 38 diseases with symptoms, remedies, and severity.
Pre-populated via seed script.
"""

import uuid

from sqlalchemy import String, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Disease(Base):
    __tablename__ = "diseases"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    crop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crops.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(
        String(200), unique=True, nullable=False, index=True
    )
    scientific_name: Mapped[str] = mapped_column(
        String(200), nullable=True
    )
    description: Mapped[str] = mapped_column(
        Text, nullable=True
    )
    severity: Mapped[str] = mapped_column(
        String(20), nullable=True  # Low / Medium / High
    )
    symptoms: Mapped[dict] = mapped_column(
        JSON, nullable=True  # List of symptom strings
    )
    remedies: Mapped[dict] = mapped_column(
        JSON, nullable=True  # List of remedy strings
    )
    prevention: Mapped[dict] = mapped_column(
        JSON, nullable=True  # List of prevention tips
    )

    # Relationships
    crop = relationship("Crop", back_populates="diseases")

    def __repr__(self) -> str:
        return f"<Disease {self.name} ({self.severity})>"
