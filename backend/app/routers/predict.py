"""
Predict router — the core disease prediction endpoint.
"""

from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.prediction import Prediction
from app.models.disease import Disease
from app.schemas.predict import PredictionResponse, PredictionResult
from app.core.dependencies import get_current_user
from app.core.exceptions import (
    InvalidImage, ImageTooLarge, InvalidCrop,
    RateLimitExceeded, PredictionFailed,
)
from app.services.ml_service import ml_service
from app.utils.redis_client import redis_client
from app.utils.minio_client import minio_client
from app.config import get_settings

from sqlalchemy import select
from PIL import Image
import io

settings = get_settings()

router = APIRouter(prefix="/api/v1", tags=["Prediction"])

# The 14 supported crops (extracted from the 38 class names)
SUPPORTED_CROPS = [
    "Apple", "Blueberry", "Cherry", "Corn", "Grape",
    "Orange", "Peach", "Pepper", "Potato", "Raspberry",
    "Soybean", "Squash", "Strawberry", "Tomato",
]

MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/predict", response_model=PredictionResponse)
async def predict_disease(
    image: UploadFile = File(...),
    crop_type: str = Form(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a leaf image and get disease prediction.

    - **image**: JPEG or PNG image of a plant leaf
    - **crop_type**: One of the 14 supported crops (e.g., "Tomato")
    """

    # 1. Rate limit check
    allowed = await redis_client.check_rate_limit(
        str(user.id), settings.RATE_LIMIT_PER_MINUTE
    )
    if not allowed:
        raise RateLimitExceeded()

    # 2. Validate crop type
    if crop_type not in SUPPORTED_CROPS:
        raise InvalidCrop(crop_type)

    # 3. Validate image format
    if image.content_type not in ("image/jpeg", "image/png"):
        raise InvalidImage("Only JPEG and PNG images are supported.")

    # 4. Read and validate image size
    image_bytes = await image.read()
    if len(image_bytes) > MAX_IMAGE_SIZE:
        raise ImageTooLarge()

    # 5. Verify it's a valid image
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.verify()
    except Exception:
        raise InvalidImage("The uploaded file is not a valid image.")

    # 6. Check Redis cache
    image_hash = ml_service.compute_image_hash(image_bytes)
    cached = await redis_client.get_cached_prediction(image_hash)
    if cached:
        # Return cached result without re-running the model
        return PredictionResponse(
            id=cached["id"],
            image_url=cached["image_url"],
            selected_crop=crop_type,
            result=PredictionResult(**cached["result"]),
            created_at=cached["created_at"],
        )

    # 7. Upload image to MinIO
    object_name = minio_client.upload_image(
        str(user.id), image_bytes, image.content_type
    )
    image_url = minio_client.get_image_url(object_name)

    # 8. Run ML prediction
    try:
        ml_result = ml_service.predict(image_bytes)
    except Exception:
        raise PredictionFailed()

    # 9. Look up disease info from database
    disease_info = await db.execute(
        select(Disease).where(Disease.name == ml_result["disease_name"])
    )
    disease = disease_info.scalar_one_or_none()

    severity = disease.severity if disease else None
    remedies = disease.remedies if disease else None
    symptoms = disease.symptoms if disease else None
    prevention = disease.prevention if disease else None

    # 10. Save prediction to database
    prediction = Prediction(
        user_id=user.id,
        image_url=object_name,  # Store MinIO path, not presigned URL
        selected_crop=crop_type,
        disease_name=ml_result["disease_name"],
        confidence=ml_result["confidence"],
        severity=severity,
        remedies=remedies,
    )
    db.add(prediction)
    await db.flush()

    # 11. Build response
    result = PredictionResult(
        disease_name=ml_result["disease_name"],
        confidence=ml_result["confidence"],
        severity=severity,
        remedies=remedies,
        symptoms=symptoms,
        prevention=prevention,
        top_predictions=ml_result["top_predictions"],
    )

    response = PredictionResponse(
        id=prediction.id,
        image_url=image_url,
        selected_crop=crop_type,
        result=result,
        created_at=prediction.created_at,
    )

    # 12. Cache the result in Redis
    await redis_client.cache_prediction(image_hash, {
        "id": str(prediction.id),
        "image_url": image_url,
        "result": result.model_dump(),
        "created_at": prediction.created_at.isoformat(),
    })

    return response
