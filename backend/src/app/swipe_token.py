"""Swipe token encoding/decoding and analysis for stateless user tracking."""

from __future__ import annotations

import base64
import random
import time

from pydantic import BaseModel, ValidationError

from app.config import settings
from app.schemas.stock import SwipeDirection


class SwipeStats(BaseModel):
    """Analyzed statistics from swipe buckets."""

    total_left: int = 0
    total_right: int = 0
    recent_left: int = 0  # last ~1 minute
    recent_right: int = 0
    streak_direction: SwipeDirection | None = None
    streak_length: int = 0
    pickiness_ratio: float = 0.5  # 0 = all right, 1 = all left


class SwipeToken(BaseModel):
    """Token containing bucketed swipe history."""

    ts: int  # last update timestamp
    buckets: list[tuple[int, int]] = []  # [(left, right), ...]

    @classmethod
    def decode(cls, token_str: str | None) -> SwipeToken:
        """Decode token from base64 string, or create fresh if invalid/missing."""
        if not token_str:
            return cls(ts=int(time.time()))

        try:
            json_bytes = base64.urlsafe_b64decode(token_str)
            return cls.model_validate_json(json_bytes)
        except (ValueError, ValidationError):
            return cls(ts=int(time.time()))

    def encode(self) -> str:
        """Encode token to base64 string."""
        return base64.urlsafe_b64encode(self.model_dump_json().encode()).decode()

    def update(self, direction: SwipeDirection) -> None:
        """Update token with a new swipe, shifting buckets as needed."""
        now = int(time.time())
        elapsed = now - self.ts
        buckets_to_shift = elapsed // settings.swipe_bucket_duration

        # Convert to mutable list for manipulation
        buckets = list(self.buckets)

        # Shift old buckets
        if buckets_to_shift > 0:
            # Prepend empty buckets for elapsed time
            new_buckets = [(0, 0) for _ in range(buckets_to_shift)]
            buckets = new_buckets + buckets
            # Trim to max count
            buckets = buckets[: settings.swipe_bucket_count]
            self.ts = now

        # Ensure at least one bucket exists
        if not buckets:
            buckets = [(0, 0)]
            self.ts = now

        # Increment current bucket
        left, right = buckets[0]
        if direction == SwipeDirection.LEFT:
            buckets[0] = (left + 1, right)
        else:
            buckets[0] = (left, right + 1)

        self.buckets = buckets

    def analyze(self) -> SwipeStats:
        """Analyze buckets to extract useful statistics."""
        stats = SwipeStats()

        if not self.buckets:
            return stats

        # Count totals
        for left, right in self.buckets:
            stats.total_left += left
            stats.total_right += right

        # Count recent (first 3 buckets ≈ 1 minute with 20s buckets)
        for left, right in self.buckets[:3]:
            stats.recent_left += left
            stats.recent_right += right

        # Calculate pickiness (ratio of left swipes)
        total = stats.total_left + stats.total_right
        if total > 0:
            stats.pickiness_ratio = stats.total_left / total

        # Detect streaks (consecutive buckets with only one direction)
        streak_dir: SwipeDirection | None = None
        streak_len = 0
        for left, right in self.buckets:
            if left == 0 and right == 0:
                break  # empty bucket ends streak analysis
            if left > 0 and right == 0:
                if streak_dir == SwipeDirection.LEFT:
                    streak_len += 1
                elif streak_dir is None:
                    streak_dir = SwipeDirection.LEFT
                    streak_len = 1
                else:
                    break
            elif right > 0 and left == 0:
                if streak_dir == SwipeDirection.RIGHT:
                    streak_len += 1
                elif streak_dir is None:
                    streak_dir = SwipeDirection.RIGHT
                    streak_len = 1
                else:
                    break
            else:
                break  # mixed bucket ends streak

        if streak_len >= settings.swipe_streak_threshold:
            stats.streak_direction = streak_dir
            stats.streak_length = streak_len

        return stats


def calculate_price_delta(
    current_price: float, direction: SwipeDirection, stats: SwipeStats
) -> float:
    """Calculate price change based on direction and user stats."""
    # Base change: random percentage of current price
    base_percent = random.uniform(
        settings.swipe_base_percent_min, settings.swipe_base_percent_max
    )
    base_delta = current_price * base_percent

    # Random multiplier
    random_mult = random.uniform(
        settings.swipe_random_multiplier_min, settings.swipe_random_multiplier_max
    )

    # Streak penalty: if user keeps swiping same direction, reduce impact
    streak_mult = 1.0
    if stats.streak_direction == direction:
        streak_mult = settings.swipe_streak_penalty

    # Pickiness bonus: picky users (many left swipes) get bonus on right swipes
    pickiness_mult = 1.0
    if direction == SwipeDirection.RIGHT and stats.pickiness_ratio > 0.6:
        # More left swipes → right swipes count more
        pickiness_mult = 1.0 + (stats.pickiness_ratio - 0.5)
    elif direction == SwipeDirection.LEFT and stats.pickiness_ratio < 0.4:
        # More right swipes → left swipes count more
        pickiness_mult = 1.0 + (0.5 - stats.pickiness_ratio)

    # Final delta
    delta = base_delta * random_mult * streak_mult * pickiness_mult

    # Apply direction
    if direction == SwipeDirection.LEFT:
        delta = -delta

    return delta
