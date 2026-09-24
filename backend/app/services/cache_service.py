import logging
from typing import Optional, Dict, Any
from backend.app.database import get_summary, save_summary

logger = logging.getLogger(__name__)

class CacheService:
    @staticmethod
    async def get_cached_summary(article_id: str, persona: str) -> Optional[Dict[str, Any]]:
        try:
            summary = await get_summary(article_id, persona)
            if summary:
                logger.info(f"Cache hit for article {article_id} [persona: {persona}]")
                return summary
        except Exception as e:
            logger.warning(f"Cache lookup failed: {e}")
        return None

    @staticmethod
    async def store_summary(summary: Dict[str, Any]) -> None:
        try:
            await save_summary(summary)
            logger.info(f"Stored summary in SQLite cache for article {summary.get('article_id')}")
        except Exception as e:
            logger.error(f"Failed to store summary in cache: {e}")

cache_service = CacheService()
