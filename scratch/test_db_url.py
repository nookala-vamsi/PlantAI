import os
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))

from app.config import get_settings
from sqlalchemy.engine.url import make_url

settings = get_settings()
print(f"DATABASE_URL in settings: {settings.DATABASE_URL}")

try:
    url = make_url(settings.DATABASE_URL)
    print(f"Parsed Host: {url.host}")
    print(f"Parsed Port: {url.port}")
    print(f"Parsed Username: {url.username}")
    print(f"Parsed Password: {url.password}")
except Exception as e:
    print(f"Failed to parse URL: {e}")
