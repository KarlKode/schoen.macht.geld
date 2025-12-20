from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.models.stock import ChangeType, PriceEvent, Stock
from app.schemas.stock import StockResponse, SwipeRequest

router = APIRouter()

SWIPE_VALUE = 0.1  # Value change per swipe


@router.post("/")
async def swipe(
    request: SwipeRequest, session: AsyncSession = Depends(get_session)
) -> StockResponse:
    """Record a swipe and update stock value."""
    stock = await session.get(Stock, request.ticker)
    if not stock:
        logger.warning("Swipe on unknown ticker: {}", request.ticker)
        raise HTTPException(status_code=404, detail="Stock not found")

    # Calculate value change and determine change type
    if request.direction == "right":
        delta = SWIPE_VALUE
        change_type = ChangeType.SWIPE_UP
    elif request.direction == "left":
        delta = -SWIPE_VALUE
        change_type = ChangeType.SWIPE_DOWN
    else:
        raise HTTPException(
            status_code=400, detail="Direction must be 'left' or 'right'"
        )

    # Calculate new price (enforce >= 0)
    new_price = max(0.0, stock.price + delta)

    # Record price event
    price_event = PriceEvent(
        ticker=stock.ticker,
        price=new_price,
        change_type=change_type,
    )
    session.add(price_event)

    stock.updated_at = datetime.now(UTC)
    session.add(stock)
    await session.commit()
    await session.refresh(stock)

    logger.debug("{} {} -> {:.2f}", request.ticker, request.direction, new_price)
    return StockResponse.model_validate(stock)
