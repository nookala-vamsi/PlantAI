import sys
from pathlib import Path
import uuid
import json

# Add backend to path
sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))

from app.seed import SEED_DATA

def escape_sql(value):
    if value is None:
        return 'NULL'
    if isinstance(value, str):
        # Escape single quotes
        escaped = value.replace("'", "''")
        return f"'{escaped}'"
    if isinstance(value, (list, dict)):
        # Convert to JSON string and escape single quotes
        json_str = json.dumps(value)
        escaped = json_str.replace("'", "''")
        return f"'{escaped}'::json"
    return str(value)

def generate_sql():
    sql_lines = ["BEGIN;"]
    
    sql_lines.append("\n-- Seeding Crops and Diseases data")
    
    for crop_name, crop_data in SEED_DATA.items():
        crop_id = str(uuid.uuid4())
        name = escape_sql(crop_name)
        scientific_name = escape_sql(crop_data.get("scientific_name"))
        description = escape_sql(crop_data.get("description"))
        
        sql_lines.append(
            f"INSERT INTO crops (id, name, scientific_name, description, image_url) "
            f"VALUES ('{crop_id}', {name}, {scientific_name}, {description}, NULL) "
            f"ON CONFLICT (name) DO UPDATE SET "
            f"scientific_name = EXCLUDED.scientific_name, description = EXCLUDED.description;"
        )
        
        for disease_data in crop_data["diseases"]:
            disease_id = str(uuid.uuid4())
            d_name = escape_sql(disease_data["name"])
            d_scientific_name = escape_sql(disease_data.get("scientific_name"))
            d_description = escape_sql(disease_data["description"])
            d_severity = escape_sql(disease_data.get("severity"))
            d_symptoms = escape_sql(disease_data.get("symptoms", []))
            d_remedies = escape_sql(disease_data.get("remedies", []))
            d_prevention = escape_sql(disease_data.get("prevention", []))
            
            sql_lines.append(
                f"INSERT INTO diseases (id, crop_id, name, scientific_name, description, severity, symptoms, remedies, prevention) "
                f"VALUES ('{disease_id}', '{crop_id}', {d_name}, {d_scientific_name}, {d_description}, {d_severity}, {d_symptoms}, {d_remedies}, {d_prevention}) "
                f"ON CONFLICT (name) DO NOTHING;"
            )
            
    sql_lines.append("\nCOMMIT;")
    
    output_path = Path(__file__).resolve().parents[1] / "supabase_seed.sql"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(sql_lines))
    print(f"Generated SQL seed file at: {output_path}")

if __name__ == "__main__":
    generate_sql()
