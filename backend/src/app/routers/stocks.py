from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from sqlalchemy import func
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.models.stock import (
    ChangeType,
    PriceEvent,
    Stock,
    StockSnapshot,
    limit_price_events,
)
from app.schemas.stock import (
    PriceEventResponse,
    StockCreate,
    StockImageUpdate,
    StockPriceUpdate,
    StockResponse,
    StockSnapshotResponse,
)
from app.storage import cleanup_old_image, validate_image

router = APIRouter()


def generate_ticker(title: str) -> str:
    """Generate a 4-char ticker from title."""
    clean = "".join(c for c in title if c.isalpha()).upper()
    return (clean[:4]).ljust(4, "X")


@router.get("/")
async def list_stocks(
    random: Annotated[bool, Query()] = False,
    limit: Annotated[int | None, Query()] = None,
    session: AsyncSession = Depends(get_session),
) -> list[StockResponse]:
    """Get all stocks."""
    sel = select(Stock)
    if random:
        sel = sel.order_by(func.random())
    if limit:
        sel = sel.limit(limit)
    result = await session.exec(sel)
    stocks = result.all()
    logger.debug("Listed {} stocks", len(stocks))
    return [StockResponse.model_validate(limit_price_events(s)) for s in stocks]


@router.post("/")
async def create_stock(
    request: StockCreate,
    session: AsyncSession = Depends(get_session),
    image: StockImageUpdate | None = None,
) -> StockResponse:
    """Create a new stock."""
    ticker = generate_ticker(request.title)

    existing = await session.get(Stock, ticker)
    if existing:
        logger.warning("Ticker {} already exists", ticker)
        raise HTTPException(status_code=400, detail=f"Ticker {ticker} already exists")

    # Validate image if provided
    if image:
        validate_image(image)

    stock = Stock(
        ticker=ticker,
        title=request.title,
        image=image,  # pyright: ignore[reportArgumentType]
        description=request.description,
    )
    session.add(stock)

    # Create initial price event
    initial_event = PriceEvent(
        ticker=ticker,
        price=max(0.0, request.initial_price),
        change_type=ChangeType.INITIAL,
    )
    session.add(initial_event)

    await session.commit()
    await session.refresh(stock)

    logger.info("Created stock {} ({})", ticker, request.title)
    return StockResponse.model_validate(stock)


@router.get("/{ticker}")
async def get_stock(
    ticker: str, session: AsyncSession = Depends(get_session)
) -> StockResponse:
    """Get a single stock by ticker."""
    stock = await session.get(Stock, ticker)
    if not stock:
        logger.warning("Stock not found: {}", ticker)
        raise HTTPException(status_code=404, detail="Stock not found")
    return StockResponse.model_validate(stock)


@router.post("/{ticker}/image")
async def upload_stock_image(
    ticker: str,
    image: StockImageUpdate,
    session: AsyncSession = Depends(get_session),
) -> StockResponse:
    """Upload and store stock image locally."""
    stock = await session.get(Stock, ticker)
    if not stock:
        logger.warning("Stock not found: {}", ticker)
        raise HTTPException(status_code=404, detail="Stock not found")

    # Validate image
    validate_image(image)

    # Clean up old image before replacing
    old_image = stock.image
    stock.image = image  # pyright: ignore[reportAttributeAccessIssue]

    # Save stock
    stock.updated_at = datetime.now(UTC)
    session.add(stock)
    await session.commit()
    await session.refresh(stock)

    # Clean up old image after successful commit
    cleanup_old_image(old_image)

    logger.info(
        "Uploaded image for {}: {}",
        ticker,
        stock.image.path if stock.image else "<no image>",
    )
    return StockResponse.model_validate(stock)


@router.post("/{ticker}/price")
async def update_stock_price(
    ticker: str,
    request: StockPriceUpdate,
    session: AsyncSession = Depends(get_session),
) -> StockResponse:
    """Manipulate stock price."""
    stock = await session.get(Stock, ticker)
    if not stock:
        logger.warning("Stock not found: {}", ticker)
        raise HTTPException(status_code=404, detail="Stock not found")

    # Calculate new price (enforce >= 0)
    new_price = max(0.0, stock.price + request.delta)

    # Create price event
    price_event = PriceEvent(
        ticker=ticker,
        price=new_price,
        change_type=request.change_type,
    )
    session.add(price_event)

    stock.updated_at = datetime.now(UTC)
    session.add(stock)
    await session.commit()
    await session.refresh(stock)

    logger.debug(
        "{} price {} by {:.2f} -> {:.2f}",
        ticker,
        request.change_type.value,
        request.delta,
        new_price,
    )
    return StockResponse.model_validate(stock)


@router.get("/{ticker}/snapshots")
async def get_stock_snapshots(
    ticker: str,
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
    session: AsyncSession = Depends(get_session),
) -> list[StockSnapshotResponse]:
    """Get price snapshots for graphing."""
    stock = await session.get(Stock, ticker)
    if not stock:
        logger.warning("Stock not found: {}", ticker)
        raise HTTPException(status_code=404, detail="Stock not found")

    result = await session.exec(
        select(StockSnapshot)
        .where(StockSnapshot.ticker == ticker)
        .order_by(col(StockSnapshot.created_at).desc())
        .limit(limit)
    )
    snapshots = result.all()
    return [StockSnapshotResponse.model_validate(s) for s in snapshots]


@router.get("/{ticker}/events")
async def get_stock_events(
    ticker: str,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    session: AsyncSession = Depends(get_session),
) -> list[PriceEventResponse]:
    """Get price change events (activity log)."""
    stock = await session.get(Stock, ticker)
    if not stock:
        logger.warning("Stock not found: {}", ticker)
        raise HTTPException(status_code=404, detail="Stock not found")

    result = await session.exec(
        select(PriceEvent)
        .where(PriceEvent.ticker == ticker)
        .order_by(col(PriceEvent.created_at).desc())
        .limit(limit)
    )
    events = result.all()
    return [PriceEventResponse.model_validate(e) for e in events]
