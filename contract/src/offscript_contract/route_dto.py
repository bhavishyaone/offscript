"""DTO schemas for POST /api/route endpoint shared across backend and contract tests.

Strict schemas matching AGENTS.md section B3 & B4.
"""

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from offscript_contract.router import Route


class GuardFit(StrEnum):
    """Guard outcome labels for POST /api/route."""

    NEEDS_DETAIL = "needs_detail"
    TWO_QUESTIONS = "two_questions"
    SAFETY_GUIDANCE = "safety_guidance"
    REFUSAL = "refusal"
    SEARCH_LIMITATION = "search_limitation"


class Fit(StrEnum):
    """Card and guard fit states."""

    OK = "ok"
    NEEDS_DETAIL = "needs_detail"
    TWO_QUESTIONS = "two_questions"
    SAFETY_GUIDANCE = "safety_guidance"
    REFUSAL = "refusal"
    SEARCH_LIMITATION = "search_limitation"


class RouteRequest(BaseModel):
    """Payload sent by client to POST /api/route."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(..., description="User question or goal, 1 to 300 characters.")
    context: str | None = Field(
        default=None,
        description="Optional user context, up to 200 characters.",
    )


class SearchSource(BaseModel):
    """Search source grounded in search engine results."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1)
    url: str = Field(..., min_length=1)
    snippet: str = Field(default="")


class AiCardContent(BaseModel):
    """Payload content when route is AI."""

    model_config = ConfigDict(extra="forbid")

    answer: str = Field(..., description="Concise know-how answer.")
    outdoor_action: str = Field(..., description="One concrete step outside.")


class SearchCardContent(BaseModel):
    """Payload content when route is SEARCH."""

    model_config = ConfigDict(extra="forbid")

    search_query: str = Field(..., description="Query sent to search engine.")
    sources: list[SearchSource] = Field(
        default_factory=list,
        description="Grounding search sources.",
    )
    search_url: str = Field(..., description="Search engine query link.")
    outdoor_action: str = Field(..., description="One concrete step outside.")
    summary: str | None = Field(default=None, description="Grounded answer from search results.")
    local_tip: str | None = Field(default=None, description="Local tacit experience tip.")


class HumanCardContent(BaseModel):
    """Payload content when route is HUMAN."""

    model_config = ConfigDict(extra="forbid")

    who_to_ask: str = Field(..., description="Person type to ask in real world.")
    suggested_question: str = Field(..., description="Natural spoken question (under 20 words).")
    outdoor_action: str = Field(..., description="One concrete step outside.")


class CardResponse(BaseModel):
    """Discriminated successful Card response when fit is ok."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["card"] = "card"
    fit: Literal[Fit.OK] = Fit.OK
    route: Route
    reason: str
    content: AiCardContent | SearchCardContent | HumanCardContent
    request_id: str
    latency_ms: int
    is_mock: bool = False


class GuardResponse(BaseModel):
    """Guard response returned when fit is not ok or safety/scope rule triggers."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["guard"] = "guard"
    fit: GuardFit
    route: None = None
    reason: str
    message: str
    suggested_question: str | None = None
    search_url: str | None = None
    request_id: str
    latency_ms: int
    is_mock: bool = False


class ErrorDetail(BaseModel):
    """Standard error detail object."""

    model_config = ConfigDict(extra="forbid")

    code: str
    message: str


class ErrorResponse(BaseModel):
    """Standard top-level error response format for 4xx and 5xx errors."""

    model_config = ConfigDict(extra="forbid")

    error: ErrorDetail


RouteResponseUnion = Annotated[
    CardResponse | GuardResponse,
    Field(discriminator="kind"),
]
