import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from backend.app.database import (
    get_article,
    get_articles,
    get_summary,
    save_article,
    toggle_bookmark,
    get_bookmarks
)
from backend.app.services.news_service import news_service, generate_article_id
from backend.app.services.groq_service import groq_service, PERSONA_PROMPTS, TASK_PROMPTS
from backend.app.services.cache_service import cache_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/news", tags=["Financial News"])

class SimplifyRequest(BaseModel):
    article_id: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    source: Optional[str] = "Custom Submission"
    persona: str = "retail_investor"
    mode: str = "financial_news"
    force_refresh: bool = False

@router.get("", response_model=Dict[str, Any])
async def list_news(
    category: str = Query("all", description="Filter by category: all, markets, tech, crypto, macro, economy"),
    query: Optional[str] = Query(None, description="Search query keyword"),
    limit: int = Query(12, ge=1, le=50, description="Number of articles to retrieve"),
    persona: str = Query("retail_investor", description="Persona for attaching cached summaries"),
    refresh: bool = Query(False, description="Force refresh fresh live news")
):
    """
    Fetches real-time financial news articles, attaching cached simplified summaries if available.
    """
    try:
        articles = await news_service.fetch_news(category=category, query=query, limit=limit, force_refresh=refresh)
        
        # Attach summary to each article if already generated
        enriched = []
        for art in articles:
            summary = await get_summary(art["id"], persona)
            enriched.append({
                **art,
                "summary": summary
            })

        return {
            "success": True,
            "count": len(enriched),
            "category": category,
            "provider": news_service.get_provider_status(),
            "is_live_newsapi": news_service.is_configured(),
            "articles": enriched
        }
    except Exception as e:
        logger.error(f"Error listing news: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch financial news: {str(e)}"
        )

@router.post("/simplify", response_model=Dict[str, Any])
async def simplify_article_endpoint(payload: SimplifyRequest):
    """
    Transforms a complex financial news article into a reader-friendly simplified breakdown
    using Groq's LLaMA 3.3-70B Versatile model.
    """
    article_id = payload.article_id
    persona = payload.persona or "retail_investor"
    mode = payload.mode or "financial_news"

    # Case 1: Custom text submission
    if not article_id and payload.title and payload.content:
        custom_id = generate_article_id("custom://user-input", payload.title)
        article_data = {
            "id": custom_id,
            "title": payload.title,
            "source": payload.source or "User Submission",
            "author": "Analyst",
            "description": payload.content[:180] + "...",
            "content": payload.content,
            "url": f"local://custom/{custom_id}",
            "url_to_image": "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=800&q=80",
            "category": "custom"
        }
        await save_article(article_data)
        article_id = custom_id
        title = payload.title
        content = payload.content

    # Case 2: Existing article lookup
    elif article_id:
        article = await get_article(article_id)
        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Article with ID {article_id} not found."
            )
        title = article["title"]
        content = article.get("content") or article.get("description") or title

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide either an article_id or both title and content."
        )

    # Check cache unless force_refresh is requested
    if not payload.force_refresh:
        cached = await cache_service.get_cached_summary(article_id, persona)
        if cached:
            return {
                "success": True,
                "cached": True,
                "article_id": article_id,
                "summary": cached
            }

    # Generate new simplified summary via Groq / LLM
    try:
        summary_result = await groq_service.simplify_article(
            title=title,
            content=content,
            persona=persona,
            mode=mode,
            article_id=article_id
        )

        # Store in SQLite cache
        await cache_service.store_summary(summary_result)

        return {
            "success": True,
            "cached": False,
            "article_id": article_id,
            "summary": summary_result
        }
    except Exception as e:
        logger.error(f"Error simplifying article {article_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Simplification failed: {str(e)}"
        )

@router.post("/fetch-and-simplify", response_model=Dict[str, Any])
async def fetch_and_simplify(
    persona: str = Query("retail_investor", description="Target audience persona"),
    mode: str = Query("financial_news", description="Analysis prompt task mode"),
    category: str = Query("all", description="News category filter"),
    limit: int = Query(6, ge=1, le=10, description="Article count")
):
    """
    One-click action: Fetches top financial news and generates/retrieves simplified summaries.
    """
    try:
        articles = await news_service.fetch_news(category=category, limit=limit)
        enriched = []

        for art in articles:
            # Check cache or generate
            summary = await cache_service.get_cached_summary(art["id"], persona)
            if not summary:
                content = art.get("content") or art.get("description") or art["title"]
                summary = await groq_service.simplify_article(
                    title=art["title"],
                    content=content,
                    persona=persona,
                    mode=mode,
                    article_id=art["id"]
                )
                await cache_service.store_summary(summary)

            enriched.append({
                **art,
                "summary": summary
            })

        return {
            "success": True,
            "count": len(enriched),
            "persona": persona,
            "mode": mode,
            "category": category,
            "articles": enriched
        }
    except Exception as e:
        logger.error(f"Fetch & Simplify failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fetch & Simplify failed: {str(e)}"
        )

@router.post("/bookmark/{article_id}", response_model=Dict[str, Any])
async def toggle_article_bookmark(article_id: str):
    """Toggles bookmark for an article."""
    is_saved = await toggle_bookmark(article_id)
    return {
        "success": True,
        "article_id": article_id,
        "is_bookmarked": is_saved,
        "message": "Article saved to bookmarks." if is_saved else "Article removed from bookmarks."
    }

@router.get("/bookmarks", response_model=Dict[str, Any])
async def list_bookmarks():
    """Returns all bookmarked articles."""
    bookmarks = await get_bookmarks()
    return {
        "success": True,
        "count": len(bookmarks),
        "articles": bookmarks
    }

@router.get("/scenarios", response_model=Dict[str, Any])
async def list_scenarios():
    """
    Returns available persona scenarios and prompt analysis task modes with descriptions and use-cases.
    """
    return {
        "scenarios": [
            {
                "id": "retail_investor",
                "name": "Retail Investor",
                "icon": "📈",
                "tagline": "Stock Market & Portfolio Impact",
                "description": "Explains how market events impact company valuations, individual stocks, and retirement portfolios without Wall Street jargon."
            },
            {
                "id": "student",
                "name": "Finance Student",
                "icon": "🎓",
                "tagline": "Educational & Conceptual Deep-Dive",
                "description": "Translates interest rate shifts, macroeconomic theories, and central bank mechanics into intuitive, foundational learning concepts."
            },
            {
                "id": "professional",
                "name": "Busy Professional",
                "icon": "⏱️",
                "tagline": "60-Second Executive Briefing",
                "description": "Delivers laser-focused bottom-line takeaways, CapEx metrics, and corporate strategic impacts before your next meeting."
            },
            {
                "id": "volatility",
                "name": "High Volatility",
                "icon": "⚡",
                "tagline": "Rapid Risk & Catalyst Intelligence",
                "description": "Immediate breakdowns of sharp market drawdowns, liquidation cascades, and critical risk drivers during volatile sessions."
            }
        ],
        "modes": [
            {
                "id": "financial_news",
                "name": "Financial News Simplification",
                "icon": "📰",
                "description": "Transforms complex financial reporting into clear, accessible, and reader-friendly insights."
            },
            {
                "id": "market_event",
                "name": "Market Event Explanation",
                "icon": "📊",
                "description": "Analyzes market catalysts, cause-and-effect price swings, and sector reactions."
            },
            {
                "id": "economic",
                "name": "Economic News Summarization",
                "icon": "🏛️",
                "description": "Deconstructs Fed rate moves, inflation reports (CPI/PPI), and macroeconomic mechanisms."
            },
            {
                "id": "business",
                "name": "Business News Interpretation",
                "icon": "🏢",
                "description": "Interprets corporate earnings, capital expenditures (CapEx), and strategic competitive moats."
            },
            {
                "id": "jargon_free",
                "name": "Jargon-Free Content Generation",
                "icon": "✨",
                "description": "Strips out Wall Street slang, converting complex concepts into intuitive everyday analogies."
            }
        ]
    }
