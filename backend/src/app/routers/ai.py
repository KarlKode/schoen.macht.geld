from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings
from app.database import get_session
from app.models.ai_task import AITask, ImageType, TaskStatus, TaskType
from app.models.stock import Stock
from app.schemas.ai import (
    AITaskCreateResponse,
    AITaskResponse,
    ApplyResultRequest,
    GenerateDescriptionRequest,
    GenerateImageRequest,
    GenerateVideoRequest,
)

router = APIRouter()

# Prompt templates
DESCRIPTION_PROMPT = (
    "You are a satirical stock market analyst. Take this stock and make "
    "its description absurd, exaggerated, and funny while keeping it "
    "believable enough for a parody stock trading game.\n\n"
    "Stock: {title}\n"
    "Current description: {description}\n\n"
    "Write a new 2-3 sentence description that is ridiculous but "
    "entertaining. Only output the description, no other text."
)

IMAGE_PROMPTS = {
    ImageType.MAIN: (
        "Corporate stock photo for {title}, professional but slightly off and weird"
    ),
    ImageType.LOGO: (
        "Minimalist corporate logo for {title}, clean vector style, simple design"
    ),
    ImageType.BILLBOARD: (
        "Highway billboard ad for {title} stock, dramatic and absurd"
    ),
    ImageType.WEBSITE: (
        "Screenshot of corporate website hero section for {title}, modern design"
    ),
}

VIDEO_PROMPT = (
    "15-second stock market ad for {title}. Dramatic corporate style "
    "with text overlays showing rising stock prices. Slightly absurd tone."
)


async def _get_stock_or_none(
    session: AsyncSession, ticker: str | None
) -> Stock | None:
    """Get stock by ticker or return None."""
    if not ticker:
        return None
    return await session.get(Stock, ticker)


@router.post("/generate/description")
async def generate_description(
    request: GenerateDescriptionRequest,
    session: AsyncSession = Depends(get_session),
) -> AITaskCreateResponse:
    """Start generating a stock description."""
    stock = await _get_stock_or_none(session, request.ticker)

    # Determine title and description
    title = request.title or (stock.title if stock else None)
    description = request.description or (stock.description if stock else "")

    if not title:
        raise HTTPException(
            status_code=400, detail="Either ticker or title must be provided"
        )

    # Build prompt
    prompt = DESCRIPTION_PROMPT.format(title=title, description=description or "None")

    # Create task
    task = AITask(
        ticker=request.ticker,
        task_type=TaskType.DESCRIPTION,
        prompt=prompt,
        model=request.model or settings.atlascloud_text_model,
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)

    logger.info(f"Created description task {task.id} for {title}")
    return AITaskCreateResponse(
        task_id=task.id,
        status=task.status,
        message=f"Description generation started for '{title}'",
    )


@router.post("/generate/image")
async def generate_image(
    request: GenerateImageRequest,
    session: AsyncSession = Depends(get_session),
) -> AITaskCreateResponse:
    """Start generating an image for a stock."""
    stock = await _get_stock_or_none(session, request.ticker)

    title = request.title or (stock.title if stock else None)
    if not title:
        raise HTTPException(
            status_code=400, detail="Either ticker or title must be provided"
        )

    # Build prompt from template
    default_prompt = IMAGE_PROMPTS[ImageType.MAIN]
    prompt_template = IMAGE_PROMPTS.get(request.image_type, default_prompt)
    prompt = prompt_template.format(title=title)

    # Create task
    task = AITask(
        ticker=request.ticker,
        task_type=TaskType.IMAGE,
        prompt=prompt,
        model=request.model or settings.atlascloud_image_model,
        image_type=request.image_type,
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)

    logger.info(f"Created image task {task.id} ({request.image_type}) for {title}")
    return AITaskCreateResponse(
        task_id=task.id,
        status=task.status,
        message=f"Image ({request.image_type.value}) generation started for '{title}'",
    )


@router.post("/generate/video")
async def generate_video(
    request: GenerateVideoRequest,
    session: AsyncSession = Depends(get_session),
) -> AITaskCreateResponse:
    """Start generating a video ad for a stock."""
    stock = await _get_stock_or_none(session, request.ticker)

    title = request.title or (stock.title if stock else None)
    if not title:
        raise HTTPException(
            status_code=400, detail="Either ticker or title must be provided"
        )

    prompt = VIDEO_PROMPT.format(title=title)

    # Choose model based on whether we have a source image
    if request.source_image_url:
        model = request.model or settings.atlascloud_video_i2v_model
    else:
        model = request.model or settings.atlascloud_video_t2v_model

    # Create task
    task = AITask(
        ticker=request.ticker,
        task_type=TaskType.VIDEO,
        prompt=prompt,
        model=model,
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)

    logger.info(f"Created video task {task.id} for {title}")
    return AITaskCreateResponse(
        task_id=task.id,
        status=task.status,
        message=f"Video generation started for '{title}'",
    )


@router.get("/tasks")
async def list_tasks(
    session: AsyncSession = Depends(get_session),
    status: TaskStatus | None = None,
    task_type: TaskType | None = None,
) -> list[AITaskResponse]:
    """List all AI tasks, optionally filtered by status or type."""
    query = select(AITask).order_by(AITask.created_at.desc())  # pyright: ignore[reportAttributeAccessIssue]

    if status:
        query = query.where(AITask.status == status)
    if task_type:
        query = query.where(AITask.task_type == task_type)

    result = await session.exec(query)
    tasks = result.all()
    return [AITaskResponse.model_validate(t) for t in tasks]


@router.get("/tasks/{task_id}")
async def get_task(
    task_id: str,
    session: AsyncSession = Depends(get_session),
) -> AITaskResponse:
    """Get a specific AI task by ID."""
    task = await session.get(AITask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return AITaskResponse.model_validate(task)


@router.post("/tasks/{task_id}/apply")
async def apply_result(
    task_id: str,
    request: ApplyResultRequest,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """Apply a completed task's result to a stock."""
    task = await session.get(AITask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Task is not completed")

    if not task.result:
        raise HTTPException(status_code=400, detail="Task has no result")

    stock = await session.get(Stock, request.ticker)
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    # Apply result based on task type
    if task.task_type == TaskType.DESCRIPTION:
        stock.description = task.result
        stock.updated_at = datetime.now(UTC)
        session.add(stock)
        await session.commit()
        logger.info(f"Applied description from task {task_id} to {request.ticker}")
        return {"message": f"Description applied to {request.ticker}"}

    elif task.task_type == TaskType.IMAGE:
        # For images, result is a file path - would need to copy/move file
        # For now, just return info about what would happen
        return {
            "message": f"Image at {task.result} ready to apply to {request.ticker}",
            "note": "Manual image upload required for now",
        }

    elif task.task_type == TaskType.VIDEO:
        return {
            "message": f"Video at {task.result} ready for {request.ticker}",
            "note": "Videos are stored separately, not applied to stock directly",
        }

    return {"message": "Unknown task type"}


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """Delete an AI task."""
    task = await session.get(AITask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    await session.delete(task)
    await session.commit()

    logger.info(f"Deleted task {task_id}")
    return {"message": f"Task {task_id} deleted"}
