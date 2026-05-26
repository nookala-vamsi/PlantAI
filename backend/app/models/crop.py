"""
Crop model — the 14 supported crop species.
Pre-populated via seed script.
"""

import uuid

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Crop(Base):
    __tablename__ = "crops"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    scientific_name: Mapped[str] = mapped_column(
        String(200), nullable=True
    )
    description: Mapped[str] = mapped_column(
        Text, nullable=True
    )
    image_url: Mapped[str] = mapped_column(
        String(500), nullable=True
    )

    # Relationships
    diseases = relationship("Disease", back_populates="crop", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Crop {self.name}>"
