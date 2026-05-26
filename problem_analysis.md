# 🔍 Problem Analysis & Solutions

> All 7 issues categorized with root causes and fixes.

---

## Section 1: ML Model Problems (Issues 4, 5, 6)

These problems are all related to how our V1 model works — they are **expected limitations** of the single-classifier approach we chose.

---

### Problem 4 & 5: Wrong Predictions for Specific Crops

> "The model gives wrong predictions for some crops"
> "Potato leaf in potato section shows a tomato disease"

#### Root Cause

Our model is a **single 38-class classifier**. It was trained on all 38 classes together (Apple_scab, Tomato_Early_blight, Potato_Late_blight, etc.). When you upload a potato leaf:

1. The model sees the image
2. It compares it against **ALL 38 classes** (including tomato diseases, apple diseases, etc.)
3. If the potato leaf looks similar to a tomato disease texture, it picks the tomato disease

**The model has NO idea which crop you selected.** The `crop_type` parameter goes to the backend, but the backend doesn't use it to filter the model's output. It just passes whatever the model predicts.

#### Quick Fix (Backend Code Change)

Filter the model's predictions to **only include diseases belonging to the selected crop**:

```
Current flow:  Image → Model → Top prediction from ALL 38 classes → Return
Fixed flow:    Image → Model → Filter by selected crop → Top prediction → Return
```

For example, if the user selects "Potato":
- Model returns: `[Tomato_Early_blight: 0.4, Potato_Late_blight: 0.35, Potato_healthy: 0.15, ...]`
- After filtering to Potato-only classes: `[Potato_Late_blight: 0.35, Potato_healthy: 0.15, Potato_Early_blight: 0.10]`
- Re-normalize confidences → Return `Potato_Late_blight: 58.3%`

This is the #1 most impactful fix. It directly solves problems 4 and 5.

#### Full Solution (Implementing Now)

The 3-Gate Pipeline — we are implementing this now:
1. **Gate 1 — Leaf Detector:** "Is this a leaf?" → Yes/No
2. **Gate 2 — Species Classifier:** "What plant is this?" → Apple/Tomato/Potato/etc.
3. **Gate 3 — Disease Classifier:** "What disease does this {plant} have?"

This completely eliminates cross-crop confusion. See [ML Model Refinement Guide](file:///F:/ML_PROJECT/ml_model_refinement_guide.md) for full details.

---

### Problem 6: Non-Leaf Images Get Predictions

> "When I upload an image other than a leaf, it confidently gives a random disease name"

#### Root Cause

The model was trained **only on leaf images**. It has never seen a dog, a car, or a shoe. When you give it a non-leaf image:

1. It doesn't know "this isn't a leaf"
2. It's **forced** to pick one of the 38 classes (that's how classification models work)
3. It picks whichever class the image *least badly* matches
4. The confidence might still be high because of how softmax probability works

**There is no "reject" option** in the model — it always outputs one of the 38 classes.

#### Quick Fix (Confidence Threshold)

Add a **minimum confidence threshold** in the backend. If the model's top prediction is below a threshold (e.g., 50%), return a message like "Could not identify the leaf. Please try a clearer image."

```
If max_confidence < 0.50 → "Unrecognized. Try a clearer leaf image."
If max_confidence < 0.30 → "This doesn't appear to be a plant leaf."
```

This won't be perfect, but it catches many non-leaf images since the model tends to have lower (but sometimes still high) confidence on completely unrelated images.

#### Full Solution (Implementing Now)

- **Gate 1 — Leaf Detector** (binary classifier: leaf vs not-leaf). A separate small model trained on leaf images vs random images. It rejects non-leaf inputs before they reach the disease classifier. See [ML Model Refinement Guide](file:///F:/ML_PROJECT/ml_model_refinement_guide.md) for training details.

---

### Summary of ML Fixes

| Fix | Impact | Effort | When |
|---|---|---|---|
| **Filter predictions by selected crop** | High — solves problems 4 & 5 | Small — backend code change | Now ✅ |
| **Confidence threshold** | Medium — reduces false positives on non-leaves | Small — backend code change | Now ✅ |
| **Leaf detection gate (Gate 1)** | High — completely rejects non-leaves | Medium — train new model | Now ✅ |
| **Species validation gate (Gate 2)** | High — validates the correct plant | Medium — train new model | Now ✅ |
| **Retrain disease classifier on more data** | High — improves all predictions | Medium — dataset + training | Now ✅ |

---

---

## Section 2: Mobile App Problems (Issues 1, 2, 3, 7)

---

### Problem 1: App Asks to Login Again on Every Restart

> "Every time I close the app and open it, it asks me to log in again"

#### Root Cause

We simplified the splash screen to **always navigate to `/login`** (to fix the hang issue). The splash screen used to check for stored tokens and auto-login, but we removed that logic:

```dart
// Current code (broken):
context.go('/login');  // Always goes to login

// Should be:
// 1. Check if tokens exist in secure storage
// 2. If yes → go to /home
// 3. If no → go to /login
```

#### Fix

Restore the auth check in the splash screen, but do it correctly this time (without the router conflict that caused the hang). The fix involves:
1. Read the token directly from `FlutterSecureStorage` (don't use the Riverpod provider)
2. Navigate based on whether a token exists

---

### Problem 2: History Not Fully Updated

> "I uploaded many images but only few reflected in history"

#### Root Cause

Two possible issues:

1. **Pagination:** The history endpoint returns paginated results (default: 10 per page). The frontend only fetches page 1 and doesn't have "load more" implemented yet.

2. **Backend caching:** The predict endpoint caches results by image hash. If you uploaded the same image twice, it returns the cached result without creating a new database entry.

#### Fix

1. Add **infinite scroll pagination** to the history screen — when the user scrolls to the bottom, fetch the next page.
2. Ensure every prediction creates a database entry (even cached ones).

---

### Problem 3: "Session Expired" While Using the App

> "I am being told my session has expired and need to log in again"

#### Root Cause

- The **access token expires after 15 minutes** (set in backend config)
- The **JWT auto-refresh interceptor** in the Dio client should silently refresh the token when it expires
- But the interceptor might not be working correctly — when the refresh fails or the logic has a bug, the user sees the error instead of a silent refresh

#### Fix

1. **Increase access token lifetime** from 15 minutes to 60 minutes (less friction during testing)
2. **Fix the Dio interceptor** to properly handle the refresh flow and retry failed requests
3. **Add proper error handling** — if refresh truly fails (e.g., after 7 days), redirect to login with a friendly message instead of a raw error

---

### Problem 7: App Needs UI Refinement

> "The app seems good, but needs a lot of refinement in terms of beautification and realisticness"

#### What Needs Improvement

| Area | Current | Should Be |
|---|---|---|
| **Crop cards** | Basic icons (Material Icons) | Real crop images (either generated or from a dataset) |
| **Animations** | Basic fade/scale on splash | Lottie animations for loading, scanning, success states |
| **Camera screen** | Basic buttons | Styled preview with rounded corners, gradient buttons |
| **Result screen** | Functional but plain | Card-based layout with shadows, animated confidence ring |
| **Empty states** | Plain text | Illustrations with helpful messages |
| **Loading states** | Basic spinner | Shimmer placeholders (skeleton loading) |
| **Typography** | Correct but uniform | Better hierarchy — larger headings, better spacing |
| **Color usage** | Good palette, but flat | Gradients, subtle shadows, glassmorphism on cards |

#### Fix

UI polish is a dedicated pass over all screens. It involves:
1. Adding crop images (generated via AI or from dataset)
2. Lottie animations for scanning/loading states
3. Better card designs with shadows and gradients
4. Animated confidence ring (circular progress)
5. Better spacing, typography hierarchy, and micro-animations

---

## Recommended Fix Order

| Priority | Fix | Solves |
|---|---|---|
| 1 | **Filter predictions by crop type** (backend) | Problems 4 & 5 |
| 2 | **Add confidence threshold** (backend) | Problem 6 |
| 3 | **Fix splash auth check** (frontend) | Problem 1 |
| 4 | **Increase token lifetime + fix refresh** (backend + frontend) | Problem 3 |
| 5 | **Fix history pagination** (frontend) | Problem 2 |
| 6 | **UI polish pass** (frontend) | Problem 7 |

> [!NOTE]
> Fixes 1-5 are code changes that can be done right now.
> Fix 6 (UI polish) is a larger effort best done as a separate pass.
> ML model improvements (Gate 1, Gate 2, retraining) are being done now — see [ML Model Refinement Guide](file:///F:/ML_PROJECT/ml_model_refinement_guide.md).
