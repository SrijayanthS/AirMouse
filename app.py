"""Run the AirMouse hand-tracking application."""

import sys

from airmouse.tracking import run_camera_test


if __name__ == "__main__":
    sys.exit(run_camera_test())
