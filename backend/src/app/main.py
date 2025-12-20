import shutil
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger
from sqlalchemy import text

from app.admin import setup_admin
from app.config import settings
from app.database import async_session_maker, engine, init_db
from app.routers import ai, stocks, swipe
from app.scheduler import scheduler, start_scheduler, stop_scheduler


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
    allow_origins=["*"] if settings.cors_allow_all else settings.cors_origins,
    # Can't use credentials with wildcard origin
    allow_credentials=not settings.cors_allow_all,
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
    """Health check endpoint with system status.

    Returns:
        - status: "ok" if all checks pass, "degraded" if some fail
        - database: connectivity status
        - scheduler: running status and job count
        - disk: free space in the images directory
    """
    checks: dict[str, dict[str, str | int | float | bool]] = {}
    all_ok = True

    # Check database connectivity
    try:
        async with async_session_maker() as session:
            await session.exec(text("SELECT 1"))  # pyright: ignore[reportArgumentType,reportCallIssue]
        checks["database"] = {"status": "ok"}
    except Exception as e:
        checks["database"] = {"status": "error", "error": str(e)}
        all_ok = False

    # Check scheduler status
    try:
        running = scheduler.running
        job_count = len(scheduler.get_jobs())  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
        checks["scheduler"] = {
            "status": "ok" if running else "stopped",
            "running": running,
            "jobs": job_count,
        }
        if not running:
            all_ok = False
    except Exception as e:
        checks["scheduler"] = {"status": "error", "error": str(e)}
        all_ok = False

    # Check disk space
    try:
        image_path = Path(settings.image_dir)
        if image_path.exists():
            disk = shutil.disk_usage(image_path)
            free_gb = disk.free / (1024**3)
            checks["disk"] = {
                "status": "ok" if free_gb > 1 else "low",
                "free_gb": round(free_gb, 2),
            }
            if free_gb < 0.5:  # Less than 500MB is concerning
                all_ok = False
        else:
            checks["disk"] = {"status": "error", "error": "Image directory not found"}
            all_ok = False
    except Exception as e:
        checks["disk"] = {"status": "error", "error": str(e)}
        all_ok = False

    return {
        "status": "ok" if all_ok else "degraded",
        "checks": checks,
    }
