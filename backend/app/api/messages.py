from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.artifact import Artifact
from app.models.message import Message
from app.models.session import Session
from app.schemas.message import (
    MessageCreate,
    MessageEdit,
    MessageResponse,
    MessageRetry,
)
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


async def _get_session_or_404(
    db: AsyncSession,
    session_id: UUID,
) -> Session:
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

    return session


async def _get_messages(
    db: AsyncSession,
    session_id: UUID,
) -> list[Message]:
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
    )

    return list(result.scalars().all())


async def _get_latest_artifact(
    db: AsyncSession,
    message_id: UUID,
) -> Artifact | None:
    result = await db.execute(
        select(Artifact)
        .where(Artifact.message_id == message_id)
        .order_by(Artifact.created_at.desc())
        .limit(1)
    )

    return result.scalar_one_or_none()


async def _delete_messages(
    db: AsyncSession,
    session_id: UUID,
    message_ids: list[UUID],
) -> None:
    if not message_ids:
        return

    await db.execute(
        delete(Artifact).where(
            Artifact.message_id.in_(message_ids)
        )
    )

    await db.execute(
        delete(Message).where(
            Message.session_id == session_id,
            Message.id.in_(message_ids),
        )
    )


def _history_snapshot(
    messages: list[Message],
) -> list[Message]:
    """
    Create detached Message-like objects for conversation history.

    The objects contain only the fields used by assistant_service.
    This prevents Edit/Retry database mutations from changing the
    history passed to the assistant.
    """

    return [
        Message(
            id=message.id,
            session_id=message.session_id,
            role=message.role,
            content=message.content,
            provider=message.provider,
            model=message.model,
            sources=list(message.sources or []),
            created_at=message.created_at,
        )
        for message in messages
    ]


async def _create_assistant_message(
    db: AsyncSession,
    session_id: UUID,
    content: str,
    conversation_history: list[Message],
    provider: str | None,
) -> Message:
    try:
        assistant_result = await answer_question(
            db,
            content,
            conversation_history=conversation_history,
            provider_name=provider,
        )
    except HTTPException:
        raise
    except Exception:
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

    if assistant_result.artifact_content:
        artifact = Artifact(
            message_id=assistant_message.id,
            type=assistant_result.artifact_type or "markdown",
            content=assistant_result.artifact_content,
        )

        db.add(artifact)
        await db.flush()

    return assistant_message


@router.get(
    "",
    response_model=list[MessageResponse],
)
async def get_messages(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    await _get_session_or_404(db, session_id)

    messages = await _get_messages(db, session_id)

    response = []

    for message in messages:
        artifact = await _get_latest_artifact(
            db,
            message.id,
        )

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
    await _get_session_or_404(db, session_id)

    conversation_history = await _get_messages(
        db,
        session_id,
    )

    user_message = Message(
        session_id=session_id,
        role="user",
        content=payload.content,
        sources=[],
    )

    db.add(user_message)

    try:
        await db.flush()

        assistant_message = await _create_assistant_message(
            db,
            session_id,
            payload.content,
            conversation_history,
            payload.provider,
        )

        await db.commit()
        await db.refresh(assistant_message)

    except HTTPException:
        await db.rollback()
        raise

    except Exception:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "ASSISTANT_UNAVAILABLE",
                "message": "The assistant is temporarily unavailable.",
            },
        )

    artifact = await _get_latest_artifact(
        db,
        assistant_message.id,
    )

    return _serialize_message(
        assistant_message,
        artifact,
    )


@router.patch(
    "/{message_id}",
    response_model=MessageResponse,
)
async def edit_message(
    session_id: UUID,
    message_id: UUID,
    payload: MessageEdit,
    db: AsyncSession = Depends(get_db),
):
    await _get_session_or_404(db, session_id)

    messages = await _get_messages(
        db,
        session_id,
    )

    target_index = next(
        (
            index
            for index, message in enumerate(messages)
            if message.id == message_id
        ),
        None,
    )

    if target_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "MESSAGE_NOT_FOUND",
                "message": "Message not found.",
            },
        )

    target_message = messages[target_index]

    if target_message.role != "user":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_MESSAGE_ROLE",
                "message": "Only user messages can be edited.",
            },
        )

    new_content = payload.content.strip()

    if not new_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "EMPTY_MESSAGE",
                "message": "Message cannot be empty.",
            },
        )

    # Snapshot the history BEFORE changing/deleting anything.
    conversation_history = _history_snapshot(
        messages[:target_index]
    )

    # Delete everything after the edited user message.
    messages_after_target = messages[target_index + 1 :]

    message_ids_to_delete = [
        message.id
        for message in messages_after_target
    ]

    try:
        # Update the existing user message.
        target_message.content = new_content
        target_message.sources = []
        target_message.provider = None
        target_message.model = None

        await db.flush()

        # Remove old assistant response and all later turns.
        await _delete_messages(
            db,
            session_id,
            message_ids_to_delete,
        )

        await db.flush()

        # Generate replacement assistant response.
        assistant_message = await _create_assistant_message(
            db,
            session_id,
            new_content,
            conversation_history,
            payload.provider,
        )

        await db.commit()
        await db.refresh(assistant_message)

    except HTTPException:
        await db.rollback()
        raise

    except Exception:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "ASSISTANT_UNAVAILABLE",
                "message": "The assistant is temporarily unavailable.",
            },
        )

    artifact = await _get_latest_artifact(
        db,
        assistant_message.id,
    )

    return _serialize_message(
        assistant_message,
        artifact,
    )


@router.post(
    "/{message_id}/retry",
    response_model=MessageResponse,
)
async def retry_message(
    session_id: UUID,
    message_id: UUID,
    payload: MessageRetry,
    db: AsyncSession = Depends(get_db),
):
    await _get_session_or_404(db, session_id)

    messages = await _get_messages(
        db,
        session_id,
    )

    target_index = next(
        (
            index
            for index, message in enumerate(messages)
            if message.id == message_id
        ),
        None,
    )

    if target_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "MESSAGE_NOT_FOUND",
                "message": "Message not found.",
            },
        )

    target_message = messages[target_index]

    if target_message.role != "assistant":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_MESSAGE_ROLE",
                "message": "Only assistant messages can be retried.",
            },
        )

    if target_index == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_CONVERSATION_STATE",
                "message": (
                    "The assistant message has no preceding "
                    "user message."
                ),
            },
        )

    previous_message = messages[target_index - 1]

    if previous_message.role != "user":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_CONVERSATION_STATE",
                "message": (
                    "The assistant message must follow a "
                    "user message."
                ),
            },
        )

    # Snapshot history before deleting the target assistant.
    conversation_history = _history_snapshot(
        messages[:target_index - 1]
    )

    question = previous_message.content

    provider = (
        payload.provider
        or target_message.provider
    )

    # Replace the selected assistant and everything after it.
    messages_to_delete = messages[target_index:]

    message_ids_to_delete = [
        message.id
        for message in messages_to_delete
    ]

    try:
        await _delete_messages(
            db,
            session_id,
            message_ids_to_delete,
        )

        await db.flush()

        assistant_message = await _create_assistant_message(
            db,
            session_id,
            question,
            conversation_history,
            provider,
        )

        await db.commit()
        await db.refresh(assistant_message)

    except HTTPException:
        await db.rollback()
        raise

    except Exception:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "ASSISTANT_UNAVAILABLE",
                "message": "The assistant is temporarily unavailable.",
            },
        )

    artifact = await _get_latest_artifact(
        db,
        assistant_message.id,
    )

    return _serialize_message(
        assistant_message,
        artifact,
    )