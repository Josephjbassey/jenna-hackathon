"""Basic motion detection using frame differencing."""
import cv2
import numpy as np
import logging

logger = logging.getLogger("jenna.vision.activity")


class MotionDetector:
    """Detects basic motion using frame differencing."""

    def __init__(self, threshold: int = 25, min_area: int = 500):
        self.threshold = threshold
        self.min_area = min_area
        self.previous_frame = None

    def process_frame(self, frame_rgb: np.ndarray) -> bool:
        """
        Processes a frame and returns True if motion is detected.
        """
        # Convert to grayscale and blur
        gray = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if self.previous_frame is None:
            self.previous_frame = gray
            return False

        # Compute absolute difference
        frame_delta = cv2.absdiff(self.previous_frame, gray)
        thresh = cv2.threshold(frame_delta, self.threshold, 255, cv2.THRESH_BINARY)[1]

        # Dilate to fill holes
        thresh = cv2.dilate(thresh, None, iterations=2)

        # Find contours
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        motion_detected = False
        for c in contours:
            if cv2.contourArea(c) > self.min_area:
                motion_detected = True
                break

        self.previous_frame = gray
        return motion_detected
