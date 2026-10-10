import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from offscript_api.config import get_settings
from offscript_api.routes import health, route
from offscript_api.services.model_service import ModelServiceError
from offscript_contract.router import FROZEN_ROUTER_PROMPT_VERSION, router_prompt_version

logger = logging.getLogger("offscript_api")


def configure_logging() -> None:
    """Log request IDs, routes, latency and error codes (AGENTS.md B8), never request content."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    # httpx logs every request URL at INFO, and SerpApi URLs carry the API key and the question.
    for noisy in ("httpx", "httpcore", "tinker"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Confirm router prompt version matches frozen version
    version = router_prompt_version()
    if version != FROZEN_ROUTER_PROMPT_VERSION:
        msg = f"Router prompt version mismatch: {version} != {FROZEN_ROUTER_PROMPT_VERSION}."
        raise RuntimeError(f"{msg} Refusing to start.")

    # Connect to Tinker now, so the first user doesn't wait for it (AGENTS.md B6: fail fast).
    settings = get_settings()
    if settings.offscript_mode == "live":
        if not settings.model_configured:
            if settings.offscript_env == "production":
                raise RuntimeError(
                    "TINKER_API_KEY and TINKER_MODEL_PATH must be set in production."
                )
            logger.warning("Tinker is not configured; /api/route returns 503 until it is")
        else:
            try:
                await route.get_model_service(settings).start()
                logger.info("Tinker sampling clients ready")
            except ModelServiceError as err:
                logger.warning("Tinker warm-up failed (%s); requests will retry", err.code)
    yield


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    app = FastAPI(title="Offscript API", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    @app.exception_handler(RequestValidationError)
    async def custom_validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = exc.errors()
        if errors:
            first_err = errors[0]
            msg = first_err.get("msg", "Invalid request body")
            code = "unprocessable_entity"
        else:
            msg = "Invalid request body"
            code = "unprocessable_entity"

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"error": {"code": code, "message": msg}},
        )

    app.include_router(health.router)
    app.include_router(route.router)

    return app


app = create_app()
