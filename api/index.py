"""
Vercel Serverless Function entry point for OmniStore AI (FastAPI Backend).
Routes API calls dynamically on Vercel's serverless Python runtime.
"""
import sys
import os
from pathlib import Path

# Set up paths so backend packages resolve cleanly on Vercel
root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "backend"

for p in [str(root_dir), str(backend_dir)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from backend.main import app

# Expose app for Vercel WSGI/ASGI handler
handler = app
