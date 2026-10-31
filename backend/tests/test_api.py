"""
Test suite for Jenna AI Assistant FastAPI Backend Engine.
Tests all endpoints: health, SAM 3.1 segmentation, Muse Spark reasoning,
streaming chat, background queue, and memory.
"""
from __future__ import annotations
import sys
import json
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from starlette.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_endpoints():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["assistant"] == "Jenna AI Assistant"
    assert "sam_3_1" in data["active_providers"]

    res_api = client.get("/api/v1/health")
    assert res_api.status_code == 200
    assert res_api.json()["status"] == "healthy"


def test_agent_roles():
    res = client.get("/api/v1/agent/roles")
    assert res.status_code == 200
    roles = res.json()["roles"]
    assert len(roles) >= 5
    role_names = [r["role"] for r in roles]
    assert "commander" in role_names
    assert "planner" in role_names
    assert "coder" in role_names
    assert "researcher" in role_names


def test_sam_segmentation():
    sample_b64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    payload = {
        "image_base64": sample_b64,
        "prompt": "Detect interface panels and code windows",
        "confidence_threshold": 0.5,
        "generate_crops": True,
        "max_segments": 5,
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
        "box_id": "box-seg-001",
        "label": "Code Editor",
        "crop_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
    }
    payload = {
        "prompt": "Evaluate code editor state and determine next agent refactoring step",
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
    assert isinstance(structured["recommended_actions"], list)


def test_agent_chat_non_stream():
    payload = {
        "messages": [
            {"role": "user", "content": "What is the status of the Jenna squad?"}
        ],
        "agent_role": "commander",
        "stream": False,
    }
    res = client.post("/api/v1/agent/chat", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "assistant"
    assert "Jenna Commander" in data["content"] or "Jenna" in data["content"]


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
    print("Running backend tests directly...")
    test_health_endpoints()
    print("✓ Health endpoints passed")
    test_agent_roles()
    print("✓ Agent roles passed")
    test_sam_segmentation()
    print("✓ SAM 3.1 segmentation passed")
    test_muse_spark_reasoning()
    print("✓ Muse Spark reasoning passed")
    test_agent_chat_non_stream()
    print("✓ Agent chat non-stream passed")
    test_agent_chat_stream()
    print("✓ Agent chat streaming passed")
    test_background_jobs()
    print("✓ Background jobs passed")
    test_memory_endpoints()
    print("✓ Memory endpoints passed")
    print("\n🎉 ALL BACKEND TESTS PASSED!")
