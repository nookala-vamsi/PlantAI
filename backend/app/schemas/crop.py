"""
Crop & Disease schemas — response models for info endpoints.
"""

from pydantic import BaseModel
from typing import Optional
import uuid


class CropResponse(BaseModel):
    id: uuid.UUID
    name: str
    scientific_name: Optional[str]
    description: Optional[str]
    image_url: Optional[str]

    model_config = {"from_attributes": True}


class DiseaseResponse(BaseModel):
    id: uuid.UUID
    name: str
    scientific_name: Optional[str]
    description: Optional[str]
    severity: Optional[str]
    symptoms: Optional[list]
    remedies: Optional[list]
    prevention: Optional[list]

    model_config = {"from_attributes": True}
