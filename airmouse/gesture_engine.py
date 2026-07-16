"""Hand gesture recognition for AirMouse."""

import math
import time
from typing import Optional, Protocol, Sequence


LEFT_CLICK = "LEFT_CLICK"
THUMB_TIP = 4
INDEX_FINGERTIP = 8


class Landmark(Protocol):
    """Coordinates required from a MediaPipe hand landmark."""

    x: float
    y: float


class GestureEngine:
    """Recognize gestures from a sequence of hand landmarks."""

    def __init__(
        self,
        pinch_threshold: float = 0.05,
        release_threshold: float = 0.08,
        cooldown_seconds: float = 0.35,
    ) -> None:
        """Configure the pinch distances and delay between click events."""
        if pinch_threshold < 0:
            raise ValueError("pinch_threshold cannot be negative")
        if release_threshold <= pinch_threshold:
            raise ValueError("release_threshold must be greater than pinch_threshold")
        if cooldown_seconds < 0:
            raise ValueError("cooldown_seconds cannot be negative")

        self.pinch_threshold = pinch_threshold
        self.release_threshold = release_threshold
        self.cooldown_seconds = cooldown_seconds

        self._pinch_active = False
        self._last_click_time: Optional[float] = None

    def detect(self, landmarks: Sequence[Landmark]) -> Optional[str]:
        """Return LEFT_CLICK for a new thumb-and-index pinch, otherwise None."""
        if len(landmarks) <= INDEX_FINGERTIP:
            raise ValueError("Gesture detection requires all 21 hand landmarks")

        thumb_tip = landmarks[THUMB_TIP]
        index_tip = landmarks[INDEX_FINGERTIP]

        # MediaPipe supplies normalized coordinates, so this is a normalized
        # two-dimensional distance between the fingertips.
        distance = math.hypot(
            thumb_tip.x - index_tip.x,
            thumb_tip.y - index_tip.y,
        )

        # Separating the fingers beyond this threshold arms the next click.
        if distance >= self.release_threshold:
            self._pinch_active = False
            return None

        # A held pinch remains active and must not create repeated clicks.
        if self._pinch_active or distance > self.pinch_threshold:
            return None

        self._pinch_active = True
        current_time = time.monotonic()

        # The cooldown filters out pinches that happen too soon after a click.
        if (
            self._last_click_time is not None
            and current_time - self._last_click_time < self.cooldown_seconds
        ):
            return None

        self._last_click_time = current_time
        return LEFT_CLICK
