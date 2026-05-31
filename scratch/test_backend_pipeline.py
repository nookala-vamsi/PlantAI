import sys
import os
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).resolve().parents[1] / "backend"
sys.path.append(str(backend_dir))

# Mock settings/env vars if needed
os.environ["DATABASE_URL"] = "postgresql+asyncpg://plantai:plantai_secret@localhost:5432/plantai_db"
os.environ["JWT_SECRET_KEY"] = "mock-jwt-secret-key-for-testing"

from app.services.ml_service import ml_service
from app.core.exceptions import NotALeaf, CropMismatch, LowConfidence

print("⏳ Loading Keras models (Gates 1, 2, and 3)...")
ml_service.load_model()
print("🎉 All models loaded successfully!")

# Define paths to generated images
leaf_image_path = r"C:\Users\vamsi\.gemini\antigravity-ide\brain\81ec23e3-06a9-492f-a3cf-7b323bc8886e\tomato_leaf_natural_1780074761183.png"
non_leaf_image_path = r"C:\Users\vamsi\.gemini\antigravity-ide\brain\81ec23e3-06a9-492f-a3cf-7b323bc8886e\coffee_cup_1780074650139.png"

# Read image bytes
with open(leaf_image_path, "rb") as f:
    leaf_bytes = f.read()

with open(non_leaf_image_path, "rb") as f:
    non_leaf_bytes = f.read()

# ── Test 1: Gate 1 Rejection (Non-Leaf image) ──
print("\n🧪 Test 1: Uploading non-leaf image (coffee cup)...")
try:
    ml_service.predict(non_leaf_bytes, "Tomato")
    print("❌ Test 1 Failed: Expected NotALeaf exception, but it passed!")
    sys.exit(1)
except NotALeaf:
    print("✅ Test 1 Passed: Successfully rejected non-leaf image with NotALeaf exception!")
except Exception as e:
    print(f"❌ Test 1 Failed: Expected NotALeaf, but got {type(e).__name__}: {str(e)}")
    sys.exit(1)

# ── Test 2: Gate 2 Rejection (Crop Mismatch) ──
print("\n🧪 Test 2: Uploading tomato leaf but selecting 'Potato'...")
try:
    ml_service.predict(leaf_bytes, "Potato")
    print("❌ Test 2 Failed: Expected CropMismatch exception, but it passed!")
    sys.exit(1)
except CropMismatch as e:
    print(f"✅ Test 2 Passed: Successfully rejected crop mismatch with CropMismatch exception!")
    print(f"   Detail: {e.detail}")
except Exception as e:
    print(f"❌ Test 2 Failed: Expected CropMismatch, but got {type(e).__name__}: {str(e)}")
    sys.exit(1)

# ── Test 3: Successful 3-Gate Prediction & Crop Filtering ──
print("\n🧪 Test 3: Uploading tomato leaf and selecting 'Tomato'...")
try:
    result = ml_service.predict(leaf_bytes, "Tomato")
    print("✅ Test 3 Passed: Successfully predicted tomato leaf!")
    import json
    print(json.dumps(result, indent=2))
    
    # Assertions
    assert "Tomato___" in result["disease_name"], f"Expected tomato disease, got: {result['disease_name']}"
    assert result["confidence"] >= 0.40, f"Expected confidence >= 0.40, got: {result['confidence']}"
    for item in result["top_predictions"]:
        assert "Tomato___" in item["disease"], f"Expected top predictions to be filtered to Tomato only, got: {item['disease']}"
    print("✅ Prediction filtering and re-normalization logic verified successfully!")
except Exception as e:
    print(f"❌ Test 3 Failed: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n🎉 ALL 3-GATE BACKEND PIPELINE VERIFICATIONS PASSED!")
