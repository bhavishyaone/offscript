"""Model service interface and implementations for Tinker and Mock modes (AGENTS.md B2, B3, B6).

Provides unified access to:
1. Base model (Qwen/Qwen3.5-9B) for guard checks and search summarization
2. Fine-tuned model checkpoint for routing (AI, SEARCH, HUMAN)
3. Mock model for offline local development and test modes
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from offscript_contract.guard import (
    GUARD_MAX_TOKENS,
    GuardOutput,
    GuardVerdict,
    build_guard_messages,
    parse_guard_output,
)
from offscript_contract.parsing import ModelOutputError
from offscript_contract.rendering import decode_completion, render_chat_prompt, stop_token_id
from offscript_contract.router import (
    BASE_MODEL,
    MAX_TOKENS,
    TEMPERATURE,
    AIOutput,
    HumanOutput,
    SearchOutput,
    build_router_messages,
    parse_router_output,
)
from offscript_contract.search_summary import (
    SUMMARY_MAX_TOKENS,
    SearchResult,
    SearchSummary,
    build_summary_messages,
    parse_summary_output,
)

logger = logging.getLogger(__name__)

CALL_TIMEOUT_S = 20.0


class ModelServiceError(Exception):
    """Base exception for model service failures."""

    def __init__(self, code: str, message: str, status_code: int = 502):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class ModelUnavailableError(ModelServiceError):
    def __init__(self, message: str = "Model service is unavailable."):
        super().__init__(code="model_unavailable", message=message, status_code=503)


class ModelTimeoutError(ModelServiceError):
    def __init__(self, message: str = "Model request timed out."):
        super().__init__(code="timeout", message=message, status_code=504)


class InvalidModelOutputError(ModelServiceError):
    def __init__(self, message: str = "Model produced an invalid response."):
        super().__init__(code="invalid_model_output", message=message, status_code=502)


class BaseRouteService(ABC):
    @property
    @abstractmethod
    def is_mock(self) -> bool: ...

    @abstractmethod
    async def check_guard(
        self, question: str, context: str | None, remaining_budget_s: float
    ) -> GuardOutput: ...

    @abstractmethod
    async def route(
        self, question: str, context: str | None, remaining_budget_s: float
    ) -> AIOutput | SearchOutput | HumanOutput: ...

    @abstractmethod
    async def summarize_search(
        self,
        question: str,
        context: str | None,
        results: list[SearchResult],
        remaining_budget_s: float,
    ) -> SearchSummary: ...


class LiveModelService(BaseRouteService):
    """Production Tinker SDK service calling real base model and tuned sampler."""

    def __init__(
        self,
        tinker_api_key: str,
        tinker_model_path: str,
    ) -> None:
        self.tinker_api_key = tinker_api_key
        self.tinker_model_path = tinker_model_path
        self._service_client: Any = None
        self._base_client: Any = None
        self._router_client: Any = None
        self._tokenizer: Any = None

    @property
    def is_mock(self) -> bool:
        return False

    async def _ensure_initialized(self) -> None:
        if self._router_client is not None:
            return
        if not self.tinker_api_key or not self.tinker_model_path:
            raise ModelUnavailableError("Tinker API key or model path is not configured.")

        try:
            import tinker

            self._service_client = tinker.ServiceClient(api_key=self.tinker_api_key)
            self._base_client = await self._service_client.create_sampling_client_async(
                base_model=BASE_MODEL
            )
            self._router_client = await self._service_client.create_sampling_client_async(
                model_path=self.tinker_model_path
            )
            self._tokenizer = self._router_client.get_tokenizer()
        except Exception as err:
            logger.error("Failed to initialize Tinker sampling clients: %s", type(err).__name__)
            raise ModelUnavailableError("Failed to connect to model service.") from err

    async def _sample_with_retry(
        self,
        client_type: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        remaining_budget_s: float,
    ) -> tuple[str, bool]:
        await self._ensure_initialized()
        import tinker

        client = self._base_client if client_type == "base" else self._router_client
        tokenizer = self._tokenizer
        prompt_ints = render_chat_prompt(tokenizer, messages)
        prompt = tinker.ModelInput.from_ints(prompt_ints)
        stop_id = stop_token_id(tokenizer)
        sampling_params = tinker.SamplingParams(
            max_tokens=max_tokens,
            temperature=TEMPERATURE,
            stop=[stop_id],
        )

        attempts = 0
        last_err: Exception | None = None

        while attempts < 2:
            attempts += 1
            call_timeout = min(remaining_budget_s, CALL_TIMEOUT_S)
            if call_timeout <= 0:
                raise ModelTimeoutError("Request time budget exhausted.")

            try:
                response = await asyncio.wait_for(
                    client.sample_async(
                        prompt=prompt,
                        num_samples=1,
                        sampling_params=sampling_params,
                    ),
                    timeout=call_timeout,
                )
                tokens = response.sequences[0].tokens
                return decode_completion(tokenizer, tokens)
            except TimeoutError as err:
                last_err = err
                if attempts < 2 and remaining_budget_s - call_timeout >= CALL_TIMEOUT_S:
                    logger.warning("Tinker call timed out; retrying once within budget")
                    continue
                raise ModelTimeoutError("Model request timed out.") from err
            except Exception as err:
                last_err = err
                if attempts < 2 and remaining_budget_s - call_timeout >= CALL_TIMEOUT_S:
                    logger.warning(
                        "Tinker call error %s; retrying once within budget", type(err).__name__
                    )
                    continue
                raise ModelUnavailableError("Model service unavailable.") from err

        if isinstance(last_err, asyncio.TimeoutError):
            raise ModelTimeoutError("Model request timed out.")
        raise ModelUnavailableError("Model service unavailable.")

    async def check_guard(
        self, question: str, context: str | None, remaining_budget_s: float
    ) -> GuardOutput:
        messages = build_guard_messages(question, context)
        text, complete = await self._sample_with_retry(
            "base", messages, GUARD_MAX_TOKENS, remaining_budget_s
        )
        try:
            return parse_guard_output(text, complete=complete)
        except ModelOutputError as err:
            logger.error("Invalid guard output: %s", err.code)
            raise InvalidModelOutputError(f"Invalid guard output: {err.code}") from err

    async def route(
        self, question: str, context: str | None, remaining_budget_s: float
    ) -> AIOutput | SearchOutput | HumanOutput:
        messages = build_router_messages(question, context)
        text, complete = await self._sample_with_retry(
            "router", messages, MAX_TOKENS, remaining_budget_s
        )
        try:
            return parse_router_output(text, complete=complete)
        except ModelOutputError as err:
            logger.error("Invalid router output: %s", err.code)
            raise InvalidModelOutputError(f"Invalid router output: {err.code}") from err

    async def summarize_search(
        self,
        question: str,
        context: str | None,
        results: list[SearchResult],
        remaining_budget_s: float,
    ) -> SearchSummary:
        messages = build_summary_messages(question, context, results)
        text, complete = await self._sample_with_retry(
            "base", messages, SUMMARY_MAX_TOKENS, remaining_budget_s
        )
        try:
            return parse_summary_output(text, complete=complete)
        except ModelOutputError as err:
            logger.error("Invalid search summary output: %s", err.code)
            raise InvalidModelOutputError(f"Invalid search summary output: {err.code}") from err


class MockModelService(BaseRouteService):
    """Offline development mock that replays recorded outputs from contract/fixtures/.

    Every output is parsed strictly by contract parsers, testing the exact runtime validation.
    """

    def __init__(self) -> None:
        self._router_fixtures: dict[str, Any] = {}
        self._guard_fixtures: dict[str, Any] = {}
        self._summary_fixtures: dict[str, Any] = {}
        self._load_fixtures()

    @property
    def is_mock(self) -> bool:
        return True

    def _find_fixture(self, rel_path: str) -> str:
        for parent in Path(__file__).resolve().parents:
            candidate = parent / "contract" / rel_path
            if candidate.is_file():
                return candidate.read_text("utf-8")
            candidate2 = parent / rel_path
            if candidate2.is_file():
                return candidate2.read_text("utf-8")

        cwd_candidate = Path.cwd() / "contract" / rel_path
        if cwd_candidate.is_file():
            return cwd_candidate.read_text("utf-8")

        raise FileNotFoundError(f"Fixture not found: {rel_path}")

    def _load_fixtures(self) -> None:
        try:
            self._router_fixtures = json.loads(self._find_fixture("fixtures/router/outputs.json"))
            self._guard_fixtures = json.loads(self._find_fixture("fixtures/guard/outputs.json"))
            summary_json = self._find_fixture("fixtures/search_summary/outputs.json")
            self._summary_fixtures = json.loads(summary_json)
        except Exception as err:
            logger.error("Failed to load contract fixtures for mock mode: %s", err)

    async def check_guard(
        self, question: str, context: str | None, remaining_budget_s: float
    ) -> GuardOutput:
        q_lower = question.lower()
        valid = {item["name"]: item["text"] for item in self._guard_fixtures.get("valid", [])}

        # Check two questions in one
        if "and where is" in q_lower or "and when is" in q_lower or "or a free" in q_lower:
            fallback = '{"verdict":"two_questions","message":"Two questions asked in one."}'
            text = valid.get("two_questions", fallback)
            return parse_guard_output(text)

        # Check missing essential location detail
        is_missing_ctx = context is None or context == "none" or not context.strip()
        location_keys = ["near me", "which is open", "open nearby"]
        if is_missing_ctx and any(k in q_lower for k in location_keys):
            fallback = '{"verdict":"needs_detail","message":"Which area will you be in?"}'
            text = valid.get("needs_detail", fallback)
            return parse_guard_output(text)

        text = valid.get("ok", '{"verdict":"ok","message":null}')
        return parse_guard_output(text)

    async def route(
        self, question: str, context: str | None, remaining_budget_s: float
    ) -> AIOutput | SearchOutput | HumanOutput:
        q_lower = question.lower()
        valid = {item["name"]: item["text"] for item in self._router_fixtures.get("valid", [])}

        human_indicators = [
            "regular",
            "regulars",
            "stall",
            "who to ask",
            "beginners",
            "beginners actually join",
            "campus club",
            "college club",
            "club like",
            "students here",
            "eat between classes",
            "walking loop",
            "people here enjoy",
            "how do people",
            "recommend",
            "advice from",
        ]
        search_indicators = [
            "where",
            "when",
            "hours",
            "open",
            "match",
            "winner",
            "won",
            "museum",
            "rating",
            "schedule",
            "cost",
            "ticket",
            "fee",
            "price",
            "yesterday",
            "today",
            "weekend",
            "workshop",
            "free entry",
            "listing",
            "stale",
            "definitely on",
        ]

        if any(k in q_lower for k in human_indicators):
            text = valid.get("human", valid.get("unicode"))
        elif any(k in q_lower for k in search_indicators):
            text = valid.get("search", valid.get("spaced_json"))
        else:
            text = valid.get("ai", valid.get("ai_bullets"))

        if not text:
            text = (
                '{"route":"AI","reason":"General know-how.",'
                '"answer":"General answer.","outdoor_action":"Try it outside."}'
            )

        parsed = parse_router_output(text)
        if isinstance(parsed, SearchOutput) and ("stale" in q_lower or "definitely on" in q_lower):
            return SearchOutput(
                route="SEARCH",
                reason=parsed.reason,
                search_query=question[:50],
                outdoor_action=parsed.outdoor_action,
            )
        return parsed

    async def summarize_search(
        self,
        question: str,
        context: str | None,
        results: list[SearchResult],
        remaining_budget_s: float,
    ) -> SearchSummary:
        valid = {item["name"]: item["text"] for item in self._summary_fixtures.get("valid", [])}
        unclear_default = '{"status":"unclear","summary":null,"source":null,"local_tip":null}'
        if not results:
            text = valid.get("unclear", unclear_default)
        else:
            text = valid.get("answered_with_tip", valid.get("answered_no_tip"))

        if not text:
            text = unclear_default

        return parse_summary_output(text)


class FakeModelService(BaseRouteService):
    """Configurable mock for automated test suites (no network, deterministic)."""

    def __init__(
        self,
        canned_guard: GuardOutput | None = None,
        canned_route: AIOutput | SearchOutput | HumanOutput | None = None,
        canned_summary: SearchSummary | None = None,
        custom_route_map: dict[str, AIOutput | SearchOutput | HumanOutput] | None = None,
        is_mock: bool = False,
    ) -> None:
        self._canned_guard = canned_guard or GuardOutput(verdict=GuardVerdict.OK, message=None)
        self._canned_route = canned_route
        self._canned_summary = canned_summary
        self._custom_route_map = custom_route_map or {}
        self._is_mock = is_mock

    @property
    def is_mock(self) -> bool:
        return self._is_mock

    async def check_guard(
        self, question: str, context: str | None, remaining_budget_s: float
    ) -> GuardOutput:
        return self._canned_guard

    async def route(
        self, question: str, context: str | None, remaining_budget_s: float
    ) -> AIOutput | SearchOutput | HumanOutput:
        if question in self._custom_route_map:
            return self._custom_route_map[question]
        if self._canned_route is not None:
            return self._canned_route
        return AIOutput(
            route="AI",
            reason="Stable practical know-how.",
            answer="Practice consistently outside.",
            outdoor_action="Try it in person outside.",
        )

    async def summarize_search(
        self,
        question: str,
        context: str | None,
        results: list[SearchResult],
        remaining_budget_s: float,
    ) -> SearchSummary:
        if self._canned_summary is not None:
            return self._canned_summary
        if results:
            return SearchSummary(
                status="answered",
                summary=f"According to {results[0].title}, details are confirmed.",
                source=1,
                local_tip="Arrive early for best experience.",
            )
        return SearchSummary(status="unclear", summary=None, source=None, local_tip=None)
