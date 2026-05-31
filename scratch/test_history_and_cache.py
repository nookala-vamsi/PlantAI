import sys
import os
import asyncio
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).resolve().parents[1] / "backend"
sys.path.append(str(backend_dir))

# Mock settings/env vars
os.environ["DATABASE_URL"] = "postgresql+asyncpg://plantai:plantai_secret@localhost:5432/plantai_db"
os.environ["JWT_SECRET_KEY"] = "mock-jwt-secret-key-for-testing"

from app.config import get_settings

async def verify_backend_settings():
    settings = get_settings()
    print("Settings check:")
    print(f"ACCESS_TOKEN_EXPIRE_MINUTES: {settings.ACCESS_TOKEN_EXPIRE_MINUTES}")
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 60, "ACCESS_TOKEN_EXPIRE_MINUTES should be 60!"
    print("✅ ACCESS_TOKEN_EXPIRE_MINUTES is exactly 60!")

if __name__ == "__main__":
    asyncio.run(verify_backend_settings())
