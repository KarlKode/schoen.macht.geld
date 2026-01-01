"""Screenshot service for capturing frontend views.

Uses Playwright to keep browser pages hot in memory for fast captures.
Designed to achieve 5-10 FPS for Pi display streaming.
"""

import asyncio
from pathlib import Path

from loguru import logger
from playwright.async_api import Browser, Page, Playwright, async_playwright

from app.config import settings

SCREENSHOT_DIR = Path(settings.static_dir) / "screenshots"


class ScreenshotService:
    """Manages browser and page lifecycle for fast screenshot capture."""

    def __init__(self) -> None:
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._pages: dict[str, Page] = {}
        self._lock = asyncio.Lock()
        self._init_lock = asyncio.Lock()
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def views(self) -> list[str]:
        return list(self._pages.keys())

    async def _ensure_started(self) -> None:
        """Lazily start the service if not already running."""
        if self._running:
            return
        async with self._init_lock:
            if not self._running:
                await self.start()

    async def start(self) -> None:
        """Start the browser and pre-load all view pages."""
        if self._running:
            logger.warning("Screenshot service already running")
            return

        SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

        logger.info("Starting screenshot service...")
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"],
        )

        # Pre-load pages for each view
        for view in settings.screenshot_views:
            _ = await self._load_page(view)

        self._running = True
        logger.info(
            "Screenshot service started with {} views", len(settings.screenshot_views)
        )

    async def _load_page(self, view: str) -> Page:
        """Load a single view page."""
        if not self._browser:
            raise RuntimeError("Browser not started")

        url = f"{settings.screenshot_frontend_url}/display/{view}"
        logger.debug("Loading page: {}", url)

        # Explicitly convert to int to avoid pydantic type metadata issues
        page = await self._browser.new_page(
            viewport={
                "width": int(settings.screenshot_width),
                "height": int(settings.screenshot_height),
            },
            screen={
                "width": int(settings.screenshot_width),
                "height": int(settings.screenshot_height),
            }
        )
        _ = await page.goto(url, wait_until="networkidle")
        self._pages[view] = page
        logger.info("Loaded view: {}", view)
        return page

    async def stop(self) -> None:
        """Stop the browser and cleanup."""
        if not self._running:
            return

        logger.info("Stopping screenshot service...")
        self._running = False

        # Close all pages
        for view, page in self._pages.items():
            try:
                await page.close()
            except Exception as e:
                logger.warning("Error closing page {}: {}", view, e)
        self._pages.clear()

        # Close browser
        if self._browser:
            await self._browser.close()
            self._browser = None

        # Stop playwright
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

        logger.info("Screenshot service stopped")

    async def capture(self, view: str) -> bytes:
        """Capture a screenshot of a view as JPEG bytes.

        Lazily starts the service on first call.
        """
        await self._ensure_started()

        page = self._pages.get(view)
        if not page:
            raise ValueError(f"Unknown view: {view}")

        async with self._lock:
            return await page.screenshot(
                type="jpeg",
                quality=int(settings.screenshot_quality),
            )

    async def capture_to_file(self, view: str) -> Path:
        """Capture a screenshot and save to file."""
        await self._ensure_started()

        page = self._pages.get(view)
        if not page:
            raise ValueError(f"Unknown view: {view}")

        path = SCREENSHOT_DIR / f"{view}.jpg"

        async with self._lock:
            _ = await page.screenshot(
                path=path,
                type="jpeg",
                quality=int(settings.screenshot_quality),
            )

        return path

    async def capture_all(self) -> dict[str, bytes]:
        """Capture all views in parallel."""
        await self._ensure_started()

        if not self._pages:
            return {}

        async def capture_one(view: str) -> tuple[str, bytes]:
            data = await self.capture(view)
            return view, data

        results = await asyncio.gather(
            *[capture_one(view) for view in self._pages.keys()]
        )
        return dict(results)

    async def capture_all_to_files(self) -> dict[str, Path]:
        """Capture all views to files."""
        await self._ensure_started()

        if not self._pages:
            return {}

        results: dict[str, Path] = {}
        for view in self._pages:
            path = await self.capture_to_file(view)
            results[view] = path

        return results

    async def reload_page(self, view: str) -> None:
        """Reload a specific view page."""
        await self._ensure_started()

        page = self._pages.get(view)
        if page:
            _ = await page.reload(wait_until="networkidle")
            logger.info("Reloaded view: {}", view)

    async def reload_all(self) -> None:
        """Reload all view pages."""
        await self._ensure_started()

        for view in self._pages:
            await self.reload_page(view)


# Global service instance
screenshot_service = ScreenshotService()
