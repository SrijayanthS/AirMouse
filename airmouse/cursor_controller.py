"""Cursor movement for AirMouse."""

import pyautogui


class CursorController:
    """Move the cursor using normalized screen coordinates."""

    def __init__(self) -> None:
        """Read and store the current screen dimensions."""
        screen_width, screen_height = pyautogui.size()
        self._screen_width = screen_width
        self._screen_height = screen_height

    def move(self, index_x: float, index_y: float) -> None:
        """Move the cursor to a normalized position between 0.0 and 1.0."""
        clamped_x = min(max(index_x, 0.0), 1.0)
        clamped_y = min(max(index_y, 0.0), 1.0)

        # Pixel coordinates start at zero, so the final valid pixel is size - 1.
        screen_x = round(clamped_x * (self._screen_width - 1))
        screen_y = round(clamped_y * (self._screen_height - 1))

        pyautogui.moveTo(screen_x, screen_y)

    def screen_size(self) -> tuple[int, int]:
        """Return the stored screen width and height in pixels."""
        return self._screen_width, self._screen_height
