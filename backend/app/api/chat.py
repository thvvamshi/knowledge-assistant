import json
import logging
import uuid

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.artifact import Artifact
from app.models.message import Message
from app.models.session import Session
from app.schemas.chat import ChatRequest
from app.services.assistant_service import stream_question


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/chat",
    tags=["chat"],
)


def _get_request_id(request: Request) -> str:
    request_id = getattr(
        request.state,
        "request_id",
        None,
    )

    if request_id:
        return request_id

    return str(uuid.uuid4())


def _error_event(
    code: str,
    message: str,
    request_id: str,
) -> dict:
    return {
        "type": "error",
        "code": code,
        "message": message,
        "request_id": request_id,
    }


@router.post("")
async def chat(
    payload: ChatRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    request_id = _get_request_id(request)

    try:
        session_result = await db.execute(
            select(Session).where(
                Session.id == payload.session_id
            )
        )

        chat_session = session_result.scalar_one_or_none()

    except Exception:
        logger.exception(
            "Failed to load chat session",
            extra={"request_id": request_id},
        )

        await db.rollback()

        return StreamingResponse(
            iter(
                [
                    json.dumps(
                        _error_event(
                            code="DATABASE_UNAVAILABLE",
                            message="The database is temporarily unavailable.",
                            request_id=request_id,
                        )
                    )
                    + "\n"
                ]
            ),
            media_type="application/x-ndjson",
            status_code=503,
            headers={"X-Request-ID": request_id},
        )

    if chat_session is None:
        return StreamingResponse(
            iter(
                [
                    json.dumps(
                        _error_event(
                            code="SESSION_NOT_FOUND",
                            message="Session not found.",
                            request_id=request_id,
                        )
                    )
                    + "\n"
                ]
            ),
            media_type="application/x-ndjson",
            status_code=404,
            headers={"X-Request-ID": request_id},
        )

    try:
        history_result = await db.execute(
            select(Message)
            .where(
                Message.session_id == payload.session_id
            )
            .order_by(Message.created_at.asc())
        )

        history = list(
            history_result.scalars().all()
        )

        user_message = Message(
            session_id=payload.session_id,
            role="user",
            content=payload.content,
            sources=[],
        )

        db.add(user_message)

        await db.commit()

    except Exception:
        logger.exception(
            "Failed to persist user message",
            extra={"request_id": request_id},
        )

        await db.rollback()

        return StreamingResponse(
            iter(
                [
                    json.dumps(
                        _error_event(
                            code="DATABASE_UNAVAILABLE",
                            message="The database is temporarily unavailable.",
                            request_id=request_id,
                        )
                    )
                    + "\n"
                ]
            ),
            media_type="application/x-ndjson",
            status_code=503,
            headers={"X-Request-ID": request_id},
        )

    async def event_stream():
        assistant_content = ""

        provider = "none"
        model = "none"

        sources = []

        artifact_content = None
        artifact_type = None
        artifact_title = None

        try:
            async for event in stream_question(
                session=db,
                question=payload.content,
                conversation_history=history,
                top_k=payload.top_k,
                similarity_threshold=payload.similarity_threshold,
                provider_name=payload.provider,
            ):
                event_type = event.get("type")

                if event_type == "token":
                    assistant_content += event.get(
                        "content",
                        "",
                    )

                elif event_type == "metadata":
                    provider = event.get(
                        "provider",
                        provider,
                    )

                    model = event.get(
                        "model",
                        model,
                    )

                elif event_type == "sources":
                    sources = event.get(
                        "sources",
                        [],
                    )

                elif event_type == "artifact":
                    artifact = event.get(
                        "artifact",
                        {},
                    )

                    artifact_content = artifact.get(
                        "content",
                        artifact_content,
                    )

                    artifact_type = artifact.get(
                        "type",
                        artifact_type,
                    )

                    artifact_title = artifact.get(
                        "title",
                        artifact_title,
                    )

                elif event_type == "complete":
                    assistant_content = event.get(
                        "answer",
                        event.get(
                            "content",
                            assistant_content,
                        ),
                    )

                    provider = event.get(
                        "provider",
                        provider,
                    )

                    model = event.get(
                        "model",
                        model,
                    )

                    sources = event.get(
                        "sources",
                        sources,
                    )

                    complete_artifact = event.get(
                        "artifact",
                        None,
                    )

                    if complete_artifact:
                        artifact_content = complete_artifact.get(
                            "content",
                            artifact_content,
                        )

                        artifact_type = complete_artifact.get(
                            "type",
                            artifact_type,
                        )

                        artifact_title = complete_artifact.get(
                            "title",
                            artifact_title,
                        )

                yield json.dumps(event) + "\n"

            assistant_message = Message(
                session_id=payload.session_id,
                role="assistant",
                content=assistant_content,
                provider=provider,
                model=model,
                sources=sources,
            )

            db.add(assistant_message)

            await db.flush()

            if artifact_content:
                artifact = Artifact(
                    message_id=assistant_message.id,
                    type=artifact_type or "markdown",
                    content=artifact_content,
                )

                db.add(artifact)

            await db.commit()

            if artifact_content:
                yield json.dumps(
                    {
                        "type": "artifact_saved",
                        "artifact": {
                            "type": artifact_type or "markdown",
                            "title": artifact_title or "Generated Markdown",
                            "content": artifact_content,
                        },
                        "provider": provider,
                        "model": model,
                        "request_id": request_id,
                    }
                ) + "\n"

        except Exception:
            logger.exception(
                "Chat streaming failed",
                extra={"request_id": request_id},
            )

            await db.rollback()

            yield json.dumps(
                _error_event(
                    code="ASSISTANT_UNAVAILABLE",
                    message="The assistant is temporarily unavailable.",
                    request_id=request_id,
                )
            ) + "\n"

    return StreamingResponse(
        event_stream(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Request-ID": request_id,
        },
    )
