"""
Drug Classification schemas — request/response models for the GIN classifier.
"""

import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Dict, Optional, List

class DrugPredictionRequest(BaseModel):
    smiles: str = Field(
        ...,
        description="SMILES molecular structure string",
        example="CC(=O)Oc1ccccc1C(=O)O"
    )

class DrugPredictionResponse(BaseModel):
    id: Optional[uuid.UUID] = None
    predicted_class: str
    prediction: str  # Backward compatibility
    confidence: Dict[str, float]  # float probabilities returned by GIN model
    note: Optional[str] = None
    warning: Optional[str] = None  # Backward compatibility
    created_at: Optional[datetime] = None
    smiles: Optional[str] = None

class DrugHistoryItem(BaseModel):
    id: uuid.UUID
    smiles: str
    predicted_class: str
    confidence: Dict[str, float]
    note: Optional[str] = None
    created_at: datetime

class DrugPaginatedHistory(BaseModel):
    items: List[DrugHistoryItem]
    total: int
    page: int
    pages: int
