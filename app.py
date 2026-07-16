import sys
import time

import cv2

from airmouse.cursor_controller import CursorController
from airmouse.gesture_engine import (
    DOUBLE_CLICK,
    DRAG_END,
    DRAG_START,
    LEFT_CLICK,
    RIGHT_CLICK,
    SCROLL_DOWN,
    SCROLL_END,
    SCROLL_START,
    SCROLL_UP,
    GestureEngine,
)
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
    click_message = ""
    dragging = False
    scrolling = False

    try:
        # Make sure the webcam is available before entering the display loop.
        if not camera.isOpened():
            print(
                "Error: Could not open the default webcam. Please connect a camera and try again.",
                file=sys.stderr,
            )
            return 1

        while True:
            gesture_debug_text = ""

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

            if results.hand_landmarks:
                first_hand_landmarks = results.hand_landmarks[0]
                event = gesture_engine.detect(first_hand_landmarks)
                gesture_debug_text = gesture_engine.debug_text

                if event == LEFT_CLICK:
                    cursor.left_click()
                    click_message = "LEFT CLICK"
                    click_message_until = time.monotonic() + CLICK_MESSAGE_SECONDS
                elif event == DOUBLE_CLICK:
                    cursor.double_click()
                    click_message = "DOUBLE CLICK"
                    click_message_until = time.monotonic() + CLICK_MESSAGE_SECONDS
                elif event == RIGHT_CLICK:
                    cursor.right_click()
                    click_message = "RIGHT CLICK"
                    click_message_until = time.monotonic() + CLICK_MESSAGE_SECONDS
                elif event == DRAG_START:
                    print("DRAG_START event received")
                    cursor.drag_start()
                    dragging = True
                elif event == DRAG_END:
                    print("DRAG_END event received")
                    cursor.drag_end()
                    dragging = False
                elif event == SCROLL_START:
                    scrolling = True
                elif event == SCROLL_UP:
                    cursor.scroll(2)
                    scrolling = True
                elif event == SCROLL_DOWN:
                    cursor.scroll(-2)
                    scrolling = True
                elif event == SCROLL_END:
                    scrolling = False

                # Scroll mode owns vertical hand movement, so pointer movement
                # pauses until SCROLL_END is received.
                if not scrolling:
                    index_fingertip = first_hand_landmarks[8]
                    cursor.move(index_fingertip.x, index_fingertip.y)

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

            # Briefly confirm the recognized click gesture on the preview.
            if time.monotonic() < click_message_until:
                cv2.putText(
                    frame,
                    click_message,
                    (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                )

            if gesture_debug_text:
                cv2.putText(
                    frame,
                    gesture_debug_text,
                    (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 165, 255),
                    2,
                )

            # Show the live video in a window.
            cv2.imshow(WINDOW_TITLE, frame)

            # Exit the loop when the user presses the quit key.
            if cv2.waitKey(1) & 0xFF == QUIT_KEY:
                break
    finally:
        try:
            # Always release the mouse button, including after Q or an error.
            cursor.drag_end()
        finally:
            # Camera cleanup still runs if releasing the mouse reports an error.
            camera.release()
            cv2.destroyAllWindows()
            tracker.close()

    return 0


if __name__ == "__main__":
    sys.exit(run_camera_test())
