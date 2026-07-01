"""AI Analyst router — conversational BI endpoints."""

import json
import logging
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.analyst_engine import run_analysis, stream_analysis
from app.ai.report_generator import generate_report
from app.auth import get_current_user
from app.database import get_db
from app.models import (
    AnalystAuditLog,
    AnalystMessage,
    Conversation,
    ConversationBookmark,
    ConversationStatus,
    FeedbackType,
    MessageRole,
    ReportDefinition,
    ReportType,
    SavedInsight,
    User,
    UserFeedback,
)

router = APIRouter(prefix="/analyst", tags=["AI Analyst"])
logger = logging.getLogger(__name__)

# Maximum number of prior messages included in the LLM context window per request.
# Keeping this bounded prevents token overflows on long conversations.
_MAX_HISTORY_MESSAGES = 20


class ConversationCreate(BaseModel):
    title: str = Field(default="New Conversation", max_length=500)
    semantic_model_id: Optional[int] = None
    dashboard_context_id: Optional[int] = None


class ConversationUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=500)
    is_favourite: Optional[bool] = None
    status: Optional[str] = None


class ConversationOut(BaseModel):
    id: int
    title: str
    status: str
    is_favourite: bool
    message_count: int
    summary: Optional[str]
    semantic_model_id: Optional[int]
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_obj(cls, obj: Conversation) -> "ConversationOut":
        return cls(
            id=obj.id,
            title=obj.title,
            status=obj.status.value,
            is_favourite=obj.is_favourite,
            message_count=obj.message_count,
            summary=obj.summary,
            semantic_model_id=obj.semantic_model_id,
            created_at=obj.created_at.isoformat(),
            updated_at=obj.updated_at.isoformat(),
        )


class QuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    stream: bool = False


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    executive_summary: Optional[str]
    key_findings: Optional[list]
    supporting_evidence: Optional[list]
    business_interpretation: Optional[str]
    confidence_level: Optional[int]
    data_sources_used: Optional[list]
    visualizations: Optional[list]
    recommendations: Optional[list]
    suggested_questions: Optional[list]
    intent: Optional[str]
    created_at: str

    @classmethod
    def from_orm_obj(cls, obj: AnalystMessage) -> "MessageOut":
        return cls(
            id=obj.id,
            role=obj.role.value,
            content=obj.content,
            executive_summary=obj.executive_summary,
            key_findings=obj.key_findings,
            supporting_evidence=obj.supporting_evidence,
            business_interpretation=obj.business_interpretation,
            confidence_level=obj.confidence_level,
            data_sources_used=obj.data_sources_used,
            visualizations=obj.visualizations,
            recommendations=obj.recommendations,
            suggested_questions=obj.suggested_questions,
            intent=obj.intent,
            created_at=obj.created_at.isoformat(),
        )


class BookmarkCreate(BaseModel):
    message_id: int
    label: str = Field(default="", max_length=255)


class InsightCreate(BaseModel):
    message_id: Optional[int] = None
    title: str = Field(min_length=1, max_length=500)
    content: str = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)


class InsightOut(BaseModel):
    id: int
    conversation_id: int
    title: str
    content: str
    tags: list[str]
    created_at: str


class FeedbackCreate(BaseModel):
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    feedback_type: str = Field(default="rating")
    comment: Optional[str] = Field(default=None, max_length=2000)


class ReportRequest(BaseModel):
    report_type: str = Field(default="executive_summary")
    conversation_id: Optional[int] = None
    title: Optional[str] = Field(default=None, max_length=500)


class SuggestedQuestionsResponse(BaseModel):
    questions: list[str]
    context: str


async def _get_conversation_or_404(
    conversation_id: int, user_id: int, db: AsyncSession
) -> Conversation:
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
            Conversation.status != ConversationStatus.deleted,
        )
    )
    conversation = result.scalar_one_or_none()
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


async def _get_message_for_conversation(
    conversation_id: int, message_id: int, db: AsyncSession
) -> AnalystMessage:
    result = await db.execute(
        select(AnalystMessage).where(
            AnalystMessage.id == message_id,
            AnalystMessage.conversation_id == conversation_id,
        )
    )
    message = result.scalar_one_or_none()
    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")
    return message


async def _get_user_message(message_id: int, user_id: int, db: AsyncSession) -> AnalystMessage:
    result = await db.execute(
        select(AnalystMessage)
        .join(Conversation, Conversation.id == AnalystMessage.conversation_id)
        .where(
            AnalystMessage.id == message_id,
            Conversation.user_id == user_id,
            Conversation.status != ConversationStatus.deleted,
        )
    )
    message = result.scalar_one_or_none()
    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")
    return message


async def _build_history(conversation_id: int, db: AsyncSession) -> list[dict]:
    result = await db.execute(
        select(AnalystMessage)
        .where(AnalystMessage.conversation_id == conversation_id)
        .order_by(AnalystMessage.created_at.asc())
        .limit(_MAX_HISTORY_MESSAGES)
    )
    messages = result.scalars().all()
    return [{"role": message.role.value, "content": message.content} for message in messages]


async def _log_audit(
    db: AsyncSession,
    user_id: int,
    action: str,
    conversation_id: int | None = None,
    question: str | None = None,
    intent: str | None = None,
    duration_ms: int = 0,
) -> None:
    log = AnalystAuditLog(
        user_id=user_id,
        conversation_id=conversation_id,
        action=action,
        question=question,
        intent=intent,
        duration_ms=duration_ms,
    )
    db.add(log)
    await db.commit()


def _assistant_message_from_payload(conversation_id: int, payload: dict) -> AnalystMessage:
    return AnalystMessage(
        conversation_id=conversation_id,
        role=MessageRole.assistant,
        content=payload.get("executive_summary", "Analysis complete."),
        executive_summary=payload.get("executive_summary"),
        key_findings=payload.get("key_findings"),
        supporting_evidence=payload.get("supporting_evidence"),
        business_interpretation=payload.get("business_interpretation"),
        confidence_level=payload.get("confidence_level"),
        data_sources_used=payload.get("data_sources_used"),
        visualizations=payload.get("visualizations"),
        recommendations=payload.get("recommendations"),
        suggested_questions=payload.get("suggested_questions"),
        intent=payload.get("intent"),
    )


@router.post("/conversations", response_model=ConversationOut, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    body: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conversation = Conversation(
        user_id=current_user.id,
        title=body.title,
        semantic_model_id=body.semantic_model_id,
        dashboard_context_id=body.dashboard_context_id,
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return ConversationOut.from_orm_obj(conversation)


@router.get("/conversations", response_model=list[ConversationOut])
async def list_conversations(
    status_filter: Optional[str] = Query(default="active", alias="status"),
    favourite: Optional[bool] = Query(default=None),
    search: Optional[str] = Query(default=None, max_length=255),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Conversation).where(
        Conversation.user_id == current_user.id,
        Conversation.status != ConversationStatus.deleted,
    )
    if status_filter and status_filter != "all":
        try:
            query = query.where(Conversation.status == ConversationStatus(status_filter))
        except ValueError:
            pass
    if favourite is not None:
        query = query.where(Conversation.is_favourite == favourite)
    if search:
        query = query.where(Conversation.title.ilike(f"%{search}%"))
    query = query.order_by(desc(Conversation.updated_at)).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    conversations = result.scalars().all()
    return [ConversationOut.from_orm_obj(conversation) for conversation in conversations]


@router.get("/conversations/{conversation_id}", response_model=ConversationOut)
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conversation = await _get_conversation_or_404(conversation_id, current_user.id, db)
    return ConversationOut.from_orm_obj(conversation)


@router.patch("/conversations/{conversation_id}", response_model=ConversationOut)
async def update_conversation(
    conversation_id: int,
    body: ConversationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conversation = await _get_conversation_or_404(conversation_id, current_user.id, db)
    if body.title is not None:
        conversation.title = body.title
    if body.is_favourite is not None:
        conversation.is_favourite = body.is_favourite
    if body.status is not None:
        try:
            conversation.status = ConversationStatus(body.status)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="Invalid status value") from exc
    await db.commit()
    await db.refresh(conversation)
    return ConversationOut.from_orm_obj(conversation)


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conversation = await _get_conversation_or_404(conversation_id, current_user.id, db)
    conversation.status = ConversationStatus.deleted
    await db.commit()


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageOut])
async def get_messages(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_conversation_or_404(conversation_id, current_user.id, db)
    result = await db.execute(
        select(AnalystMessage)
        .where(AnalystMessage.conversation_id == conversation_id)
        .order_by(AnalystMessage.created_at.asc())
    )
    messages = result.scalars().all()
    return [MessageOut.from_orm_obj(message) for message in messages]


@router.post("/conversations/{conversation_id}/messages")
async def send_question(
    conversation_id: int,
    body: QuestionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conversation = await _get_conversation_or_404(conversation_id, current_user.id, db)
    history = await _build_history(conversation_id, db)

    user_message = AnalystMessage(
        conversation_id=conversation_id,
        role=MessageRole.user,
        content=body.question,
    )
    db.add(user_message)
    conversation.message_count += 1
    await db.commit()

    if body.stream:

        async def event_generator():
            started_at = time.time()
            full_payload: dict = {}
            async for sse_line in stream_analysis(
                body.question,
                db,
                current_user.id,
                history,
                conversation.semantic_model_id,
            ):
                yield sse_line
                if sse_line.startswith("data: ") and '"type": "result"' in sse_line:
                    try:
                        data = json.loads(sse_line[6:])
                        full_payload = data.get("value", {})
                    except Exception:
                        pass

            try:
                assistant_message = _assistant_message_from_payload(conversation_id, full_payload)
                db.add(assistant_message)
                conversation.message_count += 1
                conversation.summary = full_payload.get("executive_summary")
                if conversation.message_count <= 2 and full_payload.get("executive_summary"):
                    conversation.title = body.question[:100]
                await db.commit()
                await _log_audit(
                    db,
                    current_user.id,
                    "question",
                    conversation_id,
                    body.question,
                    full_payload.get("intent"),
                    int((time.time() - started_at) * 1000),
                )
            except Exception as exc:
                logger.error("Failed to persist assistant message: %s", exc)

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    started_at = time.time()
    payload = await run_analysis(
        body.question,
        db,
        current_user.id,
        history,
        conversation.semantic_model_id,
    )
    assistant_message = _assistant_message_from_payload(conversation_id, payload)
    db.add(assistant_message)
    conversation.message_count += 1
    conversation.summary = payload.get("executive_summary")
    if conversation.message_count <= 2 and payload.get("executive_summary"):
        conversation.title = body.question[:100]
    await db.commit()
    await db.refresh(assistant_message)
    await _log_audit(
        db,
        current_user.id,
        "question",
        conversation_id,
        body.question,
        payload.get("intent"),
        int((time.time() - started_at) * 1000),
    )
    return MessageOut.from_orm_obj(assistant_message)


@router.post("/conversations/{conversation_id}/bookmarks", status_code=status.HTTP_201_CREATED)
async def create_bookmark(
    conversation_id: int,
    body: BookmarkCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_conversation_or_404(conversation_id, current_user.id, db)
    await _get_message_for_conversation(conversation_id, body.message_id, db)
    bookmark = ConversationBookmark(
        conversation_id=conversation_id,
        message_id=body.message_id,
        user_id=current_user.id,
        label=body.label,
    )
    db.add(bookmark)
    await db.commit()
    await db.refresh(bookmark)
    return {"id": bookmark.id, "label": bookmark.label, "message_id": bookmark.message_id}


@router.post("/conversations/{conversation_id}/insights", status_code=status.HTTP_201_CREATED)
async def save_insight(
    conversation_id: int,
    body: InsightCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_conversation_or_404(conversation_id, current_user.id, db)
    if body.message_id is not None:
        await _get_message_for_conversation(conversation_id, body.message_id, db)
    insight = SavedInsight(
        user_id=current_user.id,
        conversation_id=conversation_id,
        message_id=body.message_id,
        title=body.title,
        content=body.content,
        tags=body.tags,
    )
    db.add(insight)
    await db.commit()
    await db.refresh(insight)
    return InsightOut(
        id=insight.id,
        conversation_id=insight.conversation_id,
        title=insight.title,
        content=insight.content,
        tags=insight.tags,
        created_at=insight.created_at.isoformat(),
    )


@router.get("/insights", response_model=list[InsightOut])
async def list_insights(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SavedInsight)
        .where(SavedInsight.user_id == current_user.id)
        .order_by(desc(SavedInsight.created_at))
        .limit(50)
    )
    insights = result.scalars().all()
    return [
        InsightOut(
            id=insight.id,
            conversation_id=insight.conversation_id,
            title=insight.title,
            content=insight.content,
            tags=insight.tags,
            created_at=insight.created_at.isoformat(),
        )
        for insight in insights
    ]


@router.post("/messages/{message_id}/feedback", status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    message_id: int,
    body: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    message = await _get_user_message(message_id, current_user.id, db)

    try:
        feedback_type = FeedbackType(body.feedback_type)
    except ValueError:
        feedback_type = FeedbackType.rating

    feedback = UserFeedback(
        user_id=current_user.id,
        conversation_id=message.conversation_id,
        message_id=message_id,
        rating=body.rating,
        feedback_type=feedback_type,
        comment=body.comment,
    )
    db.add(feedback)
    await db.commit()
    return {"status": "received", "message_id": message_id}


@router.get("/suggested-questions", response_model=SuggestedQuestionsResponse)
async def get_suggested_questions(
    conversation_id: Optional[int] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    base_questions = [
        "What were total sales last month?",
        "Why did revenue decrease?",
        "Which region performed best this quarter?",
        "Compare this quarter with last quarter",
        "Which customers are at risk of churning?",
        "Show employee attrition by department",
        "What are the top five products by profit?",
        "Explain today's business performance",
        "What are the main cost drivers?",
        "Which markets show the highest growth potential?",
        "Forecast revenue for next quarter",
        "What operational risks should I be aware of?",
    ]

    context = "General business questions"
    if conversation_id:
        try:
            conversation = await _get_conversation_or_404(conversation_id, current_user.id, db)
            result = await db.execute(
                select(AnalystMessage)
                .where(
                    AnalystMessage.conversation_id == conversation_id,
                    AnalystMessage.role == MessageRole.assistant,
                )
                .order_by(desc(AnalystMessage.created_at))
                .limit(1)
            )
            last_message = result.scalar_one_or_none()
            if last_message and last_message.suggested_questions:
                return SuggestedQuestionsResponse(
                    questions=last_message.suggested_questions[:8],
                    context=f"Follow-up questions for: {conversation.title}",
                )
            context = f"Conversation: {conversation.title}"
        except HTTPException:
            pass

    return SuggestedQuestionsResponse(questions=base_questions[:8], context=context)


@router.post("/reports", status_code=status.HTTP_201_CREATED)
async def generate_report_endpoint(
    body: ReportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conversation_summary = ""
    if body.conversation_id:
        try:
            conversation = await _get_conversation_or_404(body.conversation_id, current_user.id, db)
            conversation_summary = conversation.summary or conversation.title
        except HTTPException:
            pass

    context = {"report_type": body.report_type, "user": current_user.full_name}
    report_content = await generate_report(body.report_type, context, conversation_summary)

    valid_report_types = {report_type.value for report_type in ReportType}
    report_definition = ReportDefinition(
        user_id=current_user.id,
        conversation_id=body.conversation_id,
        title=body.title or report_content.get("title", f"{body.report_type} Report"),
        report_type=ReportType(body.report_type)
        if body.report_type in valid_report_types
        else ReportType.executive_summary,
        content=report_content,
    )
    db.add(report_definition)
    await db.commit()
    await db.refresh(report_definition)
    return {
        "id": report_definition.id,
        "title": report_definition.title,
        "report_type": report_definition.report_type.value,
        "content": report_definition.content,
        "created_at": report_definition.created_at.isoformat(),
    }


@router.get("/reports", response_model=list[dict])
async def list_reports(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ReportDefinition)
        .where(ReportDefinition.user_id == current_user.id)
        .order_by(desc(ReportDefinition.created_at))
        .limit(20)
    )
    reports = result.scalars().all()
    return [
        {
            "id": report.id,
            "title": report.title,
            "report_type": report.report_type.value,
            "created_at": report.created_at.isoformat(),
        }
        for report in reports
    ]


@router.get("/reports/{report_id}")
async def get_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ReportDefinition).where(
            ReportDefinition.id == report_id,
            ReportDefinition.user_id == current_user.id,
        )
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return {
        "id": report.id,
        "title": report.title,
        "report_type": report.report_type.value,
        "content": report.content,
        "created_at": report.created_at.isoformat(),
    }


@router.post("/explain-dashboard")
async def explain_dashboard(
    body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    dashboard_id = body.get("dashboard_id")
    question = body.get("question", "Explain this dashboard")

    payload = await run_analysis(question, db, current_user.id, [], None)
    return {
        "dashboard_id": dashboard_id,
        "explanation": payload.get("executive_summary"),
        "key_findings": payload.get("key_findings"),
        "business_interpretation": payload.get("business_interpretation"),
        "recommendations": payload.get("recommendations"),
    }
