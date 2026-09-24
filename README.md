# FinNews AI – Financial News Simplifier 📈🤖

> An AI-powered financial intelligence and news simplification platform designed to transform complex financial terminology, macroeconomic reports, and market jargon into clear, accessible, and reader-friendly insights.

Powered by **FastAPI**, **NewsAPI**, and **Groq's LLaMA 3.3-70B Versatile**, FinNews AI bridges the gap between intricate Wall Street developments and everyday readers, students, retail investors, and busy executives.

---

## 🏛️ System Architecture

FinNews AI implements a high-performance **Client-Server REST Architecture**:

```
 ┌────────────┐               HTTP / JSON                ┌─────────────────┐
 │    User    │ ────────► ┌───────────────────┐ ───────► │ FastAPI Backend │
 └────────────┘           │   Web Frontend    │          │    (Python)     │
                          │ (HTML5/CSS3/JS)   │ ◄─────── └────────┬────────┘
                          └───────────────────┘                   │
                                    ▲                             │
                                    │                     ┌───────┴───────┐
                          Displays Simplified Data        │               │
                                                          ▼               ▼
                                                   ┌─────────────┐ ┌─────────────┐
                                                   │   NewsAPI   │ │  Groq API   │
                                                   │(Real-Time)  │ │ (LLaMA 3.3) │
                                                   └─────────────┘ └─────────────┘
                                                                  ▲
                                                                  │
                                                           ┌──────┴──────┐
                                                           │   SQLite    │
                                                           │  Database   │
                                                           └─────────────┘
```

1. **Web Frontend (Vanilla HTML5, CSS3, ES6+ JavaScript)**:
   - Interactive FinTech dark-mode dashboard with real-time continuous ticker ribbon.
   - 1-Click **"⚡ Fetch & Simplify News"** primary action.
   - Persona / Scenario selector tabs (Retail Investor, Student, Busy Pro, High Volatility).
   - In-card toggle between **"✨ FinNews AI Simplified"** and **"📰 Original Source"**.
   - Interactive Demystified Jargon chips with tooltip definitions.
   - Web Speech API integration for hands-free audio narration (🔊 Read Aloud).
   - Custom article/text simplifier modal & bookmark management.

2. **FastAPI Backend (`backend/app/`)**:
   - High-throughput asynchronous REST API with CORS middleware and Pydantic validation.
   - **Groq LLaMA 3.3-70B Versatile** inference engine with tailored prompt engineering for each scenario persona.
   - **NewsAPI Integration** with fallback curated real-world financial news feed for zero-config offline/demo readiness.
   - **SQLite Database** (`aiosqlite`) for caching AI summaries, storing fetched articles, and managing user bookmarks.
   - In-memory & `.env` runtime API key management via `/api/health/keys`.

---

## 👥 4 Real-World Scenarios Supported

| Scenario / Persona | Target Audience | AI Simplification Strategy |
| :--- | :--- | :--- |
| **📈 Retail Investor** | Everyday individual investors, 401(k) holders | Focuses on company valuations, stock sectors, price momentum, and portfolio considerations without Wall Street jargon. |
| **🎓 Finance Student** | College & university students | Translates interest rate shifts, macroeconomic theories, and central bank transmission mechanisms into intuitive concepts with clear analogies. |
| **⏱️ Busy Professional** | Executives, founders, managers | 60-Second Executive Briefing prioritizing capital allocation (CapEx), free cash flow margins, and board-level risk factors. |
| **⚡ High Volatility** | Traders & market participants during spikes | Rapid intelligence on market-moving catalysts, liquidation cascades, order book liquidity, and critical support levels. |

---

## 🧠 5 AI Prompt Engineering Task Modes

| Task Mode | Core Objective | Prompt Focus |
| :--- | :--- | :--- |
| **📰 Financial News Simplification** | Layman Translation | Converts dense financial reporting into plain English while preserving exact numbers, dates, and percentages. |
| **📊 Market Event Explanation** | Causal Breakdown | Details the triggering catalyst, how sectors reacted, and what forward indicators desks are monitoring. |
| **🏛️ Economic News Summarization** | Macro Mechanics | Unpacks Fed rate decisions, inflation indices (CPI/PPI/PCE), and the macroeconomic transmission channel. |
| **🏢 Business News Interpretation** | Corporate Health | Analyzes quarterly earnings, CapEx investments, operational margins, and enterprise competitive moats. |
| **✨ Jargon-Free Content Generation** | Wall Street Demystifier | Strips away Wall Street jargon and replaces technical terms with intuitive real-world analogies. |

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+ (Tested on Python 3.12.10)
- Modern web browser (Chrome, Edge, Safari, Firefox)

### 2. Installation

Clone or open the repository folder:
```bash
cd "Nascom"
```

Install the backend dependencies:
```bash
pip install -r backend/requirements.txt
```

### 3. Environment Variables (Optional)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

*(Note: FinNews AI comes with an intelligent fallback engine that includes rich financial news datasets and heuristic analysis. You can start immediately even before adding your keys, or input them directly via the UI Settings modal).*

To connect to live external APIs, configure:
```ini
GROQ_API_KEY=gsk_your_groq_api_key_here
NEWS_API_KEY=your_newsapi_org_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

### 4. Running the Application

Launch using the root runner:
```bash
python run.py
```
Or directly with Uvicorn:
```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open your browser at:
- **Web Dashboard**: `http://localhost:8000`
- **Swagger Interactive API Documentation**: `http://localhost:8000/docs`
- **System Health Status**: `http://localhost:8000/api/health`

---

## 🧪 Automated Testing

Run the full pytest test suite:
```bash
python -m pytest tests/test_api.py -v
```

All 8 tests cover:
- Health check diagnostics & model verification
- News listing & category filtering
- Scenario metadata resolution
- Single article AI simplification
- Multi-persona contextual adaptation (Retail vs Student vs Pro vs Volatility)
- Custom user-submitted financial text simplification
- Bookmark persistence & lifecycle
- Batch "Fetch & Simplify" processing

---

## 📡 API Reference

### 1. `GET /api/health`
Returns system diagnostics, database record count, and API connectivity status for Groq and NewsAPI.

### 2. `GET /api/news`
Fetches financial news articles with optional filters:
- `category` (`all`, `macro`, `markets`, `tech`, `crypto`, `economy`)
- `query` (search keyword)
- `limit` (default: 12)
- `persona` (attaches cached persona summary if available)

### 3. `POST /api/news/simplify`
Generates or retrieves a reader-friendly summary using LLaMA 3.3-70B.
```json
{
  "article_id": "art_fed_rates_2026",
  "persona": "retail_investor",
  "force_refresh": false
}
```

Or submit custom text:
```json
{
  "title": "Fed Minutes Signal Potential Pause in Balance Sheet Runoff",
  "content": "Dense central bank text...",
  "persona": "student"
}
```

### 4. `POST /api/news/fetch-and-simplify`
1-Click batch processing: retrieves top articles and generates LLaMA 3.3 summaries simultaneously.

### 5. `POST /api/news/bookmark/{article_id}`
Toggles bookmark state for an article.

### 6. `GET /api/news/bookmarks`
Returns all bookmarked articles.

### 7. `POST /api/health/keys`
Updates runtime API keys and synchronizes `.env` safely.

---

## 🛠️ Technology Stack
- **Backend**: FastAPI, Uvicorn, Pydantic V2, aiosqlite
- **Generative AI**: Groq API (`llama-3.3-70b-versatile`), Custom FinTech Prompt Engineering
- **News Provider**: NewsAPI.org & Curated Macroeconomic Dataset
- **Database**: SQLite
- **Frontend**: Vanilla HTML5, CSS3 (Modern dark-mode glassmorphism, responsive grid), Vanilla JavaScript (Web Speech API, Fetch API, DOM manipulation)
- **Testing**: Pytest, FastAPI TestClient

---

## 📄 License
This project is open-source and intended for educational and financial information purposes.
#   F i n a n c i a l - N e w s - S i m p l i f i e r  
 