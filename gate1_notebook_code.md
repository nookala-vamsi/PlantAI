# 🌿 Gate 1 — Leaf Detector (Kaggle Notebook Code)

> **Dataset:** [Leaf vs Non-Leaf Images](https://www.kaggle.com/datasets/robiulhasanjisan/leaf-vs-non-leaf-images)
> **Setup:** Create a new Kaggle Notebook → Add the dataset as Input → Enable GPU (Settings → Accelerator → GPU T4 x2)

Copy each cell below into separate cells in your Kaggle notebook.

---

## Cell 1 — Imports & Config

```python
import os
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns

# Config
IMG_SIZE = 224
BATCH_SIZE = 32
SEED = 42

print(f"TensorFlow: {tf.__version__}")
print(f"GPU Available: {tf.config.list_physical_devices('GPU')}")
```

---

## Cell 2 — Find & Explore Dataset

```python
# Find the dataset path
BASE_PATH = '/kaggle/input/leaf-vs-non-leaf-images'

# List contents to find the actual structure
for root, dirs, files in os.walk(BASE_PATH):
    level = root.replace(BASE_PATH, '').count(os.sep)
    indent = ' ' * 2 * level
    print(f'{indent}{os.path.basename(root)}/')
    if level < 2:  # Only show 2 levels deep
        subindent = ' ' * 2 * (level + 1)
        for f in files[:3]:
            print(f'{subindent}{f}')
        if len(files) > 3:
            print(f'{subindent}... and {len(files) - 3} more files')
```

---

## Cell 3 — Set Dataset Path

```python
# Adjust DATA_DIR based on Cell 2 output
# It should point to the folder that CONTAINS 'leaf/' and 'non_leaf/' subfolders
# Common possibilities:
#   /kaggle/input/leaf-vs-non-leaf-images/
#   /kaggle/input/leaf-vs-non-leaf-images/leaf-vs-non-leaf-images/
#   /kaggle/input/leaf-vs-non-leaf-images/dataset/

# Try to auto-detect
DATA_DIR = BASE_PATH
for item in os.listdir(BASE_PATH):
    item_path = os.path.join(BASE_PATH, item)
    if os.path.isdir(item_path):
        contents = os.listdir(item_path)
        # Check if this subdirectory contains 'leaf' and 'non_leaf'
        if 'leaf' in contents and 'non_leaf' in contents:
            DATA_DIR = item_path
            break
        # Also check for variant names
        if any('leaf' in c.lower() for c in contents):
            DATA_DIR = item_path
            break

print(f"Using DATA_DIR: {DATA_DIR}")
print(f"Contents: {os.listdir(DATA_DIR)}")

# Count images per class
for cls in sorted(os.listdir(DATA_DIR)):
    cls_path = os.path.join(DATA_DIR, cls)
    if os.path.isdir(cls_path):
        count = len([f for f in os.listdir(cls_path) if not f.startswith('.')])
        print(f"  {cls}: {count} images")
```

---

## Cell 4 — Load Dataset (Train/Val/Test Split)

```python
# Load training set (80%)
train_ds = keras.utils.image_dataset_from_directory(
    DATA_DIR,
    validation_split=0.2,
    subset='training',
    seed=SEED,
    image_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    label_mode='binary',  # Binary classification: 0 or 1
)

# Load validation set (20% → split further into val + test)
val_test_ds = keras.utils.image_dataset_from_directory(
    DATA_DIR,
    validation_split=0.2,
    subset='validation',
    seed=SEED,
    image_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    label_mode='binary',
)

# Split val_test into val (50%) and test (50%)
val_batches = int(0.5 * len(val_test_ds))
val_ds = val_test_ds.take(val_batches)
test_ds = val_test_ds.skip(val_batches)

# Class names
class_names = train_ds.class_names
print(f"Classes: {class_names}")
print(f"Train batches: {len(train_ds)}")
print(f"Val batches:   {len(val_ds)}")
print(f"Test batches:  {len(test_ds)}")
```

---

## Cell 5 — Visualize Samples

```python
plt.figure(figsize=(12, 6))
for images, labels in train_ds.take(1):
    for i in range(12):
        ax = plt.subplot(2, 6, i + 1)
        plt.imshow(images[i].numpy().astype('uint8'))
        label = class_names[int(labels[i].numpy())]
        plt.title(label, fontsize=10)
        plt.axis('off')
plt.suptitle('Sample Training Images', fontsize=14)
plt.tight_layout()
plt.show()
```

---

## Cell 6 — Data Augmentation & Prefetch

```python
# Data augmentation layer
data_augmentation = keras.Sequential([
    layers.RandomFlip('horizontal'),
    layers.RandomRotation(0.15),         # ±15% rotation
    layers.RandomZoom(0.1),              # ±10% zoom
    layers.RandomBrightness(0.1),        # ±10% brightness
    layers.RandomContrast(0.1),          # ±10% contrast
], name='data_augmentation')

# Performance optimization
AUTOTUNE = tf.data.AUTOTUNE
train_ds = train_ds.cache().shuffle(1000).prefetch(AUTOTUNE)
val_ds = val_ds.cache().prefetch(AUTOTUNE)
test_ds = test_ds.cache().prefetch(AUTOTUNE)

print("✅ Augmentation pipeline and prefetch ready")
```

---

## Cell 7 — Build Model

```python
# MobileNetV2 base (frozen)
base_model = MobileNetV2(
    input_shape=(IMG_SIZE, IMG_SIZE, 3),
    include_top=False,
    weights='imagenet',
)
base_model.trainable = False  # Freeze all layers initially

# Build the full model
inputs = keras.Input(shape=(IMG_SIZE, IMG_SIZE, 3))
x = data_augmentation(inputs)                          # Augmentation
x = keras.applications.mobilenet_v2.preprocess_input(x)  # MobileNetV2 preprocessing
x = base_model(x, training=False)                      # Feature extraction
x = layers.GlobalAveragePooling2D()(x)                 # Pool features
x = layers.Dense(128, activation='relu')(x)            # Dense layer
x = layers.Dropout(0.3)(x)                             # Regularization
outputs = layers.Dense(1, activation='sigmoid')(x)     # Binary output

model = keras.Model(inputs, outputs)

model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=1e-4),
    loss='binary_crossentropy',
    metrics=['accuracy'],
)

model.summary()
print(f"\nTotal params: {model.count_params():,}")
print(f"Trainable params: {sum(tf.keras.backend.count_params(w) for w in model.trainable_weights):,}")
```

---

## Cell 8 — Phase 1: Train Top Layers (Base Frozen)

```python
print("=" * 50)
print("PHASE 1: Training top layers (base frozen)")
print("=" * 50)

callbacks_phase1 = [
    EarlyStopping(monitor='val_loss', patience=3, restore_best_weights=True, verbose=1),
]

history_phase1 = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=3,
    callbacks=callbacks_phase1,
)

print(f"\n✅ Phase 1 complete!")
print(f"   Train Acc: {history_phase1.history['accuracy'][-1]:.4f}")
print(f"   Val Acc:   {history_phase1.history['val_accuracy'][-1]:.4f}")
```

---

## Cell 9 — Phase 2: Fine-Tune (Unfreeze Last 30 Layers)

```python
print("=" * 50)
print("PHASE 2: Fine-tuning last 30 layers")
print("=" * 50)

# Unfreeze last 30 layers of MobileNetV2
base_model.trainable = True
for layer in base_model.layers[:-30]:
    layer.trainable = False

# Re-compile with lower learning rate
model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=1e-5),  # 10x lower LR
    loss='binary_crossentropy',
    metrics=['accuracy'],
)

trainable_count = sum(tf.keras.backend.count_params(w) for w in model.trainable_weights)
print(f"Trainable params after unfreeze: {trainable_count:,}")

callbacks_phase2 = [
    EarlyStopping(
        monitor='val_loss',
        patience=4,
        restore_best_weights=True,
        verbose=1,
    ),
    ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=2,
        min_lr=1e-7,
        verbose=1,
    ),
    ModelCheckpoint(
        '/kaggle/working/leaf_detector_best.keras',
        monitor='val_accuracy',
        save_best_only=True,
        verbose=1,
    ),
]

history_phase2 = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=15,
    callbacks=callbacks_phase2,
)

print(f"\n✅ Phase 2 complete!")
print(f"   Train Acc: {history_phase2.history['accuracy'][-1]:.4f}")
print(f"   Val Acc:   {history_phase2.history['val_accuracy'][-1]:.4f}")
```

---

## Cell 10 — Training History Plots

```python
# Combine histories
acc = history_phase1.history['accuracy'] + history_phase2.history['accuracy']
val_acc = history_phase1.history['val_accuracy'] + history_phase2.history['val_accuracy']
loss = history_phase1.history['loss'] + history_phase2.history['loss']
val_loss = history_phase1.history['val_loss'] + history_phase2.history['val_loss']

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# Accuracy plot
ax1.plot(acc, label='Train Accuracy', linewidth=2)
ax1.plot(val_acc, label='Val Accuracy', linewidth=2)
ax1.axvline(x=len(history_phase1.history['accuracy']) - 0.5,
            color='gray', linestyle='--', label='Fine-tune start')
ax1.set_title('Model Accuracy', fontsize=14, fontweight='bold')
ax1.set_xlabel('Epoch')
ax1.set_ylabel('Accuracy')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Loss plot
ax2.plot(loss, label='Train Loss', linewidth=2)
ax2.plot(val_loss, label='Val Loss', linewidth=2)
ax2.axvline(x=len(history_phase1.history['loss']) - 0.5,
            color='gray', linestyle='--', label='Fine-tune start')
ax2.set_title('Model Loss', fontsize=14, fontweight='bold')
ax2.set_xlabel('Epoch')
ax2.set_ylabel('Loss')
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('/kaggle/working/gate1_training_history.png', dpi=150, bbox_inches='tight')
plt.show()
```

---

## Cell 11 — Evaluate on Test Set

```python
print("=" * 50)
print("EVALUATING ON TEST SET")
print("=" * 50)

# Load best model
best_model = keras.models.load_model('/kaggle/working/leaf_detector_best.keras')

# Evaluate
test_loss, test_acc = best_model.evaluate(test_ds, verbose=1)
print(f"\n🎯 Test Accuracy: {test_acc:.4f}")
print(f"📉 Test Loss:     {test_loss:.4f}")

# Get predictions for confusion matrix
y_true = []
y_pred = []
for images, labels in test_ds:
    preds = best_model.predict(images, verbose=0)
    y_true.extend(labels.numpy().flatten())
    y_pred.extend((preds.flatten() > 0.5).astype(int))

y_true = np.array(y_true)
y_pred = np.array(y_pred)
```

---

## Cell 12 — Confusion Matrix & Classification Report

```python
# Classification report
print("\n📊 Classification Report:")
print(classification_report(y_true, y_pred, target_names=class_names))

# Confusion matrix
cm = confusion_matrix(y_true, y_pred)
plt.figure(figsize=(7, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Greens',
            xticklabels=class_names, yticklabels=class_names)
plt.title('Confusion Matrix — Leaf Detector', fontsize=14, fontweight='bold')
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.tight_layout()
plt.savefig('/kaggle/working/gate1_confusion_matrix.png', dpi=150, bbox_inches='tight')
plt.show()
```

---

## Cell 13 — Sample Predictions

```python
plt.figure(figsize=(14, 8))
for images, labels in test_ds.take(1):
    preds = best_model.predict(images, verbose=0)
    for i in range(min(12, len(images))):
        ax = plt.subplot(2, 6, i + 1)
        plt.imshow(images[i].numpy().astype('uint8'))

        true_label = class_names[int(labels[i].numpy())]
        pred_prob = preds[i][0]
        pred_label = class_names[int(pred_prob > 0.5)]
        confidence = pred_prob if pred_prob > 0.5 else 1 - pred_prob

        color = 'green' if true_label == pred_label else 'red'
        plt.title(f'T: {true_label}\nP: {pred_label} ({confidence:.0%})',
                  fontsize=8, color=color)
        plt.axis('off')

plt.suptitle('Sample Predictions (Green=Correct, Red=Wrong)', fontsize=13)
plt.tight_layout()
plt.savefig('/kaggle/working/gate1_sample_predictions.png', dpi=150, bbox_inches='tight')
plt.show()
```

---

## Cell 14 — Save Final Model

```python
# Save the final model
best_model.save('/kaggle/working/leaf_detector.keras')

# Also save as a smaller TFLite model (optional, for mobile deployment)
converter = tf.lite.TFLiteConverter.from_keras_model(best_model)
tflite_model = converter.convert()
with open('/kaggle/working/leaf_detector.tflite', 'wb') as f:
    f.write(tflite_model)

# Print file sizes
keras_size = os.path.getsize('/kaggle/working/leaf_detector.keras') / (1024 * 1024)
tflite_size = os.path.getsize('/kaggle/working/leaf_detector.tflite') / (1024 * 1024)

print(f"\n✅ Models saved!")
print(f"   leaf_detector.keras  → {keras_size:.1f} MB")
print(f"   leaf_detector.tflite → {tflite_size:.1f} MB")
print(f"\n📥 Download from: Kaggle Output tab (right sidebar)")
print(f"   Save to: F:\\ML_PROJECT\\ml\\models\\leaf_detector.keras")
```

---

## After Training

1. Click **"Save Version"** (top-right) → **Quick Save**
2. Go to the **Output** tab (right sidebar)
3. Download `leaf_detector.keras`
4. Place it at: `F:\ML_PROJECT\ml\models\leaf_detector.keras`
