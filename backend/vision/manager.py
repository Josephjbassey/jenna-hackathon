"""Orchestrates vision tasks: camera, screen capture, and basic processing."""
import asyncio
import base64
import io
import logging

import numpy as np
from PIL import Image

from .camera import CameraCapture
from .screen import ScreenCapture
from .activity import MotionDetector

logger = logging.getLogger("jenna.vision.manager")


class VisionManager:
    """Orchestrates vision tasks: camera, screen capture, and basic processing."""

    def __init__(self):
        self.camera = CameraCapture(device_index=0)
        self.screen = ScreenCapture(monitor_index=1)
        self.motion_detector = MotionDetector()
        self._camera_available = False
        self._screen_available = False

    def start(self):
        """Starts hardware interfaces."""
        try:
            self._camera_available = self.camera.start()
            if not self._camera_available:
                logger.warning("Camera failed to start, vision will be disabled.")
        except Exception as e:
            logger.warning("Camera failed to start, vision will be disabled: %s", e)
            self._camera_available = False

        try:
            self.screen.start()
            self._screen_available = True
        except Exception as e:
            logger.warning("Screen capture failed to start: %s", e)
            self._screen_available = False

    def stop(self):
        """Stops hardware interfaces."""
        self.camera.stop()
        self.screen.stop()

    async def get_camera_image_base64(self):
        """Captures a camera frame and returns it as a base64 jpeg string."""
        if not self._camera_available:
            return None
        frame = await self.camera.capture_frame()
        return self._np_to_base64(frame)

    async def get_screen_image_base64(self):
        """Captures a screen frame and returns it as a base64 jpeg string."""
        if not self._screen_available:
            return None
        frame = await self.screen.capture_screen()
        return self._np_to_base64(frame)

    def _np_to_base64(self, img_np: np.ndarray) -> str:
        """Converts an RGB numpy array to a base64 encoded JPEG."""
        img = Image.fromarray(img_np)
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")
