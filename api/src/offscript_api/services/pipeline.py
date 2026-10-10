"""End-to-end pipeline for POST /api/route (AGENTS.md B3).

Pipeline order:
  1. Validate input  (normalize_input — raises InputError → 422 in route.py)
  2. Safety rules    (check_safety — returns guard if hit, model never called)
  3. Guard check     (base model call — stops missing details or two questions)
  4. Router call     (fine-tuned model call — determines route, reason, outdoor_action)
  5. Route handler   (AI know-how / SEARCH action & SerpApi + summary / HUMAN)
  6. Card validation (Pydantic contract schemas)
  7. Respond         (includes request_id and latency_ms)
"""

import logging
import time
import urllib.parse

from offscript_api.clients.serpapi import (
    SerpApiClient,
    SerpApiError,
    SerpApiNotConfiguredError,
    SerpApiQuotaError,
    SerpApiTimeoutError,
)
from offscript_api.services.model_service import (
    BaseRouteService,
)
from offscript_api.services.safety import check_safety
from offscript_contract.guard import GuardVerdict
from offscript_contract.route_dto import (
    AiCardContent,
    CardResponse,
    Fit,
    GuardFit,
    GuardResponse,
    HumanCardContent,
    RouteResponseUnion,
    SearchCardContent,
)
from offscript_contract.router import Route, RouterInput
from offscript_contract.search_summary import (
    SearchResult,
    SummaryStatus,
    ungrounded_numbers,
)

logger = logging.getLogger(__name__)

TOTAL_BUDGET_S = 60.0


def _build_search_url(query: str) -> str:
    encoded = urllib.parse.quote_plus(query)
    return f"https://www.google.com/search?q={encoded}"


async def run_pipeline(
    router_input: RouterInput,
    request_id: str,
    model_service: BaseRouteService,
    serpapi_client: SerpApiClient | None = None,
) -> RouteResponseUnion:
    """Execute the full route pipeline for a validated input."""
    start_time = time.perf_counter()

    def get_latency() -> int:
        return max(1, int((time.perf_counter() - start_time) * 1000))

    def get_remaining_budget() -> float:
        elapsed = time.perf_counter() - start_time
        return max(0.0, TOTAL_BUDGET_S - elapsed)

    # ── Step 2: Safety rules (before model call) ───────────────────────
    safety_result = check_safety(router_input, request_id, get_latency())
    if safety_result is not None:
        logger.info(
            "request_id=%s fit=%s latency_ms=%d",
            request_id,
            safety_result.fit,
            get_latency(),
        )
        return safety_result

    # ── Step 3: Guard check (base model, untuned) ──────────────────────
    guard_output = await model_service.check_guard(
        router_input.question,
        router_input.context if router_input.context != "none" else None,
        get_remaining_budget(),
    )

    if guard_output.verdict == GuardVerdict.NEEDS_DETAIL:
        logger.info(
            "request_id=%s fit=%s latency_ms=%d",
            request_id,
            GuardFit.NEEDS_DETAIL,
            get_latency(),
        )
        return GuardResponse(
            fit=GuardFit.NEEDS_DETAIL,
            reason="Essential detail is missing.",
            message=guard_output.message or "Please provide more detail about what you want to do.",
            request_id=request_id,
            latency_ms=get_latency(),
            is_mock=model_service.is_mock,
        )

    if guard_output.verdict == GuardVerdict.TWO_QUESTIONS:
        logger.info(
            "request_id=%s fit=%s latency_ms=%d",
            request_id,
            GuardFit.TWO_QUESTIONS,
            get_latency(),
        )
        return GuardResponse(
            fit=GuardFit.TWO_QUESTIONS,
            reason="Two separate questions asked in one.",
            message=guard_output.message or "Please ask one question at a time.",
            request_id=request_id,
            latency_ms=get_latency(),
            is_mock=model_service.is_mock,
        )

    # ── Step 4: Router call (fine-tuned model) ─────────────────────────
    router_reply = await model_service.route(
        router_input.question,
        router_input.context if router_input.context != "none" else None,
        get_remaining_budget(),
    )

    # ── Step 5: Route handlers ─────────────────────────────────────────
    if router_reply.route == Route.AI:
        card = CardResponse(
            fit=Fit.OK,
            route=Route.AI,
            reason=router_reply.reason,
            content=AiCardContent(
                answer=router_reply.answer,
                outdoor_action=router_reply.outdoor_action,
            ),
            request_id=request_id,
            latency_ms=get_latency(),
            is_mock=model_service.is_mock,
        )
        logger.info(
            "request_id=%s route=%s latency_ms=%d",
            request_id,
            Route.AI,
            get_latency(),
        )
        return card

    if router_reply.route == Route.HUMAN:
        card = CardResponse(
            fit=Fit.OK,
            route=Route.HUMAN,
            reason=router_reply.reason,
            content=HumanCardContent(
                who_to_ask=router_reply.who_to_ask,
                suggested_question=router_reply.suggested_question,
                outdoor_action=router_reply.outdoor_action,
            ),
            request_id=request_id,
            latency_ms=get_latency(),
            is_mock=model_service.is_mock,
        )
        logger.info(
            "request_id=%s route=%s latency_ms=%d",
            request_id,
            Route.HUMAN,
            get_latency(),
        )
        return card

    # Route is SEARCH
    search_query = router_reply.search_query
    search_url = _build_search_url(search_query)

    sources = []
    if serpapi_client is not None and serpapi_client.is_configured:
        try:
            sources = await serpapi_client.search(search_query, num_results=3)
        except (
            SerpApiTimeoutError,
            SerpApiQuotaError,
            SerpApiError,
            SerpApiNotConfiguredError,
        ) as err:
            logger.warning("SerpApi lookup failed: %s", type(err).__name__)
            sources = []

    # If no results found or SerpApi unavailable -> return honest search_limitation
    if not sources:
        logger.info(
            "request_id=%s fit=%s latency_ms=%d",
            request_id,
            GuardFit.SEARCH_LIMITATION,
            get_latency(),
        )
        return GuardResponse(
            fit=GuardFit.SEARCH_LIMITATION,
            reason="Public search results were unavailable or empty.",
            message=(
                "We couldn't confirm fresh public listings or hours automatically. "
                "Check the search link directly before heading out."
            ),
            search_url=search_url,
            request_id=request_id,
            latency_ms=get_latency(),
            is_mock=model_service.is_mock,
        )

    # We have results: run search summary with base model
    search_results = [SearchResult(title=s.title, snippet=s.snippet, link=s.url) for s in sources]

    summary_reply = await model_service.summarize_search(
        router_input.question,
        router_input.context if router_input.context != "none" else None,
        search_results,
        get_remaining_budget(),
    )

    summary_text = None
    local_tip = None

    if summary_reply.status == SummaryStatus.ANSWERED and summary_reply.summary is not None:
        ungrounded = ungrounded_numbers(summary_reply, search_results)
        if not ungrounded:
            summary_text = summary_reply.summary
            local_tip = summary_reply.local_tip
        else:
            logger.warning("Search summary contained ungrounded numbers; treating as unclear")

    card = CardResponse(
        fit=Fit.OK,
        route=Route.SEARCH,
        reason=router_reply.reason,
        content=SearchCardContent(
            search_query=search_query,
            sources=sources,
            search_url=search_url,
            outdoor_action=router_reply.outdoor_action,
            summary=summary_text,
            local_tip=local_tip,
        ),
        request_id=request_id,
        latency_ms=get_latency(),
        is_mock=model_service.is_mock,
    )
    logger.info(
        "request_id=%s route=%s latency_ms=%d",
        request_id,
        Route.SEARCH,
        get_latency(),
    )
    return card
