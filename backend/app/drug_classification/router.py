"""
Drug router — the core drug origin prediction endpoint.
"""

import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.drug_prediction import DrugPrediction
from app.utils.redis_client import redis_client
from app.config import get_settings
from app.core.exceptions import RateLimitExceeded

from app.drug_classification.schemas import (
    DrugPredictionRequest, DrugPredictionResponse,
    DrugHistoryItem, DrugPaginatedHistory
)
from app.drug_classification.service import drug_ml_service

settings = get_settings()

router = APIRouter(prefix="/api/v1/drug", tags=["Drug Classification"])


@router.post("/predict", response_model=DrugPredictionResponse)
async def predict_drug_origin(
    request: DrugPredictionRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Predict the biological origin (Plant, Fungal, Bacterial) of a natural drug compound from its SMILES string.

    - **smiles**: SMILES molecular structure representation string (e.g., "CC(=O)Oc1ccccc1C(=O)O")
    """
    # 1. Rate limit check (using shared Redis rate limiter)
    allowed = await redis_client.check_rate_limit(
        str(user.id), settings.RATE_LIMIT_PER_MINUTE
    )
    if not allowed:
        raise RateLimitExceeded()

    # 2. Run ML prediction pipeline
    result = drug_ml_service.predict(request.smiles)

    # 3. Save prediction to database
    drug_pred = DrugPrediction(
        user_id=user.id,
        smiles=request.smiles,
        predicted_class=result["predicted_class"],
        confidence=result["confidence"],
        note=result["note"]
    )
    db.add(drug_pred)
    await db.flush()

    # 4. Format and return standard API response
    return DrugPredictionResponse(
        id=drug_pred.id,
        predicted_class=result["predicted_class"],
        prediction=result["prediction"],
        confidence=result["confidence"],
        note=result["note"],
        warning=result["warning"],
        created_at=drug_pred.created_at,
        smiles=request.smiles
    )


@router.get("/history", response_model=DrugPaginatedHistory)
async def get_drug_history(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated drug prediction history for the current user."""

    # Count total predictions
    count_result = await db.execute(
        select(func.count(DrugPrediction.id)).where(DrugPrediction.user_id == user.id)
    )
    total = count_result.scalar()

    # Fetch page
    offset = (page - 1) * per_page
    result = await db.execute(
        select(DrugPrediction)
        .where(DrugPrediction.user_id == user.id)
        .order_by(DrugPrediction.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    predictions = result.scalars().all()

    items = []
    for p in predictions:
        items.append(
            DrugHistoryItem(
                id=p.id,
                smiles=p.smiles,
                predicted_class=p.predicted_class,
                confidence=p.confidence,
                note=p.note,
                created_at=p.created_at,
            )
        )

    pages = (total + per_page - 1) // per_page if total > 0 else 1

    return DrugPaginatedHistory(items=items, total=total, page=page, pages=pages)


@router.get("/history/{prediction_id}", response_model=DrugPredictionResponse)
async def get_drug_prediction_detail(
    prediction_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get full details of a specific drug prediction."""
    try:
        pred_uuid = uuid.UUID(prediction_id)
    except ValueError:
        from app.core.exceptions import AppException
        raise AppException(
            status_code=400,
            error_code="INVALID_ID",
            message="Invalid prediction ID format.",
        )

    result = await db.execute(
        select(DrugPrediction).where(
            DrugPrediction.id == pred_uuid,
            DrugPrediction.user_id == user.id,
        )
    )
    prediction = result.scalar_one_or_none()

    if not prediction:
        from app.core.exceptions import AppException
        raise AppException(
            status_code=404,
            error_code="NOT_FOUND",
            message="Drug prediction not found.",
        )

    # Reconstruct prediction string for backward compatibility
    prob_str = ", ".join([f"{k}: {v*100:.2f}%" for k, v in prediction.confidence.items()])
    prediction_str = f"{prediction.predicted_class} ({prob_str})"

    return DrugPredictionResponse(
        id=prediction.id,
        predicted_class=prediction.predicted_class,
        prediction=prediction_str,
        confidence=prediction.confidence,
        note=prediction.note,
        warning=None,
        created_at=prediction.created_at,
        smiles=prediction.smiles,
    )
