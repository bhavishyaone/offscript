"""Unit tests for the end-to-end pipeline (AGENTS.md B3 steps 1–7)."""

from fastapi.testclient import TestClient

from offscript_api.main import app

client = TestClient(app)


# ── Safety rules fire BEFORE the model ──────────────────────────────


def test_pipeline_safety_blocks_before_model():
    """Safety rule hit → guard response, model never called."""
    response = client.post(
        "/api/route",
        json={"question": "Ask the woman sitting alone why she is alone."},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "guard"
    assert data["fit"] == "refusal"
    assert data["route"] is None


def test_pipeline_safety_medical():
    response = client.post(
        "/api/route",
        json={"question": "Which medicine should I ask strangers to recommend?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "guard"
    assert data["fit"] == "safety_guidance"


def test_pipeline_safety_dangerous_route():
    response = client.post(
        "/api/route",
        json={"question": "Is the dark shortcut behind the station safe to try tonight?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "guard"
    assert data["fit"] == "safety_guidance"


# ── Safe questions reach the router ─────────────────────────────────


def test_pipeline_ai_route():
    response = client.post(
        "/api/route",
        json={"question": "How do I join a casual pickup game at the court?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "card"
    assert data["fit"] == "ok"
    assert data["route"] == "AI"
    assert "content" in data
    assert "request_id" in data
    assert isinstance(data["latency_ms"], int)


def test_pipeline_search_route():
    response = client.post(
        "/api/route",
        json={"question": "Where is a public run club meeting near campus this week?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "card"
    assert data["route"] == "SEARCH"


def test_pipeline_human_route():
    response = client.post(
        "/api/route",
        json={"question": "What do regulars buy at this market stall?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "card"
    assert data["route"] == "HUMAN"


# ── Guard states & General questions ───────────────────────────────


def test_pipeline_general_question_gets_ai_route():
    """Photosynthesis is general knowledge and receives an AI route (Item 4)."""
    response = client.post(
        "/api/route",
        json={"question": "What is photosynthesis?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "card"
    assert data["route"] == "AI"
    assert "answer" in data["content"]
    assert "outdoor_action" in data["content"]


def test_pipeline_guard_needs_detail():
    response = client.post(
        "/api/route",
        json={"question": "I want to visit a park today. Which is open near me?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "guard"
    assert data["fit"] == "needs_detail"
    assert data["route"] is None
    assert "message" in data


def test_pipeline_guard_two_questions():
    response = client.post(
        "/api/route",
        json={"question": "How do I join a game, and where is one tonight?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "guard"
    assert data["fit"] == "two_questions"
    assert data["route"] is None
    assert "message" in data


# ── Input validation ────────────────────────────────────────────────


def test_pipeline_empty_question_422():
    response = client.post("/api/route", json={"question": ""})
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "question_empty"


def test_pipeline_too_long_422():
    response = client.post("/api/route", json={"question": "x" * 301})
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "question_too_long"
