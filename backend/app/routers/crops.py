"""
Crops router — browse supported crops and their diseases.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.crop import Crop
from app.models.disease import Disease
from app.schemas.crop import CropResponse, DiseaseResponse
from app.core.exceptions import AppException

router = APIRouter(prefix="/api/v1", tags=["Crops & Diseases"])


@router.get("/crops", response_model=list[CropResponse])
async def list_crops(db: AsyncSession = Depends(get_db)):
    """Get all 14 supported crop species."""

    result = await db.execute(select(Crop).order_by(Crop.name))
    crops = result.scalars().all()
    return crops


@router.get("/diseases/{crop_name}", response_model=list[DiseaseResponse])
async def get_diseases_for_crop(
    crop_name: str,
    db: AsyncSession = Depends(get_db),
):
    """Get all diseases for a specific crop with symptoms & remedies."""

    # Find the crop
    result = await db.execute(select(Crop).where(Crop.name == crop_name))
    crop = result.scalar_one_or_none()

    if not crop:
        raise AppException(
            status_code=404,
            error_code="CROP_NOT_FOUND",
            message=f"Crop '{crop_name}' not found.",
        )

    # Get diseases for this crop
    result = await db.execute(
        select(Disease).where(Disease.crop_id == crop.id).order_by(Disease.name)
    )
    diseases = result.scalars().all()
    return diseases
