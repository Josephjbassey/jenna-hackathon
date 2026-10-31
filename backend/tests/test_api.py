"""
Test suite for OmniStore AI (Jenna Platform) Backend Engine.
Tests all endpoints:
  - Health & Agent Roles
  - SAM 3.1 visual segmentation & spatial bounding boxes
  - Muse Spark 1.3 cognitive multimodal reasoning & localized pricing
  - Muse Code agentic storefront synthesis
  - End-to-end physical store scan pipeline (/api/v1/scan/json)
  - Real-time streaming agent chat
  - Background async jobs & webhooks
  - Memory persistence & stats
"""
from __future__ import annotations
import sys
import json
from pathlib import Path

# Add project root and backend to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
backend_dir = root_dir / "backend"
for path in [str(root_dir), str(backend_dir)]:
    if path not in sys.path:
        sys.path.insert(0, path)

from starlette.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_endpoints():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "OmniStore" in data["assistant"] or "Jenna" in data["assistant"]
    assert "sam_3_1" in data["active_providers"]

    res_api = client.get("/api/v1/health")
    assert res_api.status_code == 200
    assert res_api.json()["status"] == "healthy"


def test_agent_roles():
    res = client.get("/api/v1/agent/roles")
    assert res.status_code == 200
    roles = res.json()["roles"]
    assert len(roles) >= 4
    role_names = [r["role"] for r in roles]
    assert "commander" in role_names
    assert "planner" in role_names
    assert "coder" in role_names


def test_sam_segmentation():
    sample_b64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    payload = {
        "image_base64": sample_b64,
        "prompt": "Detect produce items, baskets, and provisions",
        "confidence_threshold": 0.25,
        "generate_crops": True,
        "max_segments": 6,
    }
    res = client.post("/api/v1/segment", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["model_used"] == "sam-3.1"
    assert len(data["bounding_boxes"]) > 0
    assert len(data["crops"]) > 0
    first_box = data["bounding_boxes"][0]
    assert "bbox" in first_box
    assert len(first_box["bbox"]) == 4  # [ymin, xmin, ymax, xmax]


def test_muse_spark_reasoning():
    sample_crop = {
        "box_id": "seg_001",
        "label": "Local Yams",
        "crop_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
    }
    payload = {
        "prompt": "Classify physical store goods, infer local pricing in NGN, and format catalog",
        "merchant_context": {
            "store_name": "Mama Cass Market",
            "currency": "NGN",
            "location": "Akure, Nigeria",
            "whatsapp_number": "+2348012345678",
        },
        "segments": [sample_crop],
        "model": "muse-spark-1.3",
        "structured_format": True,
    }
    res = client.post("/api/v1/reason", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["model_used"] == "muse-spark-1.3"
    structured = data["structured_output"]
    assert "summary" in structured
    assert "detailed_analysis" in structured
    assert "recommended_actions" in structured
    assert len(structured["inventory"]) > 0
    assert data["store_schema"] is not None
    assert data["store_schema"]["currency"] == "NGN"


def test_muse_code_synthesis():
    payload = {
        "target_framework": "nextjs14_tailwind",
        "store_schema": {
            "store_title": "Mama Cass Market",
            "currency": "NGN",
            "location": "Akure, Nigeria",
            "whatsapp_number": "+2348012345678",
            "category": "Provisions & Fresh Produce",
            "inventory": [
                {
                    "item_id": "item_001",
                    "name": "Local Yams (Large)",
                    "category": "Tubers & Roots",
                    "suggested_price": 2500.0,
                    "estimated_quantity": 4,
                    "description": "Organic tuber from local harvest",
                    "image_segment_id": "seg_001",
                }
            ],
        },
    }
    res = client.post("/api/v1/code/generate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "compiled"
    assert data["model_used"] == "muse-code"
    assert "app/page.tsx" in data["repository_files"]
    assert "app/api/checkout/route.ts" in data["repository_files"]
    assert "prisma/schema.prisma" in data["repository_files"]
    assert data["deployment_ready"] is True


def test_end_to_end_store_scan():
    sample_b64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    payload = {
        "image_base64": sample_b64,
        "store_name": "Mama Cass Market",
        "currency": "NGN",
        "location": "Akure Central Market, Nigeria",
        "whatsapp_number": "+2348012345678",
    }
    res = client.post("/api/v1/scan/json", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "completed"
    assert len(data["bounding_boxes"]) > 0
    assert len(data["store_schema"]["inventory"]) > 0
    assert data["store_schema"]["currency"] == "NGN"
    assert data["code_synthesis"] is not None
    assert "app/page.tsx" in data["code_synthesis"]["repository_files"]


def test_agent_chat_non_stream():
    payload = {
        "messages": [
            {"role": "user", "content": "How does OmniStore digitize physical store inventory?"}
        ],
        "agent_role": "commander",
        "stream": False,
    }
    res = client.post("/api/v1/agent/chat", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "assistant"
    assert len(data["content"]) > 10


def test_agent_chat_stream():
    payload = {
        "messages": [
            {"role": "user", "content": "Stream your execution plan"}
        ],
        "agent_role": "planner",
        "stream": True,
    }
    with client.stream("POST", "/api/v1/agent/chat", json=payload) as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
        lines = list(response.iter_lines())
        data_lines = [l for l in lines if l.startswith("data: ")]
        assert len(data_lines) > 0
        assert "[DONE]" in lines[-1] or "[DONE]" in lines[-2]


def test_background_jobs():
    payload = {
        "job_type": "segmentation",
        "payload": {
            "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
            "prompt": "Test background queue",
        },
    }
    res = client.post("/api/v1/jobs", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "job_id" in data
    assert data["status"] in ("queued", "processing", "completed")

    job_id = data["job_id"]
    get_res = client.get(f"/api/v1/jobs/{job_id}")
    assert get_res.status_code == 200
    assert get_res.json()["job_id"] == job_id


def test_memory_endpoints():
    stats_res = client.get("/api/v1/memory/stats")
    assert stats_res.status_code == 200

    search_res = client.post("/api/v1/memory/search", json={"query": "assistant"})
    assert search_res.status_code == 200
    assert "results" in search_res.json()


if __name__ == "__main__":
    print("Running OmniStore AI backend tests directly...")
    test_health_endpoints()
    print("✓ Health endpoints passed")
    test_agent_roles()
    print("✓ Agent roles passed")
    test_sam_segmentation()
    print("✓ SAM 3.1 segmentation passed")
    test_muse_spark_reasoning()
    print("✓ Muse Spark reasoning passed")
    test_muse_code_synthesis()
    print("✓ Muse Code storefront synthesis passed")
    test_end_to_end_store_scan()
    print("✓ End-to-end physical store scan passed")
    test_agent_chat_non_stream()
    print("✓ Agent chat non-stream passed")
    test_agent_chat_stream()
    print("✓ Agent chat streaming passed")
    test_background_jobs()
    print("✓ Background jobs passed")
    test_memory_endpoints()
    print("✓ Memory endpoints passed")
    print("\n🎉 ALL OMNISTORE AI BACKEND TESTS PASSED!")
