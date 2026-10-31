"""
AI Model Abstraction Layer for Meta Models (sam-3.1, muse-spark-1.3, muse-code).
Centralized client wrapping Meta Model API endpoints with retry resilience.
"""
from backend.services.meta_service import (
    MetaModelService,
    get_meta_service,
    META_MODEL_API_BASE,
    META_MODEL_API_KEY,
)

__all__ = ["MetaModelService", "get_meta_service", "META_MODEL_API_BASE", "META_MODEL_API_KEY"]
