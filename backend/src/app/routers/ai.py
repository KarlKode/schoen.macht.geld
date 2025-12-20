from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlmodel import col, select
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
    GenerateHeadlinesRequest,
    GenerateImageRequest,
    GenerateVideoRequest,
    HeadlinesResponse,
    MessageResponse,
)

router = APIRouter()

# Prompt templates (German, Party-Themed for "Schön. Macht. Geld.")
DESCRIPTION_PROMPT = """Du bist ein Ghostwriter für die exzessive Zürcher Partyszene und
schreibst witzige, bissige "Börsenprospekte" in der Ich-Perspektive für das Partyspiel
"Schön. Macht. Geld.". Das Spiel wird vom "Verein für ambitionierten Konsum (VAK)" und
dem Club "Amphitheater"veranstaltet.
Das Motto: hedonistischer Konsum, Macht, Schönheit und Drogen.

Schreibe eine sarkastische, ironische und prahlerische Profilbeschreibung in der
Ich-Form, basierend auf dem Spitznamen der Person.

Spitzname: {title}
Aktuelle Beschreibung (falls vorhanden): {description}

Regeln:
1. **Perspektive:** Schreibe immer aus der Ich-Perspektive.
2. **Ton:** Selbstverliebt, sarkastisch, satirisch. Mische Finanzjargon mit Party-Slang.
3. **Themen:** Spiele mit Klischees über das Zürcher Nachtleben:
               Konsum, Status, Oberflächlichkeit und Exzesse.
4. **Länge:** Maximal 350 Zeichen (inkl. Leerzeichen).
5. **Sprache:** Deutsch.

Beispiel: "Mein Kurs? Steigt schneller als mein Puls nach der dritten Line. Ich bin
keine Aktie, ich bin ein Gerücht, eine Legende auf dem Zürcher Parkett. Investier
jetzt, bevor ich zu teuer für dein kleines Portfolio werde."

Gib nur die Beschreibung aus, keinen anderen Text."""

HEADLINES_PROMPT = """Du bist ein zynischer Finanzredakteur für ein Klatschblatt, das
über das Börsen-Partyspiel "Schön. Macht. Geld." berichtet, veranstaltet vom "Verein für
ambitionierten Konsum (VAK)" und "Amphitheater" in Zürich. Dein Publikum liebt Klatsch,
dunklen Humor und ist fasziniert von der hedonistischen Party-Szene, Konsum, Drogen und
der Absurdität, den Selbstwert an einen Aktienkurs zu koppeln.

Basierend auf den folgenden Informationen über die volatilsten Aktien, generiere ein Set
von genau {count} kurzen, schlagkräftigen und urkomischen Schlagzeilen. Jede Schlagzeile
sollte für sich stehen. Der Ton sollte scharf, ironisch und voller Satire sein. Denk an
eine Mischung aus Society-Klatsch und Finanz-Desaster.

Achte auf korrekte deutsche Rechtschreibung und die korrekte Verwendung
von Umlauten (ä, ö, ü).

Hier sind die Daten der Top-Aktien:
{stocks_data}

Generiere {count} einzigartige Schlagzeilen.
Sei provokant und einprägsam. Konzentriere dich auf Themen wie soziale Kletterei,
vergänglichen Ruhm, schlechte Entscheidungen auf Partys, Exzesse im Zürcher Nachtleben
und die Absurdität des Ganzen.

Gib die Schlagzeilen als JSON-Array aus, z.B.: ["Schlagzeile 1", "Schlagzeile 2", ...]
"""

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


async def _get_stock_or_none(session: AsyncSession, ticker: str | None) -> Stock | None:
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

    logger.info("Created description task {} for {}", task.id, title)
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

    logger.info("Created image task {} ({}) for {}", task.id, request.image_type, title)
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

    logger.info("Created video task {} for {}", task.id, title)
    return AITaskCreateResponse(
        task_id=task.id,
        status=task.status,
        message=f"Video generation started for '{title}'",
    )


@router.post("/generate/headlines")
async def generate_headlines(
    request: GenerateHeadlinesRequest,
    session: AsyncSession = Depends(get_session),
) -> HeadlinesResponse:
    """
    Generate satirical news headlines about the top volatile stocks.

    Returns headlines immediately (synchronous generation).
    """
    import json
    import re

    from app.services.atlascloud import atlascloud
    from app.services.google_ai import google_ai

    # Clamp count to valid range
    count = max(1, min(10, request.count))

    # Get top volatile stocks (sorted by absolute percent change)
    query = select(Stock).limit(count)
    result = await session.exec(query)
    all_stocks = list(result.all())

    if not all_stocks:
        return HeadlinesResponse(headlines=[], stocks_used=[])

    # Sort by absolute percent change (most volatile first)
    stocks = sorted(
        all_stocks,
        key=lambda s: abs(s.percent_change),  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType, reportAttributeAccessIssue]
        reverse=True,
    )[:count]

    # Build stocks data string for prompt
    stocks_data = "\n".join(
        f"- Börsenkürzel: {s.ticker}, Spitzname: {s.title}, "
        + f"Aktueller Wert: {s.price:.2f} CHF, "
        + f"Veränderung: {s.change:.2f} CHF ({s.percent_change:.2f}%)"  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
        for s in stocks
    )

    prompt = HEADLINES_PROMPT.format(count=count, stocks_data=stocks_data)
    model = request.model or settings.atlascloud_text_model

    # Try AtlasCloud first, fall back to Google AI
    try:
        response = await atlascloud.generate_text(prompt, model)
        response_text = str(response["choices"][0]["message"]["content"])  # pyright: ignore[reportAny]
    except Exception as e:
        logger.warning("AtlasCloud failed, trying Google AI: {}", e)
        try:
            response = await google_ai.generate_text(prompt)
            response_text = str(response["choices"][0]["message"]["content"])  # pyright: ignore[reportAny]
        except Exception as e2:
            logger.error("Both AI providers failed: {}", e2)
            raise HTTPException(status_code=503, detail="AI service unavailable")

    # Parse JSON array from response
    try:
        json_match = re.search(r"\[.*\]", response_text, re.DOTALL)
        if json_match:
            headlines = json.loads(json_match.group())  # pyright: ignore[reportAny]
        else:
            # Fallback: split by newlines and clean up
            headlines = [
                line.strip().strip('"').strip("'")
                for line in response_text.split("\n")
                if line.strip()
                and not line.startswith("[")
                and not line.startswith("]")
            ]
    except json.JSONDecodeError:
        headlines = [response_text.strip()]

    logger.info(
        "Generated {} headlines for stocks: {}",
        len(headlines),
        [s.ticker for s in stocks],
    )
    return HeadlinesResponse(
        headlines=headlines[:count],
        stocks_used=[s.ticker for s in stocks],
    )


@router.get("/tasks")
async def list_tasks(
    session: AsyncSession = Depends(get_session),
    status: TaskStatus | None = None,
    task_type: TaskType | None = None,
) -> list[AITaskResponse]:
    """List all AI tasks, optionally filtered by status or type."""
    query = select(AITask).order_by(col(AITask.created_at).desc())

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
) -> MessageResponse:
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
        logger.info("Applied description from task {} to {}", task_id, request.ticker)
        return MessageResponse(message=f"Description applied to {request.ticker}")

    elif task.task_type == TaskType.IMAGE:
        # For images, result is a file path - would need to copy/move file
        return MessageResponse(
            message=f"Image at {task.result} ready to apply to {request.ticker}",
            note="Manual image upload required for now",
        )

    elif task.task_type == TaskType.VIDEO:
        return MessageResponse(
            message=f"Video at {task.result} ready for {request.ticker}",
            note="Videos are stored separately, not applied to stock directly",
        )

    return MessageResponse(message="Unknown task type")


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: str,
    session: AsyncSession = Depends(get_session),
) -> MessageResponse:
    """Delete an AI task."""
    task = await session.get(AITask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    await session.delete(task)
    await session.commit()

    logger.info("Deleted task {}", task_id)
    return MessageResponse(message=f"Task {task_id} deleted")
