"""Download the MediaPipe Hand Landmarker model used by AirMouse."""

from pathlib import Path
import sys
import urllib.error
import urllib.request


MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/latest/hand_landmarker.task"
)
PROJECT_ROOT = Path(__file__).resolve().parent
MODEL_PATH = PROJECT_ROOT / "models" / "hand_landmarker.task"
TEMP_PATH = MODEL_PATH.with_suffix(".task.download")


def show_progress(block_number: int, block_size: int, total_size: int) -> None:
    """Display the percentage downloaded when the total size is available."""
    downloaded = block_number * block_size

    if total_size > 0:
        percentage = min(downloaded * 100 // total_size, 100)
        print(f"\rDownloading model: {percentage:3d}%", end="", flush=True)
    else:
        print(f"\rDownloaded {downloaded:,} bytes", end="", flush=True)


def main() -> int:
    """Download the model unless it is already present."""
    if MODEL_PATH.is_file():
        print(f"Model already exists at: {MODEL_PATH}")
        print("No download is needed.")
        return 0

    try:
        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        print("Downloading the official MediaPipe Hand Landmarker model...")
        print(f"Source: {MODEL_URL}")
        print(f"Destination: {MODEL_PATH}")

        urllib.request.urlretrieve(MODEL_URL, TEMP_PATH, show_progress)
        print()
        TEMP_PATH.replace(MODEL_PATH)
    except (OSError, urllib.error.URLError) as error:
        print()
        print(f"Error: Could not download the model: {error}", file=sys.stderr)

        # Remove an incomplete download while leaving any valid model untouched.
        try:
            TEMP_PATH.unlink(missing_ok=True)
        except OSError:
            pass

        return 1

    print(f"Success: Model saved to {MODEL_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
