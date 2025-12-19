from datetime import UTC, datetime
from enum import Enum
from functools import partial
from uuid import uuid4

from sqlmodel import Field, Relationship, SQLModel


class TaskType(str, Enum):
    """Type of AI generation task."""

    DESCRIPTION = "description"
    IMAGE = "image"
    VIDEO = "video"


class TaskStatus(str, Enum):
    """Status of an AI task."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ImageType(str, Enum):
    """Type of image to generate."""

    MAIN = "main"
    LOGO = "logo"
    BILLBOARD = "billboard"
    WEBSITE = "website"


def generate_uuid() -> str:
    return str(uuid4())


class AITask(SQLModel, table=True):
    """AI generation task tracking."""

    __tablename__ = "ai_task"  # pyright: ignore[reportAssignmentType]

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    ticker: str | None = Field(default=None, foreign_key="stock.ticker", index=True)
    task_type: TaskType
    status: TaskStatus = Field(default=TaskStatus.PENDING)

    prompt: str
    model: str
    image_type: ImageType | None = Field(default=None)

    atlascloud_id: str | None = Field(default=None)
    result: str | None = Field(default=None)
    error: str | None = Field(default=None)

    created_at: datetime = Field(default_factory=partial(datetime.now, UTC))
    completed_at: datetime | None = Field(default=None)

    stock: "Stock" = Relationship(back_populates="ai_tasks")  # noqa: F821, UP037  # pyright: ignore[reportAny,reportUndefinedVariable]
