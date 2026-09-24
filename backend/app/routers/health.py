import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import APIRouter
from pydantic import BaseModel

from backend.app.config import settings
from backend.app.database import get_db_stats
from backend.app.services.news_service import news_service
from backend.app.services.groq_service import groq_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/health", tags=["Health & Diagnostics"])

class KeyUpdatePayload(BaseModel):
    groq_api_key: Optional[str] = None
    news_api_key: Optional[str] = None

@router.get("", response_model=Dict[str, Any])
async def health_check():
    """
    Returns full diagnostics: Database status, NewsAPI status, Groq LLaMA 3.3-70B status.
    """
    db_stats = await get_db_stats()
    groq_ready = groq_service.is_configured()
    news_ready = news_service.is_configured()

    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "ai_engine": {
            "provider": "Groq",
            "model": settings.GROQ_MODEL,
            "configured": groq_ready,
            "status": "Active (Live Groq LLaMA 3.3 70B)" if groq_ready else "Demo Mode (Intelligent Heuristic Fallback)"
        },
        "news_provider": {
            "provider": "NewsAPI + Live Financial Wire",
            "configured": True,
            "status": f"Active ({news_service.get_provider_status()})"
        },
        "database": db_stats
    }

@router.post("/keys", response_model=Dict[str, Any])
async def update_keys(payload: KeyUpdatePayload):
    """
    Updates API keys in runtime memory and .env file.
    """
    updated = []
    if payload.groq_api_key is not None:
        settings.GROQ_API_KEY = payload.groq_api_key.strip()
        groq_service.api_key = settings.GROQ_API_KEY
        updated.append("GROQ_API_KEY")

    if payload.news_api_key is not None:
        settings.NEWS_API_KEY = payload.news_api_key.strip()
        news_service.api_key = settings.NEWS_API_KEY
        updated.append("NEWS_API_KEY")

    # Persist changes to .env file safely
    try:
        env_lines = []
        if os.path.exists(".env"):
            with open(".env", "r") as f:
                env_lines = f.readlines()

        new_lines = []
        keys_written = set()
        for line in env_lines:
            if line.startswith("GROQ_API_KEY=") and payload.groq_api_key is not None:
                new_lines.append(f"GROQ_API_KEY={settings.GROQ_API_KEY}\n")
                keys_written.add("GROQ_API_KEY")
            elif line.startswith("NEWS_API_KEY=") and payload.news_api_key is not None:
                new_lines.append(f"NEWS_API_KEY={settings.NEWS_API_KEY}\n")
                keys_written.add("NEWS_API_KEY")
            else:
                new_lines.append(line)

        if "GROQ_API_KEY" not in keys_written and payload.groq_api_key is not None:
            new_lines.append(f"GROQ_API_KEY={settings.GROQ_API_KEY}\n")
        if "NEWS_API_KEY" not in keys_written and payload.news_api_key is not None:
            new_lines.append(f"NEWS_API_KEY={settings.NEWS_API_KEY}\n")

        with open(".env", "w") as f:
            f.writelines(new_lines)

    except Exception as e:
        logger.warning(f"Could not persist keys to .env: {e}")

    return {
        "success": True,
        "updated": updated,
        "groq_configured": groq_service.is_configured(),
        "news_configured": news_service.is_configured()
    }
