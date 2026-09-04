from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.artifact import Artifact
from app.models.message import Message
from app.models.session import Session
from app.schemas.message import MessageCreate, MessageResponse
from app.services.assistant_service import answer_question

router = APIRouter(
    prefix="/api/sessions/{session_id}/messages",
    tags=["messages"],
)


def _serialize_message(
    message: Message,
    artifact: Artifact | None = None,
) -> MessageResponse:
    return MessageResponse(
        id=message.id,
        session_id=message.session_id,
        role=message.role,
        content=message.content,
        provider=message.provider,
        model=message.model,
        sources=message.sources or [],
        artifact=(
            {
                "id": artifact.id,
                "type": artifact.type,
                "content": artifact.content,
                "created_at": artifact.created_at,
            }
            if artifact
            else None
        ),
        created_at=message.created_at,
    )


@router.get(
    "",
    response_model=list[MessageResponse],
)
async def get_messages(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Session).where(Session.id == session_id)
    )

    session = result.scalar_one_or_none()

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "SESSION_NOT_FOUND",
                "message": "Session not found.",
            },
        )

    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
    )

    messages = list(result.scalars().all())

    response = []

    for message in messages:
        artifact_result = await db.execute(
            select(Artifact)
            .where(Artifact.message_id == message.id)
            .order_by(Artifact.created_at.desc())
            .limit(1)
        )

        artifact = artifact_result.scalar_one_or_none()

        response.append(
            _serialize_message(
                message,
                artifact,
            )
        )

    return response


@router.post(
    "",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_message(
    session_id: UUID,
    payload: MessageCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Session).where(Session.id == session_id)
    )

    session = result.scalar_one_or_none()

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "SESSION_NOT_FOUND",
                "message": "Session not found.",
            },
        )

    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
    )

    conversation_history = list(result.scalars().all())

    user_message = Message(
        session_id=session_id,
        role="user",
        content=payload.content,
        sources=[],
    )

    db.add(user_message)
    await db.commit()

    try:
        assistant_result = await answer_question(
            db,
            payload.content,
            conversation_history=conversation_history,
            provider_name=payload.provider,
        )
    except Exception:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "ASSISTANT_UNAVAILABLE",
                "message": "The assistant is temporarily unavailable.",
            },
        )

    assistant_message = Message(
        session_id=session_id,
        role="assistant",
        content=assistant_result.answer,
        provider=assistant_result.provider,
        model=assistant_result.model,
        sources=assistant_result.sources or [],
    )

    db.add(assistant_message)

    await db.flush()

    artifact = None

    if assistant_result.artifact_content:
        artifact = Artifact(
            message_id=assistant_message.id,
            type=assistant_result.artifact_type or "markdown",
            content=assistant_result.artifact_content,
        )

        db.add(artifact)

    await db.commit()
    await db.refresh(assistant_message)

    return _serialize_message(
        assistant_message,
        artifact,
    )
