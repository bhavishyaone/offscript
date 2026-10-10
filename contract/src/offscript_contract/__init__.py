"""Single source of truth for Offscript shapes shared by api/, training/ and web/.

router.py          input cleanup, router messages, per-route replies (AI / SEARCH / HUMAN), parser
guard.py           guard check before routing: missing detail or two questions in one
search_summary.py  grounded summary + local tip from search results, number grounding check
parsing.py         strict JSON parsing and field rules shared by all model replies
rendering.py       Qwen prompt rendering without PyTorch, for the backend
dataset.py         labelled example format and dataset validation
route_dto.py       request and response DTO schemas for POST /api/route

Planned (backend-led): request.py and responses.py for POST /api/route.
Ask before adding or renaming any field.
"""

from offscript_contract.health import HealthResponse
from offscript_contract.route_dto import (
    AiCardContent,
    CardResponse,
    ErrorDetail,
    ErrorResponse,
    Fit,
    GuardResponse,
    HumanCardContent,
    RouteRequest,
    RouteResponseUnion,
    SearchCardContent,
    SearchSource,
)

__all__ = [
    "HealthResponse",
    "RouteRequest",
    "CardResponse",
    "GuardResponse",
    "Fit",
    "ErrorDetail",
    "ErrorResponse",
    "AiCardContent",
    "SearchCardContent",
    "HumanCardContent",
    "SearchSource",
    "RouteResponseUnion",
]
