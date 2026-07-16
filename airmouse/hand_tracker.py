"""Hand detection and landmark drawing for AirMouse."""

from typing import Any

import cv2
import mediapipe as mp

from airmouse.resources import resource_path


# MediaPipe landmark indexes connected by the bones of the hand.
HAND_CONNECTIONS = (
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 4),
    (0, 5),
    (5, 6),
    (6, 7),
    (7, 8),
    (5, 9),
    (9, 10),
    (10, 11),
    (11, 12),
    (9, 13),
    (13, 14),
    (14, 15),
    (15, 16),
    (13, 17),
    (0, 17),
    (17, 18),
    (18, 19),
    (19, 20),
)

MODEL_PATH = resource_path("models", "hand_landmarker.task")


class HandTracker:
    """Detect and draw one hand using MediaPipe Hand Landmarker."""

    def __init__(
        self,
        detection_confidence: float = 0.5,
        tracking_confidence: float = 0.5,
    ) -> None:
        """Create a Hand Landmarker configured for webcam video."""
        if not MODEL_PATH.is_file():
            raise FileNotFoundError(
                "MediaPipe hand landmarker model not found at "
                f"'{MODEL_PATH}'. Place hand_landmarker.task in the project's "
                "models directory."
            )

        options = mp.tasks.vision.HandLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(MODEL_PATH)),
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_hands=1,
            min_hand_detection_confidence=detection_confidence,
            min_hand_presence_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence,
        )
        self._landmarker = mp.tasks.vision.HandLandmarker.create_from_options(options)

    def detect(self, frame: Any, timestamp_ms: int) -> Any:
        """Detect a hand in an OpenCV BGR frame at the given video timestamp."""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        media_pipe_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame,
        )
        return self._landmarker.detect_for_video(media_pipe_image, timestamp_ms)

    def draw(self, frame: Any, results: Any) -> Any:
        """Draw all detected hand landmarks and connections on a frame."""
        frame_height, frame_width = frame.shape[:2]

        for hand_landmarks in results.hand_landmarks:
            points = []
            for landmark in hand_landmarks:
                x = min(max(int(landmark.x * frame_width), 0), frame_width - 1)
                y = min(max(int(landmark.y * frame_height), 0), frame_height - 1)
                points.append((x, y))

            # Draw the connections first so landmark circles appear on top.
            for start_index, end_index in HAND_CONNECTIONS:
                cv2.line(
                    frame,
                    points[start_index],
                    points[end_index],
                    (0, 255, 0),
                    2,
                )

            for point in points:
                cv2.circle(frame, point, 4, (0, 0, 255), -1)

        return frame

    def close(self) -> None:
        """Release resources held by the MediaPipe Hand Landmarker."""
        self._landmarker.close()
