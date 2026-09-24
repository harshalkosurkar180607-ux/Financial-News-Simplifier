import pytest
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from backend.app.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client

def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "ai_engine" in data
    assert "news_provider" in data
    assert "database" in data
    from backend.app.config import settings
    assert data["ai_engine"]["model"] in ["llama-3.3-70b-versatile", settings.GROQ_MODEL]

def test_list_news_articles(client):
    response = client.get("/api/news?category=all&limit=6")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "articles" in data
    assert len(data["articles"]) > 0
    first_article = data["articles"][0]
    assert "id" in first_article
    assert "title" in first_article
    assert "category" in first_article

def test_scenarios_endpoint(client):
    response = client.get("/api/news/scenarios")
    assert response.status_code == 200
    data = response.json()
    assert "scenarios" in data
    scenario_ids = [s["id"] for s in data["scenarios"]]
    assert "retail_investor" in scenario_ids
    assert "student" in scenario_ids
    assert "professional" in scenario_ids
    assert "volatility" in scenario_ids

def test_simplify_existing_article(client):
    news_res = client.get("/api/news?limit=1")
    article_id = news_res.json()["articles"][0]["id"]

    # Request simplification for retail_investor
    simplify_res = client.post("/api/news/simplify", json={
        "article_id": article_id,
        "persona": "retail_investor"
    })
    assert simplify_res.status_code == 200
    data = simplify_res.json()
    assert data["success"] is True
    summary = data["summary"]
    assert "executive_summary" in summary
    assert "what_happened" in summary
    assert "why_it_matters" in summary
    assert "jargon_demystified" in summary
    assert "key_takeaways" in summary
    assert "market_sentiment" in summary
    assert summary["persona"] == "retail_investor"

def test_simplify_different_persona_student(client):
    news_res = client.get("/api/news?limit=1")
    article_id = news_res.json()["articles"][0]["id"]

    # Test student persona
    simplify_res = client.post("/api/news/simplify", json={
        "article_id": article_id,
        "persona": "student"
    })
    assert simplify_res.status_code == 200
    data = simplify_res.json()
    assert data["summary"]["persona"] == "student"

def test_custom_article_simplification(client):
    custom_title = "Treasury Inverts 2s10s Curve Amid Unexpected Wholesale PPI Jump"
    custom_content = "Core Producer Price Index rose 0.5% month over month as commodity and shipping rates surged, prompting concerns that Federal Reserve officials will halt quantitative easing."
    
    response = client.post("/api/news/simplify", json={
        "title": custom_title,
        "content": custom_content,
        "persona": "volatility"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    summary = data["summary"]
    assert summary["persona"] == "volatility"
    assert "executive_summary" in summary

def test_bookmark_lifecycle(client):
    news_res = client.get("/api/news?limit=1")
    article_id = news_res.json()["articles"][0]["id"]

    # Bookmark article
    bm_res = client.post(f"/api/news/bookmark/{article_id}")
    assert bm_res.status_code == 200
    assert "is_bookmarked" in bm_res.json()

    # Verify article appears in bookmarks list
    bms_list = client.get("/api/news/bookmarks")
    assert bms_list.status_code == 200
    assert "articles" in bms_list.json()

def test_fetch_and_simplify_batch(client):
    response = client.post("/api/news/fetch-and-simplify?persona=professional&category=all&limit=3")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["persona"] == "professional"
    assert len(data["articles"]) > 0
    first = data["articles"][0]
    assert first["summary"] is not None
    assert first["summary"]["persona"] == "professional"
    assert "executive_summary" in first["summary"]

def test_prompt_analysis_modes(client):
    response = client.get("/api/news/scenarios")
    assert response.status_code == 200
    data = response.json()
    assert "modes" in data
    mode_ids = [m["id"] for m in data["modes"]]
    assert "financial_news" in mode_ids
    assert "market_event" in mode_ids
    assert "economic" in mode_ids
    assert "business" in mode_ids
    assert "jargon_free" in mode_ids

def test_analysis_mode_custom_execution(client):
    res = client.post("/api/news/simplify", json={
        "title": "Federal Reserve Holds Benchmark Fed Funds Rate Steady at 5.25%-5.50%",
        "content": "Federal Open Market Committee members noted ongoing progress on disinflation toward the 2% target, balancing maximum employment against lingering price pressures in services.",
        "persona": "student",
        "mode": "economic",
        "force_refresh": True
    })
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    summary = data["summary"]
    assert summary["mode"] == "economic"
    assert summary["persona"] == "student"
    assert "executive_summary" in summary
    assert "jargon_demystified" in summary
    assert len(summary["key_takeaways"]) > 0

