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

from app.database import engine
from sqlalchemy import text

async def clear_prediction_history():
    print("⏳ Connecting to the database to clear prediction history...")
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("DELETE FROM predictions;"))
            print("✅ Deleted prediction records successfully!")
    except Exception as e:
        print(f"❌ Failed to clear database: {e}")
        return
        
    print("⏳ Connecting to Redis to clear cached predictions...")
    try:
        from app.utils.redis_client import redis_client
        await redis_client.connect()
        
        # Find all prediction cache keys
        keys = await redis_client._redis.keys("prediction:*")
        if keys:
            await redis_client._redis.delete(*keys)
            print(f"✅ Cleared {len(keys)} cached predictions from Redis!")
        else:
            print("✅ No cached predictions in Redis.")
            
        await redis_client.disconnect()
    except Exception as e:
        print(f"⚠️ Could not clear Redis cache: {e}")

if __name__ == "__main__":
    asyncio.run(clear_prediction_history())
