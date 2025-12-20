"""AtlasCloud API client for AI generation."""

import time
from typing import Any

import httpx
from loguru import logger
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import settings


class AtlasCloudError(Exception):
    """AtlasCloud API error (non-retryable, e.g. 4xx)."""

    pass


class AtlasCloudTransientError(Exception):
    """AtlasCloud transient error (retryable, e.g. 5xx, timeouts)."""

    pass


class CircuitBreaker:
    """Simple circuit breaker to prevent hammering a failing service."""

    def __init__(self, failure_threshold: int = 5, reset_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.last_failure_time: float = 0
        self.is_open = False

    def record_failure(self) -> None:
        """Record a failure and potentially open the circuit."""
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold:
            self.is_open = True
            logger.warning(
                "Circuit breaker OPEN after {} failures", self.failure_threshold
            )

    def record_success(self) -> None:
        """Record a success and reset the failure count."""
        if self.failures > 0:
            logger.debug("Circuit breaker reset after successful request")
        self.failures = 0
        self.is_open = False

    def allow_request(self) -> bool:
        """Check if a request should be allowed."""
        if not self.is_open:
            return True

        # Check if enough time has passed to try again
        elapsed = time.time() - self.last_failure_time
        if elapsed >= self.reset_timeout:
            logger.info("Circuit breaker attempting reset after {}s", elapsed)
            return True

        return False


class AtlasCloudClient:
    """Async client for AtlasCloud API with retry and circuit breaker."""

    def __init__(self) -> None:
        self.base_url: str = settings.atlascloud_base_url.rstrip("/")
        self.api_key: str = settings.atlascloud_api_key
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, reset_timeout=60.0)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @retry(
        retry=retry_if_exception_type(AtlasCloudTransientError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,  # pyright: ignore[reportAny, reportExplicitAny]
    ) -> dict[str, Any]:  # pyright: ignore[reportExplicitAny]
        """Make an API request with retry logic and circuit breaker."""
        # Check circuit breaker
        if not self.circuit_breaker.allow_request():
            raise AtlasCloudError(
                "Circuit breaker open - AtlasCloud API temporarily unavailable"
            )

        url = f"{self.base_url}{endpoint}"
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.request(
                    method,
                    url,
                    headers=self._headers(),
                    **kwargs,  # pyright: ignore[reportAny]
                )

                # 4xx errors are not retryable (client error)
                if 400 <= response.status_code < 500:
                    logger.error(
                        "AtlasCloud API client error: {} {}",
                        response.status_code,
                        response.text,
                    )
                    raise AtlasCloudError(
                        f"API error {response.status_code}: {response.text}"
                    )

                # 5xx errors are retryable (server error)
                if response.status_code >= 500:
                    self.circuit_breaker.record_failure()
                    logger.warning(
                        "AtlasCloud API server error (retrying): {} {}",
                        response.status_code,
                        response.text,
                    )
                    raise AtlasCloudTransientError(
                        f"API error {response.status_code}: {response.text}"
                    )

                self.circuit_breaker.record_success()
                return response.json()  # pyright: ignore[reportAny]

        except httpx.TimeoutException as e:
            self.circuit_breaker.record_failure()
            logger.warning("AtlasCloud API timeout (retrying): {}", e)
            raise AtlasCloudTransientError(f"Request timeout: {e}") from e

        except httpx.ConnectError as e:
            self.circuit_breaker.record_failure()
            logger.warning("AtlasCloud API connection error (retrying): {}", e)
            raise AtlasCloudTransientError(f"Connection error: {e}") from e

    async def generate_text(
        self, prompt: str, model: str | None = None
    ) -> dict[str, Any]:  # pyright: ignore[reportExplicitAny]
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
    ) -> dict[str, Any]:  # pyright: ignore[reportExplicitAny]
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
    ) -> dict[str, Any]:  # pyright: ignore[reportExplicitAny]
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
    ) -> dict[str, Any]:  # pyright: ignore[reportExplicitAny]
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

    async def get_task_status(self, task_id: str) -> dict[str, Any]:  # pyright: ignore[reportExplicitAny]
        """Get the status of an async generation task."""
        logger.debug(f"Polling task status for {task_id}")
        return await self._request("GET", f"/api/v1/model/prediction/{task_id}")

    async def download_file(self, url: str) -> bytes:
        """Download a file from a URL (for generated images/videos)."""
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.get(url)
            _ = response.raise_for_status()
            return response.content


# Singleton instance
atlascloud = AtlasCloudClient()
