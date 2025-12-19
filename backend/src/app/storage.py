"""Custom file storage with validation and unique filenames."""

import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile
from fastapi_storages import (
    FileSystemStorage,  # pyright: ignore[reportMissingTypeStubs]
    StorageImage,  # pyright: ignore[reportMissingTypeStubs]
)
from loguru import logger

from app.config import settings

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}


class UniqueFileSystemStorage(FileSystemStorage):  # pyright: ignore[reportMissingTypeStubs]
    """FileSystemStorage with unique filenames using UUID prefix."""

    def get_name(self, name: str) -> str:
        """Generate unique filename with UUID prefix."""
        # Get the sanitized base name from parent
        safe_name = super().get_name(name)
        # Add UUID prefix to ensure uniqueness
        unique_id = uuid.uuid4().hex[:12]
        return f"{unique_id}_{safe_name}"


# Singleton storage instance
storage = UniqueFileSystemStorage(path=settings.image_dir)


def validate_image_size(file: UploadFile) -> None:
    """Validate image file size.

    Args:
        file: The uploaded file to validate

    Raises:
        HTTPException: If file exceeds max size
    """
    # Try to get size from file's size attribute or by seeking
    file_size: int | None = None

    if hasattr(file, "size") and file.size is not None:
        file_size = file.size
    elif file.file:
        # Seek to end to get size
        current_pos = file.file.tell()
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(current_pos)  # Reset position

    if file_size is not None and file_size > settings.max_image_size:
        max_mb = settings.max_image_size / (1024 * 1024)
        raise HTTPException(
            status_code=400,
            detail=f"Image too large. Maximum size is {max_mb:.1f}MB.",
        )


def validate_image_type(file: UploadFile) -> None:
    """Validate image content type.

    Args:
        file: The uploaded file to validate

    Raises:
        HTTPException: If content type is not allowed
    """
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid image type. Allowed: {', '.join(ALLOWED_IMAGE_TYPES)}",
        )


def validate_image(file: UploadFile) -> None:
    """Validate image file size and type.

    Args:
        file: The uploaded file to validate

    Raises:
        HTTPException: If validation fails
    """
    validate_image_type(file)
    validate_image_size(file)


def delete_image(image: StorageImage | str | None) -> bool:
    """Delete an image file from storage.

    Args:
        image: StorageImage object or path string to delete

    Returns:
        True if deleted, False if not found or failed
    """
    if image is None:
        return False

    try:
        if isinstance(image, StorageImage):
            image.delete()  # pyright: ignore[reportAttributeAccessIssue]
            logger.debug("Deleted image via StorageImage: {}", image.name)
            return True
        # Handle path string (StorageImage extends str, so check it second)
        path = Path(settings.image_dir) / image
        if path.exists():
            path.unlink()
            logger.debug("Deleted image file: {}", image)
            return True
        logger.warning("Image file not found: {}", image)
        return False
    except Exception as e:
        logger.error("Failed to delete image: {}", e)
        return False


def cleanup_old_image(old_image: StorageImage | str | None) -> None:
    """Clean up old image when replacing with a new one.

    Args:
        old_image: The old image to delete
    """
    if old_image:
        deleted = delete_image(old_image)
        if deleted:
            logger.info("Cleaned up old image")
