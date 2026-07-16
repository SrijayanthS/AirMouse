"""Cursor movement for AirMouse."""

import sys
import time
from typing import Optional

import pyautogui

if sys.platform == "darwin":
    import Quartz
else:
    Quartz = None


class CursorController:
    """Move the cursor using normalized screen coordinates."""

    def __init__(self, smoothing_factor: float = 0.35) -> None:
        """Store the screen size and configure cursor smoothing."""
        screen_width, screen_height = pyautogui.size()
        self._screen_width = screen_width
        self._screen_height = screen_height
        self.smoothing_factor = min(max(smoothing_factor, 0.05), 1.0)
        self.previous_x: Optional[float] = None
        self.previous_y: Optional[float] = None
        self._drag_active = False

    def move(self, index_x: float, index_y: float) -> None:
        """Move the cursor to a normalized position between 0.0 and 1.0."""
        clamped_x = min(max(index_x, 0.0), 1.0)
        clamped_y = min(max(index_y, 0.0), 1.0)

        target_x = round(clamped_x * (self._screen_width - 1))
        target_y = round(clamped_y * (self._screen_height - 1))
        self._move_to_screen_position(target_x, target_y)

    def _move_to_screen_position(self, target_x: float, target_y: float) -> None:
        """Smooth, clamp, and apply a target screen position."""
        target_x = min(max(target_x, 0), self._screen_width - 1)
        target_y = min(max(target_y, 0), self._screen_height - 1)

        # Start at the first target instead of smoothing from the top-left corner.
        if self.previous_x is None or self.previous_y is None:
            self.previous_x = target_x
            self.previous_y = target_y

        smoothed_x = self.previous_x + self.smoothing_factor * (
            target_x - self.previous_x
        )
        smoothed_y = self.previous_y + self.smoothing_factor * (
            target_y - self.previous_y
        )

        self.previous_x = smoothed_x
        self.previous_y = smoothed_y

        # Do not add a blocking duration or PyAutoGUI pause to every camera
        # frame. The left button remains down independently during a drag.
        pyautogui.moveTo(smoothed_x, smoothed_y, _pause=False)

        if self._drag_active:
            print(
                "cursor moved while dragging: "
                f"x={smoothed_x:.1f}, y={smoothed_y:.1f}"
            )

    def left_click(self) -> None:
        """Perform one left mouse-button click."""
        pyautogui.click()

    def double_click(self) -> None:
        """Perform one double left click."""
        current_x, current_y = pyautogui.position()

        if sys.platform != "darwin":
            pyautogui.doubleClick(
                x=current_x,
                y=current_y,
                button="left",
                interval=0.08,
            )
            return

        cursor_position = (current_x, current_y)

        def post_left_mouse_event(event_type: int, click_state: int) -> None:
            """Create and post one left-button event at the saved position."""
            event = Quartz.CGEventCreateMouseEvent(
                None,
                event_type,
                cursor_position,
                Quartz.kCGMouseButtonLeft,
            )
            Quartz.CGEventSetIntegerValueField(
                event,
                Quartz.kCGMouseEventClickState,
                click_state,
            )
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)

        post_left_mouse_event(Quartz.kCGEventLeftMouseDown, 1)
        post_left_mouse_event(Quartz.kCGEventLeftMouseUp, 1)
        time.sleep(0.08)
        post_left_mouse_event(Quartz.kCGEventLeftMouseDown, 2)
        post_left_mouse_event(Quartz.kCGEventLeftMouseUp, 2)

    def right_click(self) -> None:
        """Perform one right mouse-button click."""
        pyautogui.rightClick()

    def scroll(self, amount: int) -> None:
        """Scroll vertically by a small signed amount."""
        pyautogui.scroll(amount)

    def drag_start(self) -> None:
        """Press and hold the left mouse button to begin dragging."""
        if not self._drag_active:
            # Set the state first so cleanup can release the button if an error
            # occurs while PyAutoGUI is pressing it.
            self._drag_active = True
            pyautogui.mouseDown()
            print("mouseDown called")

    def drag_end(self) -> None:
        """Release the left mouse button and finish any active drag."""
        if self._drag_active:
            # Only release an active drag. This keeps DRAG_END and cleanup from
            # sending duplicate mouseUp events.
            pyautogui.mouseUp()
            self._drag_active = False
            print("mouseUp called")

    def reset(self) -> None:
        """Clear the saved cursor position used by smoothing."""
        self.previous_x = None
        self.previous_y = None

    def screen_size(self) -> tuple[int, int]:
        """Return the stored screen width and height in pixels."""
        return self._screen_width, self._screen_height
