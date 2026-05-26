"""
=============================================================================
🌱 GATE 2 — SPECIES CLASSIFIER (14-Class)
=============================================================================
Plant Disease AI — 3-Gate Pipeline
Goal: Identify which of the 14 supported plant species a leaf belongs to.
      This validates the user's crop selection and catches cross-crop
      mismatches before the disease classifier runs.

Architecture : EfficientNetB0 (ImageNet pretrained) + custom head
Dataset      : PlantVillage / New Plant Diseases Dataset (Kaggle)
               — reorganized from 38 disease classes → 14 species
Training     : Two-phase transfer learning (freeze → fine-tune)
Expected Acc : 90-95%
Output       : species_classifier.keras (~15 MB)
             : species_labels.json (14 species names)

HOW TO RUN ON KAGGLE:
1. Create a new Kaggle Notebook
2. Add Input → search "New Plant Diseases Dataset" by Vipoooool
3. Enable GPU: Settings → Accelerator → GPU T4 x2
4. Copy ALL of this file into a single code cell (or split at the
   "# ====" markers into separate cells)
5. Run all cells
=============================================================================
"""


# ============================================================================
# CELL 1 — IMPORTS & CONFIGURATION
# ============================================================================

import os
import json
import shutil
import random
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.applications import EfficientNetB0
from tensorflow.keras.applications.efficientnet import preprocess_input
from tensorflow.keras.callbacks import (
    EarlyStopping,
    ReduceLROnPlateau,
    ModelCheckpoint,
)
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns

# ── Config ──
IMG_SIZE = 224
BATCH_SIZE = 32
SEED = 42

# Phase 1: train top layers only (base frozen)
PHASE1_EPOCHS = 5
PHASE1_LR = 1e-4

# Phase 2: fine-tune last 50 layers of EfficientNetB0
PHASE2_EPOCHS = 25
PHASE2_LR = 1e-5

# Class balancing target: ~2000 images per species
TARGET_PER_CLASS = 2000

random.seed(SEED)
np.random.seed(SEED)
tf.random.set_seed(SEED)

print(f"TensorFlow : {tf.__version__}")
print(f"GPU        : {tf.config.list_physical_devices('GPU')}")

# The 14 supported species — defines the mapping from disease folder names
# to species. The prefix before "___" in each PlantVillage folder name
# determines the species.
SPECIES_PREFIX_MAP = {
    "Apple":   "Apple",
    "Blueberry": "Blueberry",
    "Cherry":  "Cherry",
    "Corn":    "Corn",
    "Grape":   "Grape",
    "Orange":  "Orange",
    "Peach":   "Peach",
    "Pepper":  "Pepper",
    "Potato":  "Potato",
    "Raspberry": "Raspberry",
    "Soybean": "Soybean",
    "Squash":  "Squash",
    "Strawberry": "Strawberry",
    "Tomato":  "Tomato",
}


# ============================================================================
# CELL 2 — FIND THE PLANTVILLAGE DATASET (train + valid)
# ============================================================================

def find_all_plantvillage_dirs(search_root="/kaggle/input"):
    """
    Search for directories containing PlantVillage disease class folders.
    Prunes the walk to avoid scanning inside the image folders.
    """
    found = []
    for dirpath, dirnames, _ in os.walk(search_root):
        disease_dirs = [d for d in dirnames if "___" in d]
        if len(disease_dirs) >= 30:
            found.append(dirpath)
            dirnames.clear()  # Don't descend into the disease class folders
    return found

RAW_DIRS = find_all_plantvillage_dirs()

if not RAW_DIRS:
    raise FileNotFoundError(
        "Could not find the PlantVillage dataset under /kaggle/input/. "
        "Make sure you added 'New Plant Diseases Dataset' by Vipoooool."
    )

print(f"✅ Found {len(RAW_DIRS)} PlantVillage directories:")
for d in RAW_DIRS:
    folder_count = len([x for x in os.listdir(d) if "___" in x])
    print(f"   {d}  ({folder_count} classes)")

# Deduplicate — Kaggle sometimes exposes the same dataset with different
# parent folder casing (e.g. "New Plant..." vs "new plant...").
# Keep only the first train/ and first valid/ to avoid double-counting.
seen = set()
deduped = []
for d in RAW_DIRS:
    basename = os.path.basename(d).lower()  # "train" or "valid"
    if basename not in seen:
        seen.add(basename)
        deduped.append(d)

RAW_DIRS = deduped
print(f"\n   Using {len(RAW_DIRS)} directories (deduplicated):")
for d in RAW_DIRS:
    print(f"   → {d}")

# Collect all unique disease folder names across train + valid
all_disease_folders = set()
for raw_dir in RAW_DIRS:
    for d in os.listdir(raw_dir):
        if os.path.isdir(os.path.join(raw_dir, d)) and "___" in d:
            all_disease_folders.add(d)

all_disease_folders = sorted(all_disease_folders)
print(f"\n   Unique disease classes: {len(all_disease_folders)}")


# ============================================================================
# CELL 3 — REORGANIZE: 38 DISEASE CLASSES → 14 SPECIES FOLDERS
# ============================================================================

# Merges images from BOTH train/ and valid/ into unified species folders.
# Uses SYMLINKS (instant) instead of copying ~87K files.
# We'll do our own 80/10/10 split later.

SPECIES_DIR = "/kaggle/working/species_dataset"

if os.path.exists(SPECIES_DIR):
    shutil.rmtree(SPECIES_DIR)

def extract_species(folder_name):
    """
    Extract species name from a PlantVillage folder name.
    
    Examples:
      'Apple___Apple_scab'                  → 'Apple'
      'Cherry_(including_sour)___healthy'   → 'Cherry'
      'Corn_(maize)___Common_rust_'         → 'Corn'
      'Pepper,_bell___Bacterial_spot'       → 'Pepper'
    """
    species_part = folder_name.split("___")[0]
    
    # Normalize known variants
    if species_part.startswith("Cherry"):
        return "Cherry"
    if species_part.startswith("Corn"):
        return "Corn"
    if species_part.startswith("Pepper"):
        return "Pepper"
    return species_part

from PIL import Image

species_counts = {}
skipped = 0
file_id = 0  # Global counter to guarantee unique filenames

for raw_dir in RAW_DIRS:
    split_name = os.path.basename(raw_dir)  # "train" or "valid"
    
    for disease_folder in all_disease_folders:
        src_dir = os.path.join(raw_dir, disease_folder)
        if not os.path.isdir(src_dir):
            continue
        
        species = extract_species(disease_folder)
        
        if species not in SPECIES_PREFIX_MAP:
            print(f"  ⚠️ Unknown species: '{species}' from '{disease_folder}'")
            continue
        
        dst_dir = os.path.join(SPECIES_DIR, species)
        os.makedirs(dst_dir, exist_ok=True)
        
        disease_tag = disease_folder.split("___")[1] if "___" in disease_folder else ""
        count = 0
        
        for fname in os.listdir(src_dir):
            src_file = os.path.join(src_dir, fname)
            if not os.path.isfile(src_file):
                continue
            
            ext = os.path.splitext(fname)[1].lower()
            file_id += 1
            
            if ext in {".jpg", ".jpeg", ".png", ".bmp", ".gif"}:
                new_fname = f"{split_name}_{disease_tag}_{file_id}{ext}"
                try:
                    # Symlink instead of copy — near-instant
                    os.symlink(src_file, os.path.join(dst_dir, new_fname))
                    count += 1
                except Exception:
                    skipped += 1
            
            elif ext == ".webp":
                try:
                    with Image.open(src_file) as img:
                        rgb_img = img.convert("RGB")
                        new_fname = f"{split_name}_{disease_tag}_{file_id}.jpg"
                        rgb_img.save(os.path.join(dst_dir, new_fname), "JPEG", quality=95)
                        count += 1
                except Exception:
                    skipped += 1
            else:
                skipped += 1
        
        species_counts[species] = species_counts.get(species, 0) + count

print(f"\n✅ Reorganized into {len(species_counts)} species (train + valid merged):")
print(f"   Skipped: {skipped} files\n")

for species in sorted(species_counts.keys()):
    print(f"   {species:12s}: {species_counts[species]:,} images")

total_images = sum(species_counts.values())
print(f"\n   Total: {total_images:,} images")


# ============================================================================
# CELL 4 — CLASS BALANCING (OVERSAMPLE MINORITY / UNDERSAMPLE MAJORITY)
# ============================================================================

# Some species have way more images than others (Tomato has ~18K from 10
# disease classes, Blueberry has ~1.5K from 1 class). This imbalance would
# make the model biased toward Tomato.
#
# Strategy:
#   - Species with < TARGET_PER_CLASS images → oversample (duplicate files)
#   - Species with > TARGET_PER_CLASS images → undersample (keep random subset)

BALANCED_DIR = "/kaggle/working/species_balanced"

if os.path.exists(BALANCED_DIR):
    shutil.rmtree(BALANCED_DIR)

print(f"Target per class: ~{TARGET_PER_CLASS:,} images\n")

for species in sorted(os.listdir(SPECIES_DIR)):
    src_cls = os.path.join(SPECIES_DIR, species)
    if not os.path.isdir(src_cls):
        continue
    
    dst_cls = os.path.join(BALANCED_DIR, species)
    os.makedirs(dst_cls, exist_ok=True)
    
    files = [
        f for f in os.listdir(src_cls)
        if not f.startswith(".") and os.path.isfile(os.path.join(src_cls, f))
    ]
    original_count = len(files)
    
    if original_count >= TARGET_PER_CLASS:
        # UNDERSAMPLE: randomly pick TARGET_PER_CLASS files
        selected = random.sample(files, TARGET_PER_CLASS)
        for fname in selected:
            shutil.copy2(
                os.path.join(src_cls, fname),
                os.path.join(dst_cls, fname),
            )
        action = f"undersampled {original_count:,} → {TARGET_PER_CLASS:,}"
    else:
        # OVERSAMPLE: copy all originals + duplicate until we reach target
        for fname in files:
            shutil.copy2(
                os.path.join(src_cls, fname),
                os.path.join(dst_cls, fname),
            )
        
        # Duplicate random files to fill up to TARGET_PER_CLASS
        deficit = TARGET_PER_CLASS - original_count
        for j in range(deficit):
            src_fname = random.choice(files)
            base, ext = os.path.splitext(src_fname)
            dup_fname = f"{base}_dup{j}{ext}"
            shutil.copy2(
                os.path.join(src_cls, src_fname),
                os.path.join(dst_cls, dup_fname),
            )
        action = f"oversampled  {original_count:,} → {TARGET_PER_CLASS:,}"
    
    final_count = len(os.listdir(dst_cls))
    print(f"   {species:12s}: {action}  (final: {final_count:,})")

print(f"\n✅ Balanced dataset ready at {BALANCED_DIR}")


# ============================================================================
# CELL 5 — LOAD DATASET (TRAIN / VAL / TEST SPLIT)
# ============================================================================

# Load 80% as training set
train_ds = keras.utils.image_dataset_from_directory(
    BALANCED_DIR,
    validation_split=0.2,
    subset="training",
    seed=SEED,
    image_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    label_mode="categorical",   # 14-class → one-hot encoded
)

# Load 20% as val+test, then split in half
val_test_ds = keras.utils.image_dataset_from_directory(
    BALANCED_DIR,
    validation_split=0.2,
    subset="validation",
    seed=SEED,
    image_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    label_mode="categorical",
)

# Split val_test into validation (50%) and test (50%)
val_batches = int(0.5 * len(val_test_ds))
val_ds = val_test_ds.take(val_batches)
test_ds = val_test_ds.skip(val_batches)

class_names = train_ds.class_names
NUM_CLASSES = len(class_names)

print(f"\nClasses ({NUM_CLASSES}): {class_names}")
print(f"Train batches: {len(train_ds)}")
print(f"Val batches  : {len(val_ds)}")
print(f"Test batches : {len(test_ds)}")


# ============================================================================
# CELL 6 — VISUALIZE SAMPLE IMAGES
# ============================================================================

plt.figure(figsize=(16, 8))
for images, labels in train_ds.take(1):
    for i in range(min(14, len(images))):
        ax = plt.subplot(2, 7, i + 1)
        plt.imshow(images[i].numpy().astype("uint8"))
        label_idx = np.argmax(labels[i].numpy())
        plt.title(class_names[label_idx], fontsize=9)
        plt.axis("off")
plt.suptitle("Sample Training Images (1 per species)", fontsize=14)
plt.tight_layout()
plt.show()


# ============================================================================
# CELL 7 — DATA AUGMENTATION & PERFORMANCE OPTIMIZATION
# ============================================================================

# More aggressive augmentation than Gate 1 because species classification
# has more classes and subtler differences
data_augmentation = keras.Sequential([
    layers.RandomFlip("horizontal"),
    layers.RandomRotation(0.15),
    layers.RandomZoom(0.15),
    layers.RandomBrightness(0.15),
    layers.RandomContrast(0.15),
    layers.RandomTranslation(0.1, 0.1),
], name="data_augmentation")

# Performance optimization
AUTOTUNE = tf.data.AUTOTUNE
train_ds = train_ds.cache().shuffle(2000).prefetch(AUTOTUNE)
val_ds = val_ds.cache().prefetch(AUTOTUNE)
test_ds = test_ds.cache().prefetch(AUTOTUNE)

print("✅ Augmentation pipeline ready (with shear/translate)")
print("✅ Dataset caching & prefetch enabled")


# ============================================================================
# CELL 8 — BUILD THE MODEL (EfficientNetB0 + Custom Head)
# ============================================================================

# Load EfficientNetB0 pretrained on ImageNet
base_model = EfficientNetB0(
    input_shape=(IMG_SIZE, IMG_SIZE, 3),
    include_top=False,
    weights="imagenet",
)
base_model.trainable = False  # Freeze ALL base layers for Phase 1

print(f"EfficientNetB0 loaded: {len(base_model.layers)} layers, "
      f"{base_model.count_params():,} params (all frozen)")

# Build the model:
#   Input → Augmentation → EfficientNet preprocessing → EfficientNetB0
#   → GAP → Dense(256) → Dropout(0.4) → Dense(14, softmax)
inputs = keras.Input(shape=(IMG_SIZE, IMG_SIZE, 3))
x = data_augmentation(inputs)
x = preprocess_input(x)                 # EfficientNet expects [0, 255] → scaled
x = base_model(x, training=False)
x = layers.GlobalAveragePooling2D()(x)
x = layers.Dense(256, activation="relu")(x)
x = layers.Dropout(0.4)(x)
outputs = layers.Dense(NUM_CLASSES, activation="softmax")(x)

model = keras.Model(inputs, outputs, name="species_classifier")

model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=PHASE1_LR),
    loss="categorical_crossentropy",
    metrics=["accuracy"],
)

model.summary()

trainable = sum(
    tf.keras.backend.count_params(w) for w in model.trainable_weights
)
total = model.count_params()
print(f"\nTotal params    : {total:,}")
print(f"Trainable params: {trainable:,}")
print(f"Frozen params   : {total - trainable:,}")


# ============================================================================
# CELL 9 — PHASE 1: TRAIN TOP LAYERS (BASE FROZEN)
# ============================================================================

print("=" * 60)
print("PHASE 1: Training custom head (EfficientNetB0 base FROZEN)")
print("=" * 60)

callbacks_phase1 = [
    EarlyStopping(
        monitor="val_loss",
        patience=3,
        restore_best_weights=True,
        verbose=1,
    ),
]

history_phase1 = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=PHASE1_EPOCHS,
    callbacks=callbacks_phase1,
)

print(f"\n✅ Phase 1 complete!")
print(f"   Train Accuracy : {history_phase1.history['accuracy'][-1]:.4f}")
print(f"   Val Accuracy   : {history_phase1.history['val_accuracy'][-1]:.4f}")


# ============================================================================
# CELL 10 — PHASE 2: FINE-TUNE LAST 50 LAYERS OF EfficientNetB0
# ============================================================================

print("=" * 60)
print("PHASE 2: Fine-tuning last 50 layers of EfficientNetB0")
print("=" * 60)

# Unfreeze the last 50 layers (high-level feature layers)
base_model.trainable = True
for layer in base_model.layers[:-50]:
    layer.trainable = False

# Re-compile with lower learning rate
model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=PHASE2_LR),
    loss="categorical_crossentropy",
    metrics=["accuracy"],
)

trainable = sum(
    tf.keras.backend.count_params(w) for w in model.trainable_weights
)
print(f"Trainable params after unfreeze: {trainable:,}")

callbacks_phase2 = [
    EarlyStopping(
        monitor="val_loss",
        patience=4,
        restore_best_weights=True,
        verbose=1,
    ),
    ReduceLROnPlateau(
        monitor="val_loss",
        factor=0.5,
        patience=2,
        min_lr=1e-7,
        verbose=1,
    ),
    ModelCheckpoint(
        "/kaggle/working/species_classifier_best.keras",
        monitor="val_accuracy",
        save_best_only=True,
        verbose=1,
    ),
]

history_phase2 = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=PHASE2_EPOCHS,
    callbacks=callbacks_phase2,
)

print(f"\n✅ Phase 2 complete!")
print(f"   Train Accuracy : {history_phase2.history['accuracy'][-1]:.4f}")
print(f"   Val Accuracy   : {history_phase2.history['val_accuracy'][-1]:.4f}")


# ============================================================================
# CELL 11 — TRAINING HISTORY PLOTS
# ============================================================================

# Combine Phase 1 + Phase 2 histories
acc = history_phase1.history["accuracy"] + history_phase2.history["accuracy"]
val_acc = (
    history_phase1.history["val_accuracy"]
    + history_phase2.history["val_accuracy"]
)
loss = history_phase1.history["loss"] + history_phase2.history["loss"]
val_loss = (
    history_phase1.history["val_loss"] + history_phase2.history["val_loss"]
)

phase1_end = len(history_phase1.history["accuracy"])

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))

# Accuracy
ax1.plot(acc, label="Train Accuracy", linewidth=2)
ax1.plot(val_acc, label="Val Accuracy", linewidth=2)
ax1.axvline(
    x=phase1_end - 0.5, color="gray", linestyle="--", label="Fine-tune start"
)
ax1.set_title("Model Accuracy", fontsize=14, fontweight="bold")
ax1.set_xlabel("Epoch")
ax1.set_ylabel("Accuracy")
ax1.legend()
ax1.grid(True, alpha=0.3)

# Loss
ax2.plot(loss, label="Train Loss", linewidth=2)
ax2.plot(val_loss, label="Val Loss", linewidth=2)
ax2.axvline(
    x=phase1_end - 0.5, color="gray", linestyle="--", label="Fine-tune start"
)
ax2.set_title("Model Loss", fontsize=14, fontweight="bold")
ax2.set_xlabel("Epoch")
ax2.set_ylabel("Loss")
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(
    "/kaggle/working/gate2_training_history.png", dpi=150, bbox_inches="tight"
)
plt.show()


# ============================================================================
# CELL 12 — EVALUATE ON HELD-OUT TEST SET
# ============================================================================

print("=" * 60)
print("EVALUATING ON HELD-OUT TEST SET")
print("=" * 60)

# Load the best checkpoint
best_model = keras.models.load_model(
    "/kaggle/working/species_classifier_best.keras"
)

# Overall test metrics
test_loss, test_acc = best_model.evaluate(test_ds, verbose=1)
print(f"\n🎯 Test Accuracy : {test_acc:.4f} ({test_acc * 100:.1f}%)")
print(f"📉 Test Loss     : {test_loss:.4f}")

# Collect all predictions
y_true = []
y_pred_probs = []

for images, labels in test_ds:
    preds = best_model.predict(images, verbose=0)
    y_true.extend(np.argmax(labels.numpy(), axis=1))
    y_pred_probs.extend(preds)

y_true = np.array(y_true)
y_pred_probs = np.array(y_pred_probs)
y_pred = np.argmax(y_pred_probs, axis=1)


# ============================================================================
# CELL 13 — CLASSIFICATION REPORT & CONFUSION MATRIX
# ============================================================================

# Per-class precision, recall, F1
print("\n📊 Classification Report:")
print(classification_report(y_true, y_pred, target_names=class_names))

# Confusion matrix heatmap
cm = confusion_matrix(y_true, y_pred)
plt.figure(figsize=(14, 11))
sns.heatmap(
    cm,
    annot=True,
    fmt="d",
    cmap="YlGn",
    xticklabels=class_names,
    yticklabels=class_names,
)
plt.title(
    "Confusion Matrix — Species Classifier (Gate 2)",
    fontsize=14,
    fontweight="bold",
)
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.xticks(rotation=45, ha="right")
plt.yticks(rotation=0)
plt.tight_layout()
plt.savefig(
    "/kaggle/working/gate2_confusion_matrix.png", dpi=150, bbox_inches="tight"
)
plt.show()

# Per-class accuracy
print("\nPer-class accuracy:")
for i, name in enumerate(class_names):
    mask = y_true == i
    if mask.sum() > 0:
        class_acc = (y_pred[mask] == i).mean()
        print(f"   {name:12s}: {class_acc:.4f} ({class_acc * 100:.1f}%)  "
              f"[{mask.sum()} samples]")


# ============================================================================
# CELL 14 — VISUALIZE SAMPLE PREDICTIONS
# ============================================================================

plt.figure(figsize=(18, 12))
sample_count = 0

for images, labels in test_ds.take(2):
    preds = best_model.predict(images, verbose=0)
    for i in range(min(14 - sample_count, len(images))):
        ax = plt.subplot(2, 7, sample_count + 1)
        plt.imshow(images[i].numpy().astype("uint8"))

        true_idx = np.argmax(labels[i].numpy())
        pred_idx = np.argmax(preds[i])
        confidence = preds[i][pred_idx]

        true_label = class_names[true_idx]
        pred_label = class_names[pred_idx]

        color = "green" if true_label == pred_label else "red"
        plt.title(
            f"True: {true_label}\nPred: {pred_label}\n({confidence:.0%})",
            fontsize=8,
            color=color,
        )
        plt.axis("off")
        sample_count += 1
        if sample_count >= 14:
            break
    if sample_count >= 14:
        break

plt.suptitle(
    "Sample Predictions (Green = Correct, Red = Wrong)", fontsize=13
)
plt.tight_layout()
plt.savefig(
    "/kaggle/working/gate2_sample_predictions.png", dpi=150, bbox_inches="tight"
)
plt.show()


# ============================================================================
# CELL 15 — TOP CONFUSED SPECIES PAIRS
# ============================================================================

# Find which species pairs the model confuses most often
print("\n🔍 Most confused species pairs:")
cm_normalized = cm.astype(float)
np.fill_diagonal(cm_normalized, 0)  # Ignore correct predictions

# Find top 5 off-diagonal cells
flat_indices = np.argsort(cm_normalized.ravel())[::-1][:5]
for idx in flat_indices:
    row, col = divmod(idx, NUM_CLASSES)
    count = int(cm[row, col])
    if count == 0:
        break
    print(f"   {class_names[row]:12s} → predicted as {class_names[col]:12s}  "
          f"({count} times)")


# ============================================================================
# CELL 16 — SAVE FINAL MODEL + LABELS
# ============================================================================

# Save the best model
best_model.save("/kaggle/working/species_classifier.keras")

# Save species labels JSON (needed by the backend)
species_labels = {str(i): name for i, name in enumerate(class_names)}
with open("/kaggle/working/species_labels.json", "w") as f:
    json.dump(species_labels, f, indent=2)

print("\n📄 species_labels.json:")
print(json.dumps(species_labels, indent=2))

# Also save a TFLite version
converter = tf.lite.TFLiteConverter.from_keras_model(best_model)
tflite_model = converter.convert()
with open("/kaggle/working/species_classifier.tflite", "wb") as f:
    f.write(tflite_model)

# File sizes
keras_size = os.path.getsize("/kaggle/working/species_classifier.keras") / (1024 * 1024)
tflite_size = os.path.getsize("/kaggle/working/species_classifier.tflite") / (1024 * 1024)

print(f"\n{'=' * 60}")
print(f"✅ GATE 2 TRAINING COMPLETE!")
print(f"{'=' * 60}")
print(f"   species_classifier.keras  → {keras_size:.1f} MB")
print(f"   species_classifier.tflite → {tflite_size:.1f} MB")
print(f"   species_labels.json       → 14 classes")
print(f"   Test Accuracy             → {test_acc * 100:.1f}%")
print(f"\n📥 Download from: Kaggle Output tab (right sidebar)")
print(f"   Save to: F:\\ML_PROJECT\\ml\\models\\species_classifier.keras")
print(f"            F:\\ML_PROJECT\\ml\\models\\species_labels.json")
print(f"{'=' * 60}")


# ============================================================================
# CELL 17 — QUICK INFERENCE DEMO
# ============================================================================

def predict_species(model, image_array, class_names):
    """
    Predict which plant species a leaf image belongs to.

    Args:
        model: The loaded Keras model
        image_array: numpy array of shape (H, W, 3) with values [0, 255]
        class_names: list of species names

    Returns:
        tuple: (species_name, confidence, top3)
    """
    img = tf.image.resize(image_array, (IMG_SIZE, IMG_SIZE))
    img = tf.expand_dims(img, axis=0)
    # NOTE: Do NOT call preprocess_input — it's built into the model.

    preds = model.predict(img, verbose=0)[0]

    top3_indices = np.argsort(preds)[::-1][:3]
    top3 = [
        (class_names[idx], float(preds[idx]))
        for idx in top3_indices
    ]

    return top3[0][0], top3[0][1], top3


# Demo on test images
print("\n🔍 Quick inference demo:")
for images, labels in test_ds.take(1):
    for i in range(5):
        true_idx = np.argmax(labels[i].numpy())
        true_class = class_names[true_idx]
        pred_class, confidence, top3 = predict_species(
            best_model, images[i].numpy(), class_names
        )
        match = "✅" if pred_class == true_class else "❌"
        top3_str = " | ".join([f"{n}: {c:.1%}" for n, c in top3])
        print(f"   {match} True: {true_class:12s} → {top3_str}")
