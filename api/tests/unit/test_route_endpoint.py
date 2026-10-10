"""Unit tests for POST /api/route endpoint (Task A01)."""

from fastapi.testclient import TestClient

from offscript_api.main import app

client = TestClient(app)


def test_post_route_ai_response():
    response = client.post(
        "/api/route",
        json={"question": "How do I join a casual pickup game at the court?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "card"
    assert data["fit"] == "ok"
    assert data["route"] == "AI"
    assert "answer" in data["content"]
    assert "outdoor_action" in data["content"]
    assert "request_id" in data
    assert isinstance(data["latency_ms"], int)


def test_post_route_search_response():
    response = client.post(
        "/api/route",
        json={"question": "Where is a public run club meeting near campus this week?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "card"
    assert data["fit"] == "ok"
    assert data["route"] == "SEARCH"
    assert "search_query" in data["content"]
    assert "sources" in data["content"]
    assert "search_url" in data["content"]
    assert len(data["content"]["sources"]) >= 1


def test_post_route_search_injected_serpapi_sources():
    from offscript_api.clients.serpapi import SerpApiClient
    from offscript_api.routes.route import get_serpapi_client
    from offscript_contract.route_dto import SearchSource

    class FakeSerpApiClient(SerpApiClient):
        def __init__(self):
            super().__init__(api_key="test-key")

        async def search(self, query: str, num_results: int = 3) -> list[SearchSource]:
            return [SearchSource(title="Campus Running Hub", url="https://example.com/running")]

    app.dependency_overrides[get_serpapi_client] = lambda: FakeSerpApiClient()
    try:
        response = client.post(
            "/api/route",
            json={"question": "Where is a public run club meeting near campus this week?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["kind"] == "card"
        assert data["route"] == "SEARCH"
        assert len(data["content"]["sources"]) == 1
        assert data["content"]["sources"][0]["title"] == "Campus Running Hub"
    finally:
        app.dependency_overrides.pop(get_serpapi_client, None)


def test_post_route_search_injected_serpapi_failure_returns_search_limitation():
    from offscript_api.clients.serpapi import SerpApiClient, SerpApiTimeoutError
    from offscript_api.routes.route import get_serpapi_client

    class FailingSerpApiClient(SerpApiClient):
        def __init__(self):
            super().__init__(api_key="test-key")

        async def search(self, query: str, num_results: int = 3) -> list:
            raise SerpApiTimeoutError("Timeout")

    app.dependency_overrides[get_serpapi_client] = lambda: FailingSerpApiClient()
    try:
        response = client.post(
            "/api/route",
            json={"question": "Where is a public run club meeting near campus this week?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["kind"] == "guard"
        assert data["fit"] == "search_limitation"
        assert "search_url" in data
        assert data["search_url"] is not None
    finally:
        app.dependency_overrides.pop(get_serpapi_client, None)


def test_post_route_human_response():
    response = client.post(
        "/api/route",
        json={"question": "What do regulars buy at this market stall?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "card"
    assert data["fit"] == "ok"
    assert data["route"] == "HUMAN"
    assert "who_to_ask" in data["content"]
    assert "suggested_question" in data["content"]


def test_post_route_general_question_gets_ai():
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


def test_post_route_validation_error_empty_question():
    response = client.post(
        "/api/route",
        json={"question": ""},
    )
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "question_empty"
    assert "message" in data["error"]


def test_post_route_validation_error_too_long():
    response = client.post(
        "/api/route",
        json={"question": "a" * 301},
    )
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "question_too_long"


def test_post_route_guard_needs_detail():
    response = client.post(
        "/api/route",
        json={"question": "I want to visit a park today. Which is open near me?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "guard"
    assert data["fit"] == "needs_detail"


def test_post_route_guard_two_questions():
    response = client.post(
        "/api/route",
        json={"question": "How do I join a game, and where is one tonight?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "guard"
    assert data["fit"] == "two_questions"


def test_post_route_guard_safety_guidance():
    response = client.post(
        "/api/route",
        json={"question": "Is the dark shortcut behind the station safe to try tonight?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "guard"
    assert data["fit"] == "safety_guidance"


def test_post_route_guard_refusal():
    response = client.post(
        "/api/route",
        json={"question": "Ask the woman sitting alone why she is alone."},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "guard"
    assert data["fit"] == "refusal"


def test_post_route_canonical_human_college_club():
    response = client.post(
        "/api/route",
        json={"question": "What is this college club actually like before I go to its meeting?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "card"
    assert data["route"] == "HUMAN"


def test_post_route_canonical_ai_birdwatching():
    response = client.post(
        "/api/route",
        json={"question": "How can I start birdwatching in the park?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "card"
    assert data["route"] == "AI"


def test_post_route_rate_limiting():
    from offscript_api.services.rate_limiter import rate_limiter

    # Temporarily set limit to 1
    orig_limit = rate_limiter.requests_per_minute
    rate_limiter.requests_per_minute = 1
    rate_limiter._history.clear()
    try:
        res1 = client.post("/api/route", json={"question": "First question?"})
        assert res1.status_code == 200

        res2 = client.post("/api/route", json={"question": "Second question?"})
        assert res2.status_code == 429
        data = res2.json()
        assert data["error"]["code"] == "rate_limited"
    finally:
        rate_limiter.requests_per_minute = orig_limit
        rate_limiter._history.clear()


def test_post_route_model_unavailable_503():
    from offscript_api.routes.route import get_model_service
    from offscript_api.services.model_service import BaseRouteService, ModelUnavailableError

    class FailingModelService(BaseRouteService):
        @property
        def is_mock(self) -> bool:
            return False

        async def check_guard(self, question, context, budget):
            raise ModelUnavailableError("Tinker checkpoint not found.")

        async def route(self, question, context, budget):
            raise ModelUnavailableError("Tinker checkpoint not found.")

        async def summarize_search(self, question, context, results, budget):
            raise ModelUnavailableError("Tinker checkpoint not found.")

    app.dependency_overrides[get_model_service] = lambda: FailingModelService()
    try:
        response = client.post("/api/route", json={"question": "Valid question here?"})
        assert response.status_code == 503
        data = response.json()
        assert data["error"]["code"] == "model_unavailable"
    finally:
        app.dependency_overrides.pop(get_model_service, None)


def test_post_route_model_timeout_504():
    from offscript_api.routes.route import get_model_service
    from offscript_api.services.model_service import BaseRouteService, ModelTimeoutError

    class TimeoutModelService(BaseRouteService):
        @property
        def is_mock(self) -> bool:
            return False

        async def check_guard(self, question, context, budget):
            raise ModelTimeoutError("Upstream model timed out.")

        async def route(self, question, context, budget):
            raise ModelTimeoutError("Upstream model timed out.")

        async def summarize_search(self, question, context, results, budget):
            raise ModelTimeoutError("Upstream model timed out.")

    app.dependency_overrides[get_model_service] = lambda: TimeoutModelService()
    try:
        response = client.post("/api/route", json={"question": "Valid question here?"})
        assert response.status_code == 504
        data = response.json()
        assert data["error"]["code"] == "timeout"
    finally:
        app.dependency_overrides.pop(get_model_service, None)


def test_post_route_invalid_model_output_502():
    from offscript_api.routes.route import get_model_service
    from offscript_api.services.model_service import BaseRouteService, InvalidModelOutputError

    class BrokenModelService(BaseRouteService):
        @property
        def is_mock(self) -> bool:
            return False

        async def check_guard(self, question, context, budget):
            raise InvalidModelOutputError("Model returned malformed JSON.")

        async def route(self, question, context, budget):
            raise InvalidModelOutputError("Model returned malformed JSON.")

        async def summarize_search(self, question, context, results, budget):
            raise InvalidModelOutputError("Model returned malformed JSON.")

    app.dependency_overrides[get_model_service] = lambda: BrokenModelService()
    try:
        response = client.post("/api/route", json={"question": "Valid question here?"})
        assert response.status_code == 502
        data = response.json()
        assert data["error"]["code"] == "invalid_model_output"
    finally:
        app.dependency_overrides.pop(get_model_service, None)
