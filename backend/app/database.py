import aiosqlite
import json
import logging
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any
from backend.app.config import settings

logger = logging.getLogger(__name__)

@asynccontextmanager
async def get_db():
    async with aiosqlite.connect(settings.DATABASE_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        yield conn

async def init_db():
    """Initializes tables and indexes in SQLite."""
    async with get_db() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                source TEXT,
                author TEXT,
                description TEXT,
                content TEXT,
                url TEXT UNIQUE,
                url_to_image TEXT,
                published_at TEXT,
                category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id TEXT NOT NULL,
                persona TEXT NOT NULL,
                executive_summary TEXT NOT NULL,
                what_happened TEXT NOT NULL,
                why_it_matters TEXT NOT NULL,
                jargon_demystified TEXT NOT NULL,
                key_takeaways TEXT NOT NULL,
                market_sentiment TEXT DEFAULT 'Neutral',
                sentiment_score REAL DEFAULT 0.5,
                read_time TEXT DEFAULT '1 min read',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(article_id, persona),
                FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
            );
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS bookmarks (
                article_id TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
            );
        """)

        await conn.commit()

        # Schema migrations for analysis mode and model tracking
        try:
            await conn.execute("ALTER TABLE summaries ADD COLUMN mode TEXT DEFAULT 'financial_news'")
            await conn.commit()
        except Exception:
            pass

        try:
            await conn.execute("ALTER TABLE summaries ADD COLUMN model_used TEXT DEFAULT 'llama-3.3-70b-versatile'")
            await conn.commit()
        except Exception:
            pass

        logger.info("SQLite database schema initialized successfully.")

async def save_article(article: Dict[str, Any]):
    async with get_db() as conn:
        await conn.execute("""
            INSERT INTO articles (id, title, source, author, description, content, url, url_to_image, published_at, category)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title=excluded.title,
                description=excluded.description,
                content=excluded.content,
                url_to_image=excluded.url_to_image,
                category=excluded.category;
        """, (
            article.get("id"),
            article.get("title"),
            article.get("source"),
            article.get("author"),
            article.get("description"),
            article.get("content"),
            article.get("url"),
            article.get("url_to_image"),
            article.get("published_at"),
            article.get("category", "business")
        ))
        await conn.commit()

async def save_articles_batch(articles: List[Dict[str, Any]]):
    async with get_db() as conn:
        for article in articles:
            await conn.execute("""
                INSERT INTO articles (id, title, source, author, description, content, url, url_to_image, published_at, category)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title=excluded.title,
                    description=excluded.description,
                    content=excluded.content,
                    url_to_image=excluded.url_to_image,
                    category=excluded.category;
            """, (
                article.get("id"),
                article.get("title"),
                article.get("source"),
                article.get("author"),
                article.get("description"),
                article.get("content"),
                article.get("url"),
                article.get("url_to_image"),
                article.get("published_at"),
                article.get("category", "business")
            ))
        await conn.commit()

async def get_article(article_id: str) -> Optional[Dict[str, Any]]:
    async with get_db() as conn:
        cursor = await conn.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None

async def get_articles(limit: int = 15, category: Optional[str] = None, query: Optional[str] = None) -> List[Dict[str, Any]]:
    async with get_db() as conn:
        sql = "SELECT a.*, (b.article_id IS NOT NULL) AS is_bookmarked FROM articles a LEFT JOIN bookmarks b ON a.id = b.article_id WHERE 1=1"
        params: List[Any] = []

        if category and category.lower() != "all":
            sql += " AND LOWER(a.category) = ?"
            params.append(category.lower())

        if query and query.strip():
            sql += " AND (LOWER(a.title) LIKE ? OR LOWER(a.description) LIKE ?)"
            params.extend([f"%{query.lower()}%", f"%{query.lower()}%"])

        sql += " ORDER BY a.published_at DESC LIMIT ?"
        params.append(limit)

        cursor = await conn.execute(sql, tuple(params))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

async def save_summary(summary: Dict[str, Any]):
    async with get_db() as conn:
        await conn.execute("""
            INSERT INTO summaries (
                article_id, persona, executive_summary, what_happened, why_it_matters,
                jargon_demystified, key_takeaways, market_sentiment, sentiment_score, read_time,
                mode, model_used
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(article_id, persona) DO UPDATE SET
                executive_summary=excluded.executive_summary,
                what_happened=excluded.what_happened,
                why_it_matters=excluded.why_it_matters,
                jargon_demystified=excluded.jargon_demystified,
                key_takeaways=excluded.key_takeaways,
                market_sentiment=excluded.market_sentiment,
                sentiment_score=excluded.sentiment_score,
                read_time=excluded.read_time,
                mode=excluded.mode,
                model_used=excluded.model_used;
        """, (
            summary["article_id"],
            summary.get("persona", "retail_investor"),
            summary["executive_summary"],
            summary["what_happened"],
            summary["why_it_matters"],
            json.dumps(summary.get("jargon_demystified", {})),
            json.dumps(summary.get("key_takeaways", [])),
            summary.get("market_sentiment", "Neutral"),
            summary.get("sentiment_score", 0.5),
            summary.get("read_time", "1 min read"),
            summary.get("mode", "financial_news"),
            summary.get("model_used", settings.GROQ_MODEL)
        ))
        await conn.commit()

async def get_summary(article_id: str, persona: str = "retail_investor") -> Optional[Dict[str, Any]]:
    async with get_db() as conn:
        cursor = await conn.execute(
            "SELECT * FROM summaries WHERE article_id = ? AND persona = ?", 
            (article_id, persona)
        )
        row = await cursor.fetchone()

        if row:
            res = dict(row)
            res["jargon_demystified"] = json.loads(res.get("jargon_demystified") or "{}")
            res["key_takeaways"] = json.loads(res.get("key_takeaways") or "[]")
            res["mode"] = res.get("mode") or "financial_news"
            res["model_used"] = res.get("model_used") or settings.GROQ_MODEL
            return res
        return None

async def toggle_bookmark(article_id: str) -> bool:
    async with get_db() as conn:
        cursor = await conn.execute("SELECT 1 FROM bookmarks WHERE article_id = ?", (article_id,))
        exists = await cursor.fetchone()
        if exists:
            await conn.execute("DELETE FROM bookmarks WHERE article_id = ?", (article_id,))
            await conn.commit()
            return False
        else:
            await conn.execute("INSERT INTO bookmarks (article_id) VALUES (?)", (article_id,))
            await conn.commit()
            return True

async def get_bookmarks() -> List[Dict[str, Any]]:
    async with get_db() as conn:
        cursor = await conn.execute("""
            SELECT a.*, 1 AS is_bookmarked 
            FROM articles a 
            JOIN bookmarks b ON a.id = b.article_id 
            ORDER BY b.created_at DESC
        """)
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

async def get_db_stats() -> Dict[str, Any]:
    async with get_db() as conn:
        cursor = await conn.execute("SELECT COUNT(*) as count FROM articles")
        articles_count = (await cursor.fetchone())["count"]
        cursor = await conn.execute("SELECT COUNT(*) as count FROM summaries")
        summaries_count = (await cursor.fetchone())["count"]
        cursor = await conn.execute("SELECT COUNT(*) as count FROM bookmarks")
        bookmarks_count = (await cursor.fetchone())["count"]
        return {
            "articles_count": articles_count,
            "summaries_count": summaries_count,
            "bookmarks_count": bookmarks_count,
            "connected": True
        }
