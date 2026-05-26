"""
ML Service — loads the trained model and runs disease prediction.
"""

import json
import hashlib
from typing import Optional
from pathlib import Path

import numpy as np
from PIL import Image
import io

from app.config import get_settings

settings = get_settings()


class MLService:
    """Handles model loading and inference for plant disease prediction."""

    def __init__(self):
        self._model = None
        self._labels: dict = {}

    def load_model(self):
        """
        Load the trained .keras model and labels.json into memory.
        Called once at server startup.
        """
        import tensorflow as tf

        model_path = Path(settings.MODEL_PATH)
        labels_path = Path(settings.LABELS_PATH)

        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        if not labels_path.exists():
            raise FileNotFoundError(f"Labels file not found: {labels_path}")

        print(f"🧠 Loading model from {model_path}...")
        self._model = tf.keras.models.load_model(str(model_path))
        print(f"✅ Model loaded!")

        with open(labels_path, "r") as f:
            self._labels = json.load(f)

        print(f"✅ Labels loaded: {len(self._labels)} classes")

    def preprocess_image(self, image_bytes: bytes) -> np.ndarray:
        """
        Preprocess an image for model inference:
        1. Open as RGB
        2. Resize to 224×224
        3. Apply EfficientNet preprocessing
        4. Add batch dimension
        """
        from tensorflow.keras.applications.efficientnet import preprocess_input

        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img = img.resize((224, 224), Image.LANCZOS)
        img_array = np.array(img, dtype=np.float32)
        img_array = preprocess_input(img_array)
        img_array = np.expand_dims(img_array, axis=0)  # [1, 224, 224, 3]
        return img_array

    def predict(self, image_bytes: bytes) -> dict:
        """
        Run disease prediction on an image.
        Returns: {
            "disease_name": "Tomato___Early_blight",
            "confidence": 0.94,
            "class_index": 24,
            "all_predictions": [...]  # top 5
        }
        """
        if self._model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        img_array = self.preprocess_image(image_bytes)
        predictions = self._model.predict(img_array, verbose=0)[0]

        # Get top prediction
        top_index = int(np.argmax(predictions))
        confidence = float(predictions[top_index])
        disease_name = self._labels.get(str(top_index), f"Unknown_{top_index}")

        # Get top 5 for detailed response
        top_5_indices = np.argsort(predictions)[-5:][::-1]
        top_5 = [
            {
                "disease": self._labels.get(str(int(i)), f"Unknown_{i}"),
                "confidence": round(float(predictions[i]), 4),
            }
            for i in top_5_indices
        ]

        return {
            "disease_name": disease_name,
            "confidence": round(confidence, 4),
            "class_index": top_index,
            "top_predictions": top_5,
        }

    @staticmethod
    def compute_image_hash(image_bytes: bytes) -> str:
        """Compute a SHA-256 hash of the image bytes for caching."""
        return hashlib.sha256(image_bytes).hexdigest()


# Singleton instance
ml_service = MLService()
