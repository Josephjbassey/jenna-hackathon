"""
Jenna AI Assistant — Unified Launcher.
Delegates to backend/main.py.
"""
import sys
from pathlib import Path

# Add project root and backend to sys.path
root_dir = Path(__file__).resolve().parent
backend_dir = root_dir / "backend"
for p in [str(backend_dir), str(root_dir)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from backend.main import main

if __name__ == "__main__":
    main()
