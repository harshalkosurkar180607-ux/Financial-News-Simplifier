# FinNews AI — Financial News Simplifier 📈🤖

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python Version" />
  <img src="https://img.shields.io/badge/FastAPI-0.110.0-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/AI-Groq%20LLaMA%203.3--70B-f55036?style=for-the-badge&logo=meta&logoColor=white" alt="Groq LLaMA 3.3" />
  <img src="https://img.shields.io/badge/Database-SQLite%203-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License" />
</p>

> **FinNews AI** is an AI-powered financial intelligence and news simplification platform designed to transform complex financial terminology, macroeconomic reports, and Wall Street jargon into clear, accessible, and reader-friendly insights.

Powered by **FastAPI**, **NewsAPI**, and **Groq's LLaMA 3.3-70B Versatile**, FinNews AI bridges the gap between intricate market developments and everyday readers, students, retail investors, and busy executives.

---

## 📑 Table of Contents

- [FinNews AI — Financial News Simplifier 📈🤖](#finnews-ai--financial-news-simplifier-)
  - [📑 Table of Contents](#-table-of-contents)
  - [✨ Key Features](#-key-features)
  - [🏛️ System Architecture](#️-system-architecture)
  - [👥 4 Real-World Persona Scenarios](#-4-real-world-persona-scenarios)
  - [🧠 5 AI Prompt Engineering Task Modes](#-5-ai-prompt-engineering-task-modes)
  - [📁 Project Structure](#-project-structure)
  - [🚀 Quick Start Guide](#-quick-start-guide)
    - [1. Prerequisites](#1-prerequisites)
    - [2. Installation](#2-installation)
    - [3. Configure Environment Variables](#3-configure-environment-variables)
    - [4. Running the Application](#4-running-the-application)
  - [📡 API Documentation](#-api-documentation)
  - [🧪 Automated Testing](#-automated-testing)
  - [🛠️ Technology Stack](#️-technology-stack)
  - [📄 License](#-license)

---

## ✨ Key Features

- **⚡ 1-Click "Fetch & Simplify"**: Seamlessly fetches the latest market news and synthesizes AI summaries in batch or on-demand.
- **👥 Multi-Persona Simplification**: Tailors summaries across 4 distinct audiences (*Retail Investor*, *Finance Student*, *Busy Professional*, and *High Volatility Trader*).
- **💡 Interactive Jargon Demystifier**: Automatically identifies and extracts complex financial terms (e.g., *Yield Curve Inversion*, *CapEx*, *Liquidity Crunch*) with hoverable plain-English tooltips.
- **🔊 Web Speech Audio Narration**: Built-in text-to-speech for hands-free audio listening directly inside the dashboard.
- **🔄 Dual-View Comparison**: Instant toggling between the raw original news source and the AI-simplified explanation.
- **📊 Real-Time Market Ticker Ribbon**: Continuous live market indices ticker (`S&P 500`, `NASDAQ`, `DOW`, `BRENT`, `GOLD`, `BTC`).
- **🔖 Bookmark Management**: Save and organize important news stories with local persistence.
- **🛡️ Resilient Smart Fallbacks**: Zero-config readiness with built-in curated market datasets when offline or when third-party rate limits are reached.

---

## 🏛️ System Architecture

FinNews AI implements a high-throughput **Client-Server REST Architecture**:

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
                                                   │ (Real-Time) │ │ (LLaMA 3.3) │
                                                   └─────────────┘ └─────────────┘
                                                                  ▲
                                                                  │
                                                           ┌──────┴──────┐
                                                           │   SQLite    │
                                                           │  Database   │
                                                           └─────────────┘
```

1. **Web Frontend (Vanilla HTML5, CSS3, ES6+ JavaScript)**:
   - Modern FinTech dark-mode dashboard with smooth glassmorphism and micro-animations.
   - Scenario & persona selector tabs with persistent state.
   - Interactive modal for testing custom user-submitted financial text.
   - Real-time API key settings management directly from the UI.

2. **FastAPI Backend (`backend/app/`)**:
   - Asynchronous endpoints powered by `FastAPI` and `Uvicorn` with CORS middleware.
   - **Groq LLaMA 3.3-70B Versatile** engine with dedicated system prompts per persona.
   - **SQLite Database** (`aiosqlite`) for caching AI summaries, storing fetched articles, and managing bookmarks.
   - Built-in schema validation via **Pydantic V2**.

---

## 👥 4 Real-World Persona Scenarios

| Persona / Scenario | Target Audience | AI Simplification Strategy |
| :--- | :--- | :--- |
| **📈 Retail Investor** | Everyday individual investors, 401(k) holders | Focuses on company valuations, stock sectors, price momentum, and portfolio considerations without Wall Street jargon. |
| **🎓 Finance Student** | College & university students | Translates interest rate shifts, macroeconomic theories, and central bank transmission mechanisms into intuitive concepts with clear analogies. |
| **⏱️ Busy Professional** | Executives, founders, managers | 60-Second Executive Briefing prioritizing capital allocation (CapEx), free cash flow margins, and board-level risk factors. |
| **⚡ High Volatility** | Traders & market participants | Rapid intelligence on market-moving catalysts, liquidation cascades, order book liquidity, and critical support levels. |

---

## 🧠 5 AI Prompt Engineering Task Modes

| Task Mode | Core Objective | Prompt Focus |
| :--- | :--- | :--- |
| **📰 Financial News Simplification** | Layman Translation | Converts dense financial reporting into plain English while preserving exact numbers, dates, and percentages. |
| **📊 Market Event Explanation** | Causal Breakdown | Details the triggering catalyst, how sectors reacted, and what forward indicators desks are monitoring. |
| **🏛️ Economic News Summarization** | Macro Mechanics | Unpacks Fed rate decisions, inflation indices (CPI/PPI/PCE), and the macroeconomic transmission channel. |
| **🏢 Business News Interpretation** | Corporate Health | Analyzes quarterly earnings, CapEx investments, operational margins, and enterprise competitive moats. |
| **✨ Jargon-Free Content Generation** | Wall Street Demystifier | Strips away technical barriers and replaces jargon with intuitive, real-world analogies. |

---

## 📁 Project Structure

```
Financial-News-Simplifier/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py             # Environment settings & API keys
│   │   ├── database.py           # SQLite database schema & seed data
│   │   ├── main.py               # FastAPI application entry & middleware
│   │   ├── models.py             # Pydantic schemas & response models
│   │   ├── routers/
│   │   │   ├── health.py         # System health & API key sync
│   │   │   └── news.py           # News fetching, simplification & bookmarks
│   │   └── services/
│   │       ├── cache_service.py  # Local summary caching
│   │       ├── groq_service.py   # Groq LLaMA 3.3 inference & prompt engineering
│   │       └── news_service.py   # NewsAPI client & fallback curated news
│   └── requirements.txt          # Python dependencies
├── frontend/
│   ├── index.html                # Modern dashboard HTML layout
│   ├── styles.css                # Dark-mode glassmorphic styling
│   └── app.js                    # Dynamic frontend application logic
├── tests/
│   └── test_api.py               # Comprehensive pytest test suite (8 tests)
├── .env.example                  # Template configuration file
├── .gitignore                    # Git ignore file (excludes secrets & db)
├── README.md                     # Project documentation
└── run.py                        # Root launcher script
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Python**: Version 3.10 or higher (Tested on Python 3.12)
- **Web Browser**: Any modern browser (Google Chrome, Microsoft Edge, Mozilla Firefox, Safari)

### 2. Installation

Clone the repository and enter the directory:
```bash
git clone https://github.com/harshalkosurkar180607-ux/Financial-News-Simplifier.git
cd Financial-News-Simplifier
```

Install the required Python dependencies:
```bash
pip install -r backend/requirements.txt
```

### 3. Configure Environment Variables

Create your local `.env` configuration:
```bash
copy .env.example .env
```
*(On Linux/macOS, use `cp .env.example .env`)*

Configure your API keys in `.env` (optional — smart fallback mode is active by default):
```ini
GROQ_API_KEY=gsk_your_groq_api_key_here
NEWS_API_KEY=your_newsapi_org_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

> **Note**: FinNews AI includes an intelligent fallback mechanism with curated financial news datasets. You can run and test the application immediately even without external API keys, or enter them directly through the UI **Settings (⚙️)** dialog.

### 4. Running the Application

Launch the server using the root script:
```bash
python run.py
```

Or launch directly with Uvicorn:
```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

Once running, navigate to:
- 🌐 **Web Dashboard**: [http://localhost:8000](http://localhost:8000)
- 📖 **Interactive Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- 🩺 **Health Check Diagnostics**: [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

## 📡 API Documentation

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Returns system diagnostics, active AI model, database statistics, and external API status. |
| `GET` | `/api/news` | Fetches financial news articles with optional filters (`category`, `query`, `limit`, `persona`). |
| `POST` | `/api/news/simplify` | Generates a persona-tailored simplified explanation for an article ID or custom user text. |
| `POST` | `/api/news/fetch-and-simplify` | Batch fetches top news articles and generates AI summaries simultaneously. |
| `POST` | `/api/news/bookmark/{article_id}` | Toggles bookmark status for a specific article. |
| `GET` | `/api/news/bookmarks` | Returns all currently bookmarked articles. |
| `POST` | `/api/health/keys` | Safely updates runtime API keys and synchronizes `.env`. |

### Example Request: Simplify an Article

**Endpoint:** `POST /api/news/simplify`

```json
{
  "article_id": "art_fed_rates_2026",
  "persona": "retail_investor",
  "force_refresh": false
}
```

### Example Request: Simplify Custom Text

**Endpoint:** `POST /api/news/simplify`

```json
{
  "title": "ECB Signals Rate Plateau Amid Tightening Lending Conditions",
  "content": "The Governing Council noted that previous rate hikes continue to be transmitted forcefully into financing conditions, creating upward pressure on private sector borrowing costs...",
  "persona": "student"
}
```

---

## 🧪 Automated Testing

The project includes an automated test suite verifying all core API contracts, AI persona adaptations, and persistence:

```bash
python -m pytest tests/test_api.py -v
```

**Test Coverage Summary:**
- ✔️ System health diagnostics & model verification
- ✔️ News retrieval & category filtering (`macro`, `markets`, `tech`, `crypto`)
- ✔️ Persona metadata resolution
- ✔️ Single article AI simplification & caching
- ✔️ Multi-persona contextual adaptation (Retail vs Student vs Pro vs Volatility)
- ✔️ Custom user-submitted financial text simplification
- ✔️ Bookmark persistence & lifecycle
- ✔️ Batch "Fetch & Simplify" pipeline

---

## 🛠️ Technology Stack

- **Backend Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Asynchronous Python REST API)
- **ASGI Server**: [Uvicorn](https://www.uvicorn.org/)
- **Large Language Model (LLM)**: [Groq Cloud](https://groq.com/) — `llama-3.3-70b-versatile`
- **Data Validation**: [Pydantic V2](https://docs.pydantic.dev/)
- **Database / Cache**: [SQLite 3](https://www.sqlite.org/) via `aiosqlite`
- **Frontend**: Vanilla HTML5, Modern CSS3 (Glassmorphism & Flexbox/Grid), ES6+ JavaScript
- **Audio Synthesis**: Native Browser [Web Speech API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API)
- **Testing**: [Pytest](https://docs.pytest.org/) & FastAPI TestClient

---

## 📄 License

This project is open-source and licensed under the [MIT License](https://opensource.org/licenses/MIT).