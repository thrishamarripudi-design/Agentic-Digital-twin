"""
Agentic Digital Twin — FastAPI Backend Entry Point
Run with: uvicorn backend.main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import router

app = FastAPI(
    title="Agentic Digital Twin for Grocery Store Decision Making",
    description=(
        "A multi-agent AI system that builds a digital twin of a small grocery store "
        "and simulates future outcomes of business decisions. "
        "Supports what-if questions about inventory, loans, weather, and expansion."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
async def root():
    return {
        "name": "Agentic Digital Twin",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
