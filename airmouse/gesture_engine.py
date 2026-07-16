"""Hand gesture recognition for AirMouse."""

import math
import time
from typing import Optional, Protocol, Sequence


LEFT_CLICK = "LEFT_CLICK"
DOUBLE_CLICK = "DOUBLE_CLICK"
RIGHT_CLICK = "RIGHT_CLICK"
DRAG_START = "DRAG_START"
DRAG_END = "DRAG_END"
THUMB_TIP = 4
INDEX_FINGERTIP = 8
MIDDLE_FINGERTIP = 12
RING_FINGERTIP = 16
LITTLE_FINGERTIP = 20


class Landmark(Protocol):
    """Coordinates required from a MediaPipe hand landmark."""

    x: float
    y: float


class GestureEngine:
    """Recognize click and drag gestures from hand landmarks."""

    def __init__(
        self,
        pinch_threshold: float = 0.05,
        release_threshold: float = 0.08,
        cooldown_seconds: float = 0.35,
    ) -> None:
        """Configure pinch distances and click cooldown."""
        if pinch_threshold < 0:
            raise ValueError("pinch_threshold cannot be negative")
        if release_threshold <= pinch_threshold:
            raise ValueError("release_threshold must be greater than pinch_threshold")
        if cooldown_seconds < 0:
            raise ValueError("cooldown_seconds cannot be negative")

        self.pinch_threshold = pinch_threshold
        self.release_threshold = release_threshold
        self.cooldown_seconds = cooldown_seconds

        self._left_pinch_active = False
        self._right_pinch_active = False
        self._double_pinch_active = False
        self._drag_active = False
        self._last_left_click_time: Optional[float] = None
        self._last_right_click_time: Optional[float] = None
        self._suppress_left_until_release = False
        self._suppress_right_until_release = False
        self._suppress_double_until_release = False
        self.debug_text = ""

    @staticmethod
    def _distance(first: Landmark, second: Landmark) -> float:
        """Return the normalized two-dimensional distance between landmarks."""
        return math.hypot(first.x - second.x, first.y - second.y)

    def detect(self, landmarks: Sequence[Landmark]) -> Optional[str]:
        """Return one click or drag event, otherwise None."""
        self.debug_text = ""

        if len(landmarks) <= LITTLE_FINGERTIP:
            raise ValueError("Gesture detection requires all 21 hand landmarks")

        thumb_tip = landmarks[THUMB_TIP]
        left_distance = self._distance(thumb_tip, landmarks[INDEX_FINGERTIP])
        right_distance = self._distance(thumb_tip, landmarks[MIDDLE_FINGERTIP])
        drag_distance = self._distance(thumb_tip, landmarks[RING_FINGERTIP])
        double_distance = self._distance(thumb_tip, landmarks[LITTLE_FINGERTIP])
        current_time = time.monotonic()

        # Drag has priority over both click gestures while the ring pinch is held.
        if self._drag_active:
            if drag_distance >= self.release_threshold:
                self._drag_active = False
                self._suppress_left_until_release = (
                    left_distance < self.release_threshold
                )
                self._suppress_right_until_release = (
                    right_distance < self.release_threshold
                )
                self._suppress_double_until_release = (
                    double_distance < self.release_threshold
                )
                self.debug_text = "DRAG END"
                return DRAG_END

            self.debug_text = "DRAGGING"
            return None

        # A new thumb-ring pinch begins dragging immediately and only once.
        if drag_distance <= self.pinch_threshold:
            self._drag_active = True
            self._left_pinch_active = False
            self._right_pinch_active = False
            self._double_pinch_active = False
            self.debug_text = "DRAG START"
            return DRAG_START

        # Ignore click fingers that are still pinched when a drag ends.
        if self._suppress_left_until_release:
            if left_distance >= self.release_threshold:
                self._suppress_left_until_release = False
            return None
        if self._suppress_right_until_release:
            if right_distance >= self.release_threshold:
                self._suppress_right_until_release = False
            return None
        if self._suppress_double_until_release:
            if double_distance >= self.release_threshold:
                self._suppress_double_until_release = False
            return None

        # Thumb-little is a dedicated, one-shot double click. Keeping this
        # check before right click gives double click priority if ambiguous.
        if self._double_pinch_active:
            if double_distance >= self.release_threshold:
                self._double_pinch_active = False
            else:
                return None
        elif double_distance <= self.pinch_threshold:
            self._double_pinch_active = True
            return DOUBLE_CLICK

        # Thumb-index remains a short pinch-and-release left click.
        if self._left_pinch_active:
            if left_distance < self.release_threshold:
                return None

            self._left_pinch_active = False
            if (
                self._last_left_click_time is not None
                and current_time - self._last_left_click_time < self.cooldown_seconds
            ):
                return None

            self._last_left_click_time = current_time
            return LEFT_CLICK

        if left_distance <= self.pinch_threshold:
            self._left_pinch_active = True
            return None

        # Thumb-middle keeps its independent, one-shot right-click latch.
        if right_distance >= self.release_threshold:
            self._right_pinch_active = False

        if self._right_pinch_active or right_distance > self.pinch_threshold:
            return None

        self._right_pinch_active = True
        if (
            self._last_right_click_time is not None
            and current_time - self._last_right_click_time < self.cooldown_seconds
        ):
            return None

        self._last_right_click_time = current_time
        return RIGHT_CLICK
