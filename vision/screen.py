"""Screen capture using mss."""
import asyncio
import numpy as np
from PIL import Image
import logging

logger = logging.getLogger("jenna.vision.screen")


class VisionError(Exception):
    pass


class ScreenCapture:
    """Handles screen capture using mss."""

    def __init__(self, monitor_index: int = 1):
        self.monitor_index = monitor_index  # 1 is usually the primary monitor
        self._sct = None

    def start(self) -> None:
        """Starts the mss instance."""
        if self._sct is not None:
            return

        try:
            import mss
            logger.info("Starting screen capture...")
            self._sct = mss.mss()
            logger.info("Screen capture started.")
        except ImportError:
            logger.error("mss is not installed. Screen capture will be disabled.")
            self._sct = None
        except Exception as e:
            logger.error("Failed to initialize screen capture: %s", e)
            raise VisionError(f"Failed to initialize screen capture: {e}") from e

    def stop(self) -> None:
        """Stops the mss instance."""
        if self._sct is not None:
            logger.info("Stopping screen capture...")
            self._sct.close()
            self._sct = None

    async def capture_screen(self) -> np.ndarray:
        """Captures the current screen."""
        if self._sct is None:
            raise VisionError("Screen capture is not started.")

        try:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, self._capture_sync)
        except Exception as e:
            logger.error("Failed to capture screen: %s", e)
            raise VisionError(f"Failed to capture screen: {e}") from e

    def _capture_sync(self) -> np.ndarray:
        """Synchronous screen capture logic."""
        monitor = self._sct.monitors[self.monitor_index]
        sct_img = self._sct.grab(monitor)

        # Convert to numpy array (BGRA)
        img_np = np.array(sct_img)

        # Convert BGRA to RGB
        img_rgb = img_np[:, :, :3][:, :, ::-1]

        return img_rgb
