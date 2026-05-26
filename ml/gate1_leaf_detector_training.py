"""
=============================================================================
🌿 GATE 1 — LEAF DETECTOR (Binary Classifier)
=============================================================================
Plant Disease AI — 3-Gate Pipeline
Goal: Classify images as "leaf" or "non_leaf" to reject garbage inputs
       before they reach the disease classifier.

Architecture : MobileNetV2 (ImageNet pretrained) + custom top layers
Dataset      : Leaf vs Non-Leaf Images (Kaggle)
Training     : Two-phase transfer learning (freeze → fine-tune)
Expected Acc : 95-98%
Output       : leaf_detector.keras (~10 MB)

HOW TO RUN ON KAGGLE:
1. Create a new Kaggle Notebook
2. Add Input → search "Leaf vs Non-Leaf Images" by Robiul Hasan Jisan
3. Enable GPU: Settings → Accelerator → GPU T4 x2
4. Copy ALL of this file into a single code cell (or split at the
   "# ====" markers into separate cells)
5. Run all cells

Refined from contributor notebook: leaf-vs-non-leaf-detection.ipynb
=============================================================================
"""


# ============================================================================
# CELL 1 — IMPORTS & CONFIGURATION
# ============================================================================

import os
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
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
PHASE1_EPOCHS = 3
PHASE1_LR = 1e-4

# Phase 2: fine-tune last 30 layers of MobileNetV2
PHASE2_EPOCHS = 15
PHASE2_LR = 1e-5

print(f"TensorFlow : {tf.__version__}")
print(f"GPU        : {tf.config.list_physical_devices('GPU')}")


# ============================================================================
# CELL 2 — FIND & EXPLORE THE DATASET
# ============================================================================

def find_dataset_dir(search_root="/kaggle/input"):
    """
    Recursively search for the directory that contains BOTH
    'leaf' and 'non_leaf' as immediate subdirectories.
    """
    for dirpath, dirnames, _ in os.walk(search_root):
        if "leaf" in dirnames and "non_leaf" in dirnames:
            return dirpath
    return None

DATA_DIR = find_dataset_dir()

if DATA_DIR is None:
    raise FileNotFoundError(
        "Could not find a directory with 'leaf/' and 'non_leaf/' subdirs "
        "under /kaggle/input/. Check your dataset input."
    )

print(f"✅ Dataset found: {DATA_DIR}")

# Count images per class
for cls in sorted(os.listdir(DATA_DIR)):
    cls_path = os.path.join(DATA_DIR, cls)
    if os.path.isdir(cls_path):
        count = len([
            f for f in os.listdir(cls_path)
            if not f.startswith(".") and f.lower().endswith(
                (".jpg", ".jpeg", ".png", ".bmp", ".webp")
            )
        ])
        print(f"  {cls}: {count:,} images")


# ============================================================================
# CELL 3 — CLEAN DATASET (convert .webp → .jpg, remove corrupt files)
# ============================================================================

# TensorFlow's image_dataset_from_directory CANNOT decode .webp files.
# The dataset contains .webp images, so we need to convert them.
# /kaggle/input/ is read-only, so we copy to a writable directory.

import shutil
from PIL import Image

CLEAN_DIR = "/kaggle/working/dataset_clean"
SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif"}

if os.path.exists(CLEAN_DIR):
    shutil.rmtree(CLEAN_DIR)

converted = 0
skipped = 0
copied = 0

for cls in sorted(os.listdir(DATA_DIR)):
    src_cls = os.path.join(DATA_DIR, cls)
    if not os.path.isdir(src_cls):
        continue

    dst_cls = os.path.join(CLEAN_DIR, cls)
    os.makedirs(dst_cls, exist_ok=True)

    for fname in os.listdir(src_cls):
        src_file = os.path.join(src_cls, fname)
        ext = os.path.splitext(fname)[1].lower()

        if ext in SUPPORTED_EXTS:
            # Verify it's actually a valid image before copying
            try:
                with Image.open(src_file) as img:
                    img.verify()
                shutil.copy2(src_file, os.path.join(dst_cls, fname))
                copied += 1
            except Exception:
                skipped += 1

        elif ext == ".webp":
            # Convert .webp → .jpg using PIL
            try:
                with Image.open(src_file) as img:
                    rgb_img = img.convert("RGB")
                    new_name = os.path.splitext(fname)[0] + ".jpg"
                    rgb_img.save(os.path.join(dst_cls, new_name), "JPEG", quality=95)
                    converted += 1
            except Exception:
                skipped += 1
        else:
            skipped += 1

print(f"✅ Dataset cleaned → {CLEAN_DIR}")
print(f"   Copied     : {copied:,} files")
print(f"   Converted  : {converted:,} (.webp → .jpg)")
print(f"   Skipped    : {skipped:,} (corrupt/unsupported)")

# Update DATA_DIR to point to the clean copy
DATA_DIR = CLEAN_DIR

for cls in sorted(os.listdir(DATA_DIR)):
    cls_path = os.path.join(DATA_DIR, cls)
    if os.path.isdir(cls_path):
        print(f"   {cls}: {len(os.listdir(cls_path)):,} images")


# ============================================================================
# CELL 4 — LOAD DATASET (TRAIN / VAL / TEST SPLIT)
# ============================================================================

# Load 80% as training set
train_ds = keras.utils.image_dataset_from_directory(
    DATA_DIR,
    validation_split=0.2,
    subset="training",
    seed=SEED,
    image_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    label_mode="binary",
)

# Load 20% as val+test, then split in half
val_test_ds = keras.utils.image_dataset_from_directory(
    DATA_DIR,
    validation_split=0.2,
    subset="validation",
    seed=SEED,
    image_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    label_mode="binary",
)

# Split val_test into validation (50%) and test (50%)
val_batches = int(0.5 * len(val_test_ds))
val_ds = val_test_ds.take(val_batches)
test_ds = val_test_ds.skip(val_batches)

class_names = train_ds.class_names
print(f"\nClasses      : {class_names}")
print(f"Train batches: {len(train_ds)}")
print(f"Val batches  : {len(val_ds)}")
print(f"Test batches : {len(test_ds)}")


# ============================================================================
# CELL 4 — VISUALIZE SAMPLE IMAGES
# ============================================================================

plt.figure(figsize=(14, 6))
for images, labels in train_ds.take(1):
    for i in range(min(12, len(images))):
        ax = plt.subplot(2, 6, i + 1)
        plt.imshow(images[i].numpy().astype("uint8"))
        label = class_names[int(labels[i].numpy())]
        plt.title(label, fontsize=10)
        plt.axis("off")
plt.suptitle("Sample Training Images (raw, before augmentation)", fontsize=14)
plt.tight_layout()
plt.show()


# ============================================================================
# CELL 5 — DATA AUGMENTATION & PERFORMANCE OPTIMIZATION
# ============================================================================

# Data augmentation layer — applied ONLY during training
# This prevents overfitting by showing slightly different images each epoch
data_augmentation = keras.Sequential([
    layers.RandomFlip("horizontal"),
    layers.RandomRotation(0.15),          # ±15% rotation
    layers.RandomZoom(0.1),               # ±10% zoom
    layers.RandomBrightness(0.1),         # ±10% brightness
    layers.RandomContrast(0.1),           # ±10% contrast
], name="data_augmentation")

# Performance: cache in memory + prefetch next batch while GPU trains
AUTOTUNE = tf.data.AUTOTUNE
train_ds = train_ds.cache().shuffle(1000).prefetch(AUTOTUNE)
val_ds = val_ds.cache().prefetch(AUTOTUNE)
test_ds = test_ds.cache().prefetch(AUTOTUNE)

print("✅ Augmentation pipeline ready")
print("✅ Dataset caching & prefetch enabled")


# ============================================================================
# CELL 6 — BUILD THE MODEL (MobileNetV2 + Custom Head)
# ============================================================================

# Load MobileNetV2 pretrained on ImageNet (1.4M images, 1000 classes)
# include_top=False removes the original 1000-class classification head
base_model = MobileNetV2(
    input_shape=(IMG_SIZE, IMG_SIZE, 3),
    include_top=False,
    weights="imagenet",
)
base_model.trainable = False  # Freeze ALL base layers for Phase 1

print(f"MobileNetV2 loaded: {len(base_model.layers)} layers, "
      f"{base_model.count_params():,} params (all frozen)")

# Build the full model pipeline:
#   Input → Augmentation → MobileNetV2 preprocessing → MobileNetV2 → GAP → Dense → Output
inputs = keras.Input(shape=(IMG_SIZE, IMG_SIZE, 3))
x = data_augmentation(inputs)           # Random augmentation (train only)
x = preprocess_input(x)                 # MobileNetV2 expects [-1, 1] range
x = base_model(x, training=False)       # Feature extraction (frozen)
x = layers.GlobalAveragePooling2D()(x)  # Compress spatial features
x = layers.Dense(128, activation="relu")(x)
x = layers.Dropout(0.3)(x)             # Regularization
outputs = layers.Dense(1, activation="sigmoid")(x)  # Binary output

model = keras.Model(inputs, outputs, name="leaf_detector")

model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=PHASE1_LR),
    loss="binary_crossentropy",
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
# CELL 7 — PHASE 1: TRAIN TOP LAYERS (BASE FROZEN)
# ============================================================================

print("=" * 60)
print("PHASE 1: Training custom head (MobileNetV2 base FROZEN)")
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
# CELL 8 — PHASE 2: FINE-TUNE LAST 30 LAYERS OF MobileNetV2
# ============================================================================

print("=" * 60)
print("PHASE 2: Fine-tuning last 30 layers of MobileNetV2")
print("=" * 60)

# Unfreeze the last 30 layers (high-level feature layers)
base_model.trainable = True
for layer in base_model.layers[:-30]:
    layer.trainable = False

# Re-compile with a LOWER learning rate (prevents catastrophic forgetting)
model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=PHASE2_LR),
    loss="binary_crossentropy",
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
        "/kaggle/working/leaf_detector_best.keras",
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
# CELL 9 — TRAINING HISTORY PLOTS
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
    "/kaggle/working/gate1_training_history.png", dpi=150, bbox_inches="tight"
)
plt.show()


# ============================================================================
# CELL 10 — EVALUATE ON HELD-OUT TEST SET
# ============================================================================

print("=" * 60)
print("EVALUATING ON HELD-OUT TEST SET")
print("=" * 60)

# Load the best checkpoint from Phase 2
best_model = keras.models.load_model(
    "/kaggle/working/leaf_detector_best.keras"
)

# Overall test metrics
test_loss, test_acc = best_model.evaluate(test_ds, verbose=1)
print(f"\n🎯 Test Accuracy : {test_acc:.4f} ({test_acc * 100:.1f}%)")
print(f"📉 Test Loss     : {test_loss:.4f}")

# Collect all predictions for confusion matrix & classification report
y_true = []
y_pred_probs = []

for images, labels in test_ds:
    preds = best_model.predict(images, verbose=0)
    y_true.extend(labels.numpy().flatten())
    y_pred_probs.extend(preds.flatten())

y_true = np.array(y_true)
y_pred_probs = np.array(y_pred_probs)
y_pred = (y_pred_probs > 0.5).astype(int)


# ============================================================================
# CELL 11 — CLASSIFICATION REPORT & CONFUSION MATRIX
# ============================================================================

# Per-class precision, recall, F1
print("\n📊 Classification Report:")
print(classification_report(y_true, y_pred, target_names=class_names))

# Confusion matrix heatmap
cm = confusion_matrix(y_true, y_pred)
plt.figure(figsize=(7, 6))
sns.heatmap(
    cm,
    annot=True,
    fmt="d",
    cmap="Greens",
    xticklabels=class_names,
    yticklabels=class_names,
)
plt.title("Confusion Matrix — Leaf Detector (Gate 1)", fontsize=14, fontweight="bold")
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.tight_layout()
plt.savefig(
    "/kaggle/working/gate1_confusion_matrix.png", dpi=150, bbox_inches="tight"
)
plt.show()

# Print per-class accuracy
for i, name in enumerate(class_names):
    mask = y_true == i
    class_acc = (y_pred[mask] == i).mean()
    print(f"  {name:10s} accuracy: {class_acc:.4f} ({class_acc * 100:.1f}%)")


# ============================================================================
# CELL 12 — VISUALIZE SAMPLE PREDICTIONS
# ============================================================================

plt.figure(figsize=(16, 10))
sample_count = 0

for images, labels in test_ds.take(2):
    preds = best_model.predict(images, verbose=0)
    for i in range(min(12 - sample_count, len(images))):
        ax = plt.subplot(3, 4, sample_count + 1)
        plt.imshow(images[i].numpy().astype("uint8"))

        true_label = class_names[int(labels[i].numpy())]
        pred_prob = preds[i][0]
        pred_label = class_names[int(pred_prob > 0.5)]
        confidence = pred_prob if pred_prob > 0.5 else 1 - pred_prob

        color = "green" if true_label == pred_label else "red"
        plt.title(
            f"True: {true_label}\nPred: {pred_label} ({confidence:.0%})",
            fontsize=9,
            color=color,
        )
        plt.axis("off")
        sample_count += 1
        if sample_count >= 12:
            break
    if sample_count >= 12:
        break

plt.suptitle(
    "Sample Predictions (Green = Correct, Red = Wrong)", fontsize=13
)
plt.tight_layout()
plt.savefig(
    "/kaggle/working/gate1_sample_predictions.png", dpi=150, bbox_inches="tight"
)
plt.show()


# ============================================================================
# CELL 13 — CONFIDENCE DISTRIBUTION ANALYSIS
# ============================================================================

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# Correct predictions
correct_mask = y_pred == y_true
correct_confs = np.where(y_pred_probs > 0.5, y_pred_probs, 1 - y_pred_probs)[
    correct_mask
]
wrong_confs = np.where(y_pred_probs > 0.5, y_pred_probs, 1 - y_pred_probs)[
    ~correct_mask
]

ax1.hist(correct_confs, bins=30, color="#40916C", alpha=0.8, edgecolor="white")
ax1.set_title("Confidence on CORRECT Predictions", fontweight="bold")
ax1.set_xlabel("Confidence")
ax1.set_ylabel("Count")
ax1.axvline(x=0.7, color="red", linestyle="--", label="Gate threshold (0.7)")
ax1.legend()

if len(wrong_confs) > 0:
    ax2.hist(wrong_confs, bins=30, color="#E63946", alpha=0.8, edgecolor="white")
else:
    ax2.text(0.5, 0.5, "No wrong predictions! 🎉",
             ha="center", va="center", fontsize=14, transform=ax2.transAxes)
ax2.set_title("Confidence on WRONG Predictions", fontweight="bold")
ax2.set_xlabel("Confidence")
ax2.set_ylabel("Count")

plt.tight_layout()
plt.savefig(
    "/kaggle/working/gate1_confidence_analysis.png", dpi=150, bbox_inches="tight"
)
plt.show()

# Gate threshold analysis
print("\n📊 Gate Threshold Analysis (using 0.70 as gate threshold):")
gate_threshold = 0.70
high_conf_mask = np.where(y_pred_probs > 0.5, y_pred_probs, 1 - y_pred_probs) >= gate_threshold
print(f"   Images above threshold : {high_conf_mask.sum()} / {len(y_true)} "
      f"({high_conf_mask.mean() * 100:.1f}%)")
print(f"   Accuracy on those      : {(y_pred[high_conf_mask] == y_true[high_conf_mask]).mean():.4f}")
low_conf = ~high_conf_mask
if low_conf.sum() > 0:
    print(f"   Images BELOW threshold : {low_conf.sum()} (would be marked 'uncertain')")
else:
    print(f"   Images BELOW threshold : 0 (all confident!)")


# ============================================================================
# CELL 14 — SAVE FINAL MODEL
# ============================================================================

# Save the best model as the final output
best_model.save("/kaggle/working/leaf_detector.keras")

# Also save a TFLite version (smaller, for potential mobile deployment)
converter = tf.lite.TFLiteConverter.from_keras_model(best_model)
tflite_model = converter.convert()
with open("/kaggle/working/leaf_detector.tflite", "wb") as f:
    f.write(tflite_model)

# File sizes
keras_size = os.path.getsize("/kaggle/working/leaf_detector.keras") / (1024 * 1024)
tflite_size = os.path.getsize("/kaggle/working/leaf_detector.tflite") / (1024 * 1024)

print(f"\n{'=' * 60}")
print(f"✅ GATE 1 TRAINING COMPLETE!")
print(f"{'=' * 60}")
print(f"   leaf_detector.keras  → {keras_size:.1f} MB")
print(f"   leaf_detector.tflite → {tflite_size:.1f} MB")
print(f"   Test Accuracy        → {test_acc * 100:.1f}%")
print(f"\n📥 Download from: Kaggle Output tab (right sidebar)")
print(f"   Save to: F:\\ML_PROJECT\\ml\\models\\leaf_detector.keras")
print(f"{'=' * 60}")


# ============================================================================
# CELL 15 — QUICK INFERENCE DEMO
# ============================================================================

def predict_leaf(model, image_array):
    """
    Predict whether an image is a leaf or not.

    Args:
        model: The loaded Keras model
        image_array: numpy array of shape (H, W, 3) with values [0, 255]

    Returns:
        tuple: (class_name, confidence)
            class_name: 'leaf' or 'non_leaf'
            confidence: float 0-1
    """
    # Resize to model input size
    img = tf.image.resize(image_array, (IMG_SIZE, IMG_SIZE))
    img = tf.expand_dims(img, axis=0)  # Add batch dimension
    # NOTE: Do NOT call preprocess_input here — it's already
    # built into the model graph (see model definition).

    pred = model.predict(img, verbose=0)[0][0]

    if pred > 0.5:
        return class_names[1], float(pred)
    else:
        return class_names[0], float(1 - pred)


# Demo on a few test images
print("\n🔍 Quick inference demo:")
for images, labels in test_ds.take(1):
    for i in range(5):
        pred_class, confidence = predict_leaf(best_model, images[i].numpy())
        true_class = class_names[int(labels[i].numpy().item())]
        match = "✅" if pred_class == true_class else "❌"
        print(f"   {match} True: {true_class:8s} | Pred: {pred_class:8s} | "
              f"Confidence: {confidence:.1%}")

