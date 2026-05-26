# 🛠️ Backend Phase — Installation Guide

> Everything you need to install **before** writing any backend code.

---

## Overview: What Are We Installing?

The backend needs **3 categories** of tools:

| Category | Tools | Purpose |
|---|---|---|
| **Language** | Python 3.10+ | Write the backend code |
| **Services** | PostgreSQL, Redis, MinIO | Database, caching, image storage |
| **Python Packages** | FastAPI, TensorFlow, etc. | Libraries used in our code |

### Two Ways to Install Services

| Approach | How | Best For |
|---|---|---|
| **Docker (Recommended)** | Run PostgreSQL, Redis, MinIO inside Docker containers | Cleanest — no clutter on your system |
| **Native** | Install each service directly on Windows | If you can't use Docker |

**I recommend Docker** — one `docker-compose up` command starts everything. No manual configuration, no version conflicts, easy to delete later.

---

## 1. Python 3.10+ (Required)

### What is it?
The programming language we're writing the backend in.

### Why 3.10+?
FastAPI and TensorFlow require Python 3.10 or higher. Some features we use (like `match` statements and improved type hints) need 3.10+.

### Install
1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Download **Python 3.11.x** (stable and well-supported)
3. During installation, **check "Add Python to PATH"** ← IMPORTANT
4. Check "Install pip" (should be checked by default)

### Verify
```powershell
python --version
# Should show: Python 3.11.x

pip --version
# Should show: pip 24.x.x from ...
```

---

## 2. Docker Desktop (Recommended)

### What is it?
Docker lets you run applications inside **containers** — like lightweight virtual machines. Instead of installing PostgreSQL, Redis, and MinIO directly on your Windows machine (messy), you run them inside Docker containers (clean and isolated).

### Why do we need it?
| Without Docker | With Docker |
|---|---|
| Install PostgreSQL manually | `docker-compose up` — done |
| Install Redis (not officially supported on Windows!) | Runs perfectly in Docker |
| Install MinIO manually | Runs perfectly in Docker |
| Uninstalling is messy | `docker-compose down` — everything gone |
| Version conflicts with other projects | Each project has its own containers |

### Install
1. Go to [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/)
2. Download **Docker Desktop for Windows**
3. Install and restart your computer
4. Open Docker Desktop — let it start the Docker Engine

> [!IMPORTANT]
> Docker Desktop requires **WSL 2** (Windows Subsystem for Linux). During installation, it may ask you to enable WSL 2. Follow the prompts — it'll guide you through.

### Verify
```powershell
docker --version
# Should show: Docker version 27.x.x

docker compose version
# Should show: Docker Compose version v2.x.x
```

---

## 3. PostgreSQL (Database)

### What is it?
A relational database. Think of it like Excel spreadsheets but for applications — you store data in **tables** with rows and columns, and query it using SQL.

### Why do we need it?
We store 4 things in the database:

| Table | What It Stores |
|---|---|
| **Users** | Email, username, hashed password, account status |
| **Predictions** | Every disease prediction — image URL, disease name, confidence, remedies |
| **Crops** | The 14 supported crop species with descriptions |
| **Diseases** | The 38 diseases with symptoms, remedies, severity |

### Install

**With Docker (recommended):** No manual install needed — Docker handles it. We'll define it in `docker-compose.yml`.

**Without Docker (native):**
1. Go to [postgresql.org/download/windows](https://www.postgresql.org/download/windows/)
2. Download the installer (EDB)
3. Install with default settings
4. Remember the password you set for the `postgres` user
5. Default port: **5432**

### Verify (native only)
```powershell
psql --version
# Should show: psql (PostgreSQL) 16.x
```

---

## 4. Redis (Cache & Message Broker)

### What is it?
An **in-memory data store** — like a super-fast dictionary that lives in RAM. It stores key-value pairs and can automatically delete them after a set time (TTL = Time To Live).

### Why do we need it?
Redis does **4 jobs** in our backend:

| Job | How It Works |
|---|---|
| **JWT Blacklisting** | When a user logs out, we store their token ID in Redis. On every request, we check: "Is this token blacklisted?" Since Redis is in-memory, this check takes <1ms. |
| **Prediction Caching** | Before running the ML model, we hash the image and check Redis: "Have we seen this exact image before?" If yes, return the cached result instantly (skip the model). |
| **Rate Limiting** | We store a counter per user: "User X has made 7 requests this minute." If it hits 10, we block further requests. The counter auto-resets after 60 seconds (TTL). |
| **Celery Broker** | Celery (background task queue) uses Redis as its message broker — FastAPI puts tasks into Redis, Celery workers pick them up. |

### Install

**With Docker (recommended):** No manual install needed.

**Without Docker (native):**
> [!WARNING]
> Redis is **NOT officially supported on Windows**. You'd need to use unofficial ports or WSL. This is a major reason to use Docker.

If you must:
1. Install WSL 2 (Windows Subsystem for Linux)
2. Inside WSL: `sudo apt install redis-server`
3. Start Redis: `sudo service redis-server start`
4. Default port: **6379**

### Verify
```powershell
# If using Docker (after docker-compose up):
docker exec -it redis redis-cli ping
# Should show: PONG
```

---

## 5. MinIO (Image Storage)

### What is it?
An **object storage server** — like a private Amazon S3 on your machine. It stores files (images, documents, etc.) and gives each file a unique URL.

### Why do we need it?
When a user uploads a leaf image for prediction:
1. We save the original image in MinIO (so the user can view it later in their prediction history)
2. MinIO gives us a URL like `http://minio:9000/leaf-images/user123/img_001.jpg`
3. We store that URL in the database alongside the prediction result

### Why not just save to disk?
| Saving to disk | Using MinIO |
|---|---|
| Files tied to one server | Works across multiple servers |
| No access control | Built-in permissions and policies |
| No web UI to browse files | Web dashboard at `localhost:9001` |
| Can't scale | S3-compatible — switch to AWS S3 in production with zero code changes |

### Install

**With Docker (recommended):** No manual install needed.

**Without Docker (native):**
1. Go to [min.io/download](https://min.io/download)
2. Download the Windows binary
3. Run: `minio server C:\minio-data --console-address ":9001"`
4. Default API port: **9000**, Console port: **9001**

---

## 6. Python Packages

These are installed with `pip` inside a **virtual environment** (isolated from your system Python).

### Create Virtual Environment First
```powershell
cd F:\ML_PROJECT
python -m venv venv
.\venv\Scripts\activate
```

> [!IMPORTANT]
> Always activate the virtual environment (`.\venv\Scripts\activate`) before installing packages or running the backend. You'll see `(venv)` in your terminal prompt when it's active.

### All Packages Explained

#### Core Framework

| Package | What It Does |
|---|---|
| **fastapi** | The web framework — handles HTTP requests, routing, validation. Like Express.js for Python but faster and with automatic API documentation. |
| **uvicorn[standard]** | ASGI server — actually runs the FastAPI app and listens for HTTP requests. Think of FastAPI as the blueprint and Uvicorn as the engine. |
| **pydantic[email-validator]** | Data validation — defines the shape of request/response bodies. If a user sends invalid data, Pydantic rejects it automatically before your code runs. |
| **python-multipart** | Handles file uploads — when a user uploads an image, this package parses the multipart form data. |
| **python-dotenv** | Loads environment variables from a `.env` file — keeps secrets (DB password, JWT key) out of code. |

#### Database

| Package | What It Does |
|---|---|
| **sqlalchemy[asyncio]** | ORM (Object-Relational Mapper) — lets you interact with PostgreSQL using Python classes instead of raw SQL. The `asyncio` extra enables async database queries (non-blocking). |
| **asyncpg** | The actual PostgreSQL driver for async Python — SQLAlchemy uses this under the hood to talk to PostgreSQL. |
| **alembic** | Database migration tool — tracks changes to your database schema (add a column, rename a table) and applies them safely. Like Git but for your database structure. |

#### Authentication

| Package | What It Does |
|---|---|
| **python-jose[cryptography]** | JWT (JSON Web Token) library — creates and verifies the tokens that authenticate users. When a user logs in, we generate a JWT. On every request, we verify it. |
| **passlib[bcrypt]** | Password hashing — converts plain passwords into irreversible hashes using bcrypt. Even if the database is leaked, passwords can't be recovered. |
| **bcrypt** | The actual bcrypt algorithm that passlib uses. Installed separately to ensure compatibility. |

#### ML / Image Processing

| Package | What It Does |
|---|---|
| **tensorflow** | Loads and runs the trained `.keras` model for disease prediction. This is the big one (~500 MB install). |
| **Pillow** | Image processing — opens, resizes, and converts uploaded images before feeding them to the model. |
| **numpy** | Numerical computing — the model's input/output are numpy arrays. TensorFlow depends on it. |

#### Caching & Background Tasks

| Package | What It Does |
|---|---|
| **redis[hiredis]** | Python client for Redis — our code uses this to read/write to Redis. The `hiredis` extra is a C-based parser that makes Redis operations faster. |
| **celery** | Background task queue — runs heavy tasks (like batch exports, cleanup) without blocking the API. Uses Redis as its message broker. |

#### Storage

| Package | What It Does |
|---|---|
| **minio** | Python client for MinIO — our code uses this to upload/download images from the MinIO server. |

#### Utilities

| Package | What It Does |
|---|---|
| **aiofiles** | Async file operations — reads/writes files without blocking the event loop. Used when saving temporary uploads. |
| **httpx** | Async HTTP client — if we ever need to call external APIs (e.g., weather data for farming tips). Better than `requests` because it supports async. |

---

## 7. Install Everything

### Step 1: Python + Virtual Environment
```powershell
cd F:\ML_PROJECT
python -m venv venv
.\venv\Scripts\activate
```

### Step 2: Install All Python Packages
```powershell
pip install fastapi uvicorn[standard] pydantic[email-validator] python-multipart python-dotenv sqlalchemy[asyncio] asyncpg alembic python-jose[cryptography] passlib[bcrypt] bcrypt tensorflow Pillow numpy redis[hiredis] celery minio aiofiles httpx
```

### Step 3: Docker Services (PostgreSQL + Redis + MinIO)
We'll create a `docker-compose.yml` file when we start coding. One command starts everything:
```powershell
docker compose up -d
```

### Verify Python Packages
```powershell
pip list | findstr "fastapi uvicorn sqlalchemy tensorflow redis celery"
```

---

## Summary Checklist

- [ ] Python 3.10+ installed and in PATH
- [ ] Docker Desktop installed and running
- [ ] Virtual environment created (`python -m venv venv`)
- [ ] Virtual environment activated (`.\venv\Scripts\activate`)
- [ ] All Python packages installed via pip
- [ ] Docker services will start when we create `docker-compose.yml`

> [!TIP]
> You don't need to install PostgreSQL, Redis, or MinIO natively. Docker runs them all. The only things installed directly on your Windows machine are **Python** and **Docker Desktop**.
