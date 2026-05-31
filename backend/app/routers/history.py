"""
History router — view past predictions.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.prediction import Prediction
from app.models.disease import Disease
from app.schemas.predict import PredictionHistoryItem, PaginatedHistory, PredictionResponse, PredictionResult
from app.core.dependencies import get_current_user
from app.utils.minio_client import minio_client

router = APIRouter(prefix="/api/v1/history", tags=["History"])


@router.get("", response_model=PaginatedHistory)
async def get_history(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated prediction history for the current user."""

    # Count total predictions
    count_result = await db.execute(
        select(func.count(Prediction.id)).where(Prediction.user_id == user.id)
    )
    total = count_result.scalar()

    # Fetch page
    offset = (page - 1) * per_page
    result = await db.execute(
        select(Prediction)
        .where(Prediction.user_id == user.id)
        .order_by(Prediction.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    predictions = result.scalars().all()

    # Build response with presigned image URLs
    items = []
    for p in predictions:
        items.append(
            PredictionHistoryItem(
                id=p.id,
                image_url=minio_client.get_image_url(p.image_url),
                selected_crop=p.selected_crop,
                disease_name=p.disease_name,
                confidence=p.confidence,
                severity=p.severity,
                created_at=p.created_at,
            )
        )

    pages = (total + per_page - 1) // per_page if total > 0 else 1

    return PaginatedHistory(items=items, total=total, page=page, pages=pages)


@router.get("/{prediction_id}", response_model=PredictionResponse)
async def get_prediction_detail(
    prediction_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get full details of a specific prediction."""

    result = await db.execute(
        select(Prediction).where(
            Prediction.id == prediction_id,
            Prediction.user_id == user.id,
        )
    )
    prediction = result.scalar_one_or_none()

    if not prediction:
        from app.core.exceptions import AppException
        raise AppException(
            status_code=404,
            error_code="NOT_FOUND",
            message="Prediction not found.",
        )

    # Look up disease info dynamically from the database
    disease_info = await db.execute(
        select(Disease).where(Disease.name == prediction.disease_name)
    )
    disease = disease_info.scalar_one_or_none()

    severity = disease.severity if disease else prediction.severity
    remedies = disease.remedies if disease else (prediction.remedies.get("remedies") if isinstance(prediction.remedies, dict) else (prediction.remedies if isinstance(prediction.remedies, list) else []))
    symptoms = disease.symptoms if disease else []
    prevention = disease.prevention if disease else []

    # Synthesize top predictions from current values
    top_predictions = [
        {
            "class_name": prediction.disease_name,
            "confidence": prediction.confidence,
        }
    ]

    result_detail = PredictionResult(
        disease_name=prediction.disease_name or "Unknown",
        confidence=prediction.confidence or 0.0,
        severity=severity,
        remedies=remedies or [],
        symptoms=symptoms or [],
        prevention=prevention or [],
        top_predictions=top_predictions,
    )

    return PredictionResponse(
        id=prediction.id,
        image_url=minio_client.get_image_url(prediction.image_url),
        selected_crop=prediction.selected_crop,
        result=result_detail,
        created_at=prediction.created_at,
    )
