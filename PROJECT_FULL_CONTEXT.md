# PROJECT_FULL_CONTEXT

## Overview

This repository implements an AI-enabled plant disease detection system with a Flutter mobile frontend, a Python FastAPI backend, and machine learning training pipelines for plant leaf classification. The current project is structured as a hybrid mobile/web service offering user authentication, image upload, disease prediction, history tracking, and crop/disease lookup.

The architecture is organized into three major areas:
- `backend/`: FastAPI service, PostgreSQL schema, Redis caching, MinIO image storage, ML inference service
- `frontend/`: Flutter mobile application for Android, using Riverpod state management, GoRouter navigation, and HTTP API integration
- `ml/` and `gate_*`: machine learning training scripts, saved model artifacts, and label definitions

Additional documentation files exist at the repository root for installation, testing, design, and development phase notes.

---

## Exact Tech Stack Versions

| Category | Technology | Version |
|---|---|---|
| Frontend | Flutter SDK | ^3.11.1 |
| Frontend | Dart SDK | ^3.11.1 |
| Frontend | go_router | 14.0.0 |
| Frontend | flutter_riverpod | 2.5.0 |
| Frontend | dio | 5.4.0 |
| Frontend | connectivity_plus | 6.0.0 |
| Frontend | flutter_secure_storage | 9.2.0 |
| Frontend | image_picker | 1.1.0 |
| Frontend | cached_network_image | 3.3.0 |
| Frontend | google_fonts | 6.2.0 |
| Frontend | lottie | 3.1.0 |
| Frontend | shimmer | 3.0.0 |
| Frontend | fl_chart | 0.69.0 |
| Frontend | flutter_dotenv | 5.1.0 |
| Frontend | flutter_lints | 6.0.0 |
| Backend | FastAPI | 0.136.1 |
| Backend | uvicorn[standard] | 0.46.0 |
| Backend | SQLAlchemy[asyncio] | 2.0.49 |
| Backend | asyncpg | 0.31.0 |
| Backend | Alembic | 1.18.4 |
| Backend | python-jose[cryptography] | 3.5.0 |
| Backend | passlib[bcrypt] | 1.7.4 |
| Backend | bcrypt | 4.1.3 |
| Backend | TensorFlow | 2.21.0 |
| Backend | Redis[hiredis] | 7.4.0 |
| Backend | Celery | 5.6.3 |
| Backend | minio | >=7.0 |
| Backend | Pillow | >=10.0 |
| Backend | numpy | >=1.24 |
| Backend | pydantic[email-validator] | >=2.0 |
| Backend | pydantic-settings | >=2.0 |
| Backend | python-dotenv | 1.2.2 |
| Backend | python-multipart | 0.0.28 |
| Database | PostgreSQL | 16-alpine |
| Database | Redis | 7-alpine |
| Storage | MinIO | latest |
| DevOps | Docker Compose | 3.9 |

> Note: Python version is not explicitly pinned in the repository, but the dependency set strongly suggests Python 3.11+ compatibility.

---

## Full Folder Structure

```
ML_PROJECT/
├── .github/
│   └── java-upgrade/
│       └── .gitignore
├── .vscode/
├── backend/
│   ├── .env
│   ├── alembic.ini
│   ├── docker-compose.yml
│   ├── requirements.txt
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   │       ├── 86a26a697cc9_initial_tables.py
│   │       └── 1a9664c08f6e_initial_tables.py
│   └── app/
│       ├── __init__.py
│       ├── config.py
│       ├── database.py
│       ├── main.py
│       ├── seed.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── dependencies.py
│       │   ├── exceptions.py
│       │   └── security.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── crop.py
│       │   ├── disease.py
│       │   ├── prediction.py
│       │   └── user.py
│       ├── routers/
│       │   ├── __init__.py
│       │   ├── auth.py
│       │   ├── crops.py
│       │   ├── history.py
│       │   └── predict.py
│       ├── schemas/
│       │   ├── __init__.py
│       │   ├── auth.py
│       │   ├── crop.py
│       │   └── predict.py
│       ├── services/
│       │   ├── __init__.py
│       │   └── ml_service.py
│       └── utils/
│           ├── __init__.py
│           ├── minio_client.py
│           └── redis_client.py
├── frontend/
│   ├── .env
│   ├── README.md
│   ├── analysis_options.yaml
│   ├── pubspec.yaml
│   ├── pubspec.lock
│   ├── android/
│   │   ├── build.gradle.kts
│   │   ├── gradle.properties
│   │   ├── local.properties
│   │   ├── settings.gradle.kts
│   │   └── app/
│   │       ├── build.gradle.kts
│   │       └── src/
│   │           └── main/
│   │               ├── AndroidManifest.xml
│   │               ├── res/
│   │               │   ├── drawable/
│   │               │   ├── drawable-v21/
│   │               │   ├── mipmap-anydpi-v26/
│   │               │   └── values/
│   ├── assets/
│   │   ├── animations/
│   ├── build/  (generated)
│   ├── lib/
│   │   ├── main.dart
│   │   ├── config/
│   │   │   ├── api_config.dart
│   │   │   ├── routes.dart
│   │   │   └── theme.dart
│   │   ├── providers/
│   │   │   ├── auth_provider.dart
│   │   │   └── prediction_provider.dart
│   │   ├── screens/
│   │   │   ├── camera_screen.dart
│   │   │   ├── history_screen.dart
│   │   │   ├── home_screen.dart
│   │   │   ├── login_screen.dart
│   │   │   ├── register_screen.dart
│   │   │   ├── result_screen.dart
│   │   │   └── splash_screen.dart
│   │   └── services/
│   │       ├── api_service.dart
│   │       ├── auth_service.dart
│   │       └── prediction_service.dart
│   └── test/
├── gate_1/
│   ├── leaf_detector.keras
│   └── leaf_detector.tflite
├── gate_2/
│   ├── species_classifier.keras
│   ├── species_classifier.tflite
│   └── species_labels.json
├── ml/
│   ├── gate1_leaf_detector_training.py
│   ├── gate2_species_classifier_training.py
│   └── models/
│       ├── labels.json
│       └── plant_disease_model.keras
├── backend_installation_guide.md
├── backend_testing_guide.md
├── frontend_installation_guide.md
├── frontend_testing_guide.md
├── gate1_notebook_code.md
├── ml_model_refinement_guide.md
├── model_training_guide.md
├── phase_0_overview.md
├── phase_3_backend.md
├── phase_4_frontend.md
├── phase_5_deployment.md
├── plant_disease_system_design.md
├── problem_analysis.md
├── Tulsileafdisease.pdf
└── venv/  (Python virtual environment)
```

> Note: `frontend/build/` and `venv/` are generated directories; they contain build artifacts and virtual environment state, not source code.

---

## Backend Architecture

### Backend high-level design

The backend is implemented in `backend/app/` as a FastAPI service with:
- JWT-based authentication
- PostgreSQL database via async SQLAlchemy
- Alembic migrations for schema versioning
- Redis for rate limiting, result caching, and token blacklist support
- MinIO for image storage and signed URLs
- A model inference service that loads a TensorFlow `.keras` model and returns prediction results

The FastAPI service is started from `backend/app/main.py` and registers four router groups:
- `auth` for registration, login, refresh, logout
- `predict` for disease analysis
- `history` for viewing user prediction history
- `crops` for supported crop and disease metadata

### Configuration and environment

- `backend/.env` contains all runtime configuration.
- `backend/app/config.py` defines `Settings` using `pydantic_settings.BaseSettings` and reads `.env` automatically.

Key environment variables:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`
- `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_BUCKET_NAME`, `MINIO_SECURE`
- `MODEL_PATH`, `LABELS_PATH`
- `RATE_LIMIT_PER_MINUTE`

### Main entrypoint

#### `backend/app/main.py`

Purpose:
- Create the FastAPI application instance
- Attach CORS middleware with permissive `*` settings
- Register routers
- Implement startup/shutdown lifecycle logic
- Provide a health check endpoint

Responsibilities:
- Connect to Redis on startup
- Initialize MinIO and create the bucket if necessary
- Load the TensorFlow model into memory via `ml_service.load_model()`
- Disconnect Redis gracefully on shutdown

Connected files:
- `app/config.py`
- `app/utils/redis_client.py`
- `app/utils/minio_client.py`
- `app/services/ml_service.py`
- `app/routers/*.py`

### Database architecture

#### `backend/app/database.py`

Purpose:
- Initialize the async SQLAlchemy engine with `asyncpg`
- Create a session factory for request-scoped DB sessions
- Provide the `get_db()` dependency for routes
- Define the declarative base class for ORM models

Details:
- `engine` uses connection pooling, `echo` is enabled in debug mode
- `async_session` is configured with `expire_on_commit=False`
- `get_db()` yields an `AsyncSession` and handles rollback/commit

#### `backend/alembic/env.py`

Purpose:
- Configure Alembic for async PostgreSQL migrations
- Import SQLAlchemy metadata from `app.database.Base`
- Use environment settings for the migration URL

#### `backend/alembic/versions/86a26a697cc9_initial_tables.py`

Purpose:
- Create the initial schema for all tables
- Define `crops`, `users`, `diseases`, and `predictions`

Schema:
- `crops` with `id`, `name`, `scientific_name`, `description`, and `image_url`
- `users` with `id`, `email`, `username`, `password_hash`, `is_active`, timestamps
- `diseases` with foreign key to `crops`, `name`, `scientific_name`, text fields, `severity`, JSON fields for symptoms/remedies/prevention
- `predictions` with foreign key to `users`, stored image reference, selected crop, disease data, confidence, severity, remedies, timestamp

Note: `backend/alembic/versions/1a9664c08f6e_initial_tables.py` exists but contains an empty migration.

### ORM models

#### `backend/app/models/user.py`

Purpose:
- Represent registered users
- Store email, username, hashed password, active status, and timestamps
- Provide relationship to prediction records

Important details:
- Uses PostgreSQL `UUID` primary key
- Indexes on `email` and `username`

#### `backend/app/models/prediction.py`

Purpose:
- Store each disease prediction along with user ownership
- Save MinIO object path, selected crop, model output fields, confidence, severity, and remedies

Important details:
- Stores `image_url` as MinIO object name rather than signed URL
- Has a relationship to `User`

#### `backend/app/models/disease.py`

Purpose:
- Store disease metadata for lookup and result enrichment
- Includes symptoms, remedies, severity, prevention guidance

Important details:
- Uses JSON fields for lists of symptoms/remedies/prevention
- Links to `Crop` via `crop_id`

#### `backend/app/models/crop.py`

Purpose:
- Store crop metadata for the 14 supported plant species
- Includes name, scientific name, description, optional image URL
- Links to diseases via relationship

### API routers and endpoints

#### `backend/app/routers/auth.py`

Purpose:
- Register new users
- Log users in and issue access/refresh tokens
- Refresh access tokens
- Log users out

Endpoints:
- `POST /api/v1/auth/register`
  - Request: `{ email, username, password }`
  - Response: `{ status, message }`
- `POST /api/v1/auth/login`
  - Request: `{ email, password }`
  - Response: `{ access_token, refresh_token, token_type }`
- `POST /api/v1/auth/refresh`
  - Request: `{ refresh_token }`
  - Response: `{ access_token, token_type }`
- `POST /api/v1/auth/logout`
  - Request: Bearer access token
  - Response: `{ status, message }`

Notes:
- Passwords are hashed with bcrypt
- JWTs are created with `python-jose`
- Logout endpoint currently returns success but does not blacklist the token in this code path

#### `backend/app/routers/predict.py`

Purpose:
- Handle image upload and disease prediction
- Perform crop validation, rate limiting, cache lookup, MinIO upload, ML inference, db save, and response assembly

Endpoint:
- `POST /api/v1/predict`
  - Request: multipart form with `image` and `crop_type`
  - Auth: Bearer token required
  - Response: `PredictionResponse`

Processing flow:
1. Validate user access and rate limit using Redis
2. Validate selected crop against the supported 14 species
3. Validate image type and size (JPEG/PNG, <10 MB)
4. Verify the uploaded file is a valid image
5. Check Redis cache by SHA-256 image hash
6. Upload image bytes to MinIO
7. Run `ml_service.predict(image_bytes)`
8. Lookup disease metadata from PostgreSQL
9. Save a `Prediction` database record
10. Cache response in Redis for one hour
11. Return prediction payload including signed image URL

Important limitation:
- `crop_type` is validated but not used to filter the model's output, which means the disease classifier can still return a disease from a different crop.

#### `backend/app/routers/history.py`

Purpose:
- Expose paginated history and single-prediction detail for the authenticated user

Endpoints:
- `GET /api/v1/history`
  - Query params: `page`, `per_page`
  - Auth: Bearer token required
  - Response: `{ items, total, page, pages }`
- `GET /api/v1/history/{prediction_id}`
  - Auth: Bearer token required
  - Response: `PredictionHistoryItem`

Behavior:
- Uses `Prediction` table, ordered by descending creation time
- Returns signed MinIO URLs for image access

#### `backend/app/routers/crops.py`

Purpose:
- Expose supported crops and crop-specific diseases

Endpoints:
- `GET /api/v1/crops`
  - Response: list of supported crops
- `GET /api/v1/diseases/{crop_name}`
  - Response: list of diseases for the given crop

Behavior:
- Loads crop metadata from `Crop` table
- Returns disease metadata with symptoms and remedies

### Schemas and serialization

The backend uses Pydantic models in `backend/app/schemas/`:
- `auth.py` for register/login/refresh/logout responses
- `predict.py` for prediction result and history payloads
- `crop.py` for crop and disease detail payloads

Model config is set to `from_attributes` for ORM compatibility so route responses can be built directly from SQLAlchemy model instances.

### Security and middleware

- Authentication uses HTTP Bearer tokens in `backend/app/core/dependencies.py`
- `get_current_user()` decodes JWT, checks token type, ensures token is not blacklisted, and verifies the user exists and is active
- Custom exceptions in `backend/app/core/exceptions.py` provide standardized error payloads
- `backend/app/core/security.py` handles password hashing and JWT creation/verification

### Utility components

#### `backend/app/utils/redis_client.py`

Purpose:
- Manage Redis connection
- Handle token blacklist storage
- Support image prediction caching
- Enforce per-user request rate limiting

Key operations:
- `blacklist_token(jti, ttl_seconds)`
- `is_blacklisted(jti)`
- `cache_prediction(image_hash, result, ttl=3600)`
- `get_cached_prediction(image_hash)`
- `check_rate_limit(user_id, max_requests)`

#### `backend/app/utils/minio_client.py`

Purpose:
- Manage MinIO connection and bucket creation
- Upload image objects
- Generate presigned GET URLs for images
- Delete image objects

Important note:
- The object name stored in the database is the MinIO path, not the publicly accessible URL.

### ML inference service

#### `backend/app/services/ml_service.py`

Purpose:
- Load the TensorFlow model and label map once at startup
- Preprocess image bytes for inference
- Run model predictions and assemble structured results

Key behaviors:
- Loads model from `MODEL_PATH`
- Loads label map from `LABELS_PATH`
- Preprocesses images to `224x224` RGB using `tensorflow.keras.applications.efficientnet.preprocess_input`
- Predicts, finds the top class, and returns top-5 predictions
- Computes SHA-256 image hash for caching

Inputs/outputs:
- Input: raw image bytes
- Output: dict with `disease_name`, `confidence`, `class_index`, and `top_predictions`

Current inference model:
- `ml/models/plant_disease_model.keras`
- label map in `ml/models/labels.json`
- 38-class plant disease classifier

### Seed data

#### `backend/app/seed.py`

Purpose:
- Populate `crops` and `diseases` tables with initial metadata
- Supports 14 crop species and 38 disease classes

Behavior:
- Uses `async_session` to insert crop and disease records
- Contains detailed disease descriptions, symptoms, remedies, and prevention advice
- Intended to be executed with `python -m app.seed`

### Backend deployment setup

#### `backend/docker-compose.yml`

This Compose file defines infrastructure services only:
- PostgreSQL 16-alpine
- Redis 7-alpine
- MinIO latest

It does not define a backend service container for the FastAPI app.

Docker compose details:
- PostgreSQL exposed on `5432`
- Redis exposed on `6379`
- MinIO console on `9001`, API on `9000`
- Uses named Docker volumes for persistence

Important implication:
- The backend service is expected to run locally outside Docker or in a separate container not defined here.

---

## Frontend Architecture

### Frontend high-level design

The frontend is a Flutter mobile application stored in `frontend/`. It is an Android-capable Flutter app that provides:
- user registration and login
- crop selection
- leaf image capture or gallery selection
- disease prediction request submission
- prediction result display
- prediction history review

The app uses:
- Riverpod for state management
- GoRouter for navigation
- Dio for HTTP networking
- secure storage for tokens
- flutter_dotenv for environment variables

### Entry point and routing

#### `frontend/lib/main.dart`

Purpose:
- Initialize Flutter binding
- Load environment variables from `frontend/.env`
- Run the app using `ProviderScope`
- Configure the app with `MaterialApp.router`

#### `frontend/lib/config/routes.dart`

Purpose:
- Define app routes and navigation pages
- Map string paths to screen widgets

Routes:
- `/` → `SplashScreen`
- `/login` → `LoginScreen`
- `/register` → `RegisterScreen`
- `/home` → `HomeScreen`
- `/camera/:cropName` → `CameraScreen`
- `/result` → `ResultScreen`
- `/history` → `HistoryScreen`

### Theme and styling

#### `frontend/lib/config/theme.dart`

Purpose:
- Define color palette and theme data
- Provide custom text styling, button styling, input decoration, cards, and app bar theme

Key colors:
- primary: `#2D6A4F`
- accent: `#F77F00`
- success: `#40916C`
- error: `#E63946`

### API configuration

#### `frontend/lib/config/api_config.dart`

Purpose:
- Provide base API URL and endpoint paths
- Keep route strings centralized

Base URL:
- `API_BASE_URL` from `.env`
- Default fallback: `http://10.0.2.2:8000/api/v1`

Supported endpoints mirror the backend routes.

### State management and services

#### `frontend/lib/providers/auth_provider.dart`

Purpose:
- Manage authentication state and transitions
- Expose register/login/logout flows to UI

Behavior:
- Uses `AuthService`
- Tracks statuses: `initial`, `loading`, `authenticated`, `unauthenticated`, `error`
- Persists no internal auth state beyond tokens in storage

#### `frontend/lib/providers/prediction_provider.dart`

Purpose:
- Manage prediction request lifecycle and history data
- Provide crop list and prediction history state

States:
- `idle`, `uploading`, `analyzing`, `success`, `error`

Responsibilities:
- Submit prediction requests via `PredictionService`
- Fetch crop list and history
- Clear results when scanning again

#### `frontend/lib/services/api_service.dart`

Purpose:
- Configure Dio client with base URL and timeouts
- Attach JWT access token to requests
- Handle automatic refresh of access tokens on 401 responses

Important details:
- Uses `FlutterSecureStorage` for tokens
- Writes `Authorization: Bearer <token>` header for protected routes
- Attempts token refresh using `ApiConfig.refresh`
- Retries original request after successful refresh

#### `frontend/lib/services/auth_service.dart`

Purpose:
- Implement registration, login, logout, and auth token persistence
- Parse Dio errors into user-friendly messages

Behavior:
- Stores `access_token` and `refresh_token`
- Clears tokens on logout
- Returns boolean/auth message states to callers

#### `frontend/lib/services/prediction_service.dart`

Purpose:
- Handle prediction image upload
- Fetch crop list and prediction history via backend APIs

Behavior:
- Builds multipart form data with `image` and `crop_type`
- Uses `POST /predict` for disease detection
- Uses `GET /crops`, `GET /history`, and `GET /diseases/{crop}`

### UI screens and user flow

#### `frontend/lib/screens/splash_screen.dart`

Purpose:
- Display splash branding and transition to login

Important note:
- Current code always navigates to `/login` after 2 seconds, bypassing any stored auth token check.

#### `frontend/lib/screens/login_screen.dart`

Purpose:
- Collect email and password
- Call login flow
- Navigate to `/home` on success

Validation:
- Basic email format and password non-empty

#### `frontend/lib/screens/register_screen.dart`

Purpose:
- Collect username, email, password, password confirmation
- Register a new user and redirect to login

Validation:
- Username pattern, email, password length, password match

#### `frontend/lib/screens/home_screen.dart`

Purpose:
- Show the list of supported crops
- Navigate to camera screen for selected crop
- Allow logout and history navigation

Behavior:
- Fetches crop list from backend
- Displays cards for each crop
- Uses `context.push('/camera/${cropName}')`

#### `frontend/lib/screens/camera_screen.dart`

Purpose:
- Capture or pick an image
- Display image preview
- Submit image to backend for analysis

Behavior:
- Uses `image_picker`
- Supports camera or gallery
- Uploads file and crop type via `PredictionProvider`
- Navigates to `/result` after success

#### `frontend/lib/screens/result_screen.dart`

Purpose:
- Render prediction result details
- Show disease name, confidence, severity, symptoms, remedies, prevention
- Offer scan again or view history

Behavior:
- Reads result from provider state
- Formats disease names by replacing `___` and `_`
- Uses color-coded cards for disease severity

#### `frontend/lib/screens/history_screen.dart`

Purpose:
- Present paginated prediction history
- Refresh history data

Behavior:
- Calls history provider on init
- Displays item list with disease name, crop, confidence, severity, timestamp

### Frontend environment and config

#### `frontend/.env`

```
API_BASE_URL=http://localhost:8000/api/v1
```

This environment file is loaded at startup by `flutter_dotenv`.

---

## ML / DL Pipeline

### Overview

This project includes both deployed inference artifacts and training scripts:
- `ml/models/plant_disease_model.keras`: currently loaded by the backend for inference
- `ml/models/labels.json`: 38-class disease label map used by inference
- `gate_1/`: contains a leaf detector model and artifacts
- `gate_2/`: contains a species classifier model and artifacts
- `ml/gate1_leaf_detector_training.py`: training pipeline for leaf vs non-leaf classification
- `ml/gate2_species_classifier_training.py`: training pipeline for species classification

### Current production inference model

The backend currently uses a single disease classifier model:
- File: `ml/models/plant_disease_model.keras`
- Labels: `ml/models/labels.json`
- Classes: 38 disease categories across 14 crops
- Expected input: RGB leaf image resized to `224x224`
- Preprocessing: EfficientNet preprocessing from TensorFlow

### Disease label map

`ml/models/labels.json` maps class indexes to disease names, including:
- Apple: `Apple_scab`, `Black_rot`, `Cedar_apple_rust`, `healthy`
- Blueberry: `healthy`
- Cherry: `Powdery_mildew`, `healthy`
- Corn: `Cercospora_leaf_spot Gray_leaf_spot`, `Common_rust_`, `Northern_Leaf_Blight`, `healthy`
- Grape: `Black_rot`, `Esca_(Black_Measles)`, `Leaf_blight_(Isariopsis_Leaf_Spot)`, `healthy`
- Orange: `Haunglongbing_(Citrus_greening)`
- Peach: `Bacterial_spot`, `healthy`
- Pepper: `Bacterial_spot`, `healthy`
- Potato: `Early_blight`, `Late_blight`, `healthy`
- Raspberry: `healthy`
- Soybean: `healthy`
- Squash: `Powdery_mildew`
- Strawberry: `Leaf_scorch`, `healthy`
- Tomato: `Bacterial_spot`, `Early_blight`, `Late_blight`, `Leaf_Mold`, `Septoria_leaf_spot`, `Spider_mites Two-spotted_spider_mite`, `Target_Spot`, `Tomato_Yellow_Leaf_Curl_Virus`, `Tomato_mosaic_virus`, `healthy`

### Gate 1 — Leaf detector

`ml/gate1_leaf_detector_training.py` describes a binary classifier training pipeline:
- Goal: classify images as `leaf` or `non_leaf`
- Base model: `MobileNetV2` pretrained on ImageNet
- Input size: `224x224`
- Loss: `binary_crossentropy`
- Output: `leaf_detector.keras`
- Approach: two-phase transfer learning
  - Phase 1: freeze the base model and train custom head
  - Phase 2: unfreeze last 30 layers and fine-tune
- Augmentation: flip, rotation, zoom, brightness, contrast
- Intended use: reject non-leaf images before disease classification

### Gate 2 — Species classifier

`ml/gate2_species_classifier_training.py` describes a 14-class species classification pipeline:
- Goal: classify leaf images into one of 14 crop species
- Base model: `EfficientNetB0` pretrained on ImageNet
- Input size: `224x224`
- Loss: `categorical_crossentropy`
- Output: `species_classifier.keras`, `species_classifier.tflite`, `species_labels.json`
- Training process:
  - Reorganize 38 disease-class folders into 14 species folders
  - Balance classes to ~2000 images per species through oversampling/undersampling
  - Build an 80/10/10 training/validation/test split
  - Use augmentation: flip, rotation, zoom, brightness, contrast, translation
  - Phase 1: train custom head with frozen base model
  - Phase 2: fine-tune last 50 layers of EfficientNetB0
- Output label map: `gate_2/species_labels.json`

### Gate 3 — Disease classifier

The current backend inference path uses the disease classifier model and label map in `ml/models/`
- This is effectively the final gate in the intended pipeline
- The code currently does not integrate gate 1 or gate 2 into runtime inference

### Datasets and data handling

The training scripts reference Kaggle datasets:
- Leaf vs Non-Leaf images dataset for gate 1
- New Plant Diseases Dataset (PlantVillage) for gate 2

Data handling features in training scripts:
- automatic `.webp` conversion to JPG
- dataset sanitization to remove invalid images
- dataset balancing and normalization
- caching and prefetching for TensorFlow dataset performance

---

## Database Structure

### DB type

- PostgreSQL using `asyncpg` and SQLAlchemy async ORM
- The backend connects using `DATABASE_URL` with SQLAlchemy `create_async_engine`

### Tables

#### `users`
- `id` (UUID primary key)
- `email`, `username`
- `password_hash`
- `is_active`
- `created_at`, `updated_at`

#### `crops`
- `id` (UUID primary key)
- `name`
- `scientific_name`
- `description`
- `image_url`

#### `diseases`
- `id` (UUID primary key)
- `crop_id` (foreign key to `crops.id`)
- `name`
- `scientific_name`
- `description`
- `severity`
- `symptoms` (JSON)
- `remedies` (JSON)
- `prevention` (JSON)

#### `predictions`
- `id` (UUID primary key)
- `user_id` (foreign key to `users.id`)
- `image_url` (MinIO object path)
- `selected_crop`
- `disease_name`
- `confidence`
- `severity`
- `remedies` (JSON)
- `created_at`

### Relationships

- `User` has many `Prediction`
- `Crop` has many `Disease`
- `Prediction` links to a user and stores an inferred disease

### Migration system

- Alembic is configured in `backend/alembic/env.py`
- Initial schema is defined in `backend/alembic/versions/86a26a697cc9_initial_tables.py`
- The second revision file in `backend/alembic/versions/1a9664c08f6e_initial_tables.py` is empty, indicating a placeholder or aborted migration

### Seed loading

- `backend/app/seed.py` populates the `crops` and `diseases` tables with application-specific metadata
- It is intended to be run after the database schema exists

---

## API Documentation

| Method | Route | Purpose | Request | Response |
|---|---|---|---|---|
| GET | `/api/v1/health` | Health check | none | `status`, `app`, `version` |
| POST | `/api/v1/auth/register` | Create user | `email`, `username`, `password` | `status`, `message` |
| POST | `/api/v1/auth/login` | Login and get tokens | `email`, `password` | `access_token`, `refresh_token`, `token_type` |
| POST | `/api/v1/auth/refresh` | Refresh access token | `refresh_token` | `access_token`, `token_type` |
| POST | `/api/v1/auth/logout` | Logout current user | Bearer token | `status`, `message` |
| POST | `/api/v1/predict` | Submit leaf image for disease prediction | multipart `image`, `crop_type`, Bearer token | `PredictionResponse` |
| GET | `/api/v1/history` | Paginated prediction history | `page`, `per_page`, Bearer token | `PaginatedHistory` |
| GET | `/api/v1/history/{prediction_id}` | Single prediction detail | Bearer token | `PredictionHistoryItem` |
| GET | `/api/v1/crops` | List supported crops | Bearer token optional | list of `CropResponse` |
| GET | `/api/v1/diseases/{crop_name}` | List diseases for a crop | Bearer token optional | list of `DiseaseResponse` |

### Prediction request semantics

- `POST /api/v1/predict` expects a file upload, validates image, checks crop membership, and performs model inference.
- The backend currently caches prediction results by SHA-256 image hash and returns cached results when available.
- The `crop_type` field is stored with the prediction but is not currently applied to filter output from the disease classifier.

### Authentication rules

- Protected routes use `Authorization: Bearer <access_token>`.
- Access tokens expire after 15 minutes by default.
- Refresh tokens expire after 7 days.
- The backend is designed to support token blacklisting, but logout does not currently add the token to the blacklist in its implementation.

### Error handling

Common API errors are represented by `AppException` and include:
- `INVALID_CREDENTIALS`
- `AUTH_EXPIRED`
- `TOKEN_REVOKED`
- `USER_EXISTS`
- `USER_NOT_FOUND`
- `INVALID_IMAGE`
- `IMAGE_TOO_LARGE`
- `INVALID_CROP`
- `RATE_LIMIT`
- `PREDICTION_FAILED`

---

## Frontend Architecture

### Pages and user flow

1. `SplashScreen` loads first and currently redirects to `/login`.
2. `LoginScreen` authenticates users.
3. `RegisterScreen` creates new users.
4. `HomeScreen` displays supported crops and starts scanning.
5. `CameraScreen` captures or selects an image.
6. `ResultScreen` shows prediction details.
7. `HistoryScreen` lists previous predictions.

### Component hierarchy

- `main.dart` → initializes the app
- `config/routes.dart` → defines route-to-screen mapping
- `providers/` → state management layer using Riverpod
- `services/` → API communication layer using Dio and secure storage
- `screens/` → UI pages that consume providers and services

### State and API integration

- Authentication state is centralized in `AuthNotifier`
- Prediction and crop data flow are managed by `PredictionNotifier` and `HistoryNotifier`
- Network requests are routed through `ApiService`
- `AuthService` stores tokens and resolves login/register flows
- `PredictionService` handles multipart image upload and query operations

### Notable frontend-level features

- Automatic JWT attachment to requests via Dio interceptor
- Token refresh flow triggered on 401 responses
- Image upload using `image_picker`
- Crop selection and dynamic route parameter handling via GoRouter
- Presigned image URL usage for history items
- Basic error and loading state handling

### UI / UX notes

- The app uses a green/earth-tone theme tuned for plant/health imagery
- Current implementation is functional but has room for polish in splash and result flows
- There is no enforced authentication check on splash screen before navigation

---

## ML / DL Architecture and Pipeline

### Intended architecture

The repository is designed around a 3-gate inference pipeline:
1. **Gate 1**: leaf detector (leaf vs non-leaf)
2. **Gate 2**: species classifier (14 crops)
3. **Gate 3**: disease classifier (38 disease classes)

### Current runtime pipeline

At present, the backend runtime pipeline uses only the disease classifier model located in `ml/models/plant_disease_model.keras`.

The training and model artifact repos show an intended or in-progress enhancement toward a full multi-gate system.

### Gate 1 details

- Training script: `ml/gate1_leaf_detector_training.py`
- Base architecture: `MobileNetV2` pretrained on ImageNet
- Output: `gate_1/leaf_detector.keras` and `gate_1/leaf_detector.tflite`
- Problem solved: rejects non-leaf inputs before they reach disease classification

### Gate 2 details

- Training script: `ml/gate2_species_classifier_training.py`
- Base architecture: `EfficientNetB0` pretrained on ImageNet
- Output: `gate_2/species_classifier.keras`, `gate_2/species_classifier.tflite`, `gate_2/species_labels.json`
- Problem solved: validates the selected crop/species and reduces cross-crop errors

### Gate 3 details (current backend model)

- Model file: `ml/models/plant_disease_model.keras`
- Label file: `ml/models/labels.json`
- Input preprocessing: `224x224` RGB images, EfficientNet-style normalization
- Output: top disease class plus top-5 predictions

### Training flow and methodology

Gate 1 and Gate 2 scripts implement:
- dataset discovery from Kaggle input folders
- `.webp` conversion and data cleaning
- class balancing via oversampling/undersampling
- TensorFlow dataset pipelines with caching and prefetching
- data augmentation and transfer learning
- two-phase training (frozen base, then fine-tune last layers)
- training history plots, classification reports, confusion matrices
- final artifact saving and TFLite export

### Current ML artifacts in repo

- `ml/models/plant_disease_model.keras`
- `gate_1/leaf_detector.keras`
- `gate_1/leaf_detector.tflite`
- `gate_2/species_classifier.keras`
- `gate_2/species_classifier.tflite`
- `gate_2/species_labels.json`
- `ml/models/labels.json`

---

## Environment Setup

### Required software

- Python 3.11+ for backend
- Flutter SDK 3.11.1-compatible
- Dart SDK 3.11.1-compatible
- Android SDK / Android Studio for frontend build
- Docker and Docker Compose for backend infrastructure
- PostgreSQL client (optional for direct DB access)
- `git` for version control

### Backend setup

1. Install Python 3.11+.
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   .\\venv\\Scripts\\activate
   ```
3. Install Python dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
4. Configure `backend/.env`.
5. Start backend infrastructure:
   ```bash
   docker compose -f backend/docker-compose.yml up -d
   ```
6. Run database migrations:
   ```bash
   cd backend
   alembic upgrade head
   ```
7. Seed initial crop/disease data:
   ```bash
   python -m app.seed
   ```
8. Start the FastAPI app:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend setup

1. Install Flutter and Android toolchain.
2. Navigate to `frontend/`.
3. Install packages:
   ```bash
   flutter pub get
   ```
4. Run the app on an Android emulator or device:
   ```bash
   flutter run
   ```

### Notes

- The frontend expects `API_BASE_URL` in `frontend/.env` and defaults to `http://localhost:8000/api/v1`.
- The backend `.env` points to local services; if Docker Compose runs on the same machine, these values are correct.
- The backend model path currently points to `../ml/models/plant_disease_model.keras` and is relative to `backend/`.

---

## Current Development Status

### Completed modules

- Backend FastAPI server with user authentication, prediction endpoint, history endpoint, and crop/disease lookup
- PostgreSQL schema and async engine setup
- Redis cache/rate-limit integration
- MinIO storage integration for image uploads
- Flutter app screens for login/register/home/camera/result/history
- API integration from Flutter to backend
- Single-gate disease prediction inference using TensorFlow
- ML training scripts for leaf detection and species classification
- Seed data and domain-specific crop/disease metadata

### Partially completed / in-progress modules

- **Multi-gate inference pipeline** is conceptually present via ML scripts, but the backend currently only uses the disease classifier model.
- **Frontend auth flow** is partially incomplete; `SplashScreen` does not auto-detect logged-in users.
- **Logout implementation** is functionally returning success but not blacklisting tokens.
- **Prediction filtering by crop** is missing in the backend inference logic.
- **History pagination UX** is implemented at the API level but the frontend currently loads only one page without infinite scrolling.
- **Token refresh** exists in the Dio interceptor but may need validation for robustness.

### Observed issues and blockers

- The backend validates `crop_type` but does not filter inference results by crop, which means wrong crop predictions can still be returned.
- `backend/docker-compose.yml` covers infrastructure only; the app is not containerized there.
- The frontend splash logic bypasses token persistence, causing repeated logins.
- The logout endpoint does not actually invalidate the access token in Redis.
- There is no top-level `README.md` for the full repository; project guides are split into multiple markdown files.

### Project maturity assessment

- Core MVP is implemented and broadly functional.
- The project is in a hybrid state between prototype and production-ready: backend and frontend work together, but architecture improvements and robustness are still needed.
- The ML pipeline is stronger on the training side than on the runtime integration side.

---

## Development History and Inferred Context

### Likely development progression

1. Built a single-stage plant disease classification backend using TensorFlow and FastAPI.
2. Added Flutter mobile frontend for authentication, cropping, image upload, and prediction display.
3. Added Redis and MinIO support for caching and image storage.
4. Detected accuracy and crop-selection issues, then began refining the ML pipeline with the 3-gate approach.
5. Created training scripts for leaf detection and crop species classification, but full integration remains pending.
6. Added rich documentation and phase guides across multiple `.md` files.

### Current focus areas

- Improving model reliability by implementing gate-based validation
- Hardening authentication/session handling
- Polishing the mobile UI and improving UX
- Finalizing deployment and service orchestration

---

## Recommended Next Actions

1. **Fix backend crop-based filtering**
   - Use `crop_type` to restrict the disease classifier output to the selected crop's diseases.
   - Re-normalize confidences after filtering.

2. **Integrate gate 1 and gate 2 into inference flow**
   - Add a lightweight leaf detector before disease prediction
   - Add species validation before disease classification using `gate_2/species_classifier.keras`
   - Reject or warn when selected crop and predicted species mismatch

3. **Restore persistent auth flow in frontend**
   - Update `SplashScreen` to detect stored access token
   - Navigate to `/home` when valid, otherwise `/login`
   - Add token expiration handling and clear expired credentials

4. **Complete logout token invalidation**
   - Implement `blacklist_token()` on logout with token TTL
   - Ensure refresh token cannot be used after logout if intended

5. **Verify token refresh interceptor**
   - Test 401 refresh behavior end-to-end
   - Add fallback to force login if refresh fails

6. **Improve history UX**
   - Add paging or infinite scroll to `HistoryScreen`
   - Expose better feedback when no history exists

7. **Consolidate repository documentation**
   - Add a top-level `README.md` summarizing installation, architecture, and run commands
   - Link `backend_installation_guide.md`, `frontend_installation_guide.md`, and phase documents

8. **Finalize deployment strategy**
   - Decide whether to containerize the backend app
   - Add a Dockerfile for backend and optionally a Compose service
   - Add CI/CD workflow if target deployment is production

---

## Important files by role

### `backend/requirements.txt`

Purpose:
- Lists all Python dependencies for the backend service
- Includes FastAPI, SQLAlchemy async support, TensorFlow, Redis, MinIO, Celery, and JWT/auth libraries

Usage:
- Install with `pip install -r backend/requirements.txt`

### `backend/docker-compose.yml`

Purpose:
- Launch PostgreSQL, Redis, and MinIO dependencies in Docker

How it connects:
- Backend `.env` points to these services on localhost
- No backend or frontend service is defined here

### `backend/.env`

Purpose:
- Runtime configuration for backend services
- Must be present for local development

### `backend/app/main.py`

Purpose:
- App startup and shutdown lifecycle
- Register routes and CORS
- Load Redis, MinIO, and ML model

### `backend/app/config.py`

Purpose:
- Central settings class for the backend
- Loads environment values from `.env`

### `backend/app/database.py`

Purpose:
- Async SQLAlchemy engine and session management
- Base ORM definition

### `backend/app/services/ml_service.py`

Purpose:
- Model load and prediction logic
- Image preprocessing and label decoding

### `backend/app/routers/auth.py`

Purpose:
- Handle user auth workflows and token generation

### `backend/app/routers/predict.py`

Purpose:
- Execute the main inference workflow for leaf image prediction

### `backend/app/routers/history.py`

Purpose:
- Fetch and return prediction history records

### `backend/app/routers/crops.py`

Purpose:
- Expose crop and disease catalog data

### `backend/app/utils/redis_client.py`

Purpose:
- Rate limiting, caching, and token blacklist support

### `backend/app/utils/minio_client.py`

Purpose:
- Upload leaf images and generate presigned URLs

### `backend/app/seed.py`

Purpose:
- Insert crop/disease metadata into the database

### `frontend/pubspec.yaml`

Purpose:
- Flutter dependency manifest

### `frontend/lib/main.dart`

Purpose:
- Flutter app entry point and router initialization

### `frontend/lib/config/routes.dart`

Purpose:
- Define screen navigation paths

### `frontend/lib/config/api_config.dart`

Purpose:
- API route and base URL definitions

### `frontend/lib/services/api_service.dart`

Purpose:
- HTTP networking with auth token handling

### `frontend/lib/services/auth_service.dart`

Purpose:
- Login/register/logout logic and secure storage

### `frontend/lib/services/prediction_service.dart`

Purpose:
- Prediction API and history API calls

### `frontend/lib/providers/auth_provider.dart`

Purpose:
- Manage authentication state

### `frontend/lib/providers/prediction_provider.dart`

Purpose:
- Manage prediction request state, crop list, and history

### `frontend/lib/screens/*.dart`

Purpose:
- UI screens for login, register, home, camera, results, history, splash

### `ml/gate1_leaf_detector_training.py`

Purpose:
- Training script for leaf vs non-leaf detection

### `ml/gate2_species_classifier_training.py`

Purpose:
- Training script for 14-class species classification

---

## Summary

This repository is an AI-driven plant disease detection system with a working backend and mobile frontend. It is currently functional for authenticated users submitting leaf images and retrieving disease predictions, but it has architectural gaps in the ML inference pipeline and auth/session flow.

The project is anchored by a strong dataset and ML training story, with training artifacts for a broader 3-gate pipeline in progress, while the runtime path currently remains a simplified disease classifier flow.

`PROJECT_FULL_CONTEXT.md` is now the single-source summary for the repo and should be used as the onboarding and handover document for future work.
