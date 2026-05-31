import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).resolve().parents[1] / "backend"
sys.path.append(str(backend_dir))

# Mock settings/env vars if needed, FastAPI app config loads settings
from app.drug_classification.service import drug_ml_service

print("⏳ Loading Drug SVM model...")
drug_ml_service.load_model()
print("🎉 Model loaded successfully!")

# Test with Quercetin (high-confidence plant flavonoid)
quercetin_smiles = "O=c1c(O)c(-c2ccc(O)c(O)c2)oc2cc(O)cc(O)c12"
print(f"🧪 Classifying Quercetin SMILES: {quercetin_smiles}")
result_q = drug_ml_service.predict(quercetin_smiles)
print("🎯 Quercetin Result:")
import json
print(json.dumps(result_q, indent=2))

assert result_q["prediction"] == "Plant", f"Expected Plant, got {result_q['prediction']}"
assert result_q["warning"] is None, f"Expected no warning for Quercetin, got: {result_q['warning']}"
print("✅ High-confidence Plant prediction verified successfully!")

# Test with Aspirin (low-confidence compound)
aspirin_smiles = "CC(=O)Oc1ccccc1C(=O)O"
print(f"\n🧪 Classifying Aspirin SMILES (Low Confidence): {aspirin_smiles}")
result_a = drug_ml_service.predict(aspirin_smiles)
print("🎯 Aspirin Result:")
print(json.dumps(result_a, indent=2))

assert result_a["warning"] == "Low confidence prediction", f"Expected low confidence warning, got: {result_a['warning']}"
print("✅ Low confidence warning trigger verified successfully!")

print("\n🎉 All Backend Verifications Succeeded!")
