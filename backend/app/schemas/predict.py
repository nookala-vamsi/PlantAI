"""
Prediction schemas — request/response models for prediction endpoints.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid


class PredictionResult(BaseModel):
    disease_name: str
    confidence: float
    severity: Optional[str] = None
    remedies: Optional[list] = None
    symptoms: Optional[list] = None
    prevention: Optional[list] = None
    top_predictions: Optional[list] = None


class PredictionResponse(BaseModel):
    id: uuid.UUID
    image_url: str
    selected_crop: str
    result: PredictionResult
    created_at: datetime

    model_config = {"from_attributes": True}


class PredictionHistoryItem(BaseModel):
    id: uuid.UUID
    image_url: str
    selected_crop: str
    disease_name: Optional[str]
    confidence: Optional[float]
    severity: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedHistory(BaseModel):
    items: list[PredictionHistoryItem]
    total: int
    page: int
    pages: int
