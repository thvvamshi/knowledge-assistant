import logging
import time
import uuid
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.chat import router as chat_router
from app.api.messages import router as messages_router
from app.api.providers import router as providers_router
from app.api.sessions import router as sessions_router
from app.core.config import get_settings
from app.core.exceptions import global_exception_handler
from app.core.logging import configure_logging
from app.db.init_db import init_db
from app.db.session import AsyncSessionLocal


configure_logging()

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(application: FastAPI):
    logger.info("Initializing database")

    try:
        await init_db()
        logger.info("Database initialization completed")
    except Exception:
        logger.exception("Database initialization failed")
        raise

    yield

    logger.info("Application shutdown")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    request_id = getattr(
        request.state,
        "request_id",
        str(uuid.uuid4()),
    )

    logger.warning(
        "Request validation failed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "errors": exc.errors(),
        },
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed.",
                "details": exc.errors(),
            },
            "request_id": request_id,
        },
        headers={
            "X-Request-ID": request_id,
        },
    )


app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler,
)

app.add_exception_handler(
    Exception,
    global_exception_handler,
)


app.include_router(sessions_router)
app.include_router(messages_router)
app.include_router(providers_router)
app.include_router(chat_router)


async def _check_database() -> bool:
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))

        return True

    except Exception:
        logger.exception("Database health check failed")
        return False


async def _check_ollama() -> bool:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{settings.ollama_base_url.rstrip('/')}/api/tags"
            )

            response.raise_for_status()

            data = response.json()
            models = data.get("models", [])

            return any(
                item.get("name") == settings.ollama_model
                for item in models
            )

    except Exception:
        logger.warning(
            "Ollama health check failed",
            extra={
                "provider": "ollama",
                "model": settings.ollama_model,
            },
        )

        return False


async def _check_vector_index() -> bool:
    """
    Verify that the transcript vector column and HNSW index are available.

    This does not perform an expensive vector search. It checks PostgreSQL
    metadata so the health endpoint remains lightweight.
    """

    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text(
                    """
                    SELECT EXISTS (
                        SELECT 1
                        FROM pg_indexes
                        WHERE tablename = 'transcript_chunks'
                          AND indexname =
                              'ix_transcript_chunks_embedding_hnsw'
                    )
                    """
                )
            )

            index_exists = result.scalar()

            return bool(index_exists)

    except Exception:
        logger.exception(
            "Vector index health check failed"
        )

        return False


@app.middleware("http")
async def request_logging_middleware(
    request: Request,
    call_next,
):
    request_id = request.headers.get(
        "X-Request-ID",
        str(uuid.uuid4()),
    )

    request.state.request_id = request_id

    start_time = time.perf_counter()

    try:
        response = await call_next(request)

        duration_ms = round(
            (time.perf_counter() - start_time) * 1000,
            2,
        )

        response.headers["X-Request-ID"] = request_id

        logger.info(
            "HTTP request completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )

        return response

    except Exception:
        duration_ms = round(
            (time.perf_counter() - start_time) * 1000,
            2,
        )

        logger.exception(
            "HTTP request failed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "duration_ms": duration_ms,
            },
        )

        raise


@app.get("/api/health", tags=["health"])
async def health():
    """
    Dependency health probe.

    Reports API, PostgreSQL, Ollama/model, and vector-index status.
    """

    database_ok = await _check_database()
    ollama_ok = await _check_ollama()
    vector_index_ok = await _check_vector_index()

    dependencies_ok = (
        database_ok
        and ollama_ok
        and vector_index_ok
    )

    return {
        "status": "ok" if dependencies_ok else "degraded",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "dependencies": {
            "database": "ok" if database_ok else "unavailable",
            "ollama": "ok" if ollama_ok else "unavailable",
            "vector_index": (
                "ok"
                if vector_index_ok
                else "unavailable"
            ),
        },
    }


@app.get("/api/health/ready", tags=["health"])
async def readiness():
    """
    Readiness check.

    Confirms that PostgreSQL is reachable.
    """

    database_ok = await _check_database()

    if database_ok:
        return {
            "status": "ready",
            "service": settings.app_name,
            "version": settings.app_version,
            "database": "ok",
        }

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "not_ready",
            "service": settings.app_name,
            "version": settings.app_version,
            "database": "unavailable",
        },
    )
