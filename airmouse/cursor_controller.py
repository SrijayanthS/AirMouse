"""Cursor movement for AirMouse."""

from typing import Optional

import pyautogui


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

    def move(self, index_x: float, index_y: float) -> None:
        """Move the cursor to a normalized position between 0.0 and 1.0."""
        clamped_x = min(max(index_x, 0.0), 1.0)
        clamped_y = min(max(index_y, 0.0), 1.0)

        # Pixel coordinates start at zero, so the final valid pixel is size - 1.
        target_x = round(clamped_x * (self._screen_width - 1))
        target_y = round(clamped_y * (self._screen_height - 1))

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

        pyautogui.moveTo(smoothed_x, smoothed_y)

    def left_click(self) -> None:
        """Perform one left mouse-button click."""
        pyautogui.click()

    def right_click(self) -> None:
        """Perform one right mouse-button click."""
        pyautogui.rightClick()

    def reset(self) -> None:
        """Clear the saved cursor position used by smoothing."""
        self.previous_x = None
        self.previous_y = None

    def screen_size(self) -> tuple[int, int]:
        """Return the stored screen width and height in pixels."""
        return self._screen_width, self._screen_height
