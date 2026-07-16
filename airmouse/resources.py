"""Paths for AirMouse resources in development and packaged builds."""

from pathlib import Path
import sys


def is_packaged() -> bool:
    """Return True when AirMouse is running from a PyInstaller bundle."""
    return bool(getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"))


def resource_path(*parts: str) -> Path:
    """Return a path to a read-only project or bundled resource."""
    if is_packaged():
        base_path = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    else:
        base_path = Path(__file__).resolve().parent.parent

    return base_path.joinpath(*parts)


def settings_path() -> Path:
    """Return the writable settings path for the current environment."""
    if is_packaged() and sys.platform == "darwin":
        return (
            Path.home()
            / "Library"
            / "Application Support"
            / "AirMouse"
            / "settings.json"
        )

    return resource_path("config", "settings.json")
