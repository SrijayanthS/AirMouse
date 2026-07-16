"""Persistent settings for AirMouse."""

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Mapping


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SETTINGS_PATH = PROJECT_ROOT / "config" / "settings.json"


@dataclass
class AirMouseSettings:
    """User-adjustable AirMouse settings."""

    cursor_smoothing: float = 0.35
    pinch_sensitivity: float = 0.05
    scroll_sensitivity: int = 2

    def validated(self) -> "AirMouseSettings":
        """Return a copy with every value inside the supported UI range."""
        return AirMouseSettings(
            cursor_smoothing=min(max(float(self.cursor_smoothing), 0.05), 1.0),
            pinch_sensitivity=min(max(float(self.pinch_sensitivity), 0.02), 0.10),
            scroll_sensitivity=min(max(int(self.scroll_sensitivity), 1), 5),
        )

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any]) -> "AirMouseSettings":
        """Build validated settings from decoded JSON values."""
        settings = cls(
            cursor_smoothing=values.get("cursor_smoothing", cls.cursor_smoothing),
            pinch_sensitivity=values.get(
                "pinch_sensitivity", cls.pinch_sensitivity
            ),
            scroll_sensitivity=values.get(
                "scroll_sensitivity", cls.scroll_sensitivity
            ),
        )
        return settings.validated()


def load_settings() -> AirMouseSettings:
    """Load saved settings, falling back to defaults if the file is invalid."""
    try:
        values = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        if not isinstance(values, dict):
            raise ValueError("settings must be a JSON object")
        return AirMouseSettings.from_mapping(values)
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return AirMouseSettings()


def save_settings(settings: AirMouseSettings) -> None:
    """Validate and save settings to config/settings.json."""
    validated_settings = settings.validated()
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(
        json.dumps(asdict(validated_settings), indent=2) + "\n",
        encoding="utf-8",
    )
