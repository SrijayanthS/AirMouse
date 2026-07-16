"""Persistent settings for AirMouse."""

from dataclasses import asdict, dataclass
import json
from typing import Any, Mapping

from airmouse.resources import resource_path, settings_path


BUNDLED_SETTINGS_PATH = resource_path("config", "settings.json")
SETTINGS_PATH = settings_path()


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
    # A packaged app first checks the user's writable settings. If none exist,
    # it reads the default settings bundled inside AirMouse.app.
    paths = (SETTINGS_PATH, BUNDLED_SETTINGS_PATH)
    for path in dict.fromkeys(paths):
        try:
            values = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(values, dict):
                raise ValueError("settings must be a JSON object")
            return AirMouseSettings.from_mapping(values)
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            continue

    return AirMouseSettings()


def save_settings(settings: AirMouseSettings) -> None:
    """Validate and save settings to the writable settings location."""
    validated_settings = settings.validated()
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(
        json.dumps(asdict(validated_settings), indent=2) + "\n",
        encoding="utf-8",
    )
