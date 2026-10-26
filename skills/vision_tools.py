"""Vision tool: capture camera/screen images as base64 for the model."""
from langchain_core.tools import tool
import logging

logger = logging.getLogger("jenna.vision.tool")

_vision = None


def _get_vision():
    global _vision
    if _vision is None:
        # Resolve the vision package regardless of how this module was loaded
        # (load_skills imports by stem name, breaking relative imports).
        import os, sys
        _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if _root not in sys.path:
            sys.path.insert(0, _root)
        from vision.manager import VisionManager
        _vision = VisionManager()
        try:
            _vision.start()
        except Exception as e:
            logger.warning("VisionManager start failed: %s", e)
    return _vision


@tool
def capture_camera() -> str:
    """Capture an image from the web camera and return it as base64 JPEG.
    Returns None if no camera is available."""
    import asyncio

    vis = _get_vision()
    try:
        b64 = asyncio.run(vis.get_camera_image_base64())
    except Exception as e:
        logger.warning("Camera capture failed: %s", e)
        return "Camera capture failed: " + str(e)
    if not b64:
        return "No camera available."
    return f"data:image/jpeg;base64,{b64}"


@tool
def capture_screen() -> str:
    """Capture the current screen and return it as base64 JPEG.
    Returns None if screen capture is unavailable."""
    import asyncio

    vis = _get_vision()
    try:
        b64 = asyncio.run(vis.get_screen_image_base64())
    except Exception as e:
        logger.warning("Screen capture failed: %s", e)
        return "Screen capture failed: " + str(e)
    if not b64:
        return "No screen capture available."
    return f"data:image/jpeg;base64,{b64}"
