from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.ai_task import ImageType, TaskStatus, TaskType


class GenerateDescriptionRequest(BaseModel):
    """Request to generate/modify a stock description."""

    ticker: str | None = None  # If provided, uses stock's current data
    title: str | None = None  # Custom title (required if no ticker)
    description: str | None = None  # Existing description to modify
    model: str | None = None  # Override default model


class GenerateImageRequest(BaseModel):
    """Request to generate an image for a stock."""

    ticker: str | None = None  # If provided, uses stock's title for prompt
    title: str | None = None  # Custom title (required if no ticker)
    image_type: ImageType = ImageType.MAIN
    model: str | None = None  # Override default model


class GenerateVideoRequest(BaseModel):
    """Request to generate a video ad for a stock."""

    ticker: str | None = None  # If provided, uses stock's title for prompt
    title: str | None = None  # Custom title (required if no ticker)
    source_image_url: str | None = None  # If provided, uses image-to-video
    duration: int = 5  # Video duration in seconds (5-10)
    model: str | None = None  # Override default model


class AITaskResponse(BaseModel):
    """Response schema for an AI task."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    ticker: str | None
    task_type: TaskType
    status: TaskStatus
    prompt: str
    model: str
    image_type: ImageType | None
    result: str | None
    error: str | None
    created_at: datetime
    completed_at: datetime | None


class AITaskCreateResponse(BaseModel):
    """Response when creating an AI task."""

    task_id: str
    status: TaskStatus
    message: str


class ApplyResultRequest(BaseModel):
    """Request to apply a generated result to a stock."""

    ticker: str  # Target stock ticker
