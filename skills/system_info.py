"""System info tool: RAM/disk usage (handy on 8 GB machines)."""
import shutil
from langchain_core.tools import tool


@tool
def system_info() -> str:
    """Report RAM and disk usage."""
    total, used, free = shutil.disk_usage("/")
    mem = _read_mem()
    return (
        f"Disk: {free // (2**30)} GB free of {total // (2**30)} GB. "
        f"Memory: {mem}."
    )


def _read_mem() -> str:
    try:
        with open("/proc/meminfo") as f:
            info = {k: int(v.split()[0]) for k, v in (line.split(":", 1) for line in f if ":" in line)}
        total = info.get("MemTotal", 0) // (2**20)
        avail = info.get("MemAvailable", 0) // (2**20)
        return f"{avail} MB available of {total} MB"
    except Exception:
        return "unknown"
