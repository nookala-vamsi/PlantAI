# 🚀 Phase 5 — Integration & Deployment

> **Goal:** Dockerize all services, connect frontend to backend, test end-to-end, and ensure every teammate can run the project with a single command.
>
> **Estimated Time:** 3–5 days | **Who:** Entire team

---

## Step 1: Dockerize Each Service

### 1.1 What Is Docker and Why Do You Need It?
Docker packages your application along with ALL its dependencies (Python version, libraries, system tools) into a **container** — a lightweight, isolated environment that runs identically on every machine.

**Without Docker:** "It works on my laptop" → teammate installs different Python version → different TensorFlow version → models don't load → 2 days wasted debugging.

**With Docker:** Everyone runs the same container → identical environment → zero setup issues.

### 1.2 Backend Dockerfile

Create a Dockerfile for the FastAPI backend that does the following:
1. Start from a Python 3.11 base image
2. Set the working directory inside the container
3. Copy `requirements.txt` and install all Python dependencies
4. Copy the entire backend source code
5. Copy the trained ML models into the container (or mount them as a volume)
6. Expose port 8000
7. Define the startup command: run Uvicorn (the ASGI server) with FastAPI

### 1.3 Nginx Dockerfile/Config

Create an Nginx configuration that:
1. Listens on port 80
2. Forwards all `/api/` requests to the FastAPI backend (port 8000)
3. Sets appropriate proxy headers (X-Real-IP, X-Forwarded-For)
4. Configures rate limiting (10 requests/minute per IP for the predict endpoint)
5. Sets maximum upload size to 10 MB (for image uploads)

### 1.4 What Doesn't Need a Dockerfile
These services use **official pre-built images** from Docker Hub:
- PostgreSQL → `postgres:15-alpine`
- Redis → `redis:7-alpine`
- MinIO → `minio/minio`

You just configure them in Docker Compose (no custom Dockerfile needed).

---

## Step 2: Docker Compose — Orchestrate Everything

### 2.1 What Docker Compose Does
Docker Compose lets you define ALL your services (backend, database, redis, nginx, minio, celery) in a single YAML file and start them all with one command.

### 2.2 Services to Define

**1. nginx** (Reverse Proxy)
- Uses the Nginx config from Step 1.3
- Maps port 80 on host → port 80 in container
- Depends on: backend (won't start until backend is ready)

**2. backend** (FastAPI)
- Built from the backend Dockerfile
- Reads environment variables from `.env` file
- Mounts the trained models directory as a volume (so you can update models without rebuilding the container)
- Depends on: postgres, redis (waits for them to be ready)

**3. celery_worker** (Background Tasks)
- Uses the SAME Dockerfile as backend (same code, different startup command)
- Startup command: `celery -A app.tasks worker --loglevel=info`
- Depends on: redis, backend

**4. postgres** (Database)
- Official PostgreSQL 15 Alpine image
- Environment: database name, username, password (from `.env`)
- Volume: persists data to a named volume (data survives container restarts)
- Maps port 5432

**5. redis** (Cache + Broker)
- Official Redis 7 Alpine image
- Maps port 6379

**6. minio** (Image Storage)
- Official MinIO image
- Environment: root user and password (from `.env`)
- Volume: persists uploaded images
- Maps port 9000 (API) and 9001 (web console)

### 2.3 Service Dependencies & Startup Order
```
PostgreSQL ──┐
             ├──→ Backend ──→ Nginx
Redis ───────┤        │
             │        └──→ Celery Worker
MinIO ───────┘
```

Docker Compose's `depends_on` ensures services start in the right order.

---

## Step 3: Environment Variables

### 3.1 Create `.env.example`
This file lists ALL required environment variables with placeholder values. Every teammate copies it to `.env` and fills in their own values.

**Variables to include:**

| Variable | Example Value | Purpose |
|---|---|---|
| `DB_HOST` | `postgres` | Database hostname (service name in Docker) |
| `DB_PORT` | `5432` | Database port |
| `DB_NAME` | `plantdisease` | Database name |
| `DB_USER` | `admin` | Database username |
| `DB_PASSWORD` | `your_secure_password` | Database password |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection string |
| `JWT_SECRET_KEY` | `your_random_secret_key` | Secret for signing JWT tokens |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Access token lifetime |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime |
| `MINIO_ENDPOINT` | `minio:9000` | MinIO address |
| `MINIO_ROOT_USER` | `minioadmin` | MinIO username |
| `MINIO_ROOT_PASSWORD` | `your_minio_password` | MinIO password |
| `MODEL_PATH` | `/app/ml_models` | Path to trained models inside container |

### 3.2 Important Security Rules
- `.env` is in `.gitignore` — NEVER commit it to Git
- `.env.example` IS committed — it shows what variables are needed (with dummy values)
- Each teammate generates their own `JWT_SECRET_KEY` (any random 64-character string)
- Database and MinIO passwords should be different for each teammate (local dev)

---

## Step 4: Connect Flutter to Backend

### 4.1 Finding the Backend URL

**For Android Emulator:**
- The emulator can't use `localhost` (that refers to the emulator itself)
- Use `10.0.2.2` — this special IP maps to the host machine's localhost
- Backend URL: `http://10.0.2.2:80/api/v1`

**For Physical Device (same WiFi):**
- Find your laptop's local IP (e.g., `192.168.1.105`)
- Backend URL: `http://192.168.1.105:80/api/v1`

**For iOS Simulator:**
- Use `localhost` directly
- Backend URL: `http://localhost:80/api/v1`

### 4.2 Configuration
- Store the base URL in a config file in the Flutter project
- Make it configurable (dev vs production) so you can switch environments easily

---

## Step 5: End-to-End Testing

### 5.1 Test the Full Flow
After everything is connected, test each scenario:

**Scenario 1 — Happy Path:**
1. Register a new user
2. Login with those credentials
3. Select "Potato" crop
4. Upload a clear potato leaf image with early blight
5. Verify: result shows "Early Blight" with high confidence + remedies
6. Check history — the prediction should appear

**Scenario 2 — Non-Leaf Rejection:**
1. Login
2. Select any crop
3. Upload a photo of a car/dog/phone
4. Verify: response says "This doesn't look like a leaf"

**Scenario 3 — Species Mismatch:**
1. Login
2. Select "Potato" crop
3. Upload a tomato leaf image
4. Verify: response says "This doesn't look like a Potato leaf. It appears to be a Tomato leaf."

**Scenario 4 — Auth Flow:**
1. Login → get tokens
2. Wait 15+ minutes (or manually expire the access token)
3. Make a prediction request
4. Verify: the JWT interceptor auto-refreshes the token and the request succeeds
5. Logout → try making a request → should get 401

**Scenario 5 — Edge Cases:**
1. Upload a very large image (>10 MB) → should get "Image too large" error
2. Upload a non-image file (rename a .txt to .jpg) → should get "Invalid image" error
3. Try rapid-fire predictions → should get rate-limited after 10/minute

### 5.2 API Testing with Swagger
- FastAPI auto-generates interactive API docs at `http://localhost:80/docs`
- Use this to test endpoints independently of the Flutter app
- Useful for debugging: if something fails in Flutter, test the same request in Swagger to isolate whether it's a frontend or backend issue

---

## Step 6: Teammate Onboarding

### 6.1 What a Teammate Needs to Install
Only **3 things:**
1. **Git** — to clone the repo
2. **Docker Desktop** — to run all services
3. **Flutter SDK** — to run the mobile app (only needed for the frontend developer)

That's it. No Python, no PostgreSQL, no Redis, no manual setup.

### 6.2 Steps for a Teammate to Run the Project

**Step 1:** Clone the repository
```
git clone <repo-url>
cd plant-disease-ai
```

**Step 2:** Create the environment file
```
cp .env.example .env
# Edit .env with your own passwords (any values work for local dev)
```

**Step 3:** Download the trained models
- The trained model files (.h5) are large (100+ MB) — they shouldn't be in Git
- Host them on Google Drive, Dropbox, or Git LFS
- Download and place them in `ml/models/`

**Step 4:** Start all backend services
```
cd docker
docker-compose up --build
```
Wait for all services to start (first time takes 5–10 minutes to download images and build).

**Step 5:** Run the Flutter app
```
cd mobile
flutter pub get
flutter run
```

**Done!** The entire backend stack is running in Docker, and the Flutter app connects to it.

### 6.3 Model File Sharing Strategy
Since `.h5` model files are too large for Git:

| Option | How | Best For |
|---|---|---|
| **Google Drive** | Upload models to shared Drive folder, teammates download | Small teams |
| **Git LFS** | Git extension for large files | If repo host supports it |
| **DVC (Data Version Control)** | Version-controlled model storage | Professional ML projects |
| **Shared network drive** | Place models on campus shared drive | Same campus team |

> [!TIP]
> For a college project, **Google Drive** is the simplest. Create a shared folder, upload the 3 `.h5` files, and share the link in the project README.

---

## Step 7: Common Issues & Troubleshooting

| Issue | Cause | Fix |
|---|---|---|
| Docker Compose fails to start | Docker Desktop not running | Start Docker Desktop first |
| "Port 5432 already in use" | Local PostgreSQL running | Stop local PostgreSQL or change the port in `.env` |
| Backend can't connect to DB | Database not ready yet | Add health check in Compose, or just restart |
| Flutter can't reach backend | Wrong base URL | Use `10.0.2.2` for emulator, local IP for physical device |
| Model loading fails | Models not in the expected path | Check `MODEL_PATH` in `.env` matches the volume mount |
| "Permission denied" on model files | Docker file permissions | Set proper file permissions or run as root in container |
| Out of memory during prediction | TensorFlow loading all 3 models | Use `tf.lite` models or increase Docker memory limit |
| Image upload fails | Nginx body size limit | Set `client_max_body_size 10M;` in nginx.conf |

---

## ✅ Phase 5 Checklist

- [ ] Backend Dockerfile created and builds successfully
- [ ] Nginx config created with proxy and rate limiting
- [ ] Docker Compose file orchestrates all 6 services
- [ ] `.env.example` created with all required variables
- [ ] `docker-compose up --build` starts everything successfully
- [ ] Flutter app connects to the Dockerized backend
- [ ] Scenario 1 (happy path) passes end-to-end
- [ ] Scenario 2 (non-leaf) passes
- [ ] Scenario 3 (species mismatch) passes
- [ ] Scenario 4 (auth flow) passes
- [ ] Scenario 5 (edge cases) passes
- [ ] Teammate onboarding documented in README
- [ ] Model files hosted on Google Drive with download link
- [ ] README has complete setup instructions

---

> **← Previous:** [Phase 4: Frontend](file:///C:/Users/vamsi/.gemini/antigravity/brain/7f085e6e-cd54-4d50-bbba-e2fa9de78b1c/artifacts/phase_4_frontend.md) | **🏠 Overview:** [Phase Overview](file:///C:/Users/vamsi/.gemini/antigravity/brain/7f085e6e-cd54-4d50-bbba-e2fa9de78b1c/artifacts/phase_0_overview.md)
