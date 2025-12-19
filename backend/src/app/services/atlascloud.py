"""AtlasCloud API client for AI generation."""

from typing import Any

import httpx
from loguru import logger

from app.config import settings


class AtlasCloudError(Exception):
    """AtlasCloud API error."""

    pass


class AtlasCloudClient:
    """Async client for AtlasCloud API."""

    def __init__(self) -> None:
        self.base_url = settings.atlascloud_base_url.rstrip("/")
        self.api_key = settings.atlascloud_api_key

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def _request(
        self, method: str, endpoint: str, **kwargs: Any
    ) -> dict[str, Any]:
        """Make an API request."""
        url = f"{self.base_url}{endpoint}"
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.request(
                method, url, headers=self._headers(), **kwargs
            )
            if response.status_code >= 400:
                logger.error(
                    f"AtlasCloud API error: {response.status_code} {response.text}"
                )
                raise AtlasCloudError(
                    f"API error {response.status_code}: {response.text}"
                )
            return response.json()  # pyright: ignore[reportAny]

    async def generate_text(
        self, prompt: str, model: str | None = None
    ) -> dict[str, Any]:
        """Generate text using chat completion API."""
        model = model or settings.atlascloud_text_model
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 500,
            "temperature": 1,
            "stream": False,
        }
        logger.debug(f"Generating text with model {model}")
        return await self._request("POST", "/v1/chat/completions", json=payload)

    async def generate_image(
        self, prompt: str, model: str | None = None, size: str = "1024x1024"
    ) -> dict[str, Any]:
        """Start image generation. Returns task info with ID for polling."""
        model = model or settings.atlascloud_image_model
        payload = {
            "model": model,
            "prompt": prompt,
            "size": size,
        }
        logger.debug(f"Starting image generation with model {model}")
        return await self._request("POST", "/api/v1/model/generateImage", json=payload)

    async def generate_video_from_text(
        self,
        prompt: str,
        model: str | None = None,
        duration: int = 5,
        size: str = "832*480",
    ) -> dict[str, Any]:
        """Start video generation from text. Returns task info with ID for polling."""
        model = model or settings.atlascloud_video_t2v_model
        payload = {
            "model": model,
            "prompt": prompt,
            "duration": duration,
            "size": size,
        }
        logger.debug(f"Starting text-to-video generation with model {model}")
        return await self._request("POST", "/api/v1/model/generateVideo", json=payload)

    async def generate_video_from_image(
        self,
        prompt: str,
        image_url: str,
        model: str | None = None,
        duration: int = 5,
        size: str = "832*480",
    ) -> dict[str, Any]:
        """Start video generation from image. Returns task info with ID for polling."""
        model = model or settings.atlascloud_video_i2v_model
        payload = {
            "model": model,
            "prompt": prompt,
            "image": image_url,
            "duration": duration,
            "size": size,
        }
        logger.debug(f"Starting image-to-video generation with model {model}")
        return await self._request("POST", "/api/v1/model/generateVideo", json=payload)

    async def get_task_status(self, task_id: str) -> dict[str, Any]:
        """Get the status of an async generation task."""
        logger.debug(f"Polling task status for {task_id}")
        return await self._request("GET", f"/api/v1/model/prediction/{task_id}")

    async def download_file(self, url: str) -> bytes:
        """Download a file from a URL (for generated images/videos)."""
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content


# Singleton instance
atlascloud = AtlasCloudClient()
