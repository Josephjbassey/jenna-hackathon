"""Web camera capture using OpenCV."""
import asyncio
import cv2
import numpy as np
from typing import Optional
import logging

logger = logging.getLogger("jenna.vision.camera")


class VisionError(Exception):
    pass


class CameraCapture:
    """Handles image capture from the web camera."""

    def __init__(self, device_index: int = 0):
        self.device_index = device_index
        self._cap: Optional[cv2.VideoCapture] = None

    def start(self) -> bool:
        """Starts the camera."""
        if self._cap is not None:
            return True

        logger.info("Starting camera (device %s)...", self.device_index)
        self._cap = cv2.VideoCapture(self.device_index)
        if not self._cap.isOpened():
            self._cap = None
            logger.error("Failed to open camera device %s", self.device_index)
            return False
        logger.info("Camera started successfully.")
        return True

    @property
    def is_available(self) -> bool:
        """Returns True if the camera is currently open and available."""
        return self._cap is not None

    def stop(self) -> None:
        """Stops the camera."""
        if self._cap is not None:
            logger.info("Stopping camera...")
            self._cap.release()
            self._cap = None

    async def capture_frame(self) -> np.ndarray:
        """Captures a single frame from the camera."""
        if self._cap is None:
            raise VisionError("Camera is not started.")

        loop = asyncio.get_running_loop()
        ret, frame = await loop.run_in_executor(None, self._cap.read)

        if not ret:
            logger.error("Failed to capture frame from camera.")
            raise VisionError("Failed to capture frame from camera.")

        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return frame_rgb
