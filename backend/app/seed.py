"""
Database seed script — populates Crops and Diseases tables with data.
Run: python -m app.seed
"""

import asyncio
from sqlalchemy import select
from app.database import engine, async_session, Base
from app.models.crop import Crop
from app.models.disease import Disease


# ── Crop and Disease Data ──
# Each crop has its diseases with symptoms, remedies, severity, and prevention tips.

SEED_DATA = {
    "Apple": {
        "scientific_name": "Malus domestica",
        "description": "A widely cultivated fruit tree known for its nutritional value.",
        "diseases": [
            {
                "name": "Apple___Apple_scab",
                "scientific_name": "Venturia inaequalis",
                "severity": "Medium",
                "description": "A fungal disease causing olive-green to black spots on leaves and fruit.",
                "symptoms": ["Olive-green spots on leaves", "Dark scabby lesions on fruit", "Premature leaf drop", "Distorted fruit shape"],
                "remedies": ["Apply fungicide (captan or myclobutanil)", "Remove and destroy fallen leaves", "Prune for better air circulation", "Apply lime sulfur during dormant season"],
                "prevention": ["Plant resistant varieties", "Ensure good air circulation", "Apply preventive fungicide in spring", "Keep orchard floor clean"],
            },
            {
                "name": "Apple___Black_rot",
                "scientific_name": "Botryosphaeria obtusa",
                "severity": "High",
                "description": "A fungal disease causing leaf spots, fruit rot, and cankers on branches.",
                "symptoms": ["Purple-bordered brown leaf spots", "Black rotting fruit", "Cankers on branches", "Frog-eye leaf spot pattern"],
                "remedies": ["Remove infected fruit and cankers", "Apply captan or thiophanate-methyl fungicide", "Prune dead wood", "Maintain tree vigor with proper fertilization"],
                "prevention": ["Remove mummified fruit", "Prune dead branches annually", "Apply dormant spray", "Maintain proper tree nutrition"],
            },
            {
                "name": "Apple___Cedar_apple_rust",
                "scientific_name": "Gymnosporangium juniperi-virginianae",
                "severity": "Medium",
                "description": "A fungal disease requiring both apple and cedar/juniper trees to complete its lifecycle.",
                "symptoms": ["Bright orange-yellow spots on leaves", "Orange tube-like structures on leaf undersides", "Premature defoliation", "Spots on fruit surface"],
                "remedies": ["Apply myclobutanil fungicide", "Remove nearby cedar/juniper trees if possible", "Apply fungicide at bloom and petal fall", "Use protectant sprays in spring"],
                "prevention": ["Plant rust-resistant varieties", "Remove cedar trees within 2-mile radius", "Apply preventive fungicide", "Monitor trees in spring"],
            },
            {
                "name": "Apple___healthy",
                "scientific_name": None,
                "severity": None,
                "description": "A healthy apple leaf showing no signs of disease.",
                "symptoms": [],
                "remedies": [],
                "prevention": ["Regular monitoring", "Proper nutrition", "Adequate watering", "Good orchard hygiene"],
            },
        ],
    },
    "Blueberry": {
        "scientific_name": "Vaccinium corymbosum",
        "description": "A perennial flowering plant producing nutrient-rich berries.",
        "diseases": [
            {
                "name": "Blueberry___healthy",
                "scientific_name": None,
                "severity": None,
                "description": "A healthy blueberry leaf with no disease symptoms.",
                "symptoms": [],
                "remedies": [],
                "prevention": ["Maintain acidic soil pH (4.5-5.5)", "Mulch around plants", "Prune annually", "Water consistently"],
            },
        ],
    },
    "Cherry": {
        "scientific_name": "Prunus avium",
        "description": "A fruit tree known for its sweet cherries and ornamental blossoms.",
        "diseases": [
            {
                "name": "Cherry_(including_sour)___Powdery_mildew",
                "scientific_name": "Podosphaera clandestina",
                "severity": "Medium",
                "description": "A fungal disease causing white powdery coating on leaves and shoots.",
                "symptoms": ["White powdery patches on leaves", "Curled or distorted new growth", "Stunted shoot growth", "Premature leaf drop"],
                "remedies": ["Apply sulfur-based fungicide", "Use neem oil spray", "Remove infected shoots", "Improve air circulation through pruning"],
                "prevention": ["Avoid overhead watering", "Space trees properly", "Apply preventive fungicide", "Remove infected debris"],
            },
            {
                "name": "Cherry_(including_sour)___healthy",
                "scientific_name": None,
                "severity": None,
                "description": "A healthy cherry leaf with no disease symptoms.",
                "symptoms": [],
                "remedies": [],
                "prevention": ["Regular pruning", "Proper watering", "Good air circulation", "Monitor for early symptoms"],
            },
        ],
    },
    "Corn": {
        "scientific_name": "Zea mays",
        "description": "A major cereal grain and one of the most important food crops worldwide.",
        "diseases": [
            {
                "name": "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
                "scientific_name": "Cercospora zeae-maydis",
                "severity": "High",
                "description": "A fungal disease causing rectangular gray-brown lesions on corn leaves.",
                "symptoms": ["Rectangular gray-tan lesions", "Lesions parallel to leaf veins", "Leaves dry out prematurely", "Reduced photosynthesis"],
                "remedies": ["Apply foliar fungicide (strobilurin or triazole)", "Crop rotation with non-host crops", "Tillage to bury infected residue", "Plant resistant hybrids"],
                "prevention": ["Use resistant varieties", "Rotate crops", "Manage crop residue", "Avoid continuous corn planting"],
            },
            {
                "name": "Corn_(maize)___Common_rust_",
                "scientific_name": "Puccinia sorghi",
                "severity": "Medium",
                "description": "A fungal disease producing small reddish-brown pustules on both leaf surfaces.",
                "symptoms": ["Reddish-brown pustules on leaves", "Pustules on both leaf surfaces", "Chlorotic halos around pustules", "Severe cases cause premature leaf death"],
                "remedies": ["Apply triazole fungicide", "Plant resistant hybrids", "Early planting to avoid peak rust season", "Scout fields regularly"],
                "prevention": ["Plant resistant varieties", "Early planting", "Monitor weather conditions", "Scout fields from V8 stage"],
            },
            {
                "name": "Corn_(maize)___Northern_Leaf_Blight",
                "scientific_name": "Exserohilum turcicum",
                "severity": "High",
                "description": "A fungal disease causing long cigar-shaped gray-green lesions on corn leaves.",
                "symptoms": ["Long elliptical gray-green lesions", "Cigar-shaped spots 1-6 inches long", "Lesions may coalesce", "Lower leaves affected first"],
                "remedies": ["Apply strobilurin or triazole fungicide", "Remove infected crop debris", "Rotate with non-host crops", "Plant resistant hybrids"],
                "prevention": ["Use resistant hybrids", "Crop rotation", "Tillage to reduce inoculum", "Balanced fertilization"],
            },
            {
                "name": "Corn_(maize)___healthy",
                "scientific_name": None,
                "severity": None,
                "description": "A healthy corn leaf with no disease symptoms.",
                "symptoms": [],
                "remedies": [],
                "prevention": ["Proper spacing", "Adequate fertilization", "Crop rotation", "Monitor for pests"],
            },
        ],
    },
    "Grape": {
        "scientific_name": "Vitis vinifera",
        "description": "A widely cultivated vine fruit used for eating, wine, and juice production.",
        "diseases": [
            {
                "name": "Grape___Black_rot",
                "scientific_name": "Guignardia bidwellii",
                "severity": "High",
                "description": "A devastating fungal disease causing brown leaf spots and black shriveled fruit.",
                "symptoms": ["Tan-brown circular leaf spots", "Black pycnidia in lesions", "Fruit turns brown then black", "Mummified berries remain on vine"],
                "remedies": ["Apply mancozeb or myclobutanil fungicide", "Remove mummified berries", "Prune for air circulation", "Apply fungicide from bud break through veraison"],
                "prevention": ["Remove mummified fruit", "Prune and train vines properly", "Apply preventive fungicide", "Sanitation and canopy management"],
            },
            {
                "name": "Grape___Esca_(Black_Measles)",
                "scientific_name": "Phaeoacremonium spp.",
                "severity": "High",
                "description": "A complex trunk disease caused by multiple fungi, often fatal to older vines.",
                "symptoms": ["Tiger-striped leaf discoloration", "Dark spots on berries (measles)", "Trunk cankers and wood decay", "Sudden vine death in severe cases"],
                "remedies": ["No effective chemical cure", "Remove severely infected vines", "Apply wound protectants after pruning", "Trunk renewal in mild cases"],
                "prevention": ["Protect pruning wounds", "Minimize large pruning cuts", "Use clean pruning tools", "Plant certified disease-free stock"],
            },
            {
                "name": "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)",
                "scientific_name": "Pseudocercospora vitis",
                "severity": "Medium",
                "description": "A fungal disease causing dark brown angular spots on grape leaves.",
                "symptoms": ["Dark brown angular leaf spots", "Yellow halo around spots", "Premature defoliation", "Reduced fruit quality"],
                "remedies": ["Apply copper-based fungicide", "Remove infected leaves", "Improve canopy airflow", "Apply foliar sprays during wet periods"],
                "prevention": ["Proper vine spacing", "Canopy management", "Remove leaf litter", "Preventive fungicide application"],
            },
            {
                "name": "Grape___healthy",
                "scientific_name": None,
                "severity": None,
                "description": "A healthy grape leaf with no disease symptoms.",
                "symptoms": [],
                "remedies": [],
                "prevention": ["Proper trellising", "Regular pruning", "Good drainage", "Monitor vine health"],
            },
        ],
    },
    "Orange": {
        "scientific_name": "Citrus sinensis",
        "description": "A major citrus fruit tree cultivated in tropical and subtropical regions.",
        "diseases": [
            {
                "name": "Orange___Haunglongbing_(Citrus_greening)",
                "scientific_name": "Candidatus Liberibacter asiaticus",
                "severity": "High",
                "description": "The most destructive citrus disease worldwide, spread by the Asian citrus psyllid.",
                "symptoms": ["Asymmetric blotchy mottling on leaves", "Lopsided small bitter fruit", "Yellow shoots (yellow dragon)", "Premature fruit drop"],
                "remedies": ["No cure exists — manage symptoms", "Control psyllid vector with insecticide", "Remove severely infected trees", "Nutritional therapy (micronutrient sprays)"],
                "prevention": ["Control Asian citrus psyllid", "Use certified disease-free nursery stock", "Regular scouting", "Regional management programs"],
            },
        ],
    },
    "Peach": {
        "scientific_name": "Prunus persica",
        "description": "A deciduous fruit tree producing sweet fuzzy-skinned fruit.",
        "diseases": [
            {
                "name": "Peach___Bacterial_spot",
                "scientific_name": "Xanthomonas arboricola pv. pruni",
                "severity": "Medium",
                "description": "A bacterial disease causing spots on leaves and fruit, leading to defoliation.",
                "symptoms": ["Angular water-soaked leaf spots", "Shot-hole appearance on leaves", "Sunken dark spots on fruit", "Premature defoliation"],
                "remedies": ["Apply copper-based bactericide", "Oxytetracycline sprays during bloom", "Remove infected branches", "Avoid overhead irrigation"],
                "prevention": ["Plant resistant varieties", "Proper spacing for airflow", "Avoid wetting foliage", "Copper spray in fall"],
            },
            {
                "name": "Peach___healthy",
                "scientific_name": None,
                "severity": None,
                "description": "A healthy peach leaf with no disease symptoms.",
                "symptoms": [],
                "remedies": [],
                "prevention": ["Annual pruning", "Proper fertilization", "Pest monitoring", "Adequate watering"],
            },
        ],
    },
    "Pepper": {
        "scientific_name": "Capsicum annuum",
        "description": "A warm-season vegetable crop with numerous cultivated varieties.",
        "diseases": [
            {
                "name": "Pepper,_bell___Bacterial_spot",
                "scientific_name": "Xanthomonas campestris pv. vesicatoria",
                "severity": "High",
                "description": "A bacterial disease causing dark water-soaked spots on leaves and fruit.",
                "symptoms": ["Small dark water-soaked leaf spots", "Raised scab-like spots on fruit", "Yellowing and defoliation", "Reduced fruit quality"],
                "remedies": ["Apply copper-based bactericide", "Remove infected plants", "Avoid overhead watering", "Use pathogen-free seeds"],
                "prevention": ["Use certified disease-free seed", "Crop rotation (2-3 years)", "Avoid working in wet fields", "Use resistant varieties"],
            },
            {
                "name": "Pepper,_bell___healthy",
                "scientific_name": None,
                "severity": None,
                "description": "A healthy bell pepper leaf with no disease symptoms.",
                "symptoms": [],
                "remedies": [],
                "prevention": ["Proper spacing", "Balanced fertilization", "Mulching", "Regular monitoring"],
            },
        ],
    },
    "Potato": {
        "scientific_name": "Solanum tuberosum",
        "description": "One of the world's most important food crops, a starchy tuber vegetable.",
        "diseases": [
            {
                "name": "Potato___Early_blight",
                "scientific_name": "Alternaria solani",
                "severity": "Medium",
                "description": "A fungal disease causing dark concentric-ringed spots (target spots) on older leaves.",
                "symptoms": ["Dark brown spots with concentric rings", "Target-board pattern on leaves", "Lower leaves affected first", "Premature defoliation"],
                "remedies": ["Apply chlorothalonil or mancozeb fungicide", "Remove infected plant debris", "Maintain adequate nitrogen", "Irrigate in early morning"],
                "prevention": ["Crop rotation (3 years)", "Use certified seed potatoes", "Adequate plant spacing", "Proper fertilization"],
            },
            {
                "name": "Potato___Late_blight",
                "scientific_name": "Phytophthora infestans",
                "severity": "High",
                "description": "A devastating oomycete disease that caused the Irish Potato Famine. Rapidly destroys foliage and tubers.",
                "symptoms": ["Water-soaked dark patches on leaves", "White fuzzy growth on leaf undersides", "Rapid plant death in humid conditions", "Brown firm rot in tubers"],
                "remedies": ["Apply metalaxyl or chlorothalonil fungicide immediately", "Remove and destroy infected plants", "Avoid overhead irrigation", "Harvest tubers before infection spreads"],
                "prevention": ["Use resistant varieties", "Avoid planting near infected fields", "Destroy volunteer potatoes", "Monitor weather for blight conditions"],
            },
            {
                "name": "Potato___healthy",
                "scientific_name": None,
                "severity": None,
                "description": "A healthy potato leaf with no disease symptoms.",
                "symptoms": [],
                "remedies": [],
                "prevention": ["Use certified seed", "Proper hilling", "Adequate drainage", "Crop rotation"],
            },
        ],
    },
    "Raspberry": {
        "scientific_name": "Rubus idaeus",
        "description": "A perennial fruit-bearing shrub producing sweet aggregate berries.",
        "diseases": [
            {
                "name": "Raspberry___healthy",
                "scientific_name": None,
                "severity": None,
                "description": "A healthy raspberry leaf with no disease symptoms.",
                "symptoms": [],
                "remedies": [],
                "prevention": ["Proper pruning", "Good air circulation", "Weed management", "Adequate spacing"],
            },
        ],
    },
    "Soybean": {
        "scientific_name": "Glycine max",
        "description": "A major legume crop used for oil, protein, and animal feed production.",
        "diseases": [
            {
                "name": "Soybean___healthy",
                "scientific_name": None,
                "severity": None,
                "description": "A healthy soybean leaf with no disease symptoms.",
                "symptoms": [],
                "remedies": [],
                "prevention": ["Crop rotation", "Proper seed treatment", "Balanced fertilization", "Scout regularly"],
            },
        ],
    },
    "Squash": {
        "scientific_name": "Cucurbita spp.",
        "description": "A warm-season vegetable crop in the gourd family.",
        "diseases": [
            {
                "name": "Squash___Powdery_mildew",
                "scientific_name": "Podosphaera xanthii",
                "severity": "Medium",
                "description": "A common fungal disease causing white powdery coating on squash leaves.",
                "symptoms": ["White powdery spots on upper leaf surface", "Yellowing of infected leaves", "Stunted plant growth", "Reduced fruit quality"],
                "remedies": ["Apply sulfur or potassium bicarbonate", "Use neem oil", "Remove severely infected leaves", "Apply fungicide at first sign"],
                "prevention": ["Plant resistant varieties", "Ensure good air circulation", "Avoid overhead watering", "Space plants properly"],
            },
        ],
    },
    "Strawberry": {
        "scientific_name": "Fragaria × ananassa",
        "description": "A popular fruit crop cultivated worldwide for its sweet aromatic berries.",
        "diseases": [
            {
                "name": "Strawberry___Leaf_scorch",
                "scientific_name": "Diplocarpon earlianum",
                "severity": "Medium",
                "description": "A fungal disease causing dark purple spots that coalesce to scorch the entire leaf.",
                "symptoms": ["Dark purple irregular spots", "Spots merge causing leaf scorch", "Dried brown leaf margins", "Reduced plant vigor"],
                "remedies": ["Apply captan or thiram fungicide", "Remove infected leaves", "Renovate beds after harvest", "Improve air circulation"],
                "prevention": ["Use resistant varieties", "Proper plant spacing", "Remove old leaves", "Apply preventive fungicide"],
            },
            {
                "name": "Strawberry___healthy",
                "scientific_name": None,
                "severity": None,
                "description": "A healthy strawberry leaf with no disease symptoms.",
                "symptoms": [],
                "remedies": [],
                "prevention": ["Proper spacing", "Mulching", "Regular watering", "Remove runners as needed"],
            },
        ],
    },
    "Tomato": {
        "scientific_name": "Solanum lycopersicum",
        "description": "One of the most widely grown vegetable crops, cultivated in gardens and farms worldwide.",
        "diseases": [
            {
                "name": "Tomato___Bacterial_spot",
                "scientific_name": "Xanthomonas vesicatoria",
                "severity": "High",
                "description": "A bacterial disease causing dark spots on leaves, stems, and fruit.",
                "symptoms": ["Small dark raised spots on leaves", "Water-soaked lesions", "Scabby spots on fruit", "Defoliation in severe cases"],
                "remedies": ["Apply copper-based bactericide", "Remove infected plants", "Use pathogen-free seeds", "Avoid overhead irrigation"],
                "prevention": ["Use disease-free transplants", "Crop rotation", "Avoid working in wet fields", "Resistant varieties"],
            },
            {
                "name": "Tomato___Early_blight",
                "scientific_name": "Alternaria solani",
                "severity": "Medium",
                "description": "A common fungal disease with characteristic target-like spots on lower leaves.",
                "symptoms": ["Dark brown concentric-ring spots", "Target-board pattern", "Lower leaves affected first", "Yellowing around spots"],
                "remedies": ["Apply chlorothalonil fungicide", "Remove infected lower leaves", "Mulch around base", "Stake plants for airflow"],
                "prevention": ["Crop rotation (3 years)", "Mulch to prevent soil splash", "Adequate spacing", "Water at base, not overhead"],
            },
            {
                "name": "Tomato___Late_blight",
                "scientific_name": "Phytophthora infestans",
                "severity": "High",
                "description": "A devastating disease that can destroy entire tomato crops within days in wet conditions.",
                "symptoms": ["Large irregular water-soaked patches", "White mold on leaf undersides", "Brown-black stem lesions", "Firm brown rot on fruit"],
                "remedies": ["Apply metalaxyl or copper fungicide immediately", "Remove and destroy infected plants", "Do not compost infected material", "Protect healthy plants with fungicide"],
                "prevention": ["Use resistant varieties", "Good air circulation", "Avoid wet foliage", "Scout during humid weather"],
            },
            {
                "name": "Tomato___Leaf_Mold",
                "scientific_name": "Passalora fulva",
                "severity": "Medium",
                "description": "A fungal disease mainly occurring in greenhouse tomatoes with high humidity.",
                "symptoms": ["Pale yellow spots on upper leaf surface", "Olive-green velvety mold on underside", "Leaves curl and wither", "Mainly affects older leaves"],
                "remedies": ["Improve ventilation", "Reduce humidity below 85%", "Apply chlorothalonil fungicide", "Remove infected leaves"],
                "prevention": ["Maintain low greenhouse humidity", "Good air circulation", "Avoid leaf wetness", "Use resistant varieties"],
            },
            {
                "name": "Tomato___Septoria_leaf_spot",
                "scientific_name": "Septoria lycopersici",
                "severity": "Medium",
                "description": "A fungal disease causing numerous small spots with dark borders and gray centers.",
                "symptoms": ["Small circular spots with gray centers", "Dark brown borders on spots", "Lower leaves affected first", "Progressive defoliation upward"],
                "remedies": ["Apply chlorothalonil or mancozeb", "Remove infected lower leaves", "Mulch to prevent splash", "Prune for air circulation"],
                "prevention": ["Crop rotation", "Remove plant debris", "Mulching", "Avoid overhead irrigation"],
            },
            {
                "name": "Tomato___Spider_mites Two-spotted_spider_mite",
                "scientific_name": "Tetranychus urticae",
                "severity": "Medium",
                "description": "Tiny arachnid pests that feed on leaf cells, causing stippling and webbing.",
                "symptoms": ["Fine stippling on leaf surface", "Yellowing of leaves", "Fine webbing on undersides", "Leaf bronzing and drop"],
                "remedies": ["Apply miticide (abamectin)", "Use insecticidal soap", "Release predatory mites", "Increase humidity around plants"],
                "prevention": ["Monitor regularly with hand lens", "Keep plants well-watered", "Avoid dusty conditions", "Introduce beneficial predators"],
            },
            {
                "name": "Tomato___Target_Spot",
                "scientific_name": "Corynespora cassiicola",
                "severity": "Medium",
                "description": "A fungal disease producing concentric ring patterns on leaves.",
                "symptoms": ["Brown spots with concentric rings", "Spots may have yellow halo", "Affects leaves, stems, and fruit", "Progressive defoliation"],
                "remedies": ["Apply azoxystrobin or chlorothalonil", "Remove infected leaves", "Improve air circulation", "Reduce leaf wetness"],
                "prevention": ["Crop rotation", "Proper spacing", "Mulching", "Avoid wet foliage"],
            },
            {
                "name": "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
                "scientific_name": "Tomato yellow leaf curl virus (TYLCV)",
                "severity": "High",
                "description": "A devastating viral disease transmitted by whiteflies, causing severe yield loss.",
                "symptoms": ["Upward curling of leaf margins", "Yellowing of young leaves", "Stunted plant growth", "Flower drop and reduced fruit set"],
                "remedies": ["No cure — remove infected plants", "Control whitefly vector", "Use reflective mulch to repel whiteflies", "Apply imidacloprid for whitefly control"],
                "prevention": ["Use TYLCV-resistant varieties", "Control whitefly populations", "Use insect-proof netting", "Remove infected plants immediately"],
            },
            {
                "name": "Tomato___Tomato_mosaic_virus",
                "scientific_name": "Tomato mosaic virus (ToMV)",
                "severity": "High",
                "description": "A highly contagious viral disease spread by contact, tools, and infected seeds.",
                "symptoms": ["Light and dark green mosaic pattern", "Leaf curling and distortion", "Stunted growth", "Reduced and deformed fruit"],
                "remedies": ["No cure — remove infected plants", "Disinfect tools with 10% bleach", "Wash hands with soap between plants", "Do not smoke near tomato plants (TMV in tobacco)"],
                "prevention": ["Use virus-free seed", "Disinfect tools regularly", "Wash hands before handling plants", "Use resistant varieties"],
            },
            {
                "name": "Tomato___healthy",
                "scientific_name": None,
                "severity": None,
                "description": "A healthy tomato leaf with no disease symptoms.",
                "symptoms": [],
                "remedies": [],
                "prevention": ["Proper staking", "Consistent watering", "Balanced fertilization", "Regular monitoring"],
            },
        ],
    },
}


async def seed_database():
    """Populate the database with crop and disease data."""

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # Check if already seeded
        result = await session.execute(select(Crop))
        if result.scalars().first():
            print("⚠️  Database already seeded. Skipping.")
            return

        print("🌱 Seeding database...")

        for crop_name, crop_data in SEED_DATA.items():
            # Create crop
            crop = Crop(
                name=crop_name,
                scientific_name=crop_data["scientific_name"],
                description=crop_data["description"],
            )
            session.add(crop)
            await session.flush()  # Get the crop ID

            # Create diseases for this crop
            for disease_data in crop_data["diseases"]:
                disease = Disease(
                    crop_id=crop.id,
                    name=disease_data["name"],
                    scientific_name=disease_data.get("scientific_name"),
                    description=disease_data["description"],
                    severity=disease_data.get("severity"),
                    symptoms=disease_data.get("symptoms", []),
                    remedies=disease_data.get("remedies", []),
                    prevention=disease_data.get("prevention", []),
                )
                session.add(disease)

            print(f"   ✅ {crop_name}: {len(crop_data['diseases'])} diseases")

        await session.commit()
        print(f"\n🎉 Seeded {len(SEED_DATA)} crops with all diseases!")


if __name__ == "__main__":
    asyncio.run(seed_database())
