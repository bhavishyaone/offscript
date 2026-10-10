from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from offscript_api.config import get_settings
from offscript_api.routes import health, route
from offscript_contract.router import FROZEN_ROUTER_PROMPT_VERSION, router_prompt_version


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Confirm router prompt version matches frozen version
    version = router_prompt_version()
    if version != FROZEN_ROUTER_PROMPT_VERSION:
        msg = f"Router prompt version mismatch: {version} != {FROZEN_ROUTER_PROMPT_VERSION}."
        raise RuntimeError(f"{msg} Refusing to start.")
    yield


def create_app() -> FastAPI:
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
