from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.entities import Conversation, Document, Message, MessageRole
from app.rag.access import build_access_scope
from app.rag.agent import hr_agent
from app.schemas.auth import CurrentUser
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.answer_cache import get_cached_answer, make_answer_key, set_cached_answer
from app.services.audit import record_audit
from app.services.rate_limit import enforce_rate_limit

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    await enforce_rate_limit(f"chat:{user.id}", 30, 60)
    conversation = None
    if payload.conversation_id:
        conversation = await db.scalar(
            select(Conversation).where(
                Conversation.id == payload.conversation_id, Conversation.user_id == user.id
            )
        )
        if not conversation:
            raise HTTPException(404, detail="Conversation not found")
    if not conversation:
        conversation = Conversation(id=uuid4(), user_id=user.id, title=payload.message[:80])
        db.add(conversation)
        await db.flush()

    previous = (
        await db.scalars(
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .order_by(Message.created_at.desc())
            .limit(6)
        )
    ).all()
    history = [{"role": item.role.value, "content": item.content} for item in reversed(previous)]
    now = datetime.now(UTC)
    db.add(
        Message(
            id=uuid4(), conversation_id=conversation.id, role=MessageRole.USER,
            content=payload.message, citations=[], trace={}, created_at=now,
        )
    )
    scope = build_access_scope(user)
    corpus_version = int(await db.scalar(select(func.max(Document.corpus_version))) or 0)
    cache_key = make_answer_key(scope, payload.message, corpus_version)
    cached = await get_cached_answer(cache_key) if not history else None
    if cached:
        result = {**cached, "trace": {**cached.get("trace", {}), "cache_hit": True}}
    else:
        result = await hr_agent.run(db, scope, payload.message, history)
        if not history:
            await set_cached_answer(
                cache_key,
                {
                    "answer": result["answer"], "citations": result.get("citations", []),
                    "trace": result.get("trace", {}), "route": result.get("route"),
                },
            )
    answer_message = Message(
        id=uuid4(), conversation_id=conversation.id, role=MessageRole.ASSISTANT,
        content=result["answer"], citations=result.get("citations", []), trace=result.get("trace", {}),
        created_at=datetime.now(UTC),
    )
    db.add(answer_message)
    await record_audit(
        db, "chat.answer", "conversation", user.id, str(conversation.id),
        {"route": result.get("route"), "retrieved_chunks": len(result.get("chunks", []))},
    )
    await db.commit()
    return ChatResponse(
        conversation_id=conversation.id, message_id=answer_message.id, answer=answer_message.content,
        citations=answer_message.citations,
    )


@router.get("/conversations")
async def conversations(
    user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[dict]:
    rows = (
        await db.scalars(
            select(Conversation).where(Conversation.user_id == user.id).order_by(Conversation.updated_at.desc())
        )
    ).all()
    return [{"id": row.id, "title": row.title, "updated_at": row.updated_at} for row in rows]


@router.get("/conversations/{conversation_id}/messages")
async def messages(
    conversation_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    conversation = await db.scalar(
        select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user.id)
    )
    if not conversation:
        raise HTTPException(404, detail="Conversation not found")
    rows = (
        await db.scalars(
            select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at)
        )
    ).all()
    return [
        {"id": row.id, "role": row.role.value, "content": row.content, "citations": row.citations,
         "created_at": row.created_at}
        for row in rows
    ]
