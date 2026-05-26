# 🧠 ML Model Refinement Guide — 3-Gate Pipeline

> Transform the single 38-class classifier into a production-grade 3-gate pipeline.

---

## Why the Current Model Fails

Our current model is a **single EfficientNetB0** trained on 38 classes from PlantVillage:

```
Image → EfficientNetB0 → 1 of 38 classes → Done
```

### Problems with this approach:

| Problem | Why It Happens |
|---|---|
| Non-leaf images get predictions | Model has no "reject" option — always picks one of 38 |
| Potato leaf shows Tomato disease | All 38 classes compete equally, no crop filtering |
| High confidence on wrong predictions | Softmax forces probabilities to sum to 1, even on garbage input |
| Can't validate the plant species | Model jumps straight to disease — skips species check |

### The Solution: 3-Gate Pipeline

```
Image → Gate 1 (Leaf?) → Gate 2 (Which plant?) → Gate 3 (Which disease?) → Result
         ↓ REJECT          ↓ MISMATCH             ↓ DIAGNOSIS
       "Not a leaf"     "Wrong plant"         "Tomato Early Blight"
```

Each gate is a **separate, focused model** that does one job well.

---

## Gate 1: Leaf Detector (Binary Classifier)

### Job
> "Is this image a leaf or not?"

**Input:** Any image
**Output:** `leaf` (proceed) or `not_leaf` (reject)

### Architecture

**MobileNetV2** (lightweight, fast, perfect for binary classification)
- Pre-trained on ImageNet (transfer learning)
- Remove the top classification layer
- Add: GlobalAveragePooling → Dense(128, ReLU) → Dropout(0.3) → Dense(1, Sigmoid)
- Total trainable params: ~300K (very fast inference)

### Why MobileNetV2?
- It's **tiny** (~3.4M params) — loads fast, predicts in <50ms
- Excellent accuracy for simple binary tasks
- Already knows textures, shapes, edges from ImageNet pre-training
- We don't need a heavy model for "leaf vs not-leaf"

### Dataset

**Using:** [Leaf vs Non-Leaf Images](https://www.kaggle.com/datasets/robiulhasanjisan/leaf-vs-non-leaf-images) by Robiul Hasan Jisan (Kaggle)

| Detail | Value |
|---|---|
| **License** | MIT |
| **Size** | ~2.4 GB |
| **Classes** | 2 — `leaf` and `non_leaf` |
| **Format** | .jpg, .jpeg, .png, .bmp, .webp |

#### Dataset Structure (already organized for training):
```
leaf-vs-non-leaf-images/
├── leaf/              # Leaf images
│   ├── leafimage0001.jpg
│   ├── leafimage0002.jpg
│   └── ...
└── non_leaf/          # Non-leaf images (backgrounds, random objects, etc.)
    ├── nonleafimage0001.jpg
    ├── nonleafimage0002.jpg
    └── ...
```

This dataset is already structured for `flow_from_directory` / `ImageFolder` — no reorganization needed. Just load it directly in the Kaggle notebook.

#### How to use in Kaggle:
1. Open a new Kaggle Notebook
2. Click **"Add Input"** → search **"Leaf vs Non-Leaf Images"**
3. Add the dataset — it'll be available at `/kaggle/input/leaf-vs-non-leaf-images/`

### Training Parameters

| Parameter | Value | Why |
|---|---|---|
| Base model | MobileNetV2 (ImageNet weights) | Fast, lightweight |
| Image size | 224 × 224 | MobileNetV2 default |
| Batch size | 32 | Good balance |
| Epochs | 15-20 | Binary task converges fast |
| Optimizer | Adam (lr=0.0001) | Standard for transfer learning |
| Loss | Binary Crossentropy | Binary classification |
| Augmentation | Rotation, flip, brightness, zoom | Prevent overfitting |
| Freeze layers | Freeze base → train top 3 epochs → unfreeze last 30 layers → fine-tune 15 epochs | Two-phase transfer learning |
| Callbacks | EarlyStopping (patience=4) + ReduceLROnPlateau (patience=2) | Stop before overfitting |

### Expected Accuracy: **95-98%**

Binary leaf detection is a straightforward task — leaves have very distinct visual patterns (veins, green tones, organic shapes) that differ sharply from non-leaf objects. With this large, curated dataset the model should learn robustly.

### Output File
- `leaf_detector.keras` (~10 MB)

---

## Gate 2: Species Classifier (14-Class)

### Job
> "Which plant species is this leaf from?"

**Input:** A leaf image (already confirmed by Gate 1)
**Output:** One of 14 species: `Apple`, `Blueberry`, `Cherry`, `Corn`, `Grape`, `Orange`, `Peach`, `Pepper`, `Potato`, `Raspberry`, `Soybean`, `Squash`, `Strawberry`, `Tomato`

### Architecture

**EfficientNetB0** (same as our current model — proven to work well on plant images)
- Pre-trained on ImageNet
- Remove top → GlobalAveragePooling → Dense(256, ReLU) → Dropout(0.4) → Dense(14, Softmax)

### Dataset

**Reuse our existing PlantVillage dataset!** Just re-organize it by species:

```
Current structure (38 classes):          Reorganized (14 species):
├── Apple___Apple_scab/                  ├── Apple/         ← all Apple_* images
├── Apple___Black_rot/                   ├── Blueberry/     ← all Blueberry_* images
├── Apple___Cedar_apple_rust/            ├── Cherry/
├── Apple___healthy/                     ├── Corn/
├── Tomato___Early_blight/               ├── Grape/
├── Tomato___Late_blight/                ├── Orange/
├── ...                                  ├── Peach/
                                         ├── Pepper/
                                         ├── Potato/
                                         ├── Raspberry/
                                         ├── Soybean/
                                         ├── Squash/
                                         ├── Strawberry/
                                         └── Tomato/        ← ALL Tomato_* images combined
```

No new data needed! Just a Python script to copy/reorganize the existing images by their species prefix.

#### Class Balance
Some species have many more images (Tomato has 10 disease classes = lots of images) while others have few (Blueberry has 1 class). To handle this:
- **Oversample** minority classes (duplicate/augment Blueberry, Raspberry, Soybean images)
- **Undersample** majority classes (randomly pick a subset of Tomato images)
- Target: ~1000-2000 images per species

### Training Parameters

| Parameter | Value |
|---|---|
| Base model | EfficientNetB0 (ImageNet weights) |
| Image size | 224 × 224 |
| Batch size | 32 |
| Epochs | 25-30 |
| Optimizer | Adam (lr=0.0001) |
| Loss | Categorical Crossentropy |
| Augmentation | Rotation, flip, brightness, zoom, shear |
| Strategy | Freeze → train top → unfreeze last 50 layers → fine-tune |

### Expected Accuracy: **90-95%**

Species classification is easier than disease classification because species have more visually distinct features (leaf shape, size, vein pattern, color tone).

### Output File
- `species_classifier.keras` (~15 MB)
- `species_labels.json` (14 labels)

---

## Gate 3: Disease Classifier (Refined + PlantDoc)

### Job
> "What disease does this {species} leaf have?"

**Input:** A leaf image + confirmed species from Gate 2
**Output:** The specific disease for that species

### Our Approach: Single Model + Crop Filtering + PlantDoc Data

Keep our existing 38-class model architecture, but **retrain it** with additional real-world data and **filter the output by the species detected in Gate 2**.

### The Core Problem: Lab vs Real World

Our current model was trained **only on PlantVillage** — perfectly cropped, single leaves on plain backgrounds:

```
PlantVillage images:          Real-world photos (what users actually take):
┌──────────────────┐          ┌──────────────────┐
│                  │          │  🌿🌿  soil      │
│     🍃           │          │    🤚 hand       │
│  (single leaf)   │          │  🌿 multiple     │
│  (plain bg)      │          │    leaves + sky   │
│                  │          │  blurry, angled   │
└──────────────────┘          └──────────────────┘
```

When a user takes a real photo with their phone, there's:
- **Hands** holding the leaf
- **Soil** or ground in the background
- **Multiple leaves** in the frame
- **Varying lighting** — shadows, sunlight, overexposed
- **Different angles** — not perfectly flat

The model has NEVER seen any of this during training. So it panics and gives random predictions.

### The Fix: Add PlantDoc Dataset

**PlantDoc** is a dataset of **2,598 real-world plant disease images** collected from the internet. Unlike PlantVillage:

| Feature | PlantVillage (current) | PlantDoc (adding) |
|---|---|---|
| Background | Plain/lab-controlled | Real-world (soil, sky, hands) |
| Leaf count | Single isolated leaf | Multiple leaves, full plants |
| Lighting | Consistent studio lighting | Natural light, shadows, varying |
| Angle | Flat, top-down | Various angles |
| Quality | High-res, clean | Varies (phone photos, web images) |
| Crops covered | 14 species | 13 species (overlapping) |
| Disease classes | 38 | 27 (partially overlapping) |

#### PlantDoc Classes (27 total):

```
Apple       → Scab, Black rot, Cedar rust, Healthy
Bell Pepper → Bacterial spot, Healthy
Blueberry   → Healthy
Cherry      → Healthy, Powdery mildew
Corn        → Common rust, Gray leaf spot, Northern blight, Healthy
Grape       → Black rot, Black measles (Esca), Leaf blight, Healthy
Peach       → Bacterial spot, Healthy
Potato      → Early blight, Late blight, Healthy
Raspberry   → Healthy
Soybean     → Healthy
Squash      → Powdery mildew
Strawberry  → Healthy, Leaf scorch
Tomato      → Bacterial spot, Early blight, Late blight, Leaf mold,
              Septoria, Spider mites, Target spot, Mosaic virus,
              Yellow leaf curl, Healthy
```

Most of these **overlap with our existing PlantVillage classes** — so the PlantDoc images just add more variety to existing classes.

### How We Combine the Datasets

```
Combined Dataset:
├── Apple___Apple_scab/
│   ├── plantvillage_001.jpg     ← lab image (clean)
│   ├── plantvillage_002.jpg
│   ├── plantdoc_001.jpg         ← real-world image (hands, soil, etc.)
│   ├── plantdoc_002.jpg
│   └── ...
├── Apple___Black_rot/
│   ├── plantvillage_001.jpg
│   ├── plantdoc_001.jpg
│   └── ...
└── ... (all 38 classes)
```

For PlantDoc classes that match our existing ones → merge directly.
For PlantDoc classes that DON'T exist in PlantVillage → skip them (we keep our 38 classes).

### Training Improvements

| Change | What | Why |
|---|---|---|
| **Combined dataset** | PlantVillage (~54K) + PlantDoc (~2.6K) | Real-world robustness |
| **Aggressive augmentation** | Random crop, color jitter, Gaussian blur, rotation ±30°, horizontal flip, brightness ±20% | Simulate messy real-world photos — also prevents overfitting |
| **Background noise** | Random background insertion during training | Model learns to ignore backgrounds |
| **Smart training** | 25 epochs max with **EarlyStopping** (patience=5) + **ReduceLROnPlateau** (patience=3) | Trains just enough — stops automatically when validation loss stops improving, preventing overfitting |
| **Class weighting** | Higher weights for under-represented classes | Balanced predictions |
| **Larger model** | EfficientNetB2 (up from B0) — more capacity | Better feature extraction |

> [!IMPORTANT]
> **Why we won't overfit:**
> 1. **EarlyStopping** — monitors validation loss and stops training if it hasn't improved for 5 epochs. The model is automatically rolled back to the best checkpoint.
> 2. **ReduceLROnPlateau** — if validation loss plateaus for 3 epochs, the learning rate drops by 50%. This gives the model finer control instead of overshooting.
> 3. **More data** — adding PlantDoc increases our dataset size, which naturally reduces overfitting.
> 4. **Heavy augmentation** — every epoch the model sees slightly different versions of each image, so it can't memorize the training set.
> 5. **Dropout (0.4)** — randomly disables 40% of neurons during training, forcing the model to learn redundant features.

### Crop Filtering Logic

After the model predicts, we filter by the species confirmed in Gate 2:

```
Raw model output (38 probabilities):
  Tomato_EarlyBlight: 0.40
  Potato_LateBlight: 0.35
  Tomato_healthy: 0.10
  Potato_healthy: 0.08
  ... (34 more classes)

Gate 2 confirmed: "Potato"

Step 1 — Filter to Potato classes only:
  Potato_LateBlight: 0.35
  Potato_healthy: 0.08
  Potato_EarlyBlight: 0.02

Step 2 — Re-normalize (divide by sum, so they add to 1.0):
  Potato_LateBlight: 0.35 / 0.45 = 0.778  → 77.8%
  Potato_healthy: 0.08 / 0.45 = 0.178     → 17.8%
  Potato_EarlyBlight: 0.02 / 0.45 = 0.044 → 4.4%

Final result: "Potato Late Blight" at 77.8% confidence
```

This ensures the user **ONLY** sees diseases relevant to their crop, regardless of what the model's raw output says.

### Confidence Threshold (After Filtering)

Even after filtering, if the confidence is too low, the prediction is unreliable:

```
If filtered_confidence < 0.40 → "Unable to identify the disease clearly.
                                  Try a clearer, well-lit photo of the leaf."
```

### Output File
- `plant_disease_model_v2.keras` (~20 MB, retrained with PlantDoc)

---

## Full Pipeline Flow

Here's exactly how a prediction works with all 3 gates:

```
User uploads image + selects "Potato"
           │
           ▼
    ┌─────────────┐
    │   GATE 1    │   leaf_detector.keras
    │  Leaf Check │   "Is this a leaf?"
    └──────┬──────┘
           │
     ┌─────┴─────┐
     ▼           ▼
   LEAF      NOT LEAF
     │        → REJECT: "This doesn't look like a leaf.
     │                   Please upload a clear leaf image."
     ▼
    ┌─────────────┐
    │   GATE 2    │   species_classifier.keras
    │  Species ID │   "Which plant is this?"
    └──────┬──────┘
           │
     ┌─────┴──────┐
     ▼            ▼
  MATCHES      MISMATCH
  "Potato"     "Tomato" (user said Potato)
     │          → WARNING: "This looks like a Tomato leaf,
     │                      not Potato. Scan as Tomato instead?"
     ▼
    ┌─────────────┐
    │   GATE 3    │   plant_disease_model.keras
    │ Disease ID  │   (filtered to Potato diseases only)
    └──────┬──────┘
           │
           ▼
    RESULT: "Potato Late Blight"
    Confidence: 87.3%
    Severity: High
    Remedies: [...]
```

### Possible Outcomes:
1. **REJECT** (Gate 1 fails) → "Not a leaf" message
2. **MISMATCH** (Gate 2 species ≠ selected crop) → Warning + option to re-scan
3. **DIAGNOSIS** (all gates pass) → Disease result with remedies

---

## Backend Integration

The `MLService` in `app/services/ml_service.py` will change to load all 3 models:

```
Current:
  - Loads 1 model (plant_disease_model.keras)
  - Single predict() method

After:
  - Loads 3 models on startup:
    1. leaf_detector.keras
    2. species_classifier.keras
    3. plant_disease_model.keras
  - predict() method runs all 3 gates in sequence
  - Returns different response types based on which gate fails
```

### Model Files Location:
```
F:\ML_PROJECT\ml\models\
├── leaf_detector.keras           # Gate 1 (~10 MB)
├── species_classifier.keras      # Gate 2 (~15 MB)
├── species_labels.json           # 14 species labels
├── plant_disease_model.keras     # Gate 3 (~30 MB, existing)
└── labels.json                   # 38 disease labels (existing)
```

---

## Dataset Sources

| Dataset | What It Has | Size | Where |
|---|---|---|---|
| **PlantVillage** (already have) | 38 classes of diseased/healthy leaves | ~54K images | Already downloaded |
| **Leaf vs Non-Leaf** | Leaf and non-leaf images for Gate 1 | ~2.4 GB | [Kaggle](https://www.kaggle.com/datasets/robiulhasanjisan/leaf-vs-non-leaf-images) |
| **PlantDoc** | Real-world plant disease images (not lab-controlled) | ~2,600 images | Kaggle |

> [!TIP]
> PlantVillage images are lab-controlled (single leaf on plain background). PlantDoc has real-world images (leaves on trees, multiple leaves, varying backgrounds). Training on BOTH makes the model much more robust in the real world.

---

## Training Platform

We'll train on **Kaggle Notebooks** (same as Phase 2):
- **Free GPU:** 30 hours/week of T4 GPU
- **Pre-installed:** TensorFlow, Keras, all ML libraries
- **Easy dataset access:** Upload datasets to Kaggle and import directly

### Training Order:
1. **Gate 1 (Leaf Detector):** ~30 min training time
2. **Gate 2 (Species Classifier):** ~1-2 hours training time
3. **Gate 3 (Disease Classifier refinement):** ~2-3 hours training time

Total: **~4-5 hours of GPU time** (well within Kaggle's free tier)

---

## Expected Improvements

| Metric | Current (V1) | After 3-Gate (V2) |
|---|---|---|
| Non-leaf rejection | ❌ No rejection | ✅ 95%+ rejection rate |
| Cross-crop confusion | ❌ Potato shows Tomato disease | ✅ Eliminated (species verified first) |
| Overall accuracy | ~70-75% (all classes mixed) | ~85-90% (per-crop filtered) |
| User confidence | Low (random-seeming results) | High (clear reject/mismatch/diagnosis) |
| False positives | High | Low (3 layers of validation) |

---

## Implementation Steps

| Step | Task | Effort |
|---|---|---|
| 1 | Add [Leaf vs Non-Leaf Images](https://www.kaggle.com/datasets/robiulhasanjisan/leaf-vs-non-leaf-images) dataset in Kaggle notebook | 5 min |
| 2 | Train Gate 1 (MobileNetV2 binary classifier) on Kaggle | 30 min GPU |
| 3 | Prepare Gate 2 dataset (reorganize PlantVillage by species) | 1 hour |
| 4 | Train Gate 2 (EfficientNetB0 14-class) on Kaggle | 1-2 hours GPU |
| 5 | Download PlantDoc dataset from Kaggle | 10 min |
| 6 | Merge PlantDoc into PlantVillage (map matching classes) | 1-2 hours |
| 7 | Retrain Gate 3 on combined dataset (EfficientNetB2, 38-class) | 2-3 hours GPU |
| 8 | Download all 3 models to `ml/models/` | 10 min |
| 9 | Update backend `MLService` to run 3-gate pipeline + crop filtering | 1-2 hours |
| 10 | Update frontend `ResultScreen` to handle reject/mismatch states | 1 hour |
| 11 | Test end-to-end with real-world photos | 1 hour |
