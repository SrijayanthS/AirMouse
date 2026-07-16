"""Hand gesture recognition for AirMouse."""

import math
import time
from typing import Optional, Protocol, Sequence


LEFT_CLICK = "LEFT_CLICK"
DOUBLE_CLICK = "DOUBLE_CLICK"
RIGHT_CLICK = "RIGHT_CLICK"
DRAG_START = "DRAG_START"
DRAG_END = "DRAG_END"
SCROLL_START = "SCROLL_START"
SCROLL_UP = "SCROLL_UP"
SCROLL_DOWN = "SCROLL_DOWN"
SCROLL_END = "SCROLL_END"
TOGGLE_CONTROL = "TOGGLE_CONTROL"
THUMB_TIP = 4
INDEX_PIP = 6
INDEX_FINGERTIP = 8
PALM_ANCHOR = 9
MIDDLE_PIP = 10
MIDDLE_FINGERTIP = 12
RING_PIP = 14
RING_FINGERTIP = 16
LITTLE_PIP = 18
LITTLE_FINGERTIP = 20
FINGER_STATE_MARGIN = 0.02


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
        scroll_dead_zone: float = 0.02,
        scroll_interval: float = 0.12,
        fist_hold_seconds: float = 1.0,
    ) -> None:
        """Configure pinch, scroll, and fist timing."""
        if pinch_threshold < 0:
            raise ValueError("pinch_threshold cannot be negative")
        if release_threshold <= pinch_threshold:
            raise ValueError("release_threshold must be greater than pinch_threshold")
        if cooldown_seconds < 0:
            raise ValueError("cooldown_seconds cannot be negative")
        if scroll_dead_zone < 0:
            raise ValueError("scroll_dead_zone cannot be negative")
        if scroll_interval < 0:
            raise ValueError("scroll_interval cannot be negative")
        if fist_hold_seconds <= 0:
            raise ValueError("fist_hold_seconds must be greater than zero")

        self.pinch_threshold = pinch_threshold
        self.release_threshold = release_threshold
        self.cooldown_seconds = cooldown_seconds
        self.scroll_dead_zone = scroll_dead_zone
        self.scroll_interval = scroll_interval
        self.fist_hold_seconds = fist_hold_seconds

        self._left_pinch_active = False
        self._right_pinch_active = False
        self._double_pinch_active = False
        self._drag_active = False
        self._scroll_active = False
        self._previous_scroll_y: Optional[float] = None
        self._last_scroll_time: Optional[float] = None
        self._fist_started_at: Optional[float] = None
        self._fist_latched = False
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

    @staticmethod
    def _is_scroll_pose(landmarks: Sequence[Landmark]) -> bool:
        """Return whether index/middle are up and ring/little are folded."""
        index_extended = (
            landmarks[INDEX_FINGERTIP].y
            < landmarks[INDEX_PIP].y - FINGER_STATE_MARGIN
        )
        middle_extended = (
            landmarks[MIDDLE_FINGERTIP].y
            < landmarks[MIDDLE_PIP].y - FINGER_STATE_MARGIN
        )
        ring_folded = (
            landmarks[RING_FINGERTIP].y
            > landmarks[RING_PIP].y + FINGER_STATE_MARGIN
        )
        little_folded = (
            landmarks[LITTLE_FINGERTIP].y
            > landmarks[LITTLE_PIP].y + FINGER_STATE_MARGIN
        )
        return index_extended and middle_extended and ring_folded and little_folded

    @staticmethod
    def _is_closed_fist(landmarks: Sequence[Landmark]) -> bool:
        """Return whether all four fingertips are folded toward the palm."""
        return (
            landmarks[INDEX_FINGERTIP].y
            > landmarks[INDEX_PIP].y + FINGER_STATE_MARGIN
            and landmarks[MIDDLE_FINGERTIP].y
            > landmarks[MIDDLE_PIP].y + FINGER_STATE_MARGIN
            and landmarks[RING_FINGERTIP].y
            > landmarks[RING_PIP].y + FINGER_STATE_MARGIN
            and landmarks[LITTLE_FINGERTIP].y
            > landmarks[LITTLE_PIP].y + FINGER_STATE_MARGIN
        )

    def _clear_action_states(self) -> None:
        """Clear click, drag, and scroll latches after a control toggle."""
        self._left_pinch_active = False
        self._right_pinch_active = False
        self._double_pinch_active = False
        self._drag_active = False
        self._scroll_active = False
        self._previous_scroll_y = None
        self._last_scroll_time = None
        self._suppress_left_until_release = False
        self._suppress_right_until_release = False
        self._suppress_double_until_release = False

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
        scroll_pose = self._is_scroll_pose(landmarks)
        closed_fist = self._is_closed_fist(landmarks)

        # A fist has top priority so no action gesture fires while it is held.
        if closed_fist:
            if self._fist_latched:
                self.debug_text = "FIST HELD"
                return None

            if self._fist_started_at is None:
                self._fist_started_at = current_time
                self.debug_text = "HOLD FIST"
                return None

            if current_time - self._fist_started_at >= self.fist_hold_seconds:
                self._fist_latched = True
                self._clear_action_states()
                self.debug_text = "CONTROL TOGGLE"
                return TOGGLE_CONTROL

            self.debug_text = "HOLD FIST"
            return None

        # Opening any finger re-arms the fist for a future toggle.
        self._fist_started_at = None
        self._fist_latched = False

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

        # Once scrolling starts, it suppresses every click and drag gesture
        # until the two-up/two-down finger pose is released.
        if self._scroll_active:
            if not scroll_pose:
                self._scroll_active = False
                self._previous_scroll_y = None
                self._last_scroll_time = None
                self.debug_text = "SCROLL END"
                return SCROLL_END

            current_scroll_y = landmarks[PALM_ANCHOR].y
            assert self._previous_scroll_y is not None
            vertical_change = current_scroll_y - self._previous_scroll_y
            self.debug_text = "SCROLL MODE"

            if abs(vertical_change) < self.scroll_dead_zone:
                return None
            if (
                self._last_scroll_time is not None
                and current_time - self._last_scroll_time < self.scroll_interval
            ):
                return None

            self._previous_scroll_y = current_scroll_y
            self._last_scroll_time = current_time
            if vertical_change < 0:
                self.debug_text = "SCROLL UP"
                return SCROLL_UP

            self.debug_text = "SCROLL DOWN"
            return SCROLL_DOWN

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

        no_click_pinch = (
            left_distance >= self.release_threshold
            and right_distance >= self.release_threshold
            and drag_distance >= self.release_threshold
            and double_distance >= self.release_threshold
            and not self._left_pinch_active
            and not self._right_pinch_active
            and not self._double_pinch_active
        )
        if scroll_pose and no_click_pinch:
            self._scroll_active = True
            self._previous_scroll_y = landmarks[PALM_ANCHOR].y
            self._last_scroll_time = current_time
            self.debug_text = "SCROLL MODE"
            return SCROLL_START

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
