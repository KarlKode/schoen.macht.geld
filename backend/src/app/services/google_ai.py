"""Google AI client for text generation (fallback provider)."""

from typing import Any

import httpx
from loguru import logger

from app.config import settings


class GoogleAIError(Exception):
    """Google AI API error."""

    pass


class GoogleAIClient:
    """Simple async client for Google AI text generation."""

    def __init__(self) -> None:
        self.base_url: str = settings.google_ai_base_url.rstrip("/")
        self.api_key: str = settings.google_ai_api_key

    async def generate_text(
        self, prompt: str, model: str | None = None
    ) -> dict[str, Any]:  # pyright: ignore[reportExplicitAny]
        """Generate text using Google AI.

        Returns response in same format as AtlasCloud for compatibility:
        {"choices": [{"message": {"content": "..."}}]}
        """
        model = model or settings.google_ai_text_model
        url = f"{self.base_url}/models/{model}:generateContent"

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "maxOutputTokens": 500,
                "temperature": 1.0,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    url,
                    json=payload,
                    params={"key": self.api_key},
                    headers={"Content-Type": "application/json"},
                )

                if response.status_code >= 400:
                    logger.error(
                        "Google AI API error: {} {}",
                        response.status_code,
                        response.text,
                    )
                    raise GoogleAIError(
                        f"API error {response.status_code}: {response.text}"
                    )

                data = response.json()  # pyright: ignore[reportAny]

                # Extract text from Google's response format
                text = (  # pyright: ignore[reportAny]
                    data.get("candidates", [{}])[0]  # pyright: ignore[reportAny]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text", "")
                )

                # Return in AtlasCloud-compatible format
                return {"choices": [{"message": {"content": text}}]}

        except httpx.TimeoutException as e:
            logger.warning("Google AI API timeout: {}", e)
            raise GoogleAIError(f"Request timeout: {e}") from e

        except httpx.ConnectError as e:
            logger.warning("Google AI API connection error: {}", e)
            raise GoogleAIError(f"Connection error: {e}") from e


# Singleton instance
google_ai = GoogleAIClient()
