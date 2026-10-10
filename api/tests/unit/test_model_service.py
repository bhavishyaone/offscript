"""Unit tests for the live Tinker model service with fake clients (AGENTS.md B3, B10).

No network: the sampling clients and tokenizer are replaced with fakes, so these tests check the
retry, timeout and error mapping around real contract prompt building and parsing.
"""

import asyncio
from types import SimpleNamespace

import pytest

from offscript_api.services import model_service
from offscript_api.services.model_service import (
    InvalidModelOutputError,
    LiveModelService,
    ModelTimeoutError,
    ModelUnavailableError,
)
from offscript_contract.rendering import STOP_TOKEN

AI_REPLY = (
    '{"route":"AI","reason":"Stable know-how.","answer":"Hold the line taut.",'
    '"outdoor_action":"Fly the kite once in an open field."}'
)


class FakeTokenizer:
    """One token per character; the stop token is 0."""

    def encode(self, text: str, **kwargs: object) -> list[int]:
        return [0] if text == STOP_TOKEN else [ord(char) for char in text]

    def decode(self, tokens: list[int], **kwargs: object) -> str:
        return "".join(chr(token) for token in tokens)


class FakeSamplingClient:
    """Plays back a list of outcomes: reply text, an exception to raise, or "hang"."""

    def __init__(self, *outcomes: object) -> None:
        self.outcomes = list(outcomes)
        self.calls = 0

    async def sample_async(self, **kwargs: object) -> SimpleNamespace:
        outcome = self.outcomes[min(self.calls, len(self.outcomes) - 1)]
        self.calls += 1
        if outcome == "hang":
            await asyncio.sleep(10)
        if isinstance(outcome, Exception):
            raise outcome
        tokens = FakeTokenizer().encode(str(outcome)) + [0]
        return SimpleNamespace(sequences=[SimpleNamespace(tokens=tokens)])


def live_service(router: FakeSamplingClient) -> LiveModelService:
    service = LiveModelService(tinker_api_key="test-key", tinker_model_path="tinker://test")
    service._router_client = router
    service._base_client = router
    service._tokenizer = FakeTokenizer()
    return service


@pytest.fixture(autouse=True)
def short_call_timeout(monkeypatch):
    monkeypatch.setattr(model_service, "CALL_TIMEOUT_S", 0.05)


def test_valid_reply_is_parsed_with_the_contract_parser():
    router = FakeSamplingClient(AI_REPLY)
    reply = asyncio.run(live_service(router).route("How do I fly a kite?", None, 60))
    assert reply.route == "AI" and reply.answer == "Hold the line taut."
    assert router.calls == 1


def test_invalid_reply_is_not_retried():
    router = FakeSamplingClient("Sure! Here is my answer.")
    with pytest.raises(InvalidModelOutputError) as error:
        asyncio.run(live_service(router).route("How do I fly a kite?", None, 60))
    assert error.value.status_code == 502
    assert router.calls == 1


def test_network_error_is_retried_once_then_succeeds():
    router = FakeSamplingClient(ConnectionError("reset"), AI_REPLY)
    reply = asyncio.run(live_service(router).route("How do I fly a kite?", None, 60))
    assert reply.route == "AI"
    assert router.calls == 2


def test_repeated_timeouts_return_504_after_one_retry():
    router = FakeSamplingClient("hang")
    with pytest.raises(ModelTimeoutError) as error:
        asyncio.run(live_service(router).route("How do I fly a kite?", None, 60))
    assert error.value.status_code == 504
    assert router.calls == 2


def test_no_retry_when_the_budget_cannot_cover_another_call():
    router = FakeSamplingClient(ConnectionError("reset"), AI_REPLY)
    with pytest.raises(ModelUnavailableError) as error:
        asyncio.run(live_service(router).route("How do I fly a kite?", None, 0.06))
    assert error.value.status_code == 503
    assert router.calls == 1


def test_missing_keys_return_503_without_calling_tinker():
    service = LiveModelService(tinker_api_key="", tinker_model_path="")
    with pytest.raises(ModelUnavailableError):
        asyncio.run(service.start())
