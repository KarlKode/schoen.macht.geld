"""Custom file storage with validation and image processing."""

from io import BytesIO
from pathlib import Path

import pillow_heif  # pyright: ignore[reportMissingTypeStubs]
from fastapi import HTTPException, UploadFile
from fastapi_storages import (  # pyright: ignore[reportMissingTypeStubs]
    FileSystemStorage,
    StorageImage,
)
from loguru import logger
from PIL import Image, UnidentifiedImageError

from app.config import settings

# Register HEIF/HEIC support with Pillow
pillow_heif.register_heif_opener()  # pyright: ignore[reportUnknownMemberType]

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/avif",
    "image/heic",
    "image/heif",
    "image/bmp",
}


class NonOverwritingFileSystemStorage(FileSystemStorage):
    """FileSystemStorage that doesn't overwrite existing files.

    This is achieved by appending an incrementing number to the filename if
    a file with the same name already exists
    """

    OVERWRITE_EXISTING_FILE: bool = False


# Singleton storage instance
storage = NonOverwritingFileSystemStorage(path=settings.image_dir)


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
        _ = file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        _ = file.file.seek(current_pos)  # Reset position

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


async def process_image(file: UploadFile) -> UploadFile:
    """Process image: resize if too large, compress as JPEG.

    Args:
        file: The uploaded image file

    Returns:
        Processed UploadFile (may be the same file if no processing needed)
    """
    try:
        # Read image data
        content = await file.read()
        await file.seek(0)

        # Open with Pillow
        img = Image.open(BytesIO(content))

        # Convert to RGB if necessary (for JPEG output)
        if img.mode in ("RGBA", "LA", "P"):
            # Create white background for transparent images
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # Resize if larger than max dimension
        max_dim = settings.image_max_dimension
        if img.width > max_dim or img.height > max_dim:
            original_width, original_height = img.width, img.height
            img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
            logger.debug(
                "Resized image from {}x{} to {}x{}",
                original_width,
                original_height,
                img.width,
                img.height,
            )

        # Compress as JPEG
        output = BytesIO()
        img.save(output, format="JPEG", quality=settings.image_quality, optimize=True)
        _ = output.seek(0)

        # Get original filename and change extension to .jpg
        original_name = file.filename or "image.jpg"
        new_name = Path(original_name).stem + ".jpg"

        # Create new UploadFile with compressed data

        new_file = UploadFile(file=output, filename=new_name)

        original_size = len(content)
        new_size = output.getbuffer().nbytes
        logger.info(
            "Processed image: {} -> {} ({:.1f}KB -> {:.1f}KB, {:.0f}% reduction)",
            original_name,
            new_name,
            original_size / 1024,
            new_size / 1024,
            (1 - new_size / original_size) * 100 if original_size > 0 else 0,
        )

        return new_file

    except UnidentifiedImageError as e:
        # Pillow can't recognize the image format - use original
        logger.warning("Cannot identify image format, using original: {}", e)
        await file.seek(0)
        return file
    except OSError as e:
        # File I/O or corrupt image data - use original
        logger.warning("Image I/O error, using original: {}", e)
        await file.seek(0)
        return file
    except ValueError as e:
        # Mode conversion issues - use original
        logger.warning("Image conversion error, using original: {}", e)
        await file.seek(0)
        return file


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
            image.delete()  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
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
