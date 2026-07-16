import sys
import time

import cv2

from airmouse.cursor_controller import CursorController
from airmouse.gesture_engine import LEFT_CLICK, GestureEngine
from airmouse.hand_tracker import HandTracker


WINDOW_TITLE = "AirMouse - Camera Test"
QUIT_KEY = ord("q")
CLICK_MESSAGE_SECONDS = 0.5


def run_camera_test() -> int:
    """Open the webcam, show hand landmarks, and exit on 'q'."""
    tracker = HandTracker()
    cursor = CursorController()
    gesture_engine = GestureEngine()
    camera = cv2.VideoCapture(0)
    last_timestamp_ms = -1
    click_message_until = 0.0

    try:
        # Make sure the webcam is available before entering the display loop.
        if not camera.isOpened():
            print(
                "Error: Could not open the default webcam. Please connect a camera and try again.",
                file=sys.stderr,
            )
            return 1

        while True:
            # Read one frame from the webcam.
            success, frame = camera.read()
            if not success:
                print("Error: Failed to read a frame from the webcam.", file=sys.stderr)
                break

            # Mirror the frame horizontally so it feels like a normal camera view.
            frame = cv2.flip(frame, 1)

            # MediaPipe video timestamps must increase for every frame.
            current_time_ms = time.monotonic_ns() // 1_000_000
            timestamp_ms = max(current_time_ms, last_timestamp_ms + 1)
            last_timestamp_ms = timestamp_ms

            # Detect one hand in the mirrored frame.
            results = tracker.detect(frame, timestamp_ms)

            # Landmark 8 is the tip of the index finger.
            if results.hand_landmarks:
                first_hand_landmarks = results.hand_landmarks[0]
                index_fingertip = first_hand_landmarks[8]
                cursor.move(index_fingertip.x, index_fingertip.y)

                event = gesture_engine.detect(first_hand_landmarks)
                if event == LEFT_CLICK:
                    cursor.left_click()
                    click_message_until = time.monotonic() + CLICK_MESSAGE_SECONDS

            # Draw the detected hand landmarks on the camera frame.
            tracker.draw(frame, results)

            # Add a simple on-screen hint for the user.
            cv2.putText(
                frame,
                "Press Q to quit",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
            )

            # Briefly confirm a recognized left-click gesture on the preview.
            if time.monotonic() < click_message_until:
                cv2.putText(
                    frame,
                    "LEFT CLICK",
                    (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                )

            # Show the live video in a window.
            cv2.imshow(WINDOW_TITLE, frame)

            # Exit the loop when the user presses the quit key.
            if cv2.waitKey(1) & 0xFF == QUIT_KEY:
                break
    finally:
        # Always release the camera so the device is not left hanging.
        camera.release()

        # Always close any OpenCV windows that were opened.
        cv2.destroyAllWindows()

        # Always release resources used by MediaPipe Hands.
        tracker.close()

    return 0


if __name__ == "__main__":
    sys.exit(run_camera_test())
