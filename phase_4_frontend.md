# 📱 Phase 4 — Frontend Development (Flutter)

> **Goal:** Build the Flutter mobile app with authentication, crop selection, camera/gallery integration, prediction display, and history tracking.
>
> **Estimated Time:** 1–2 weeks | **Who:** Frontend Lead
>
> **Can run in parallel with Phase 3** if API contract is agreed upon upfront.

---

## Step 1: Project Setup

### 1.1 Initialize Flutter Project
- Create a new Flutter project targeting Android (and optionally iOS)
- Set minimum Android SDK version to 21 (Android 5.0+)
- Add required packages to `pubspec.yaml`:
  - **Dio** — HTTP client with interceptor support (for JWT auto-attach)
  - **Riverpod** — state management
  - **flutter_secure_storage** — securely store JWT tokens on device
  - **image_picker** — access camera and gallery
  - **go_router** — navigation/routing
  - **cached_network_image** — efficient image loading and caching
  - **lottie** — animations for loading states and empty states
  - **google_fonts** — modern typography (Inter or Outfit font)

### 1.2 Project Structure
```
lib/
├── main.dart                    # App entry point
├── config/
│   ├── api_config.dart          # Base URL, endpoints
│   ├── theme.dart               # App theme (colors, fonts, spacing)
│   └── routes.dart              # Route definitions
├── models/
│   ├── user.dart                # User data model
│   ├── prediction.dart          # Prediction result model
│   ├── crop.dart                # Crop info model
│   └── disease.dart             # Disease info model
├── providers/
│   ├── auth_provider.dart       # Auth state
│   ├── prediction_provider.dart # Prediction state
│   └── history_provider.dart    # History state
├── services/
│   ├── api_service.dart         # Dio client setup
│   ├── auth_service.dart        # Login/register/logout API calls
│   └── prediction_service.dart  # Predict/history API calls
├── screens/
│   ├── splash_screen.dart
│   ├── login_screen.dart
│   ├── register_screen.dart
│   ├── home_screen.dart
│   ├── crop_selection_screen.dart
│   ├── camera_screen.dart
│   ├── result_screen.dart
│   └── history_screen.dart
├── widgets/
│   ├── crop_card.dart
│   ├── prediction_card.dart
│   ├── loading_overlay.dart
│   └── custom_button.dart
└── utils/
    ├── validators.dart
    └── helpers.dart
```

---

## Step 2: API Service Layer (Dio Setup)

### 2.1 Base Dio Client
- Configure Dio with the backend's base URL (e.g., `http://10.0.2.2:8000/api/v1` for Android emulator, or the actual server IP)
- Set default timeout: 30 seconds for uploads, 10 seconds for regular requests
- Add JSON content type headers

### 2.2 JWT Interceptor
This is a Dio interceptor that automatically handles authentication:

**On every outgoing request:**
1. Read the stored access token from secure storage
2. If a token exists, attach it to the request header: `Authorization: Bearer {token}`

**On error response (when backend returns 401):**
1. The access token has expired
2. Automatically read the refresh token from secure storage
3. Call the `/auth/refresh` endpoint to get a new access token
4. Store the new access token
5. Retry the original failed request with the new token
6. If the refresh also fails → clear all tokens → redirect user to login screen

This makes the auth flow **completely invisible** to the user — they never see "session expired" unless the refresh token itself has expired (after 7 days).

### 2.3 Error Handling
- Parse backend error responses into user-friendly messages
- Show appropriate UI feedback: toast messages, dialogs, or inline errors
- Handle network errors (no internet) with a clear "No connection" message

---

## Step 3: Authentication Screens

### 3.1 Splash Screen
**What it does:**
1. Show the app logo/branding with a loading animation
2. Check secure storage — does a valid refresh token exist?
3. If YES → try to get a new access token silently → navigate to Home
4. If NO → navigate to Login screen

**Duration:** 2–3 seconds (enough for the animation + token check)

### 3.2 Login Screen
**UI Elements:**
- App logo/branding at the top
- Email text field (with email keyboard type)
- Password text field (with show/hide toggle)
- "Login" button
- "Don't have an account? Register" link at bottom

**Flow:**
1. User enters email and password
2. Client-side validation: email format, password not empty
3. Call `POST /api/v1/auth/login`
4. On success: store access + refresh tokens in secure storage → navigate to Home
5. On error: show error message (wrong credentials, account not found, etc.)

### 3.3 Register Screen
**UI Elements:**
- Username field
- Email field
- Password field (with strength indicator)
- Confirm password field
- "Register" button
- "Already have an account? Login" link

**Flow:**
1. Client-side validation: email format, password match, password strength (min 8 chars)
2. Call `POST /api/v1/auth/register`
3. On success: show success message → navigate to Login screen
4. On error: show specific error (email taken, username taken, etc.)

---

## Step 4: Home Screen

### 4.1 Layout
This is the main screen after login. It should have:

**Top Section:**
- Welcome message with username
- A logout button/icon

**Main Section — Crop Grid:**
- A grid of cards showing all 14 supported crops
- Each card shows: crop image + crop name
- Tapping a card → navigates to the Camera screen with the selected crop type

**Bottom Section (Optional):**
- Quick stats: total predictions made, last prediction date
- Navigation to History screen

### 4.2 Data Loading
- On screen load, call `GET /api/v1/crops` to fetch the crop list
- Cache the crop list locally (it rarely changes)
- Show a loading skeleton while fetching

---

## Step 5: Crop Selection → Camera Flow

### 5.1 Crop Selection
When the user taps a crop card on the Home screen:
1. Store the selected crop type (e.g., "Potato") in the provider/state
2. Navigate to the Camera screen
3. The selected crop name should be visible on the Camera screen (so the user knows which crop section they're in)

### 5.2 Camera Screen
**UI Elements:**
- Header showing: "Scanning for: {selected_crop}" (e.g., "Scanning for: Potato")
- Two buttons:
  - 📷 **Take Photo** — opens the device camera
  - 🖼️ **Choose from Gallery** — opens the device photo gallery
- Instructions text: "Take a clear photo of a single leaf against a plain background"

**Flow:**
1. User taps "Take Photo" or "Choose from Gallery"
2. The `image_picker` package opens the camera or gallery
3. User captures/selects an image
4. Show a **preview of the selected image** with two options:
   - ✅ **Analyze** — proceed to prediction
   - 🔄 **Retake** — go back to camera/gallery
5. When "Analyze" is tapped:
   - Show a loading overlay with a nice animation (e.g., Lottie scanning animation)
   - Call `POST /api/v1/predict` with the image file + selected crop type
   - On response → navigate to Result screen

### 5.3 Image Preparation Before Upload
- Compress the image if it's larger than 5 MB (reduce quality to 85%)
- Convert to JPEG format if it's in a different format
- Do NOT resize on the client — let the backend handle preprocessing (ensures consistency)

---

## Step 6: Result Screen

This screen shows the prediction result. It has **3 possible states** based on the backend response:

### 6.1 State: Non-Leaf Detected (Gate 1 Rejected)
- Show a **warning/error card** with a red/orange theme
- Icon: ❌ or warning icon
- Message: "This doesn't look like a leaf"
- Sub-message: "Please upload a clear image of a plant leaf"
- Show the uploaded image thumbnail
- Button: "Try Again" → go back to Camera screen

### 6.2 State: Species Mismatch (Gate 2 Rejected)
- Show a **mismatch card** with a yellow/amber theme
- Icon: ⚠️
- Message: "This doesn't look like a {selected_crop} leaf"
- Sub-message: "It appears to be a {detected_species} leaf"
- Show the uploaded image thumbnail
- Two buttons:
  - "Try Again" → go back to Camera screen
  - "Scan as {detected_species}" → re-run prediction with the detected species (optional enhancement)

### 6.3 State: Disease Predicted (All Gates Passed ✅)
- Show a **success card** with a green theme
- **Disease Name** in large text
- **Confidence Score** as a percentage with a visual bar/circle (e.g., "94% confident")
- **Severity** indicator (Low/Medium/High with color coding)
- **Detected Species** confirmation
- **Uploaded Image** thumbnail

- **Remedies Section:**
  - A list of treatment recommendations
  - Each remedy as a card/bullet point

- **Symptoms Section (Optional):**
  - What the disease looks like on the plant

- **Prevention Section (Optional):**
  - How to prevent this disease in the future

- **Actions:**
  - "Scan Another" → go back to Home
  - "View History" → go to History screen
  - "Share" → share the result (optional)

---

## Step 7: History Screen

### 7.1 Layout
- A scrollable list of past predictions, newest first
- Each prediction card shows:
  - Thumbnail of the uploaded image
  - Crop name + disease name
  - Confidence score
  - Date and time
- Tapping a card → shows the full Result screen for that prediction

### 7.2 Data Loading
- Call `GET /api/v1/history` with pagination (page number + page size)
- Show a loading spinner at the bottom when loading more items
- Show an empty state with a Lottie animation if no history exists

---

## Step 8: State Management (Riverpod)

### 8.1 Why Riverpod?
- Compile-time safe (catches errors before runtime)
- No `BuildContext` needed to read state
- Auto-disposal of unused state
- Easy to test

### 8.2 Key Providers

**Auth Provider:**
- Manages: login state, current user, token storage
- States: `loading`, `authenticated`, `unauthenticated`, `error`
- Actions: `login()`, `register()`, `logout()`, `checkAuthStatus()`

**Prediction Provider:**
- Manages: current prediction request and result
- States: `idle`, `uploading`, `analyzing`, `success`, `error`
- Actions: `predict(image, cropType)`, `clearResult()`

**History Provider:**
- Manages: list of past predictions with pagination
- States: `loading`, `loaded`, `loadingMore`, `error`
- Actions: `fetchHistory(page)`, `refreshHistory()`

**Crops Provider:**
- Manages: list of supported crops (fetched once, cached)
- States: `loading`, `loaded`, `error`
- Actions: `fetchCrops()`

---

## Step 9: UI/UX Design Guidelines

### 9.1 Design Principles
- **Nature-inspired color palette:** Greens, earthy tones, warm accents
- **Clean and modern:** Rounded corners, card-based layouts, ample whitespace
- **Accessible:** Readable font sizes, good color contrast, clear tap targets (min 48×48 dp)

### 9.2 Color Palette Suggestion

| Usage | Color | Hex |
|---|---|---|
| Primary | Deep Green | `#2D6A4F` |
| Primary Light | Mint Green | `#52B788` |
| Accent | Warm Orange | `#F77F00` |
| Background | Off-white | `#F8F9FA` |
| Surface (Cards) | White | `#FFFFFF` |
| Error | Soft Red | `#E63946` |
| Warning | Amber | `#FCBF49` |
| Success | Green | `#40916C` |
| Text Primary | Dark Gray | `#212529` |
| Text Secondary | Medium Gray | `#6C757D` |

### 9.3 Typography
- Use **Google Fonts — Inter** or **Outfit** for a clean, modern look
- Headings: Bold, 20–28sp
- Body: Regular, 14–16sp
- Captions: Light, 12sp

### 9.4 Animations
- **Screen transitions:** Smooth slide animations between screens
- **Loading state:** Lottie animation of a leaf being scanned
- **Result reveal:** Fade-in with a slight scale animation
- **Confidence score:** Animated circular progress indicator
- **Crop cards:** Subtle scale-up on tap

---

## ✅ Phase 4 Checklist

- [ ] Flutter project created and structured
- [ ] Dio client configured with JWT interceptor
- [ ] Secure token storage working
- [ ] Login and Register screens functional
- [ ] Home screen displaying crop grid from API
- [ ] Camera/Gallery integration working
- [ ] Image preview + analyze flow working
- [ ] Prediction result screen showing all 3 states (non-leaf, mismatch, disease)
- [ ] History screen with pagination working
- [ ] Riverpod state management wired up for all features
- [ ] UI polished with theme, colors, fonts, animations
- [ ] Error states handled (no internet, server error, etc.)

---

> **← Previous:** [Phase 3: Backend](file:///C:/Users/vamsi/.gemini/antigravity/brain/7f085e6e-cd54-4d50-bbba-e2fa9de78b1c/artifacts/phase_3_backend.md) | **Next →** [Phase 5: Integration & Deployment](file:///C:/Users/vamsi/.gemini/antigravity/brain/7f085e6e-cd54-4d50-bbba-e2fa9de78b1c/artifacts/phase_5_deployment.md)
