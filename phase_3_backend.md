# ⚙️ Phase 3 — Backend Development

> **Goal:** Build the FastAPI backend with authentication, database, prediction API, and ML pipeline integration.
>
> **Estimated Time:** 1–2 weeks | **Who:** Backend Lead

---

## Step 1: Project Setup

### 1.1 Initialize the Backend Project
- Create a Python virtual environment (or use Docker from the start)
- Install core dependencies: FastAPI, Uvicorn (ASGI server), SQLAlchemy, Alembic, Pydantic, python-jose (JWT), passlib (password hashing), Redis client, Celery, Pillow, TensorFlow, OpenCV
- Create the folder structure as defined in the system design document

### 1.2 Configuration Management
- Create a settings/config module using Pydantic's `BaseSettings`
- All secrets and config values come from **environment variables** (never hardcoded)
- Key variables: database URL, Redis URL, JWT secret key, token expiry times, model file paths, MinIO credentials
- Create a `.env.example` file documenting all required variables (teammates copy this to `.env` and fill in values)

### 1.3 Application Entry Point
- Initialize the FastAPI application instance
- Add CORS middleware (allow requests from the Flutter app)
- Register all API route groups (auth, predict, history, crops)
- Add a startup event that loads the ML model (`.keras`) and label mapping (`labels.json`) into memory when the server starts (so inference is fast — no loading delay per request)
  > **Future:** When Gate 1 (leaf detection) and Gate 2 (species classification) models are trained, load all 3 models here.
- Add a health check endpoint at `/api/v1/health`

---

## Step 2: Database Setup

### 2.1 PostgreSQL Connection
- Use SQLAlchemy 2.0 with async support (using `asyncpg` driver)
- Create a database session factory that provides a session per request
- Use FastAPI's dependency injection to pass the DB session to route handlers

### 2.2 Define the Database Models
Create SQLAlchemy ORM models for these 4 tables:

**Users Table:**
- `id` (UUID, primary key)
- `email` (unique)
- `username` (unique)
- `password_hash` (bcrypt hashed — never store plain passwords)
- `created_at`, `updated_at`
- `is_active` (for soft-delete/banning)

**Predictions Table:**
- `id` (UUID, primary key)
- `user_id` (foreign key → Users)
- `image_url` (where the uploaded image is stored in MinIO)
- `selected_crop` (what crop section the user was in)
- `disease_name` (predicted disease class, e.g., "Tomato___Early_blight")
- `confidence` (float 0–1, highest softmax probability)
- `severity` (Low/Medium/High)
- `remedies` (JSON array)
- `created_at`

> **Future columns (when 3-gate system is added):**
> - `is_leaf` (boolean — Gate 1 result)
> - `detected_species` (what Gate 2 predicted)
> - `species_match` (boolean — does Gate 2 match the selected crop?)

**Crops Table:**
- `id`, `name`, `scientific_name`, `description`, `image_url`
- Pre-populated with the 14 supported crop species

**Diseases Table:**
- `id`, `crop_id` (FK → Crops), `name`, `scientific_name`
- `description`, `severity`, `symptoms` (JSON), `remedies` (JSON), `prevention` (JSON)
- Pre-populated with all 38 disease entries and their treatment info

### 2.3 Database Migrations
- Initialize Alembic for database migration management
- Create the initial migration that creates all 4 tables
- Create a seed script that populates the Crops and Diseases tables with pre-defined data (crop names, disease info, remedies)

---

## Step 3: Authentication System (JWT)

### 3.1 Password Handling
- Use `passlib` with bcrypt algorithm (12 rounds) for hashing passwords
- When a user registers: hash the password → store the hash
- When a user logs in: hash the input → compare with stored hash

### 3.2 JWT Token Strategy
- **Access Token:** Short-lived (15 minutes), sent with every API request in the `Authorization: Bearer {token}` header
- **Refresh Token:** Long-lived (7 days), used ONLY to get a new access token when the old one expires
- Both tokens contain the `user_id` and `exp` (expiration timestamp) in their payload

### 3.3 Token Flow

**Registration:**
1. User sends `email`, `username`, `password`
2. Validate inputs (email format, password strength, username uniqueness)
3. Hash the password
4. Save user to database
5. Return success (user can now login)

**Login:**
1. User sends `email` + `password`
2. Find user by email in database
3. Compare password hash
4. If valid → generate access token + refresh token
5. Return both tokens

**Accessing Protected Routes:**
1. Every request sends the access token in the header
2. Backend middleware extracts the token
3. Check if token is in Redis blacklist (logged out tokens)
4. Decode the JWT → extract `user_id` and `exp`
5. If expired → return 401 (client should use refresh token)
6. If valid → attach `user_id` to the request context → proceed

**Token Refresh:**
1. Client sends the refresh token
2. Backend verifies the refresh token is valid and not expired
3. Generate a new access token
4. Return the new access token

**Logout:**
1. Client sends the current access token
2. Backend adds the token to Redis blacklist with TTL = remaining expiry time
3. The token is now invalid even though it hasn't technically expired

### 3.4 Redis for Token Blacklisting
- When a user logs out, store their token's unique ID (JTI) in Redis
- Set the TTL (time-to-live) to the token's remaining valid time
- On every request, check Redis: is this token's JTI blacklisted?
- This way, blacklisted tokens auto-expire from Redis when they would have expired naturally

---

## Step 4: Build the Prediction API

### 4.1 The `/api/v1/predict` Endpoint

This is the **most important endpoint** in the entire app. Here's the detailed flow:

**Request:**
- Method: POST
- Auth: Required (JWT)
- Body: Multipart form data with `image` (file) + `crop_type` (string, e.g., "Potato")

**Validation Steps:**
1. Verify the JWT token is valid
2. Check rate limit — max 10 predictions per minute per user (via Redis counter)
3. Validate the uploaded file:
   - Is it a valid image format? (JPEG or PNG only)
   - Is it under the size limit? (max 10 MB)
   - Can it be opened as an image? (not a corrupted file)
4. Validate `crop_type` — is it one of the 14 supported crops?

**Processing Steps:**
1. **Generate image hash** — compute a hash of the image pixels (not the file, the actual pixel content)
2. **Check Redis cache** — has this exact image been analyzed before?
   - If YES (cache hit) → return the cached result immediately (saves inference time)
   - If NO (cache miss) → continue to ML pipeline
3. **Upload image to MinIO** — store the original image for history/audit
4. **Run the ML inference pipeline** (detailed in Step 5 below)
5. **Cache the result in Redis** — store with the image hash as key, TTL of 1 hour
6. **Save prediction to database** — create a new row in the Predictions table
7. **Return the response** — JSON with all prediction details

### 4.2 Other API Endpoints

**History Endpoints:**
- `GET /api/v1/history` — return paginated list of user's past predictions (newest first)
- `GET /api/v1/history/{id}` — return full details of a specific prediction

**Crop/Disease Info Endpoints:**
- `GET /api/v1/crops` — return list of all 14 supported crops with images
- `GET /api/v1/diseases/{crop}` — return all diseases for a specific crop with symptoms & remedies

---

## Step 5: ML Pipeline Integration

### 5.1 Model Loading (On Server Startup)
- When FastAPI starts, load the trained disease classifier (`plant_disease_model.keras`) into memory
- Also load the class-label mapping (`labels.json`) — maps indices (0–37) to disease names
- Keep them as global/singleton objects — they stay in memory for the entire server lifetime
- This avoids loading the model from disk on every prediction request

### 5.2 Current Inference Pipeline (Single Model — Disease Classification)

When a prediction request arrives:

1. Preprocess the image: resize to 224×224, apply `preprocess_input()`
2. Run through the disease classification model
3. Get the output: probabilities for all 38 disease classes
4. Take the top prediction (highest softmax probability)
5. Look up the disease in the Diseases database table → fetch remedies, severity, symptoms
6. Return the full prediction response

> [!NOTE]
> **Future: 3-Gate Pipeline**
> The code should be structured so that the inference pipeline is a single function. When Gate 1 (leaf detection) and Gate 2 (species classification) models are trained later, we add them as **pre-checks** before the disease classifier:
>
> ```
> Gate 1 (Leaf?) → Gate 2 (Species match?) → Gate 3 (Disease classification)
> ```
>
> This only requires updating the pipeline function — no changes to the API endpoints, database, or frontend.

### 5.3 Image Preprocessing
- Convert image bytes to RGB format (handle grayscale or RGBA inputs)
- Resize to 224×224 (EfficientNetB0's expected input size)
- Apply `keras.applications.efficientnet.preprocess_input()` (scales pixel values to the range the model expects)
- Add a batch dimension (model expects shape [1, 224, 224, 3])

---

## Step 6: Redis Setup

### 6.1 Uses of Redis in this project

| Use Case | How |
|---|---|
| **JWT Blacklist** | Store invalidated token IDs with TTL |
| **Prediction Cache** | Store image_hash → prediction result (TTL: 1 hour) |
| **Rate Limiting** | Per-user request counter with TTL (resets every minute) |
| **Celery Broker** | Message queue for async background tasks |

### 6.2 Caching Strategy
- Before running the ML pipeline, compute a hash of the image
- Check Redis: does this hash exist as a key?
- If yes → return the cached prediction (skip all 3 gates)
- If no → run the pipeline, then store the result in Redis

This means if the same user (or different users) upload the same image, the 2nd+ requests are near-instant.

---

## Step 7: Celery Task Queue

### 7.1 What Celery Handles
Celery runs heavy/non-urgent tasks in the **background**, so the API remains fast:

- **Batch history export** — if a user wants to download their full prediction history as CSV/PDF
- **Image cleanup** — periodically delete old uploaded images from MinIO
- **Usage analytics** — aggregate prediction counts per crop, per disease
- **Future: Model retraining** — if you ever add a feedback loop where users correct wrong predictions

### 7.2 How It Works
1. FastAPI sends a task to Redis (the message broker)
2. A Celery worker picks up the task from Redis
3. The worker executes it in the background
4. The result (if any) is stored back in Redis

> [!NOTE]
> For the initial version, Celery is mainly for future extensibility. The core prediction flow is synchronous (fast enough without Celery since inference takes < 300ms).

---

## Step 8: Error Handling

### 8.1 Standardized Error Responses
Every error response should follow a consistent format:
- `status`: "error"
- `error_code`: a machine-readable code (e.g., "INVALID_IMAGE", "RATE_LIMIT_EXCEEDED")
- `message`: a human-readable explanation
- `details`: optional extra info

### 8.2 Key Error Cases

| Scenario | Status Code | Error Code | Message |
|---|---|---|---|
| Invalid/expired JWT | 401 | AUTH_EXPIRED | "Your session has expired. Please login again." |
| Invalid image format | 400 | INVALID_IMAGE | "Only JPEG and PNG images are supported." |
| Image too large | 400 | IMAGE_TOO_LARGE | "Image must be under 10 MB." |
| Unsupported crop type | 400 | INVALID_CROP | "'{crop}' is not a supported crop." |
| Rate limit exceeded | 429 | RATE_LIMIT | "Too many requests. Please wait a moment." |
| ML model error | 500 | PREDICTION_FAILED | "Unable to process this image. Please try again." |
| Database error | 500 | SERVER_ERROR | "Something went wrong. Please try again later." |

---

## ✅ Phase 3 Checklist

- [ ] FastAPI project initialized with proper folder structure
- [ ] PostgreSQL connected with SQLAlchemy async
- [ ] All 4 database tables created (Users, Predictions, Crops, Diseases)
- [ ] Alembic migrations working
- [ ] Crops & Diseases tables seeded with data
- [ ] Registration + Login + Logout endpoints working
- [ ] JWT access + refresh token flow working
- [ ] Redis connected — blacklisting, caching, rate limiting
- [ ] `/api/v1/predict` endpoint working with the disease classification model
- [ ] History endpoints working
- [ ] MinIO connected — image uploads working
- [ ] Error handling standardized across all endpoints
- [ ] All endpoints testable via Swagger UI (`/docs`)

---

> **← Previous:** [Phase 2: Model Training](file:///C:/Users/vamsi/.gemini/antigravity/brain/7f085e6e-cd54-4d50-bbba-e2fa9de78b1c/artifacts/phase_2_model_training.md) | **Next →** [Phase 4: Frontend Development](file:///C:/Users/vamsi/.gemini/antigravity/brain/7f085e6e-cd54-4d50-bbba-e2fa9de78b1c/artifacts/phase_4_frontend.md)
