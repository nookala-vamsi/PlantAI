# 🧪 Backend Testing Guide — Step by Step

> Follow these steps **in order** to run and test the entire backend locally.

---

## Prerequisites Checklist

Before starting, confirm:

- [x] Docker Desktop installed
- [x] Python 3.13 + virtual environment created (`F:\ML_PROJECT\venv\`)
- [x] All packages installed
- [x] Model files present in `F:\ML_PROJECT\ml\models\`
  - `plant_disease_model.keras` (30.4 MB)
  - `labels.json` (1.4 KB)

---

## Step 1: Open Docker Desktop

1. Launch **Docker Desktop** from your Start Menu
2. Wait until the Docker icon in the system tray shows **"Docker Desktop is running"**
3. You'll know it's ready when you can run this in PowerShell:

```powershell
docker info
```

If you see `Server: Docker Desktop`, you're good.

---

## Step 2: Start Docker Services

Open a **PowerShell terminal** and run:

```powershell
cd F:\ML_PROJECT\backend
docker compose up -d
```

This starts 3 services in the background:

| Service | Port | What It Does |
|---|---|---|
| PostgreSQL | 5432 | Database |
| Redis | 6379 | Cache + JWT blacklist |
| MinIO | 9000 (API), 9001 (Console) | Image storage |

### Verify they're running:

```powershell
docker compose ps
```

You should see all 3 containers as **"running"** with **(healthy)** status. Wait ~15 seconds for health checks to pass.

> [!WARNING]
> If any container fails, run `docker compose logs <service_name>` to check errors.
> Common issue: Port already in use → close the other app using that port.

---

## Step 3: Activate Virtual Environment

In the **same terminal** (or a new one):

```powershell
cd F:\ML_PROJECT\backend
& F:\ML_PROJECT\venv\Scripts\Activate.ps1
```

---

## Step 4: Run Database Migration

Create the 4 tables (Users, Predictions, Crops, Diseases):

```powershell
alembic revision --autogenerate -m "Initial tables"
alembic upgrade head
```

### What happens:
1. **First command:** Compares our SQLAlchemy models with the database → generates a migration script
2. **Second command:** Applies the migration → creates the tables

### Verify:
```powershell
docker exec plantai_postgres psql -U plantai -d plantai_db -c "\dt"
```

You should see:
```
         List of relations
 Schema |    Name     | Type  | Owner
--------+-------------+-------+--------
 public | crops       | table | plantai
 public | diseases    | table | plantai
 public | predictions | table | plantai
 public | users       | table | plantai
```

---

## Step 5: Seed the Database

Populate the Crops and Diseases tables with data:

```powershell
python -m app.seed
```

### Expected output:
```
🌱 Seeding database...
   ✅ Apple: 4 diseases
   ✅ Blueberry: 1 diseases
   ✅ Cherry: 2 diseases
   ✅ Corn: 4 diseases
   ✅ Grape: 4 diseases
   ✅ Orange: 1 diseases
   ✅ Peach: 2 diseases
   ✅ Pepper: 2 diseases
   ✅ Potato: 3 diseases
   ✅ Raspberry: 1 diseases
   ✅ Soybean: 1 diseases
   ✅ Squash: 1 diseases
   ✅ Strawberry: 2 diseases
   ✅ Tomato: 10 diseases

🎉 Seeded 14 crops with all diseases!
```

---

## Step 6: Start the FastAPI Server

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Expected output:
```
🚀 Starting PlantDiseaseAI backend...
✅ Redis connected
✅ MinIO connected
🧠 Loading model from ..\ml\models\plant_disease_model.keras...
✅ Model loaded!
✅ Labels loaded: 38 classes
🌿 PlantDiseaseAI v1.0.0 is ready!
INFO:     Uvicorn running on http://0.0.0.0:8000
```

> [!IMPORTANT]
> Keep this terminal open — the server runs here. Open a **new terminal** for testing, or use the browser.

---

## Step 7: Open Swagger UI

Open your browser and go to:

```
http://localhost:8000/docs
```

This opens FastAPI's **built-in API documentation** — you can test every endpoint directly from the browser. No extensions needed!

---

## Step 8: Test Each Endpoint

### 8.1 — Health Check ✅

1. Find `GET /api/v1/health` in the list
2. Click on it to expand
3. Click **"Try it out"** → **"Execute"**

**Expected response (200):**
```json
{
  "status": "healthy",
  "app": "PlantDiseaseAI",
  "version": "1.0.0"
}
```

---

### 8.2 — Register a User 👤

1. Find `POST /api/v1/auth/register`
2. Click **"Try it out"**
3. Replace the body with:

```json
{
  "email": "test@example.com",
  "username": "testuser",
  "password": "Test@1234"
}
```

4. Click **"Execute"**

**Expected (201):** `"Registration successful. You can now login."`

---

### 8.3 — Login 🔑

1. Find `POST /api/v1/auth/login`
2. Click **"Try it out"**
3. Enter:

```json
{
  "email": "test@example.com",
  "password": "Test@1234"
}
```

4. Click **"Execute"**

**Expected (200):**
```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "eyJhbGciOi...",
  "token_type": "bearer"
}
```

5. **COPY the `access_token` value** — you need it for the next steps!

---

### 8.4 — Authorize Swagger UI 🔓

To test protected endpoints (predict, history, logout), you need to add your token:

1. Scroll to the **top** of the Swagger page
2. Click the **"Authorize"** button (🔓 lock icon, top-right area)
3. In the **"Value"** field, type `Bearer ` followed by your access token:
   ```
   Bearer eyJhbGciOi...paste_your_full_token_here...
   ```
4. Click **"Authorize"** → **"Close"**

Now all protected endpoints will automatically include your JWT token!

> [!IMPORTANT]
> Make sure to type `Bearer ` (with a space) before the token. Example:
> `Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

---

### 8.5 — Predict Disease 🌿 (The Main Test!)

1. Find `POST /api/v1/predict`
2. Click **"Try it out"**
3. For **`crop_type`**: type `Tomato` (or whichever crop matches your image)
4. For **`image`**: click **"Choose File"** → select any leaf image from your computer
   - Use a tomato, potato, or apple leaf image for best results
   - If you don't have one, search Google for "tomato leaf disease" and save any image
5. Click **"Execute"**

**Expected (200):**
```json
{
  "id": "uuid-here",
  "image_url": "http://localhost:9000/...",
  "selected_crop": "Tomato",
  "result": {
    "disease_name": "Tomato___Early_blight",
    "confidence": 0.9423,
    "severity": "Medium",
    "remedies": ["Apply chlorothalonil fungicide", "..."],
    "symptoms": ["Dark brown concentric-ring spots", "..."],
    "prevention": ["Crop rotation (3 years)", "..."],
    "top_predictions": [...]
  },
  "created_at": "2026-05-12T..."
}
```

🎉 **If you see this, the entire pipeline works:** image upload → MinIO storage → ML prediction → database lookup → cached in Redis → saved to database!

---

### 8.6 — View Prediction History 📜

1. Find `GET /api/v1/history`
2. Click **"Try it out"** → **"Execute"**

**Expected:** Your previous prediction(s) appear in a paginated list.

---

### 8.7 — Browse Crops 🌾

1. Find `GET /api/v1/crops`
2. Click **"Try it out"** → **"Execute"**

**Expected:** List of all 14 crops with descriptions.

---

### 8.8 — Browse Diseases for a Crop 🦠

1. Find `GET /api/v1/diseases/{crop_name}`
2. Click **"Try it out"**
3. Type `Tomato` in the `crop_name` field
4. Click **"Execute"**

**Expected:** All 10 tomato diseases with symptoms, remedies, and severity.

---

### 8.9 — Token Refresh 🔄

1. Find `POST /api/v1/auth/refresh`
2. Click **"Try it out"**
3. Paste the `refresh_token` you got from login:

```json
{
  "refresh_token": "eyJhbGciOi...your_refresh_token_from_login..."
}
```

4. Click **"Execute"**

**Expected:** New access token.

---

### 8.10 — Logout 👋

1. Find `POST /api/v1/auth/logout`
2. Click **"Try it out"** → **"Execute"**

**Expected:** `"Logged out successfully."`

---

## Step 9: Check MinIO Console (Optional)

Open your browser:

```
http://localhost:9001
```

Login:
- **Username:** `minioadmin`
- **Password:** `minioadmin123`

You should see the `leaf-images` bucket with the image you uploaded during the predict test.

---

## Step 10: Shutting Down

### Stop the FastAPI server:
Press `Ctrl+C` in the terminal running uvicorn.

### Stop Docker services:
```powershell
cd F:\ML_PROJECT\backend
docker compose down
```

### To stop AND delete all data (fresh start):
```powershell
docker compose down -v
```
> The `-v` flag removes the data volumes (database, redis, minio). Only use this if you want a completely clean restart.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `docker compose up` fails | Make sure Docker Desktop is running |
| Port already in use | Close the app using that port, or change the port in `docker-compose.yml` |
| `alembic` command not found | Make sure venv is activated: `F:\ML_PROJECT\venv\Scripts\activate` |
| Model loading error | Verify files exist in `F:\ML_PROJECT\ml\models\` |
| Database connection refused | Wait 15s after `docker compose up` for PostgreSQL to initialize |
| Redis connection refused | Check `docker compose ps` — redis should show "healthy" |
| `ModuleNotFoundError` | Activate venv and ensure all packages installed |
