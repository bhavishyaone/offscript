"""Pytest fixtures for offscript-api tests.
Ensures all tests run offline without network calls using fake Tinker and SerpApi clients.
"""

import pytest
from fastapi.testclient import TestClient

from offscript_api.clients.serpapi import SerpApiClient
from offscript_api.main import app as main_app
from offscript_api.routes.route import get_model_service, get_serpapi_client
from offscript_api.services.model_service import MockModelService
from offscript_api.services.rate_limiter import rate_limiter
from offscript_contract.route_dto import SearchSource


class TestSerpApiClient(SerpApiClient):
    """Deterministic offline SerpApi client for test runs."""

    def __init__(self):
        super().__init__(api_key="test-serpapi-key")

    async def search(self, query: str, num_results: int = 3) -> list[SearchSource]:
        # R24: Missing or stale evidence returns empty results
        if "stale" in query.lower() or "definitely on" in query.lower():
            return []
        return [
            SearchSource(
                title=f"Public listing: {query[:35]}",
                url="https://example.com/listing",
                snippet="Open today. Schedule and admission details verified.",
            )
        ]


@pytest.fixture
def app():
    return main_app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_dependencies(app):
    """Setup default test dependency overrides and clear rate limiter history."""
    rate_limiter._history.clear()
    rate_limiter.requests_per_minute = 1000  # High limit for unit test runs

    app.dependency_overrides[get_model_service] = lambda: MockModelService()
    app.dependency_overrides[get_serpapi_client] = lambda: TestSerpApiClient()

    yield

    app.dependency_overrides.pop(get_model_service, None)
    app.dependency_overrides.pop(get_serpapi_client, None)
    rate_limiter._history.clear()
    rate_limiter.requests_per_minute = 60
