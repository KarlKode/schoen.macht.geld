import asyncio
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.models.stock import ChangeType, PriceEvent, Stock
from app.schemas.stock import SwipeDirection, SwipeRequest, SwipeResponse
from app.swipe_token import SwipeToken, calculate_price_delta

router = APIRouter()

# Per-ticker locks to prevent race conditions on concurrent swipes
# This ensures swipes on the same stock are serialized, while swipes on
# different stocks can proceed concurrently.
_ticker_locks: dict[str, asyncio.Lock] = {}


def _get_ticker_lock(ticker: str) -> asyncio.Lock:
    """Get or create a lock for the given ticker."""
    if ticker not in _ticker_locks:
        _ticker_locks[ticker] = asyncio.Lock()
    return _ticker_locks[ticker]


@router.post("/")
async def swipe(
    request: SwipeRequest, session: AsyncSession = Depends(get_session)
) -> SwipeResponse:
    """Record a swipe and update stock value.

    Uses per-ticker locking to prevent race conditions when multiple users
    swipe the same stock simultaneously.
    """
    # Decode/create swipe token and update with this swipe (outside lock, no DB)
    token = SwipeToken.decode(request.swipe_token)
    token.update(request.direction)
    stats = token.analyze()

    # Acquire lock for this ticker to serialize concurrent swipes on same stock
    lock = _get_ticker_lock(request.ticker)
    async with lock:
        # Read stock inside lock to get current price
        stock = await session.get(Stock, request.ticker)
        if not stock:
            logger.warning("Swipe on unknown ticker: {}", request.ticker)
            raise HTTPException(status_code=404, detail="Stock not found")

        # Calculate price delta based on direction and user stats
        delta = calculate_price_delta(stock.price, request.direction, stats)

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
        request.direction.value,
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
