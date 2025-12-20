from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.models.stock import ChangeType, PriceEvent, Stock
from app.schemas.stock import SwipeDirection, SwipeRequest, SwipeResponse
from app.swipe_token import SwipeToken, calculate_price_delta

router = APIRouter()


@router.post("/")
async def swipe(
    request: SwipeRequest, session: AsyncSession = Depends(get_session)
) -> SwipeResponse:
    """Record a swipe and update stock value."""
    stock = await session.get(Stock, request.ticker)
    if not stock:
        logger.warning("Swipe on unknown ticker: {}", request.ticker)
        raise HTTPException(status_code=404, detail="Stock not found")

    # Decode/create swipe token and update with this swipe
    token = SwipeToken.decode(request.swipe_token)
    direction = request.direction.value
    token.update(direction)

    # Analyze swipe history for price modifiers
    stats = token.analyze()

    # Calculate price delta based on direction and user stats
    delta = calculate_price_delta(stock.price, direction, stats)

    # Calculate new price (enforce >= 0)
    new_price = max(0.0, stock.price + delta)

    # Determine change type
    change_type = (
        ChangeType.SWIPE_UP
        if request.direction == SwipeDirection.RIGHT
        else ChangeType.SWIPE_DOWN
    )

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

    logger.debug(
        "{} {} -> {:.2f} (delta: {:.2f}, streak: {}, pickiness: {:.2f})",
        request.ticker,
        direction,
        new_price,
        delta,
        stats.streak_length,
        stats.pickiness_ratio,
    )

    return SwipeResponse(
        ticker=stock.ticker,
        new_price=new_price,
        delta=delta,
        swipe_token=token.encode(),
    )
