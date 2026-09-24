from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime

class ArticleBase(BaseModel):
    id: str
    title: str
    source: str
    author: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    url: str
    url_to_image: Optional[str] = None
    published_at: Optional[str] = None
    category: Optional[str] = "business"

class SimplifiedSummary(BaseModel):
    article_id: str
    persona: str = "retail_investor"  # retail_investor, student, professional, volatility
    executive_summary: str
    what_happened: str
    why_it_matters: str
    jargon_demystified: Dict[str, str] = Field(default_factory=dict)
    key_takeaways: List[str] = Field(default_factory=list)
    market_sentiment: str = "Neutral"  # Bullish, Bearish, Neutral
    sentiment_score: float = 0.5
    read_time: str = "1 min read"
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class ArticleWithSummary(ArticleBase):
    summary: Optional[SimplifiedSummary] = None
    is_bookmarked: bool = False

class FetchNewsRequest(BaseModel):
    category: Optional[str] = "all"
    query: Optional[str] = None
    limit: Optional[int] = 10

class SimplifyArticleRequest(BaseModel):
    article_id: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    source: Optional[str] = None
    url: Optional[str] = None
    persona: str = "retail_investor"

class ApiKeysUpdate(BaseModel):
    groq_api_key: Optional[str] = None
    news_api_key: Optional[str] = None

class HealthStatus(BaseModel):
    status: str
    groq_api: Dict[str, Any]
    news_api: Dict[str, Any]
    database: Dict[str, Any]
    model: str
    version: str
