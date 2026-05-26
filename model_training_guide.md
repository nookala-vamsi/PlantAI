# 🧠 Model Training Guide — Plant Disease Classifier (38 Classes)

> **Platform:** Kaggle Notebook (GPU P100 or T4 x 2)
>
> **Dataset:** New Plant Diseases Dataset (87K images, 38 classes)
>
> **Goal:** Train a model that takes a leaf image → outputs which disease it has (or if it's healthy)

---

## Why Kaggle Instead of Colab?

| Feature | Kaggle | Google Colab |
|---|---|---|
| **Dataset access** | Dataset is already ON Kaggle — zero download time | Need to download via API (~3 GB, wastes time) |
| **GPU quota** | 30 hours/week (P100 or T4 x 2) | ~4-5 hours/day on free tier |
| **File system** | Dataset at `/kaggle/input/`, output at `/kaggle/working/` | Everything on `/content/`, wiped on disconnect |
| **Saving output** | Auto-saved as "Output" of notebook | Need Google Drive mount |

**Bottom line:** Since the dataset is ON Kaggle, using Kaggle notebooks is the smartest choice. No downloading, no API setup, no storage issues.

---

## Step 1: Create a Kaggle Notebook

1. Go to the dataset page: [New Plant Diseases Dataset](https://www.kaggle.com/datasets/vipoooool/new-plant-diseases-dataset)
2. Click **"New Notebook"** button on the dataset page
3. This automatically **attaches the dataset** to your notebook — no download needed
4. The dataset will be available at: `/kaggle/input/new-plant-diseases-dataset/`

### Set GPU Accelerator:
- Click **Settings** (right sidebar) → **Accelerator** → Select **GPU P100** or **GPU T4 x 2**
- This gives you a powerful GPU for free (30 hrs/week)

### What's the file system?

```
/kaggle/
├── input/                              ← READ-ONLY (your datasets live here)
│   └── new-plant-diseases-dataset/
│       ├── New Plant Diseases Dataset(Augmented)/
│       │   ├── train/                  ← 70,295 images in 38 folders
│       │   └── valid/                  ← 17,572 images in 38 folders
│       └── test/                       ← 33 test images
│
└── working/                            ← READ-WRITE (your outputs go here)
    ├── plant_disease_model.keras       ← Your trained model (we save here)
    └── labels.json                     ← Class labels mapping
```

> [!IMPORTANT]
> `/kaggle/input/` is **read-only**. You cannot write files there. All your outputs (trained models, plots, etc.) go to `/kaggle/working/`.

---

## Step 2: Understand the Dataset

### What's in it?

| Property | Value |
|---|---|
| Total images | ~87,000 |
| Training images | ~70,295 (80%) |
| Validation images | ~17,572 (20%) |
| Number of classes | 38 |
| Number of crop species | 14 |
| Image type | RGB color photos |
| Augmentation | Already done offline (flips, rotations, etc.) |

### What are the 38 classes?

Each class name follows this pattern: `{Species}___{Condition}`

Examples:
- `Tomato___Early_blight` → Tomato leaf with Early Blight disease
- `Tomato___healthy` → Healthy tomato leaf
- `Potato___Late_blight` → Potato leaf with Late Blight disease
- `Apple___Apple_scab` → Apple leaf with Apple Scab disease

Some species have many diseases (Tomato has 10+1 healthy), some have only healthy (Blueberry, Raspberry, Soybean).

### What do the images look like?

These are **lab-quality images** — leaves photographed against controlled backgrounds with consistent lighting. They're clean and well-organized. This makes training easier but means the model might struggle with messy real-world phone photos (we'll address this in future refinements).

---

## Step 3: Understand Transfer Learning

### The Problem

Training a deep learning model from scratch needs **millions of images** and **days of GPU time**. We have 87K images and a few hours of free GPU. Not enough.

### The Solution: Transfer Learning

Instead of starting from zero, we take a model that **someone else already trained** on millions of images (ImageNet — 14 million images, 1000 categories like dogs, cars, flowers, buildings, etc.) and **reuse its knowledge**.

### Analogy

Think of it like this:
- **From scratch** = Teaching a baby to identify plant diseases. They need to first learn what colors are, what shapes are, what edges are, what textures are... and THEN learn about diseases. Takes years.
- **Transfer learning** = Teaching a medical student to identify plant diseases. They already know about colors, shapes, textures, and biology. They just need to learn the specific diseases. Takes days.

### How it works (two phases):

**Phase A — Freeze & Train Top (the "teach the specialist" phase):**
1. Take the pretrained model (knows generic image features)
2. **Freeze** all its layers (don't change what it already knows)
3. Add new layers on top specifically for our 38 classes
4. Train ONLY the new top layers
5. This teaches the model: "Use your existing knowledge to classify these 38 diseases"

**Phase B — Fine-tune (the "polish" phase):**
1. **Unfreeze** the last few layers of the pretrained model
2. Train these unfrozen layers + top layers together with a **very small learning rate**
3. This gently adjusts the pretrained features to be more specific to leaf diseases
4. Think of it as: "Now that you understand the task, let's fine-tune your vision for leaves specifically"

> [!WARNING]
> Why a smaller learning rate in Phase B? Because the pretrained layers already have good knowledge. A large learning rate would destroy that knowledge (called "catastrophic forgetting"). A small rate gently adjusts it.

---

## Step 4: Choose the Architecture

### What is EfficientNetB0?

It's a family of models designed by Google that achieve high accuracy with fewer parameters (efficient). The "B0" means it's the smallest variant.

### Why EfficientNetB0?

| Architecture | Parameters | Accuracy | Input Size | Model File Size | Why? |
|---|---|---|---|---|---|
| MobileNetV2 | 3.5M | Good | 224x224 | ~9 MB | Too simple for 38 classes |
| **EfficientNetB0** | **5.3M** | **Very Good** | **224x224** | **~20 MB** | **Best balance for our task** |
| EfficientNetB3 | 12M | Excellent | 300x300 | ~48 MB | Overkill, slower training |
| ResNet50 | 25.6M | Good | 224x224 | ~98 MB | Too heavy, older design |

**EfficientNetB0 is the sweet spot:**
- Small enough to train quickly on free GPU
- Powerful enough for 38-class classification
- Small model file (~20 MB) — easy to deploy on a server
- 224x224 input — standard size, fast inference

---

## Step 5: The Training Workflow (What Happens Step by Step)

### 5.1 — Load the Dataset

Read images from the train/ and valid/ folders. Each subfolder name becomes the class label.

- Images are loaded in **batches** (e.g., 32 images at a time) — we can't load all 87K into memory at once
- Images are **resized** to 224x224 pixels (EfficientNetB0's expected input)
- Labels are **one-hot encoded** (e.g., class 5 of 38 → `[0,0,0,0,0,1,0,...,0]`)

### 5.2 — Preprocess Images

EfficientNet expects a specific pixel format. We apply `preprocess_input()` which scales pixel values from `[0, 255]` to the range the model expects. This is built into TensorFlow — one line.

### 5.3 — Build the Model

Stack these layers:

```
Input (224x224x3 image)
    ↓
EfficientNetB0 (pretrained, frozen) — extracts visual features
    ↓
GlobalAveragePooling2D — compresses features into a flat vector
    ↓
Dropout (0.5) — randomly drops 50% of connections during training (prevents overfitting)
    ↓
Dense (256 neurons, ReLU) — learns disease-specific patterns
    ↓
Dropout (0.3) — more regularization
    ↓
Dense (38 neurons, Softmax) — outputs probability for each of 38 classes
```

**What Dropout does:** During training, it randomly turns off neurons. This forces the model to not rely on any single feature — making it more robust. It's like studying with random pages removed from your textbook — you learn to understand concepts, not memorize pages.

**What Softmax does:** Converts raw numbers into probabilities that sum to 1.0. For example: `[0.85 Tomato_Blight, 0.10 Tomato_Spot, 0.03 Tomato_Healthy, 0.02 others...]`. The highest probability is the prediction.

### 5.4 — Compute Class Weights

Some classes have more images than others:
- `Orange___Haunglongbing` → ~2,010 images
- `Corn___Cercospora_leaf_spot` → ~1,642 images

If we don't account for this, the model biases toward classes with more images. **Class weights** tell the model: "Pay more attention to smaller classes."

Formula: `weight = total_images / (num_classes x class_count)`
- Large class → small weight (you already have enough examples)
- Small class → large weight (learn harder from these)

### 5.5 — Phase A: Train Top Layers (Frozen Base)

- **What's frozen:** All EfficientNetB0 layers (5.3M parameters) — they don't change
- **What trains:** Only the Dense + Dropout layers we added (~76K parameters)
- **Learning rate:** 0.001 (standard)
- **Epochs:** Up to 5 (but may stop early)
- **Purpose:** Teach the new layers to use EfficientNet's features for disease classification

### 5.6 — Phase B: Fine-tune (Unfreeze Last 20 Layers)

- **What unfreezes:** Last 20 layers of EfficientNetB0 (the most "high-level" feature layers)
- **Learning rate:** 0.0001 (10x smaller — gentle adjustments)
- **Epochs:** Up to 15 (but may stop early)
- **Purpose:** Gently adjust EfficientNet's features to be more specific to leaf diseases

### 5.7 — Evaluate on Validation Set

After training, test the model on the 17,572 validation images (images it has NEVER seen during training).

---

## Step 6: What Are Callbacks?

Callbacks are "automatic rules" that run during training. We use 3:

### EarlyStopping
- **What:** Monitors validation loss each epoch. If it doesn't improve for X epochs in a row, STOP training.
- **Why:** Prevents wasting time + prevents overfitting (when model memorizes training data instead of learning patterns)
- **Setting:** `patience=5` → Stop if no improvement for 5 consecutive epochs
- **Extra:** `restore_best_weights=True` → After stopping, revert to the best epoch's weights (not the last epoch)

### ModelCheckpoint
- **What:** After each epoch, if validation accuracy improved, SAVE the model to disk.
- **Why:** If training crashes or overfitting starts, you still have the best version saved.
- **Setting:** `save_best_only=True` → Only save when it's better than the previous best

### ReduceLROnPlateau
- **What:** If validation loss stops improving for X epochs, reduce the learning rate by half.
- **Why:** Sometimes training gets "stuck" — a smaller learning rate helps it find better solutions.
- **Setting:** `patience=3, factor=0.5` → If stuck for 3 epochs, halve the learning rate
- **Analogy:** Like walking with large steps when you're far from the destination, then switching to small careful steps when you're close.

---

## Step 7: Evaluation — How Do We Know It's Good?

### Metric 1: Accuracy
- **What:** % of images correctly classified
- **Target:** ≥ 95% on validation set
- **Example:** 17,000 / 17,572 = 96.7% accuracy

### Metric 2: Per-Class Precision, Recall, F1-Score

For EACH of the 38 classes:

- **Precision:** Of all images the model SAID are "Tomato_Blight", what % actually were? (Low precision = too many false alarms)
- **Recall:** Of all actual "Tomato_Blight" images, what % did the model catch? (Low recall = missing diseases)
- **F1-Score:** Harmonic mean of precision and recall. A balanced measure.

**Why per-class matters:** Overall accuracy might be 95%, but if "Potato___Early_blight" has 60% recall, the model is BAD at detecting that specific disease. Per-class metrics reveal this.

### Metric 3: Confusion Matrix

A 38x38 grid showing:
- Row = actual class
- Column = predicted class
- Diagonal = correct predictions (should be high)
- Off-diagonal = mistakes (should be low/zero)

It visually reveals which diseases get confused with each other. For example, you might see that `Tomato___Early_blight` and `Tomato___Late_blight` get confused often — they look similar!

---

## Step 8: Save the Model

After training, we save **two files**:

### 1. The Model File (`plant_disease_model.keras`)
- Contains the entire trained model (architecture + weights)
- Size: ~20 MB
- This is what the backend loads to make predictions

### 2. The Labels File (`labels.json`)
- Maps class indices to human-readable names
- Example: `{"0": "Apple___Apple_scab", "1": "Apple___Black_rot", ...}`
- The model outputs index 17 → labels.json tells you that's `Pepper,_bell___Bacterial_spot`

### How to get these files?

On Kaggle, anything saved to `/kaggle/working/` becomes the **notebook's "Output"**. After training:
1. Go to notebook → **Output** tab
2. Click **Download** → downloads a zip with your model + labels
3. Put these in your backend project's `ml/models/` folder

---

## Step 9: How Will the Backend Use This Model?

```
User uploads image via Flutter app
        ↓
Backend (FastAPI) receives the image
        ↓
Load the .keras model (loaded once at startup, stays in memory)
        ↓
Resize image to 224x224 → preprocess → pass through model
        ↓
Model outputs: [0.01, 0.02, ..., 0.89, ..., 0.01]  (38 probabilities)
        ↓
Pick highest probability → index 24 → labels.json → "Tomato___Early_blight"
        ↓
Return to user: "Tomato — Early Blight (89% confidence)"
```

---

## Step 10: Future Refinements (After V1 Works)

| Refinement | What It Does | Difficulty |
|---|---|---|
| **Confidence threshold** | If max probability < 85%, say "uncertain, retake photo" | Add 5 lines of code in backend |
| **Leaf detection (Gate 1)** | Reject non-leaf images before prediction | Train separate small model |
| **Species validation (Gate 2)** | Check if predicted species matches user selection | Train separate model |
| **PlantDoc fine-tuning** | Improve accuracy on real-world phone photos | Fine-tune existing model on PlantDoc dataset |
| **More crops** | Add crops not in current 14 species | Extend dataset and retrain |

---

## Summary

| Item | Detail |
|---|---|
| **Platform** | Kaggle Notebook with GPU P100 or T4 x 2 |
| **Dataset** | New Plant Diseases (87K images, 38 classes, already attached) |
| **Architecture** | EfficientNetB0 (transfer learning from ImageNet) |
| **Training** | Phase A: frozen base (5 epochs) → Phase B: fine-tune 20 layers (15 epochs) |
| **No augmentation** | Dataset is already augmented offline |
| **Output** | `plant_disease_model.keras` (~20 MB) + `labels.json` |
| **Expected accuracy** | 95-99% on validation set |
| **Training time** | ~30-45 minutes on GPU |
| **Total output size** | ~20 MB (model) — easy to download and deploy |
