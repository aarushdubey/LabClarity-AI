"""
Integration Tests for Flask Web Application & API Endpoints
"""

import json
import pytest
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_index_route(client):
    """Test index route loads HTML interface."""
    res = client.get("/")
    assert res.status_code == 200
    assert b"LabClarity" in res.data
    assert b"Research Microscopy" in res.data


def test_presets_api(client):
    """Test presets endpoint returns valid pipelines."""
    res = client.get("/api/presets")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "fluorescence" in data["presets"]
    assert "histology_2x" in data["presets"]


def test_samples_and_load_workflow(client):
    """Test sample listing, loading, and enhancement cycle."""
    # 1. Get samples
    res = client.get("/api/samples")
    assert res.status_code == 200
    samples_data = res.get_json()
    assert samples_data["success"] is True
    assert len(samples_data["samples"]) > 0

    first_sample_id = samples_data["samples"][0]["id"]

    # 2. Load sample
    load_res = client.post(
        "/api/load_sample",
        data=json.dumps({"sample_id": first_sample_id}),
        content_type="application/json",
    )
    assert load_res.status_code == 200
    load_data = load_res.get_json()
    assert load_data["success"] is True
    task_id = load_data["task_id"]
    assert task_id is not None

    # 3. Enhance specimen
    enhance_res = client.post(
        "/api/enhance",
        data=json.dumps({
            "task_id": task_id,
            "preset": "fluorescence",
            "denoise_strength": 0.5,
            "upscale_factor": 1,
            "clahe_clip": 2.0,
            "sharpness": 0.3,
            "flat_field": False,
        }),
        content_type="application/json",
    )
    assert enhance_res.status_code == 200
    enh_data = enhance_res.get_json()
    assert enh_data["success"] is True
    assert "metrics" in enh_data
    assert "ai_analysis" in enh_data
    assert "modality" in enh_data["ai_analysis"]

    # 4. Chat with assistant
    chat_res = client.post(
        "/api/chat",
        data=json.dumps({
            "query": "How does Poisson Anscombe denoising work?",
            "task_id": task_id,
        }),
        content_type="application/json",
    )
    assert chat_res.status_code == 200
    chat_data = chat_res.get_json()
    assert chat_data["success"] is True
    assert len(chat_data["reply"]) > 20

    # 5. Export Report
    export_res = client.get(f"/api/export/report_json/{task_id}")
    assert export_res.status_code == 200
    report_json = json.loads(export_res.data)
    assert report_json["project"] == "LabClarity AI: Research Microscopy Image Enhancer"


def test_health_check(client):
    """Test health check route."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "healthy"
    assert data["team"] == "Team 4"
