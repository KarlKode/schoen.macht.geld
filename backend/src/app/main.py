from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from app.admin import setup_admin
from app.config import settings
from app.database import engine, init_db
from app.routers import ai, stocks, swipe
from app.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):  # pyright: ignore[reportUnusedParameter]
    """Initialize database and scheduler on startup."""
    logger.info("Starting up")
    await init_db()

    # Create image directory if needed
    image_dir = Path(settings.image_dir)
    image_dir.mkdir(parents=True, exist_ok=True)

    start_scheduler()
    yield
    stop_scheduler()
    logger.info("Shutting down")


app = FastAPI(
    title="Schoen Macht Geld API",
    description="Backend for the stock exchange party game",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stocks.router, prefix="/stocks", tags=["stocks"])
app.include_router(swipe.router, prefix="/swipe", tags=["swipe"])
app.include_router(ai.router, prefix="/ai", tags=["ai"])

# Serve uploaded images
app.mount("/images", StaticFiles(directory=settings.image_dir), name="images")

# Admin panel at /admin
_ = setup_admin(app, engine)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
