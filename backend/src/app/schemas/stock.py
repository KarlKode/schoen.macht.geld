from datetime import datetime
from enum import Enum

from fastapi import UploadFile
from pydantic import BaseModel, ConfigDict, computed_field

from app.config import settings
from app.models.stock import ChangeType


class PriceEventResponse(BaseModel):
    """Price change event for API response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    price: float
    change_type: ChangeType
    created_at: datetime


class StockSnapshotResponse(BaseModel):
    """Price snapshot for graphs."""

    model_config = ConfigDict(from_attributes=True)

    price: float
    created_at: datetime


class StockResponse(BaseModel):
    """Stock response matching frontend interface."""

    model_config = ConfigDict(from_attributes=True)

    ticker: str
    title: str
    image: str | None
    description: str
    is_active: bool
    price: float
    price_events: list[PriceEventResponse] = []
    created_at: datetime
    updated_at: datetime

    # Reference price from last snapshot (for percentage change calculation)
    reference_price: float | None = None
    reference_price_at: datetime | None = None
    percentage_change: float | None = None  # Change since last snapshot

    # Ranking by price (1 = highest price)
    rank: int | None = None
    previous_rank: int | None = None
    rank_change: int | None = None  # Positive = moved up

    # Ranking by percentage change (1 = highest gain)
    change_rank: int | None = None
    previous_change_rank: int | None = None
    change_rank_change: int | None = None  # Positive = moved up

    @computed_field
    @property
    def initial_price(self) -> float:
        """Get initial price from first entry."""
        if self.price_events:
            return self.price_events[-1].price
        return settings.stock_base_price

    @computed_field
    @property
    def change(self) -> float:
        """Absolute change from initial price."""
        return self.price - self.initial_price

    @computed_field
    @property
    def percent_change(self) -> float:
        """Percentage change from initial price (total lifetime change)."""
        if self.initial_price == 0:
            return 0.0
        return (self.change / self.initial_price) * 100


class StockCreate(BaseModel):
    """Schema for creating a stock."""

    ticker: str
    title: str
    description: str = ""
    initial_price: float = settings.stock_base_price


class StockPriceUpdate(BaseModel):
    """Schema for manipulating stock price."""

    delta: float
    change_type: ChangeType = ChangeType.ADMIN


class StockImageUpdate(UploadFile):
    pass


class SwipeDirection(str, Enum):
    """Swipe direction."""

    LEFT = "left"
    RIGHT = "right"


class SwipeRequest(BaseModel):
    """Schema for a swipe action."""

    ticker: str
    direction: SwipeDirection
    swipe_token: str | None = None  # Token from previous swipe response


class SwipeResponse(BaseModel):
    """Response after a swipe action."""

    ticker: str
    new_price: float
    delta: float  # actual change applied
    swipe_token: str  # token for next request
