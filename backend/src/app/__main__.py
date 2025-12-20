"""Run the application with configured uvicorn settings."""

import uvicorn

from app.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.uvicorn_host,
        port=settings.uvicorn_port,
        workers=settings.uvicorn_workers,
        reload=settings.debug,
        root_path=settings.root_path,
    )
