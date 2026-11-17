"""Application entry point for the FastAPI backend.

This module initializes the FastAPI application, configures CORS middleware
for frontend-backend communication, manages application lifespan (including
pre-warming solver pattern databases), mounts the API router, and exposes
root/health endpoints.
"""

from contextlib import asynccontextmanager
import logging
import os
import sys
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.api.routes import router
from app.solver.solver import get_algorithms

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("cubevi.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager.

    Pre-warms the solver heuristics (CornerPatternDatabase) upon startup
    so that user requests to solve cubes don't encounter cold-start latency.
    """
    logger.info("Initializing CubeVI backend...")
    logger.info("Pre-warming solver heuristics (Pattern Databases)...")
    start_t = time.perf_counter()
    get_algorithms()
    elapsed_ms = (time.perf_counter() - start_t) * 1000
    logger.info(f"Solver heuristics ready in {elapsed_ms:.1f}ms. CubeVI backend startup complete.")
    yield
    logger.info("CubeVI backend shutting down...")


app = FastAPI(
    title="CubeVI API",
    version="0.1.0",
    description=(
        "Backend API for CubeVI: An AI-based Rubik's Cube assistant providing "
        "step-by-step 2x2 cube solving, 3D simulation support, and state validation."
    ),
    lifespan=lifespan,
)

# Dynamic CORS configuration
# Reads allowed origins from CORS_ORIGINS env variable (comma-separated), e.g.:
# CORS_ORIGINS="https://cubevi.vercel.app,http://localhost:5173"
default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
env_origins = os.getenv("CORS_ORIGINS", "")
allowed_origins = [o.strip() for o in env_origins.split(",") if o.strip()] if env_origins else default_origins
allow_all = "*" in allowed_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all else allowed_origins,
    allow_origin_regex=os.getenv("CORS_ORIGIN_REGEX", r"https://.*\.vercel\.app"),
    allow_credentials=True if not allow_all else False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes under /api
app.include_router(router, prefix="/api")


@app.get("/", tags=["Root"])
def root() -> dict[str, str]:
    """Root endpoint providing service status and quick links."""
    return {
        "name": "CubeVI API",
        "status": "online",
        "version": "0.1.0",
        "docs_url": "/docs",
    }


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
