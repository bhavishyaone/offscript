"""Unit tests for the end-to-end pipeline (AGENTS.md B3 steps 1–7)."""

import asyncio

from fastapi.testclient import TestClient

from offscript_api.clients.serpapi import SerpApiClient
from offscript_api.main import app
from offscript_api.services.model_service import FakeModelService, InvalidModelOutputError
from offscript_api.services.pipeline import run_pipeline
from offscript_contract.route_dto import SearchSource
from offscript_contract.router import AIOutput, SearchOutput, normalize_input
from offscript_contract.search_summary import SearchSummary

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


# ── SEARCH summary: cited source and failures ───────────────────────

SEARCH_REPLY = SearchOutput(
    route="SEARCH",
    reason="Opening hours change.",
    search_query="Lalbagh open Republic Day",
    outdoor_action="If it is open, visit during its listed hours.",
)


class TwoResultSerpApi(SerpApiClient):
    def __init__(self):
        super().__init__(api_key="test")

    async def search(self, query: str, num_results: int = 3) -> list[SearchSource]:
        return [
            SearchSource(
                title="Hours", url="https://www.example.org/hours", snippet="Open 7 to 6."
            ),
            SearchSource(title="Tickets", url="https://tickets.example.com", snippet="Entry 30."),
        ]


class FailingSummaryService(FakeModelService):
    async def summarize_search(self, *args, **kwargs):
        raise InvalidModelOutputError("Invalid search summary output: not_json")


def _run_search(service):
    return asyncio.run(
        run_pipeline(normalize_input("Is Lalbagh open on Republic Day?"), "req_s", service,
                     TwoResultSerpApi())
    )  # fmt: skip


def test_search_card_keeps_the_cited_source():
    summary = SearchSummary(status="answered", summary="Open 7 to 6.", source=1, local_tip=None)
    card = _run_search(FakeModelService(canned_route=SEARCH_REPLY, canned_summary=summary))
    assert card.content.summary == "Open 7 to 6."
    assert card.content.summary_source == 1


def test_failed_summary_still_returns_the_search_links():
    card = _run_search(FailingSummaryService(canned_route=SEARCH_REPLY))
    assert card.kind == "card" and card.route == "SEARCH"
    assert len(card.content.sources) == 2
    assert card.content.summary is None and card.content.summary_source is None


def test_null_outdoor_action_passes_through_and_is_never_invented():
    reply = AIOutput(
        route="AI",
        reason="Exchange-rate maths is stable know-how.",
        answer="Multiply the dollars by the current rate.",
        outdoor_action=None,
    )
    card = asyncio.run(
        run_pipeline(normalize_input("How do I convert 50 dollars to rupees?"), "req_n",
                     FakeModelService(canned_route=reply), TwoResultSerpApi())
    )  # fmt: skip
    assert card.kind == "card" and card.route == "AI"
    assert card.content.outdoor_action is None
