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
from app.core.exceptions import NotALeaf, CropMismatch, LowConfidence

settings = get_settings()

# Crop-to-label prefix mapping to filter Gate 3 predictions
CROP_TO_LABEL_PREFIX = {
    "Apple": "Apple___",
    "Blueberry": "Blueberry___",
    "Cherry": "Cherry",
    "Corn": "Corn",
    "Grape": "Grape___",
    "Orange": "Orange___",
    "Peach": "Peach___",
    "Pepper": "Pepper",
    "Potato": "Potato___",
    "Raspberry": "Raspberry___",
    "Soybean": "Soybean___",
    "Squash": "Squash___",
    "Strawberry": "Strawberry___",
    "Tomato": "Tomato___",
}


class MLService:
    """Handles model loading and inference for plant disease prediction using a 3-gate pipeline."""

    def __init__(self):
        self._model = None
        self._labels: dict = {}
        self._gate1_model = None
        self._gate2_model = None
        self._gate2_labels: dict = {}

    def load_model(self):
        """
        Load the trained .keras models and labels into memory.
        Called once at server startup.
        """
        import tensorflow as tf

        model_path = Path(settings.MODEL_PATH)
        labels_path = Path(settings.LABELS_PATH)
        gate1_path = Path(settings.GATE1_MODEL_PATH)
        gate2_path = Path(settings.GATE2_MODEL_PATH)
        gate2_labels_path = Path(settings.GATE2_LABELS_PATH)

        # Validate existence of all required assets
        for p in [model_path, labels_path, gate1_path, gate2_path, gate2_labels_path]:
            if not p.exists():
                raise FileNotFoundError(f"Required ML file not found: {p}")

        # Load Gate 1 (Leaf vs Non-Leaf Detector)
        print(f"🧠 Loading Gate 1 model from {gate1_path}...")
        self._gate1_model = tf.keras.models.load_model(str(gate1_path))
        print("✅ Gate 1 loaded!")

        # Load Gate 2 (Plant Species Classifier)
        print(f"🧠 Loading Gate 2 model from {gate2_path}...")
        self._gate2_model = tf.keras.models.load_model(str(gate2_path))
        print("✅ Gate 2 loaded!")

        with open(gate2_labels_path, "r") as f:
            self._gate2_labels = json.load(f)
        print(f"✅ Gate 2 labels loaded: {len(self._gate2_labels)} classes")

        # Load Gate 3 (Disease Classifier)
        print(f"🧠 Loading Gate 3 model from {model_path}...")
        self._model = tf.keras.models.load_model(str(model_path))
        print("✅ Gate 3 loaded!")

        with open(labels_path, "r") as f:
            self._labels = json.load(f)
        print(f"✅ Gate 3 labels loaded: {len(self._labels)} classes")

    def preprocess_image(self, image_bytes: bytes) -> np.ndarray:
        """
        Preprocess an image for Gate 3 model inference:
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

    def _preprocess_for_gates(self, image_bytes: bytes) -> np.ndarray:
        """
        Preprocess an image for Gates 1 & 2.
        Gates 1 & 2 have preprocess_input built into their Keras graphs,
        so they expect raw float32 pixels of shape [1, 224, 224, 3] in the [0, 255] range.
        """
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img = img.resize((224, 224), Image.LANCZOS)
        img_array = np.array(img, dtype=np.float32)
        img_array = np.expand_dims(img_array, axis=0)  # [1, 224, 224, 3]
        return img_array

    def predict(self, image_bytes: bytes, selected_crop: str) -> dict:
        """
        Run the complete 3-Gate disease prediction pipeline on an image.

        1. Gate 1 (Leaf Detector): If pred > 0.5 (non-leaf), raise NotALeaf.
        2. Gate 2 (Species Classifier): If predicted plant species does not match
           selected_crop (case-insensitive), raise CropMismatch.
        3. Gate 3 (Disease Classifier + Crop Filtering):
           - Predict 38 classes
           - Filter to selected crop's disease classes
           - Re-normalize probabilities to sum to exactly 1.0
           - If top re-normalized confidence < 0.40, raise LowConfidence.
        """
        if self._model is None or self._gate1_model is None or self._gate2_model is None:
            raise RuntimeError("ML Models are not fully loaded. Call load_model() first.")

        # ── Preprocess image for Gates 1 & 2 ──
        gate_img_array = self._preprocess_for_gates(image_bytes)

        # ── Gate 1: Leaf Detector Check ──
        gate1_pred = self._gate1_model.predict(gate_img_array, verbose=0)[0][0]
        # pred <= 0.5 is leaf, pred > 0.5 is non_leaf
        is_leaf = gate1_pred <= 0.5
        if not is_leaf:
            raise NotALeaf()

        # ── Gate 2: Plant Species Classifier Check ──
        gate2_preds = self._gate2_model.predict(gate_img_array, verbose=0)[0]
        gate2_idx = int(np.argmax(gate2_preds))
        predicted_species = self._gate2_labels.get(str(gate2_idx), f"Unknown_{gate2_idx}")

        if predicted_species.lower() != selected_crop.lower():
            raise CropMismatch(predicted=predicted_species, selected=selected_crop)

        # ── Gate 3: Disease Classifier with Crop Filtering ──
        img_array = self.preprocess_image(image_bytes)
        predictions = self._model.predict(img_array, verbose=0)[0]

        # Extract only the crop-specific indices (e.g. Tomato___)
        prefix = CROP_TO_LABEL_PREFIX.get(selected_crop)
        if not prefix:
            raise ValueError(f"Invalid crop type: {selected_crop}")

        crop_indices = []
        for idx_str, name in self._labels.items():
            if name.startswith(prefix):
                crop_indices.append(int(idx_str))

        if not crop_indices:
            raise ValueError(f"No label mappings found for crop: {selected_crop}")

        # Re-normalize crop-specific probabilities to sum to exactly 1.0
        filtered_preds = np.zeros_like(predictions)
        total_prob = sum(predictions[i] for i in crop_indices)

        if total_prob > 0:
            for i in crop_indices:
                filtered_preds[i] = predictions[i] / total_prob
        else:
            for i in crop_indices:
                filtered_preds[i] = 1.0 / len(crop_indices)

        # Sort crop disease indices by re-normalized probability in descending order
        sorted_indices = sorted(crop_indices, key=lambda i: filtered_preds[i], reverse=True)
        top_index = sorted_indices[0]
        confidence = float(filtered_preds[top_index])

        # Enforce confidence threshold of 40%
        if confidence < 0.40:
            raise LowConfidence()

        disease_name = self._labels.get(str(top_index), f"Unknown_{top_index}")

        # Build top crop-specific predictions
        top_list = [
            {
                "disease": self._labels.get(str(int(i)), f"Unknown_{i}"),
                "confidence": round(float(filtered_preds[i]), 4),
            }
            for i in sorted_indices[:5]  # Limit to top 5
        ]

        return {
            "disease_name": disease_name,
            "confidence": round(confidence, 4),
            "class_index": top_index,
            "top_predictions": top_list,
        }

    @staticmethod
    def compute_image_hash(image_bytes: bytes) -> str:
        """Compute a SHA-256 hash of the image bytes for caching."""
        return hashlib.sha256(image_bytes).hexdigest()


# Singleton instance
ml_service = MLService()
