from datetime import UTC, datetime
from enum import Enum
from functools import partial
from typing import override

from fastapi_storages import StorageImage  # pyright: ignore[reportMissingTypeStubs]
from fastapi_storages.integrations.sqlalchemy import (  # pyright: ignore[reportMissingTypeStubs]
    ImageType,
)
from sqlmodel import Column, Field, Relationship, SQLModel
from sqlmodel._compat import SQLModelConfig

from app.config import settings
from app.storage import storage


class ChangeType(str, Enum):
    """Type of price change."""

    INITIAL = "initial"
    SWIPE_UP = "swipe_up"
    SWIPE_DOWN = "swipe_down"
    RANDOM = "random"
    ADMIN = "admin"


class PriceEvent(SQLModel, table=True):
    """Price change event for a stock."""

    __tablename__ = "price_event"  # pyright: ignore[reportAssignmentType]

    id: int | None = Field(default=None, primary_key=True)
    ticker: str = Field(foreign_key="stock.ticker", index=True)
    price: float
    change_type: ChangeType = Field(default=ChangeType.ADMIN)
    created_at: datetime = Field(default_factory=partial(datetime.now, UTC))

    stock: "Stock" = Relationship(back_populates="price_events")  # pyright: ignore[reportAny]  # noqa: UP037

    @override
    def __repr__(self) -> str:
        return f"<PriceEvent #{self.id} ({self.ticker}) {self.change_type.value}>"


class StockSnapshot(SQLModel, table=True):
    """Periodic price snapshot for graphs and percentage change calculation."""

    __tablename__ = "stock_snapshot"  # pyright: ignore[reportAssignmentType]

    id: int | None = Field(default=None, primary_key=True)
    ticker: str = Field(foreign_key="stock.ticker", index=True)
    price: float
    created_at: datetime = Field(default_factory=partial(datetime.now, UTC))

    stock: "Stock" = Relationship(back_populates="snapshots")  # pyright: ignore[reportAny]  # noqa: UP037

    @override
    def __repr__(self) -> str:
        return f"<StockSnapshot #{self.id} ({self.ticker}) {self.price}>"


class Stock(SQLModel, table=True):
    """Stock database model."""

    __tablename__ = "stock"  # pyright: ignore[reportAssignmentType]
    model_config = SQLModelConfig(from_attributes=True, arbitrary_types_allowed=True)  # pyright: ignore[reportCallIssue]

    ticker: str = Field(max_length=4, primary_key=True)
    title: str = Field(max_length=100)
    image: StorageImage | None = Field(sa_column=Column(ImageType(storage=storage)))
    description: str = ""
    is_active: bool = Field(default=True)

    # Reference price for percentage change calculation (set by snapshot job)
    reference_price: float | None = Field(default=None)
    reference_price_at: datetime | None = Field(default=None)

    created_at: datetime = Field(default_factory=partial(datetime.now, UTC))
    updated_at: datetime = Field(default_factory=partial(datetime.now, UTC))

    price_events: list[PriceEvent] = Relationship(  # pyright: ignore[reportAny]
        back_populates="stock",
        sa_relationship_kwargs={
            "lazy": "selectin",
            "order_by": "PriceEvent.created_at.desc()",
        },
    )

    snapshots: list[StockSnapshot] = Relationship(  # pyright: ignore[reportAny]
        back_populates="stock",
        sa_relationship_kwargs={
            "lazy": "selectin",
            "order_by": "StockSnapshot.created_at.desc()",
        },
    )

    ai_tasks: list["AITask"] = Relationship(back_populates="stock")  # noqa: F821, UP037  # pyright: ignore[reportAny,reportUndefinedVariable]

    @override
    def __repr__(self) -> str:
        return f"<Stock [{self.ticker}] {self.title}>"

    @property
    def price(self) -> float:
        """Get current price from latest PriceEvent entry."""
        if self.price_events:
            return self.price_events[0].price
        return settings.stock_base_price

    @property
    def percentage_change(self) -> float | None:
        """Calculate percentage change from reference price."""
        if self.reference_price is None or self.reference_price == 0:
            return None
        return ((self.price - self.reference_price) / self.reference_price) * 100


def limit_price_events(s: Stock) -> Stock:
    """Limit price events to most recent 10."""
    s.price_events = s.price_events[:10] if s.price_events else s.price_events
    return s
