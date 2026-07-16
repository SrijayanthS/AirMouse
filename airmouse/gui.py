"""Tkinter launcher and settings window for AirMouse."""

import queue
import sys
import threading
import tkinter as tk
from tkinter import ttk
import traceback
from types import TracebackType
from typing import Optional

from airmouse.config import AirMouseSettings, load_settings, save_settings
from airmouse.tracking import run_camera_test


class AirMouseLauncher:
    """Manage settings and one background AirMouse tracking session."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("AirMouse")
        self.root.resizable(False, False)

        settings = load_settings()
        self.smoothing_var = tk.DoubleVar(value=settings.cursor_smoothing)
        self.pinch_var = tk.DoubleVar(value=settings.pinch_sensitivity)
        self.scroll_var = tk.IntVar(value=settings.scroll_sensitivity)
        self.status_var = tk.StringVar(value="Stopped")

        self._stop_event = threading.Event()
        self._tracking_thread: Optional[threading.Thread] = None
        self._messages: queue.Queue[tuple[str, object]] = queue.Queue()
        self._closing = False

        self._build_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(100, self._poll_worker)

    def _build_widgets(self) -> None:
        """Create the launcher controls."""
        container = ttk.Frame(self.root, padding=16)
        container.grid(row=0, column=0, sticky="nsew")

        ttk.Label(container, text="AirMouse", font=("TkDefaultFont", 18, "bold")).grid(
            row=0, column=0, columnspan=2, pady=(0, 12)
        )

        ttk.Label(container, text="Status:").grid(row=1, column=0, sticky="w")
        ttk.Label(container, textvariable=self.status_var).grid(
            row=1, column=1, sticky="w"
        )

        tk.Scale(
            container,
            label="Cursor smoothing",
            variable=self.smoothing_var,
            from_=0.05,
            to=1.0,
            resolution=0.05,
            orient=tk.HORIZONTAL,
            length=280,
        ).grid(row=2, column=0, columnspan=2, pady=(8, 0))

        tk.Scale(
            container,
            label="Pinch sensitivity",
            variable=self.pinch_var,
            from_=0.02,
            to=0.10,
            resolution=0.005,
            orient=tk.HORIZONTAL,
            length=280,
        ).grid(row=3, column=0, columnspan=2)

        tk.Scale(
            container,
            label="Scroll sensitivity",
            variable=self.scroll_var,
            from_=1,
            to=5,
            resolution=1,
            orient=tk.HORIZONTAL,
            length=280,
        ).grid(row=4, column=0, columnspan=2)

        ttk.Button(container, text="Start AirMouse", command=self.start).grid(
            row=5, column=0, sticky="ew", padx=(0, 4), pady=(12, 4)
        )
        ttk.Button(container, text="Stop AirMouse", command=self.stop).grid(
            row=5, column=1, sticky="ew", padx=(4, 0), pady=(12, 4)
        )
        ttk.Button(
            container,
            text="Reset to defaults",
            command=self.reset_defaults,
        ).grid(row=6, column=0, columnspan=2, sticky="ew")

    def _settings_from_controls(self) -> AirMouseSettings:
        """Create a validated settings snapshot from the sliders."""
        return AirMouseSettings(
            cursor_smoothing=self.smoothing_var.get(),
            pinch_sensitivity=self.pinch_var.get(),
            scroll_sensitivity=self.scroll_var.get(),
        ).validated()

    def start(self) -> None:
        """Start one tracking session on a worker thread."""
        if self._tracking_thread is not None and self._tracking_thread.is_alive():
            self.status_var.set("AirMouse is already running")
            return

        settings = self._settings_from_controls()
        save_settings(settings)
        self._stop_event = threading.Event()
        self.status_var.set("Starting...")

        self._tracking_thread = threading.Thread(
            target=self._run_tracking,
            args=(settings, self._stop_event),
            name="AirMouseTracking",
            daemon=True,
        )
        self._tracking_thread.start()
        self.status_var.set("Running")

    def _run_tracking(
        self,
        settings: AirMouseSettings,
        stop_event: threading.Event,
    ) -> None:
        """Run tracking without touching Tkinter from the worker thread."""
        try:
            result = run_camera_test(stop_event=stop_event, settings=settings)
            self._messages.put(("finished", result))
        except Exception as error:
            print("AirMouse tracking session failed:", file=sys.stderr)
            traceback.print_exc()
            self._messages.put(("error", str(error)))

    def stop(self) -> None:
        """Request a safe stop for the active tracking session."""
        if self._tracking_thread is None or not self._tracking_thread.is_alive():
            self.status_var.set("Stopped")
            return

        self.status_var.set("Stopping...")
        self._stop_event.set()

    def reset_defaults(self) -> None:
        """Restore and save the default slider values."""
        defaults = AirMouseSettings()
        self.smoothing_var.set(defaults.cursor_smoothing)
        self.pinch_var.set(defaults.pinch_sensitivity)
        self.scroll_var.set(defaults.scroll_sensitivity)
        save_settings(defaults)
        self.status_var.set("Defaults restored (applies on next start)")

    def _poll_worker(self) -> None:
        """Process worker results safely on the Tkinter thread."""
        try:
            while True:
                message_type, value = self._messages.get_nowait()
                if message_type == "error":
                    self.status_var.set(f"Error: {value}")
                elif value == 0:
                    self.status_var.set("Stopped")
                else:
                    self.status_var.set("Stopped: camera unavailable")
        except queue.Empty:
            pass

        if self._tracking_thread is not None and not self._tracking_thread.is_alive():
            self._tracking_thread = None

        if self._closing and self._tracking_thread is None:
            self.root.destroy()
            return

        self.root.after(100, self._poll_worker)

    def close(self) -> None:
        """Save settings, stop tracking, and close after cleanup finishes."""
        if self._closing:
            return

        self._closing = True
        save_settings(self._settings_from_controls())
        self.stop()

        if self._tracking_thread is None:
            self.root.destroy()


def main() -> None:
    """Open the AirMouse launcher window."""
    root: Optional[tk.Tk] = None
    try:
        root = tk.Tk()

        # Tkinter normally sends callback failures to stderr. Installing an
        # explicit handler keeps that behavior clear in packaged test builds.
        def log_callback_exception(
            exception_type: type[BaseException],
            exception: BaseException,
            exception_traceback: Optional[TracebackType],
        ) -> None:
            print("AirMouse launcher callback failed:", file=sys.stderr)
            traceback.print_exception(
                exception_type,
                exception,
                exception_traceback,
                file=sys.stderr,
            )

        root.report_callback_exception = log_callback_exception
        AirMouseLauncher(root)
        root.mainloop()
    except Exception:
        print("AirMouse launcher failed to initialize:", file=sys.stderr)
        traceback.print_exc()
        if root is not None:
            try:
                root.destroy()
            except tk.TclError:
                pass
        raise


if __name__ == "__main__":
    main()
