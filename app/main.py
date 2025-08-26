import asyncio
import logging
import time
import uuid
from contextlib import asynccontextmanager
import json

import structlog
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse
from pymongo.errors import PyMongoError

from app.config import settings
from app.domain import errors as domain_errors
from app.infra.logging import configure_logging
from app.infra.mongo import close_mongo_connection, connect_to_mongo, ensure_indexes, db
from app.routes.metrics import router as metrics_router
from app.routes.orders import router as orders_router
from app.routes import health as health_router
from app.utils import request_context
from app.utils.errors import problem

configure_logging(level=settings.log_level)
log = structlog.get_logger("bootstrap")
log.info("app_booting", service_name=settings.service_name)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("lifespan.startup.begin")
    await connect_to_mongo()
    try:
        await ensure_indexes()
    except Exception as e:
        log.warning("lifespan.startup.ensure_indexes.failed", error=str(e))
    log.info("Application startup complete")
    yield
    log.info("lifespan.shutdown.begin")
    await close_mongo_connection()
    log.info("lifespan.shutdown.end")


async def logging_middleware(request: Request, call_next):
    request_context.clear_context()

    # Extraer o generar Request ID
    request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))
    request_context.set_request_id(request_id)

    # Extraer otros IDs relevantes de la ruta
    if "order_id" in request.path_params:
        request_context.set_order_id(request.path_params["order_id"])

    structlog.contextvars.bind_contextvars(
        request_id=request_context.get_request_id(),
    )
    request_log = structlog.get_logger("api.request")

    start_time = time.perf_counter()
    request_log.info("request_started", method=request.method, path=request.url.path)

    response = await call_next(request)
    response.headers["X-Request-Id"] = request_id
    status_code = response.status_code

    duration = time.perf_counter() - start_time
    request_log.info(
        "request_finished",
        status_code=status_code,
        duration_ms=round(duration * 1000, 2),
    )
    request_context.clear_context()
    return response


app = FastAPI(
    title="Backend Microservice - Ecommerce Order Processing Service ",
    version="1.0.0",
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
)

# Middleware & Routers
app.middleware("http")(logging_middleware)
app.include_router(orders_router)
app.include_router(metrics_router)


# --- Health Endpoints ---

@app.get("/health", tags=["Health"], status_code=status.HTTP_200_OK)
async def health():
    """Health check: confirma que la app puede conectar con sus dependencias (Mongo)."""
    try:
        await asyncio.wait_for(
            db().command("ping"),
            timeout=2.0
        )
        return {"status": "ok", "mongo": "ok"}
    except Exception:
        log.warning("health.check.failed", dependency="mongo")
        return problem(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message="Service degraded",
            code="service_degraded",
            details={"mongo": "error"},
        )


# --- Exception Handlers ---

@app.exception_handler(PyMongoError)
async def mongo_exception_handler(request: Request, exc: PyMongoError):
    log.error("mongo.error", error=str(exc), exc_info=True)
    return problem(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="Unexpected database error",
        code="db_error",
        details=str(exc),
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Nota: mantenemos 400 para no romper contratos existentes
    log.warning("api.validation.error", errors=exc.errors())
    
    # Convertir exc.errors() a un formato JSON serializable
    serializable_errors = []
    for error in exc.errors():
        # error is already a dict, check and decode 'input' if it is bytes
        if 'input' in error and isinstance(error['input'], bytes):
            error['input'] = error['input'].decode('utf-8', errors='ignore')
        serializable_errors.append(error)

    return problem(
        status_code=status.HTTP_400_BAD_REQUEST,
        message="Request validation failed",
        code="bad_request",
        details=serializable_errors,
    )


@app.exception_handler(domain_errors.NotFound)
async def not_found_exception_handler(request: Request, exc: domain_errors.NotFound):
    return problem(
        status_code=status.HTTP_404_NOT_FOUND,
        message=str(exc),
        code="not_found",
    )

@app.exception_handler(domain_errors.Conflict)
async def conflict_exception_handler(request: Request, exc: domain_errors.Conflict):
    return problem(
        status_code=status.HTTP_409_CONFLICT,
        message=str(exc),
        code="conflict",
    )

@app.exception_handler(domain_errors.InvalidTransition)
async def invalid_transition_exception_handler(request: Request, exc: domain_errors.InvalidTransition):
    return problem(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message=str(exc),
        code="invalid_transition",
    )

# Mover este handler DESPUÉS de app.include_router para que capture 404/405
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Unifica shape para errores Starlette/FastAPI típicos:
    - 404 Not Found (ruta inexistente)
    - 405 Method Not Allowed
    - 415 Unsupported Media Type
    y cualquier otro HTTPException lanzado explícitamente.
    """
    level = "warning" if exc.status_code < 500 else "error"
    getattr(log, level)("http.exception", status_code=exc.status_code, detail=str(exc.detail))
    # Si detail es dict/list ya compatible, lo enviamos como details
    details = exc.detail if isinstance(exc.detail, (dict, list)) else {"detail": str(exc.detail)}
    code_map = {
        404: "not_found",
        405: "method_not_allowed",
        415: "unsupported_media_type",
        400: "bad_request",
        409: "conflict",
        422: "unprocessable_entity",
    }
    return problem(
        status_code=exc.status_code,
        message=str(exc.detail) if isinstance(exc.detail, str) else "HTTP error",
        code=code_map.get(exc.status_code, "http_error"),
        details=details,
    )