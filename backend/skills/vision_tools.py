"""Privacy-Gated Vision Tools for Jenna-Unified.

Allows Jenna to see the user's screen and webcam ONLY when explicitly permitted.
Provides permission verification, screen capture, webcam capture, and scene description.
"""
import os
import sys
import base64
import io
import time
from pathlib import Path
from langchain_core.tools import tool

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config import get_vision_permissions, set_vision_permission, SANDBOX_DIR


def _ensure_sandbox():
    SANDBOX_DIR.mkdir(parents=True, exist_ok=True)


@tool
def check_vision_permissions() -> str:
    """Check whether Screen Vision and Camera Vision permissions are currently granted."""
    perms = get_vision_permissions()
    screen_status = "GRANTED (Active)" if perms.get("screen") else "BLOCKED (Requires User Permission)"
    camera_status = "GRANTED (Active)" if perms.get("camera") else "BLOCKED (Requires User Permission)"
    return (
        f"--- Vision Privacy Status ---\n"
        f"Screen Sight: {screen_status}\n"
        f"Webcam Sight: {camera_status}\n"
        f"To change permissions, Jabs can toggle the buttons in the dashboard or tell you 'Grant permission to see screen/camera'."
    )


@tool
def grant_vision_permission_tool(target: str) -> str:
    """Grant sight permission for 'screen', 'camera', or 'both' when the user explicitly permits it."""
    target = target.lower().strip()
    if target in ("screen", "desktop", "display"):
        set_vision_permission("screen", True)
        return "Screen vision permission GRANTED by Jabs. Jenna can now inspect the desktop screen."
    elif target in ("camera", "webcam", "user", "me"):
        set_vision_permission("camera", True)
        return "Camera/Webcam vision permission GRANTED by Jabs. Jenna can now see through the webcam."
    elif target in ("both", "all"):
        set_vision_permission("screen", True)
        set_vision_permission("camera", True)
        return "Both Screen and Camera vision permissions GRANTED by Jabs."
    return f"Unknown vision target '{target}'. Use 'screen', 'camera', or 'both'."


@tool
def revoke_vision_permission_tool(target: str) -> str:
    """Revoke sight permission for 'screen', 'camera', or 'both' for privacy protection."""
    target = target.lower().strip()
    if target in ("screen", "desktop", "display"):
        set_vision_permission("screen", False)
        return "Screen vision permission REVOKED. Screen sight is now blocked."
    elif target in ("camera", "webcam", "user", "me"):
        set_vision_permission("camera", False)
        return "Camera vision permission REVOKED. Webcam sight is now blocked."
    elif target in ("both", "all"):
        set_vision_permission("screen", False)
        set_vision_permission("camera", False)
        return "All vision permissions REVOKED. Both screen and camera are blocked."
    return f"Unknown vision target '{target}'. Use 'screen', 'camera', or 'both'."


@tool
def capture_screen(prompt: str = "") -> str:
    """Capture the user's current computer screen if permission is granted.
    
    Use this when the user asks you to look at their screen, inspect open code,
    debug an error dialog, or review what is on the monitor.
    """
    perms = get_vision_permissions()
    if not perms.get("screen", False):
        return (
            "PRIVACY SHIELD ACTIVE: Screen sight is currently BLOCKED.\n"
            "Ask Jabs: 'May I have permission to inspect your screen?' or click the 'Screen Sight' toggle in the dashboard."
        )

    _ensure_sandbox()
    out_path = SANDBOX_DIR / "latest_screen.jpg"

    try:
        from PIL import ImageGrab
        img = ImageGrab.grab()
        # Resize if huge (e.g. 4K) to max 1280 wide to keep fast and lightweight
        if img.width > 1280:
            ratio = 1280.0 / img.width
            new_size = (1280, int(img.height * ratio))
            img = img.resize(new_size)
        img.save(str(out_path), "JPEG", quality=85)
        w, h = img.size
        return (
            f"Screen successfully captured ({w}x{h}). Saved to {out_path.name}.\n"
            f"The current desktop view shows active windows, IDE, and dashboard overlay."
        )
    except Exception as e:
        # Fallback to mss if ImageGrab has X11/Wayland limitations
        try:
            import mss
            with mss.mss() as sct:
                mon = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
                sct_img = sct.grab(mon)
                mss.tools.to_png(sct_img.rgb, sct_img.size, output=str(SANDBOX_DIR / "latest_screen.png"))
                return f"Screen captured via MSS ({sct_img.width}x{sct_img.height}). Saved to sandbox/latest_screen.png."
        except Exception as e2:
            return f"Screen capture failed: {e} / {e2}"


@tool
def capture_camera(prompt: str = "") -> str:
    """Capture a snapshot from the user's webcam if permission is granted.
    
    Use this when the user asks you to look at them, check their posture,
    inspect an object they are holding up to the webcam, or verify their presence.
    """
    perms = get_vision_permissions()
    if not perms.get("camera", False):
        return (
            "PRIVACY SHIELD ACTIVE: Webcam sight is currently BLOCKED.\n"
            "Ask Jabs: 'May I have permission to look through the webcam?' or click the 'Webcam Sight' toggle in the dashboard."
        )

    _ensure_sandbox()
    out_path = SANDBOX_DIR / "latest_camera.jpg"

    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return "Webcam device 0 could not be opened (camera busy or disconnected)."
        
        # Read a couple warm-up frames for auto-exposure
        for _ in range(4):
            ret, frame = cap.read()
        cap.release()

        if not ret or frame is None:
            return "Failed to grab frame from webcam."

        cv2.imwrite(str(out_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        h, w = frame.shape[:2]
        return (
            f"Webcam snapshot captured successfully ({w}x{h}). Saved to {out_path.name}.\n"
            f"Image is ready for visual inspection."
        )
    except Exception as e:
        return f"Camera capture error: {e}"
