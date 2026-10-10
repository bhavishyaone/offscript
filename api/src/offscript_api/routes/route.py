"""POST /api/route endpoint implementation (AGENTS.md B3, B4)."""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from offscript_api.clients.serpapi import SerpApiClient
from offscript_api.config import Settings, get_settings
from offscript_api.services.model_service import (
    BaseRouteService,
    LiveModelService,
    MockModelService,
    ModelServiceError,
)
from offscript_api.services.pipeline import run_pipeline
from offscript_api.services.rate_limiter import rate_limiter
from offscript_contract.route_dto import ErrorResponse, RouteRequest, RouteResponseUnion
from offscript_contract.router import InputError, normalize_input

router = APIRouter()

_serpapi_instance: SerpApiClient | None = None
_model_service_instance: BaseRouteService | None = None


def get_model_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> BaseRouteService:
    """Dependency that provides the appropriate model service (live Tinker or mock)."""
    global _model_service_instance
    if _model_service_instance is not None:
        return _model_service_instance

    if settings.offscript_mode == "mock":
        _model_service_instance = MockModelService()
    else:
        _model_service_instance = LiveModelService(
            tinker_api_key=settings.tinker_api_key,
            tinker_model_path=settings.tinker_model_path,
        )
    return _model_service_instance


def get_serpapi_client(
    settings: Annotated[Settings, Depends(get_settings)],
) -> SerpApiClient | None:
    """Dependency that provides a shared SerpApiClient instance if configured, or None."""
    global _serpapi_instance
    if settings.serpapi_api_key:
        if _serpapi_instance is None or _serpapi_instance.api_key != settings.serpapi_api_key:
            _serpapi_instance = SerpApiClient(api_key=settings.serpapi_api_key)
        return _serpapi_instance
    return None


@router.post(
    "/api/route",
    response_model=RouteResponseUnion,
    responses={
        422: {"model": ErrorResponse, "description": "Input validation error"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        502: {"model": ErrorResponse, "description": "Invalid model output / upstream failure"},
        503: {"model": ErrorResponse, "description": "Model unavailable"},
        504: {"model": ErrorResponse, "description": "Timeout"},
    },
)
async def route_request(
    payload: RouteRequest,
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    model_service: Annotated[BaseRouteService, Depends(get_model_service)],
    serpapi_client: Annotated[SerpApiClient | None, Depends(get_serpapi_client)] = None,
) -> Any:
    """Classify and return a card or guard response for user question."""
    request_id = f"req_{uuid.uuid4().hex[:12]}"

    # Rate limit check (Item 10)
    client_ip = request.client.host if request.client else "127.0.0.1"
    if not rate_limiter.is_allowed(client_ip):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": {
                    "code": "rate_limited",
                    "message": "Too many requests. Please wait a moment before trying again.",
                }
            },
        )

    # Step 1: Validate input
    try:
        norm_input = normalize_input(question=payload.question, context=payload.context)
    except InputError as err:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"error": {"code": err.code, "message": str(err)}},
        )

    # Steps 2–7: Safety → Guard Check → Router → Route Handlers → Card
    try:
        return await run_pipeline(
            norm_input,
            request_id=request_id,
            model_service=model_service,
            serpapi_client=serpapi_client,
        )
    except ModelServiceError as err:
        return JSONResponse(
            status_code=err.status_code,
            content={"error": {"code": err.code, "message": err.message}},
        )
