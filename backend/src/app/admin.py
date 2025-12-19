from typing import Any, override

from fastapi import FastAPI
from fastapi_storages import StorageImage  # pyright: ignore[reportMissingTypeStubs]
from loguru import logger
from sqladmin import Admin, ModelView
from sqlalchemy.ext.asyncio import AsyncEngine
from starlette.requests import Request

from app.config import settings
from app.models.ai_task import AITask
from app.models.stock import Stock, StockPrice
from app.storage import ALLOWED_IMAGE_TYPES, cleanup_old_image


def inspect_and_format(m: Stock, _: str)-> list[str]:
    return ["{}".format(repr(p)) for p in m.prices]


class StockAdmin(ModelView, model=Stock):
    column_list = ["ticker", "title", "is_active", "created_at"]
    column_details_list = ["ticker", "title", "description", "is_active", "created_at", "updated_at", "prices", "ai_tasks"]
    column_searchable_list = ["ticker", "title"]
    column_sortable_list = ["ticker", "is_active"]
    column_default_sort = [("ticker", False)]
    column_formatters_detail = {"prices": lambda m, _: [repr(p) for p in m.prices]}  # pyright: ignore[reportUnknownLambdaType, reportUnknownMemberType]
    form_include_pk = True
    form_widget_args = {"image": {"accept": "image/*", "capture": "environment"}}
    form_excluded_columns = ["prices", "created_at", "updated_at", "ai_tasks"]
    can_export = False

    _old_image: StorageImage | None = None

    @override
    async def on_model_change(
        self, data: dict[str, Any], model: Stock, is_created: bool, request: Request  # pyright: ignore[reportExplicitAny]
    ) -> None:
        """Validate image before model change."""
        image = data.get("image")

        if image and hasattr(image, "content_type"):
            # Validate content type
            if image.content_type not in ALLOWED_IMAGE_TYPES:
                raise ValueError(
                    f"Invalid image type '{image.content_type}'. Allowed: {', '.join(ALLOWED_IMAGE_TYPES)}"  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
                )

            # Validate file size
            if hasattr(image, "size") and image.size is not None:
                if image.size > settings.max_image_size:
                    max_mb = settings.max_image_size / (1024 * 1024)
                    raise ValueError(f"Image too large. Max size: {max_mb:.1f}MB.")
            elif hasattr(image, "file") and image.file:
                # Try to get size by seeking
                current_pos = image.file.tell()
                image.file.seek(0, 2)  # Seek to end
                file_size = image.file.tell()
                image.file.seek(current_pos)  # Reset position
                if file_size > settings.max_image_size:
                    max_mb = settings.max_image_size / (1024 * 1024)
                    raise ValueError(f"Image too large. Max size: {max_mb:.1f}MB.")

        # Store old image reference for cleanup after commit
        if not is_created and model.image and image:
            self._old_image = model.image
        else:
            self._old_image = None

    async def after_model_change(  # pyright: ignore[reportAny]
        self, data: dict[str, Any], model: Stock, is_created: bool, request: Request
    ) -> None:
        """Clean up old image after model change."""
        if self._old_image:
            cleanup_old_image(self._old_image)
            logger.info("Admin: cleaned up old image for stock {}", model.ticker)


class StockPriceAdmin(ModelView, model=StockPrice):
    column_list = ["id", "ticker", "price", "change_type", "created_at"]
    column_sortable_list = ["id", "ticker", "created_at"]
    column_default_sort = [("created_at", True)]
    can_create = False
    can_edit = False
    can_export = False


class AITaskAdmin(ModelView, model=AITask):
    column_list = [
        "id", "ticker", "task_type", "status", "model", "created_at", "completed_at"
    ]
    column_searchable_list = ["id", "ticker", "prompt"]
    column_sortable_list = ["id", "status", "task_type", "created_at"]
    column_default_sort = [("created_at", True)]
    can_create = False
    can_edit = False
    can_export = False
    name = "AI Task"
    name_plural = "AI Tasks"


def setup_admin(app: FastAPI, engine: AsyncEngine) -> Admin:
    admin = Admin(app, engine, title="Schoen Macht Geld Admin")
    admin.add_view(StockAdmin)
    admin.add_view(StockPriceAdmin)
    admin.add_view(AITaskAdmin)
    return admin
