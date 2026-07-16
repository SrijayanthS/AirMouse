"""Hand gesture recognition for AirMouse."""

import math
import time
from typing import Optional, Protocol, Sequence


LEFT_CLICK = "LEFT_CLICK"
RIGHT_CLICK = "RIGHT_CLICK"
THUMB_TIP = 4
INDEX_FINGERTIP = 8
MIDDLE_FINGERTIP = 12


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
        self._right_pinch_active = False
        self._last_right_click_time: Optional[float] = None

    def detect(self, landmarks: Sequence[Landmark]) -> Optional[str]:
        """Return one click event for a new fingertip pinch, otherwise None."""
        if len(landmarks) <= MIDDLE_FINGERTIP:
            raise ValueError("Gesture detection requires all 21 hand landmarks")

        thumb_tip = landmarks[THUMB_TIP]
        index_tip = landmarks[INDEX_FINGERTIP]
        middle_tip = landmarks[MIDDLE_FINGERTIP]

        # Thumb-to-index distance controls left click.
        left_distance = math.hypot(
            thumb_tip.x - index_tip.x,
            thumb_tip.y - index_tip.y,
        )

        # Thumb-to-middle distance controls right click independently.
        right_distance = math.hypot(
            thumb_tip.x - middle_tip.x,
            thumb_tip.y - middle_tip.y,
        )

        # Separating either finger pair arms that gesture for its next click.
        if left_distance >= self.release_threshold:
            self._pinch_active = False
        if right_distance >= self.release_threshold:
            self._right_pinch_active = False

        new_left_pinch = (
            not self._pinch_active and left_distance <= self.pinch_threshold
        )
        new_right_pinch = (
            not self._right_pinch_active and right_distance <= self.pinch_threshold
        )

        # Latch both new pinches, even when left-click priority resolves an
        # ambiguous frame. This prevents the held right pinch firing next frame.
        if new_left_pinch:
            self._pinch_active = True
        if new_right_pinch:
            self._right_pinch_active = True

        if not new_left_pinch and not new_right_pinch:
            return None

        current_time = time.monotonic()

        # Check left click first so it wins when both pinches are detected.
        if new_left_pinch:
            if (
                self._last_click_time is not None
                and current_time - self._last_click_time < self.cooldown_seconds
            ):
                return None

            self._last_click_time = current_time
            return LEFT_CLICK

        if (
            self._last_right_click_time is not None
            and current_time - self._last_right_click_time < self.cooldown_seconds
        ):
            return None

        self._last_right_click_time = current_time
        return RIGHT_CLICK
