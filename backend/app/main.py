import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse

from backend.app.config import settings
from backend.app.database import init_db, get_db_stats
from backend.app.routers.news import router as news_router
from backend.app.routers.health import router as health_router
from backend.app.services.news_service import news_service

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("finnews_app")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    logger.info("Initializing FinNews AI backend...")
    await init_db()
    
    # Pre-populate database with initial articles if empty
    stats = await get_db_stats()
    if stats["articles_count"] == 0:
        logger.info("Database is empty. Pre-populating with initial financial articles...")
        await news_service.fetch_news(category="all", limit=6)
    
    yield
    # Shutdown actions
    logger.info("Shutting down FinNews AI backend...")

app = FastAPI(
    title="FinNews AI – Financial News Simplifier",
    description="AI-powered financial news simplification platform using Groq LLaMA 3.3-70B and NewsAPI.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(news_router)
app.include_router(health_router)

# Mount Frontend directory if present
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))

if os.path.isdir(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.api_route("/", methods=["GET", "HEAD"])
    async def serve_index():
        index_file = os.path.join(frontend_dir, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return JSONResponse({"message": "FinNews AI Backend is active. Frontend index.html not found."})

# Global error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global unhandled exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error occurred.",
            "detail": str(exc)
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
