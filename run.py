#!/usr/bin/env python3
"""
FinNews AI – Launcher Script
Runs the FastAPI server with hot-reload and opens the application.
"""
import os
import sys
import uvicorn

def main():
    print("=" * 65)
    print("  FinNews AI – Financial News Simplifier")
    print("  AI Engine: Groq LLaMA 3.3-70B Versatile | Real-Time NewsAPI")
    print("=" * 65)
    print("  • Web Dashboard:  http://localhost:8000")
    print("  • Swagger Docs:   http://localhost:8000/docs")
    print("  • Health Status:  http://localhost:8000/api/health")
    print("=" * 65)

    # Ensure current directory is on PYTHONPATH
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
