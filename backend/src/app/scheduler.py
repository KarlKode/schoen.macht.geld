import random
from datetime import UTC, datetime
from pathlib import Path

from apscheduler.schedulers.asyncio import (  # pyright: ignore[reportMissingTypeStubs]
    AsyncIOScheduler,
)
from loguru import logger
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings
from app.database import async_session_maker
from app.models.ai_task import AITask, TaskStatus, TaskType
from app.models.stock import ChangeType, Stock, StockPrice
from app.services.atlascloud import AtlasCloudError, atlascloud

scheduler = AsyncIOScheduler()


async def tick_prices() -> None:
    """Apply random price changes to all active stocks."""
    async with async_session_maker() as session:
        result = await session.exec(select(Stock).where(Stock.is_active == True))  # noqa: E712
        stocks = result.all()

        if not stocks:
            logger.debug("No active stocks to tick")
            return

        for stock in stocks:
            # Random delta between -5% and +5% of current price
            max_delta = stock.price * 0.05
            delta = random.uniform(-max_delta, max_delta)

            # Enforce price >= 0
            new_price = max(0.0, stock.price + delta)

            price_entry = StockPrice(
                ticker=stock.ticker,
                price=new_price,
                change_type=ChangeType.RANDOM,
            )
            session.add(price_entry)

            stock.updated_at = datetime.now(UTC)
            session.add(stock)

        await session.commit()
        logger.debug("Ticked prices for {} stocks", len(stocks))


async def process_ai_tasks() -> None:
    """Process pending and in-progress AI tasks."""
    async with async_session_maker() as session:
        # Get pending and processing tasks
        result = await session.exec(
            select(AITask).where(
                AITask.status.in_([TaskStatus.PENDING, TaskStatus.PROCESSING])  # pyright: ignore[reportAttributeAccessIssue]
            )
        )
        tasks = result.all()

        if not tasks:
            return

        for task in tasks:
            try:
                if task.status == TaskStatus.PENDING:
                    await _submit_task(task, session)
                elif task.status == TaskStatus.PROCESSING:
                    await _poll_task(task, session)
            except AtlasCloudError as e:
                logger.error(f"AtlasCloud error for task {task.id}: {e}")
                task.status = TaskStatus.FAILED
                task.error = str(e)
                task.completed_at = datetime.now(UTC)
                session.add(task)
            except Exception as e:
                logger.exception(f"Error processing task {task.id}: {e}")
                task.status = TaskStatus.FAILED
                task.error = str(e)
                task.completed_at = datetime.now(UTC)
                session.add(task)

        await session.commit()


async def _submit_task(task: AITask, session: AsyncSession) -> None:
    """Submit a pending task to AtlasCloud."""
    logger.info(f"Submitting {task.task_type.value} task {task.id}")

    if task.task_type == TaskType.DESCRIPTION:
        # Text generation is synchronous (fast)
        response = await atlascloud.generate_text(task.prompt, task.model)
        # Extract text from chat completion response
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        task.result = content.strip()
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now(UTC)
        logger.info(f"Completed text task {task.id}")

    elif task.task_type == TaskType.IMAGE:
        response = await atlascloud.generate_image(task.prompt, task.model)
        data = response.get("data", {})
        task.atlascloud_id = data.get("id")
        task.status = TaskStatus.PROCESSING
        logger.info(f"Started image task {task.id}, atlascloud_id={task.atlascloud_id}")

    elif task.task_type == TaskType.VIDEO:
        response = await atlascloud.generate_video_from_text(task.prompt, task.model)
        data = response.get("data", {})
        task.atlascloud_id = data.get("id")
        task.status = TaskStatus.PROCESSING
        logger.info(f"Started video task {task.id}, atlascloud_id={task.atlascloud_id}")

    session.add(task)


async def _poll_task(task: AITask, session: AsyncSession) -> None:
    """Poll a processing task for completion."""
    if not task.atlascloud_id:
        logger.warning(f"Task {task.id} has no atlascloud_id, marking failed")
        task.status = TaskStatus.FAILED
        task.error = "No external task ID"
        session.add(task)
        return

    # Check timeout (handle both naive and aware datetimes)
    now = datetime.now(UTC)
    created = task.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=UTC)
    elapsed = (now - created).total_seconds()
    if elapsed > settings.ai_task_timeout:
        logger.warning(f"Task {task.id} timed out after {elapsed}s")
        task.status = TaskStatus.FAILED
        task.error = "Task timed out"
        task.completed_at = datetime.now(UTC)
        session.add(task)
        return

    response = await atlascloud.get_task_status(task.atlascloud_id)
    data = response.get("data", {})
    status = data.get("status", "").lower()

    if status == "completed":
        # Download and save the result
        output_urls = data.get("outputs", [])
        if output_urls:
            await _download_result(task, output_urls[0])
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now(UTC)
        logger.info(f"Task {task.id} completed: {task.result}")

    elif status == "failed":
        task.status = TaskStatus.FAILED
        task.error = data.get("error", "Unknown error")
        task.completed_at = datetime.now(UTC)
        logger.error(f"Task {task.id} failed: {task.error}")

    # else: still processing, do nothing

    session.add(task)


async def _download_result(task: AITask, url: str) -> None:
    """Download generated media and save locally."""
    # Determine file extension
    if task.task_type == TaskType.IMAGE:
        ext = ".png"
        subdir = "ai_images"
    elif task.task_type == TaskType.VIDEO:
        ext = ".mp4"
        subdir = "ai_videos"
    else:
        return

    # Create output directory
    output_dir = Path(settings.image_dir).parent / subdir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Download file
    content = await atlascloud.download_file(url)

    # Save with task ID as filename
    filename = f"{task.id}{ext}"
    filepath = output_dir / filename
    filepath.write_bytes(content)

    task.result = str(filepath)
    logger.info(f"Downloaded {task.task_type.value} to {filepath}")


def start_scheduler() -> None:
    """Start the background scheduler."""
    if settings.price_tick_enabled:
        _ = scheduler.add_job(  # pyright: ignore[reportUnknownMemberType]
            tick_prices,
            "interval",
            seconds=settings.price_tick_interval,
            id="price_tick",
            replace_existing=True,
        )
        logger.info(
            "Started price tick scheduler (interval: {}s)", settings.price_tick_interval
        )

    # AI task processor - always enabled if API key is set
    if settings.atlascloud_api_key:
        _ = scheduler.add_job(  # pyright: ignore[reportUnknownMemberType]
            process_ai_tasks,
            "interval",
            seconds=settings.ai_task_poll_interval,
            id="ai_task_processor",
            replace_existing=True,
        )
        logger.info(
            "Started AI task processor (interval: {}s)", settings.ai_task_poll_interval
        )
    else:
        logger.warning("AtlasCloud API key not set, AI task processor disabled")

    if scheduler.get_jobs():
        scheduler.start()


def stop_scheduler() -> None:
    """Stop the background scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Stopped price tick scheduler")
