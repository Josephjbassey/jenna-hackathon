"""System info tool: RAM/disk usage (cross-platform, works on Linux/Windows/macOS)."""
import shutil
import platform
from langchain_core.tools import tool

try:
    import psutil
    _HAS_PSUTIL = True
except ImportError:
    _HAS_PSUTIL = False


@tool
def system_info() -> str:
    """Report system CPU, RAM, and disk usage across Linux, Windows, and macOS."""
    # Disk usage
    path = "C:\\" if platform.system().lower() == "windows" else "/"
    try:
        total, used, free = shutil.disk_usage(path)
        disk_str = f"Disk: {free // (2**30)} GB free of {total // (2**30)} GB"
    except Exception:
        disk_str = "Disk: unknown"

    # Memory & CPU usage
    if _HAS_PSUTIL:
        vm = psutil.virtual_memory()
        cpu_pct = psutil.cpu_percent(interval=None)
        mem_str = f"Memory: {vm.available // (2**20)} MB available of {vm.total // (2**20)} MB ({vm.percent}% used). CPU: {cpu_pct}%."
    else:
        mem_str = f"Memory: {_read_mem_fallback()}."

    os_str = f"OS: {platform.system()} {platform.release()}"
    return f"{os_str}. {disk_str}. {mem_str}"


def _read_mem_fallback() -> str:
    try:
        with open("/proc/meminfo") as f:
            info = {k: int(v.split()[0]) for k, v in (line.split(":", 1) for line in f if ":" in line)}
        total = info.get("MemTotal", 0) // (2**20)
        avail = info.get("MemAvailable", 0) // (2**20)
        return f"{avail} MB available of {total} MB"
    except Exception:
        return "unknown"
