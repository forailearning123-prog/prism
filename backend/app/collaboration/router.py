from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import get_current_user
from app.models import User

from app.collaboration.models import (
    Workspace,
    WorkspaceMember,
    Discussion,
    Comment,
    DecisionRecord,
    DecisionParticipant,
    DecisionHistory,
    ActionItem,
    ApprovalWorkflow,
    ApprovalWorkflowStep,
    ApprovalInstance,
    ApprovalAction,
    MeetingSummary,
    MeetingPack,
    KnowledgeArticle,
    Notification,
    NotificationPreference,
    CollaborationMetric,
    DecisionImpact,
    DiscussionContextType,
    NotificationType,
    ActionStatus,
    DecisionStatus,
)
from app.collaboration.schemas import (
    WorkspaceCreate,
    WorkspaceUpdate,
    WorkspaceMemberAdd,
    WorkspaceMemberUpdate,
    WorkspaceOut,
    WorkspaceListOut,
    DiscussionCreate,
    DiscussionUpdate,
    DiscussionOut,
    DiscussionListOut,
    CommentCreate,
    CommentUpdate,
    CommentOut,
    ReactionToggle,
    DecisionCreate,
    DecisionUpdate,
    DecisionParticipantAdd,
    DecisionOut,
    DecisionListOut,
    DecisionHistoryOut,
    ActionCreate,
    ActionUpdate,
    ActionOut,
    ActionListOut,
    ApprovalWorkflowCreate,
    ApprovalWorkflowUpdate,
    ApprovalWorkflowStepCreate,
    ApprovalWorkflowOut,
    ApprovalSubmit,
    ApprovalActionCreate,
    ApprovalInstanceOut,
    MeetingSummaryCreate,
    MeetingSummaryUpdate,
    MeetingSummaryOut,
    MeetingPackGenerate,
    MeetingPackOut,
    AIAssistantAgendaRequest,
    AIAssistantSummaryRequest,
    AIAssistantAgendaOut,
    AIAssistantSummaryOut,
    KnowledgeArticleCreate,
    KnowledgeArticleUpdate,
    KnowledgeArticleOut,
    KnowledgeSearchRequest,
    KnowledgeListOut,
    NotificationOut,
    NotificationListOut,
    NotificationPreferenceUpdate,
    NotificationPreferenceOut,
    CollaborationAnalyticsQuery,
    CollaborationAnalyticsDashboard,
    CollaborationMetricOut,
    DecisionImpactCreate,
    DecisionImpactUpdate,
    DecisionImpactOut,
    TimelineEvent,
    TimelineOut,
)
from app.collaboration.workspace_service import WorkspaceService
from app.collaboration.discussion_service import DiscussionService, CommentService
from app.collaboration.decision_service import DecisionService
from app.collaboration.action_service import ActionService
from app.collaboration.approval_service import ApprovalService
from app.collaboration.meeting_service import MeetingService, AIAssistantService
from app.collaboration.knowledge_service import KnowledgeService
from app.collaboration.notification_service import NotificationService
from app.collaboration.analytics_service import AnalyticsService
from app.collaboration.impact_service import ImpactService

router = APIRouter(prefix="/api/v1/collaboration", tags=["Collaboration"])


def get_workspace_service(db: AsyncSession = Depends(get_db)) -> WorkspaceService:
    return WorkspaceService(db)


def get_discussion_service(db: AsyncSession = Depends(get_db)) -> DiscussionService:
    return DiscussionService(db)


def get_comment_service(db: AsyncSession = Depends(get_db)) -> CommentService:
    return CommentService(db)


def get_decision_service(db: AsyncSession = Depends(get_db)) -> DecisionService:
    return DecisionService(db)


def get_action_service(db: AsyncSession = Depends(get_db)) -> ActionService:
    return ActionService(db)


def get_approval_service(db: AsyncSession = Depends(get_db)) -> ApprovalService:
    return ApprovalService(db)


def get_meeting_service(db: AsyncSession = Depends(get_db)) -> MeetingService:
    return MeetingService(db)


def get_ai_assistant_service(db: AsyncSession = Depends(get_db)) -> AIAssistantService:
    return AIAssistantService(db)


def get_knowledge_service(db: AsyncSession = Depends(get_db)) -> KnowledgeService:
    return KnowledgeService(db)


def get_notification_service(db: AsyncSession = Depends(get_db)) -> NotificationService:
    return NotificationService(db)


def get_analytics_service(db: AsyncSession = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(db)


def get_impact_service(db: AsyncSession = Depends(get_db)) -> ImpactService:
    return ImpactService(db)


# ── Helper ──

async def get_user_name(user_id: int, db: AsyncSession) -> str:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    return user.full_name if user else "Unknown"


def pagination_params(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    return page, page_size


# ═══════════════════════════════════════════
# WORKSPACE ENDPOINTS
# ═══════════════════════════════════════════

@router.post("/workspaces", response_model=WorkspaceOut, status_code=201)
async def create_workspace(
    data: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    svc: WorkspaceService = Depends(get_workspace_service),
):
    workspace = await svc.create_workspace(data, current_user.id)
    counts = await svc.get_workspace_counts(workspace.id)
    return WorkspaceOut(
        id=workspace.id,
        name=workspace.name,
        description=workspace.description,
        workspace_type=workspace.workspace_type.value,
        owner_id=workspace.owner_id,
        is_archived=workspace.is_archived,
        member_count=counts["member_count"],
        discussion_count=counts["discussion_count"],
        decision_count=counts["decision_count"],
        action_count=counts["action_count"],
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
    )


@router.get("/workspaces", response_model=WorkspaceListOut)
async def list_workspaces(
    search: Optional[str] = Query(None),
    workspace_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    svc: WorkspaceService = Depends(get_workspace_service),
    pagination: tuple = Depends(pagination_params),
):
    page, page_size = pagination
    workspaces, total = await svc.list_workspaces(
        current_user.id, search=search, workspace_type=workspace_type,
        page=page, page_size=page_size,
    )

    items = []
    for w in workspaces:
        counts = await svc.get_workspace_counts(w.id)
        items.append(WorkspaceOut(
            id=w.id,
            name=w.name,
            description=w.description,
            workspace_type=w.workspace_type.value,
            owner_id=w.owner_id,
            is_archived=w.is_archived,
            member_count=counts["member_count"],
            discussion_count=counts["discussion_count"],
            decision_count=counts["decision_count"],
            action_count=counts["action_count"],
            created_at=w.created_at,
            updated_at=w.updated_at,
        ))

    return WorkspaceListOut(items=items, total=total, page=page, page_size=page_size)


@router.get("/workspaces/{workspace_id}", response_model=WorkspaceOut)
async def get_workspace(
    workspace_id: int,
    current_user: User = Depends(get_current_user),
    svc: WorkspaceService = Depends(get_workspace_service),
):
    workspace = await svc.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    counts = await svc.get_workspace_counts(workspace.id)
    return WorkspaceOut(
        id=workspace.id,
        name=workspace.name,
        description=workspace.description,
        workspace_type=workspace.workspace_type.value,
        owner_id=workspace.owner_id,
        is_archived=workspace.is_archived,
        member_count=counts["member_count"],
        discussion_count=counts["discussion_count"],
        decision_count=counts["decision_count"],
        action_count=counts["action_count"],
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
    )


@router.put("/workspaces/{workspace_id}", response_model=WorkspaceOut)
async def update_workspace(
    workspace_id: int,
    data: WorkspaceUpdate,
    current_user: User = Depends(get_current_user),
    svc: WorkspaceService = Depends(get_workspace_service),
):
    workspace = await svc.update_workspace(workspace_id, data)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    counts = await svc.get_workspace_counts(workspace.id)
    return WorkspaceOut(
        id=workspace.id,
        name=workspace.name,
        description=workspace.description,
        workspace_type=workspace.workspace_type.value,
        owner_id=workspace.owner_id,
        is_archived=workspace.is_archived,
        member_count=counts["member_count"],
        discussion_count=counts["discussion_count"],
        decision_count=counts["decision_count"],
        action_count=counts["action_count"],
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
    )


@router.delete("/workspaces/{workspace_id}")
async def archive_workspace(
    workspace_id: int,
    current_user: User = Depends(get_current_user),
    svc: WorkspaceService = Depends(get_workspace_service),
):
    success = await svc.archive_workspace(workspace_id)
    if not success:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return {"message": "Workspace archived"}


@router.post("/workspaces/{workspace_id}/members")
async def add_workspace_member(
    workspace_id: int,
    data: WorkspaceMemberAdd,
    current_user: User = Depends(get_current_user),
    svc: WorkspaceService = Depends(get_workspace_service),
):
    member = await svc.add_member(workspace_id, data)
    if not member:
        raise HTTPException(status_code=404, detail="Workspace not found")
    user_name = await get_user_name(member.user_id, svc.db)
    return {"id": member.id, "workspace_id": member.workspace_id, "user_id": member.user_id,
            "user_name": user_name, "role": member.role.value, "joined_at": member.joined_at}


@router.put("/workspaces/{workspace_id}/members/{user_id}")
async def update_member_role(
    workspace_id: int,
    user_id: int,
    data: WorkspaceMemberUpdate,
    current_user: User = Depends(get_current_user),
    svc: WorkspaceService = Depends(get_workspace_service),
):
    member = await svc.update_member_role(workspace_id, user_id, data)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    user_name = await get_user_name(member.user_id, svc.db)
    return {"id": member.id, "workspace_id": member.workspace_id, "user_id": member.user_id,
            "user_name": user_name, "role": member.role.value, "joined_at": member.joined_at}


@router.delete("/workspaces/{workspace_id}/members/{user_id}")
async def remove_workspace_member(
    workspace_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    svc: WorkspaceService = Depends(get_workspace_service),
):
    success = await svc.remove_member(workspace_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Member not found")
    return {"message": "Member removed"}


@router.get("/workspaces/{workspace_id}/members")
async def list_workspace_members(
    workspace_id: int,
    current_user: User = Depends(get_current_user),
    svc: WorkspaceService = Depends(get_workspace_service),
):
    members = await svc.get_members(workspace_id)
    result = []
    for m in members:
        user_name = await get_user_name(m.user_id, svc.db)
        result.append({"id": m.id, "workspace_id": m.workspace_id, "user_id": m.user_id,
                       "user_name": user_name, "role": m.role.value, "joined_at": m.joined_at})
    return result


# ═══════════════════════════════════════════
# DISCUSSION ENDPOINTS
# ═══════════════════════════════════════════

@router.post("/discussions", status_code=201)
async def create_discussion(
    data: DiscussionCreate,
    current_user: User = Depends(get_current_user),
    svc: DiscussionService = Depends(get_discussion_service),
):
    discussion = await svc.create_discussion(data, current_user.id)
    creator_name = await get_user_name(discussion.created_by, svc.db)
    return DiscussionOut(
        id=discussion.id,
        workspace_id=discussion.workspace_id,
        title=discussion.title,
        context_type=discussion.context_type.value if discussion.context_type else None,
        context_id=discussion.context_id,
        is_pinned=discussion.is_pinned,
        is_archived=discussion.is_archived,
        comment_count=discussion.comment_count,
        created_by=discussion.created_by,
        creator_name=creator_name,
        created_at=discussion.created_at,
        updated_at=discussion.updated_at,
    )


@router.get("/discussions", response_model=DiscussionListOut)
async def list_discussions(
    workspace_id: int = Query(...),
    search: Optional[str] = Query(None),
    context_type: Optional[str] = Query(None),
    context_id: Optional[int] = Query(None),
    is_pinned: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    svc: DiscussionService = Depends(get_discussion_service),
    pagination: tuple = Depends(pagination_params),
):
    page, page_size = pagination
    discussions, total = await svc.list_discussions(
        workspace_id, search=search, context_type=context_type,
        context_id=context_id, is_pinned=is_pinned, page=page, page_size=page_size,
    )
    items = []
    for d in discussions:
        creator_name = await get_user_name(d.created_by, svc.db)
        items.append(DiscussionOut(
            id=d.id,
            workspace_id=d.workspace_id,
            title=d.title,
            context_type=d.context_type.value if d.context_type else None,
            context_id=d.context_id,
            is_pinned=d.is_pinned,
            is_archived=d.is_archived,
            comment_count=d.comment_count,
            created_by=d.created_by,
            creator_name=creator_name,
            created_at=d.created_at,
            updated_at=d.updated_at,
        ))
    return DiscussionListOut(items=items, total=total, page=page, page_size=page_size)


@router.put("/discussions/{discussion_id}")
async def update_discussion(
    discussion_id: int,
    data: DiscussionUpdate,
    current_user: User = Depends(get_current_user),
    svc: DiscussionService = Depends(get_discussion_service),
):
    discussion = await svc.update_discussion(discussion_id, data)
    if not discussion:
        raise HTTPException(status_code=404, detail="Discussion not found")
    creator_name = await get_user_name(discussion.created_by, svc.db)
    return DiscussionOut(
        id=discussion.id,
        workspace_id=discussion.workspace_id,
        title=discussion.title,
        context_type=discussion.context_type.value if discussion.context_type else None,
        context_id=discussion.context_id,
        is_pinned=discussion.is_pinned,
        is_archived=discussion.is_archived,
        comment_count=discussion.comment_count,
        created_by=discussion.created_by,
        creator_name=creator_name,
        created_at=discussion.created_at,
        updated_at=discussion.updated_at,
    )


@router.delete("/discussions/{discussion_id}")
async def archive_discussion(
    discussion_id: int,
    current_user: User = Depends(get_current_user),
    svc: DiscussionService = Depends(get_discussion_service),
):
    success = await svc.archive_discussion(discussion_id)
    if not success:
        raise HTTPException(status_code=404, detail="Discussion not found")
    return {"message": "Discussion archived"}


@router.patch("/discussions/{discussion_id}/pin")
async def toggle_pin_discussion(
    discussion_id: int,
    current_user: User = Depends(get_current_user),
    svc: DiscussionService = Depends(get_discussion_service),
):
    discussion = await svc.toggle_pin(discussion_id)
    if not discussion:
        raise HTTPException(status_code=404, detail="Discussion not found")
    return {"is_pinned": discussion.is_pinned}


# ═══════════════════════════════════════════
# COMMENT ENDPOINTS
# ═══════════════════════════════════════════

@router.post("/comments", status_code=201)
async def create_comment(
    data: CommentCreate,
    current_user: User = Depends(get_current_user),
    svc: CommentService = Depends(get_comment_service),
):
    comment = await svc.create_comment(data, current_user.id)
    if not comment:
        raise HTTPException(status_code=404, detail="Discussion not found")
    creator_name = await get_user_name(comment.created_by, svc.db)
    replies = await svc.get_replies(comment.id) if not comment.parent_id else []
    return CommentOut(
        id=comment.id,
        discussion_id=comment.discussion_id,
        parent_id=comment.parent_id,
        content=comment.content,
        content_rich_text=comment.content_rich_text,
        mentions=comment.mentions,
        attachments=comment.attachments,
        reactions=comment.reactions,
        is_deleted=comment.is_deleted,
        created_by=comment.created_by,
        creator_name=creator_name,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        reply_count=len(replies),
    )


@router.get("/discussions/{discussion_id}/comments")
async def list_comments(
    discussion_id: int,
    current_user: User = Depends(get_current_user),
    svc: CommentService = Depends(get_comment_service),
    pagination: tuple = Depends(pagination_params),
):
    page, page_size = pagination
    comments, total = await svc.get_comments(discussion_id, page=page, page_size=page_size)
    items = []
    for c in comments:
        creator_name = await get_user_name(c.created_by, svc.db)
        replies = await svc.get_replies(c.id)
        reply_items = []
        for r in replies:
            reply_creator = await get_user_name(r.created_by, svc.db)
            reply_items.append(CommentOut(
                id=r.id, discussion_id=r.discussion_id, parent_id=r.parent_id,
                content=r.content, content_rich_text=r.content_rich_text,
                mentions=r.mentions, attachments=r.attachments, reactions=r.reactions,
                is_deleted=r.is_deleted, created_by=r.created_by,
                creator_name=reply_creator, created_at=r.created_at, updated_at=r.updated_at,
                reply_count=0,
            ))
        items.append(CommentOut(
            id=c.id, discussion_id=c.discussion_id, parent_id=c.parent_id,
            content=c.content, content_rich_text=c.content_rich_text,
            mentions=c.mentions, attachments=c.attachments, reactions=c.reactions,
            is_deleted=c.is_deleted, created_by=c.created_by,
            creator_name=creator_name, created_at=c.created_at, updated_at=c.updated_at,
            reply_count=len(replies),
        ))
        # Append replies
        items.extend(reply_items)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.put("/comments/{comment_id}")
async def update_comment(
    comment_id: int,
    data: CommentUpdate,
    current_user: User = Depends(get_current_user),
    svc: CommentService = Depends(get_comment_service),
):
    comment = await svc.update_comment(comment_id, data, current_user.id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found or unauthorized")
    creator_name = await get_user_name(comment.created_by, svc.db)
    return CommentOut(
        id=comment.id, discussion_id=comment.discussion_id, parent_id=comment.parent_id,
        content=comment.content, content_rich_text=comment.content_rich_text,
        mentions=comment.mentions, attachments=comment.attachments, reactions=comment.reactions,
        is_deleted=comment.is_deleted, created_by=comment.created_by,
        creator_name=creator_name, created_at=comment.created_at, updated_at=comment.updated_at,
        reply_count=0,
    )


@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    svc: CommentService = Depends(get_comment_service),
):
    success = await svc.delete_comment(comment_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Comment not found or unauthorized")
    return {"message": "Comment deleted"}


@router.post("/comments/{comment_id}/reactions")
async def toggle_reaction(
    comment_id: int,
    data: ReactionToggle,
    current_user: User = Depends(get_current_user),
    svc: CommentService = Depends(get_comment_service),
):
    comment = await svc.toggle_reaction(comment_id, data, current_user.id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    return {"reactions": comment.reactions}


# ═══════════════════════════════════════════
# DECISION ENDPOINTS
# ═══════════════════════════════════════════

@router.post("/decisions", status_code=201)
async def create_decision(
    data: DecisionCreate,
    current_user: User = Depends(get_current_user),
    svc: DecisionService = Depends(get_decision_service),
):
    decision = await svc.create_decision(data, current_user.id)
    return await _format_decision(decision, svc)


@router.get("/decisions", response_model=DecisionListOut)
async def list_decisions(
    workspace_id: int = Query(...),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    owner_id: Optional[int] = Query(None),
    context_type: Optional[str] = Query(None),
    context_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    svc: DecisionService = Depends(get_decision_service),
    pagination: tuple = Depends(pagination_params),
):
    page, page_size = pagination
    decisions, total = await svc.list_decisions(
        workspace_id, search=search, status=status, priority=priority,
        owner_id=owner_id, context_type=context_type, context_id=context_id,
        page=page, page_size=page_size,
    )
    items = [await _format_decision(d, svc) for d in decisions]
    return DecisionListOut(items=items, total=total, page=page, page_size=page_size)


@router.get("/decisions/{decision_id}")
async def get_decision(
    decision_id: int,
    current_user: User = Depends(get_current_user),
    svc: DecisionService = Depends(get_decision_service),
):
    decision = await svc.get_decision(decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    return await _format_decision(decision, svc)


@router.put("/decisions/{decision_id}")
async def update_decision(
    decision_id: int,
    data: DecisionUpdate,
    current_user: User = Depends(get_current_user),
    svc: DecisionService = Depends(get_decision_service),
):
    decision = await svc.update_decision(decision_id, data, current_user.id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    return await _format_decision(decision, svc)


@router.post("/decisions/{decision_id}/participants")
async def add_decision_participant(
    decision_id: int,
    data: DecisionParticipantAdd,
    current_user: User = Depends(get_current_user),
    svc: DecisionService = Depends(get_decision_service),
):
    participant = await svc.add_participant(decision_id, data)
    if not participant:
        raise HTTPException(status_code=404, detail="Decision not found")
    user_name = await get_user_name(participant.user_id, svc.db)
    return {"id": participant.id, "decision_id": participant.decision_id,
            "user_id": participant.user_id, "user_name": user_name,
            "role": participant.role.value, "added_at": participant.added_at}


@router.delete("/decisions/{decision_id}/participants/{user_id}")
async def remove_decision_participant(
    decision_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    svc: DecisionService = Depends(get_decision_service),
):
    success = await svc.remove_participant(decision_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Participant not found")
    return {"message": "Participant removed"}


@router.get("/decisions/{decision_id}/participants")
async def list_decision_participants(
    decision_id: int,
    current_user: User = Depends(get_current_user),
    svc: DecisionService = Depends(get_decision_service),
):
    participants = await svc.get_participants(decision_id)
    result = []
    for p in participants:
        user_name = await get_user_name(p.user_id, svc.db)
        result.append({"id": p.id, "decision_id": p.decision_id, "user_id": p.user_id,
                       "user_name": user_name, "role": p.role.value, "added_at": p.added_at})
    return result


@router.get("/decisions/{decision_id}/history")
async def get_decision_history(
    decision_id: int,
    current_user: User = Depends(get_current_user),
    svc: DecisionService = Depends(get_decision_service),
):
    history = await svc.get_history(decision_id)
    items = []
    for h in history:
        changer_name = await get_user_name(h.changed_by, svc.db)
        items.append(DecisionHistoryOut(
            id=h.id, decision_id=h.decision_id, field_changed=h.field_changed,
            old_value=h.old_value, new_value=h.new_value,
            changed_by=h.changed_by, changer_name=changer_name, created_at=h.created_at,
        ))
    return items


async def _format_decision(decision: DecisionRecord, svc: DecisionService) -> DecisionOut:
    owner_name = await get_user_name(decision.owner_id, svc.db)
    creator_name = await get_user_name(decision.created_by, svc.db)
    participants = await svc.get_participants(decision.id)
    history = await svc.get_history(decision.id)
    return DecisionOut(
        id=decision.id, workspace_id=decision.workspace_id,
        title=decision.title, description=decision.description,
        context_type=decision.context_type.value if decision.context_type else None,
        context_id=decision.context_id,
        owner_id=decision.owner_id, owner_name=owner_name,
        priority=decision.priority.value, status=decision.status.value,
        business_rationale=decision.business_rationale,
        expected_outcome=decision.expected_outcome,
        actual_outcome=decision.actual_outcome,
        due_date=decision.due_date, completed_at=decision.completed_at,
        created_by=decision.created_by, creator_name=creator_name,
        participant_count=len(participants), history_count=len(history),
        created_at=decision.created_at, updated_at=decision.updated_at,
    )


# ═══════════════════════════════════════════
# ACTION ENDPOINTS
# ═══════════════════════════════════════════

@router.post("/actions", status_code=201)
async def create_action(
    data: ActionCreate,
    current_user: User = Depends(get_current_user),
    svc: ActionService = Depends(get_action_service),
):
    action = await svc.create_action(data, current_user.id)
    return await _format_action(action, svc)


@router.get("/actions", response_model=ActionListOut)
async def list_actions(
    workspace_id: int = Query(...),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    assignee_id: Optional[int] = Query(None),
    context_type: Optional[str] = Query(None),
    context_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    svc: ActionService = Depends(get_action_service),
    pagination: tuple = Depends(pagination_params),
):
    page, page_size = pagination
    actions, total = await svc.list_actions(
        workspace_id, search=search, status=status, priority=priority,
        assignee_id=assignee_id, context_type=context_type, context_id=context_id,
        page=page, page_size=page_size,
    )
    items = [await _format_action(a, svc) for a in actions]
    return ActionListOut(items=items, total=total, page=page, page_size=page_size)


@router.get("/actions/{action_id}")
async def get_action(
    action_id: int,
    current_user: User = Depends(get_current_user),
    svc: ActionService = Depends(get_action_service),
):
    action = await svc.get_action(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    return await _format_action(action, svc)


@router.put("/actions/{action_id}")
async def update_action(
    action_id: int,
    data: ActionUpdate,
    current_user: User = Depends(get_current_user),
    svc: ActionService = Depends(get_action_service),
):
    action = await svc.update_action(action_id, data)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    return await _format_action(action, svc)


@router.patch("/actions/{action_id}/complete")
async def complete_action(
    action_id: int,
    current_user: User = Depends(get_current_user),
    svc: ActionService = Depends(get_action_service),
):
    action = await svc.complete_action(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    return await _format_action(action, svc)


@router.get("/actions/calendar")
async def get_action_calendar(
    workspace_id: int = Query(...),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    svc: ActionService = Depends(get_action_service),
):
    from datetime import datetime as dt
    start = dt.fromisoformat(start_date) if start_date else datetime.now(timezone.utc)
    end = dt.fromisoformat(end_date) if end_date else start.replace(month=start.month + 1)
    actions = await svc.list_actions_by_due_date(workspace_id, start, end)
    return [await _format_action(a, svc) for a in actions]


@router.get("/actions/kanban")
async def get_action_kanban(
    workspace_id: int = Query(...),
    current_user: User = Depends(get_current_user),
    svc: ActionService = Depends(get_action_service),
):
    counts = await svc.get_action_counts_by_status(workspace_id)
    # Get all non-cancelled actions
    actions, _ = await svc.list_actions(workspace_id, page_size=100)
    formatted = [await _format_action(a, svc) for a in actions]
    return {
        "columns": {
            "open": {"title": "To Do", "items": [a for a in formatted if a.status == "open"]},
            "in_progress": {"title": "In Progress", "items": [a for a in formatted if a.status == "in_progress"]},
            "blocked": {"title": "Blocked", "items": [a for a in formatted if a.status == "blocked"]},
            "completed": {"title": "Completed", "items": [a for a in formatted if a.status == "completed"]},
        },
        "counts": counts,
    }


async def _format_action(action: ActionItem, svc: ActionService) -> ActionOut:
    creator_name = await get_user_name(action.created_by, svc.db)
    assignee_name = await get_user_name(action.assignee_id, svc.db) if action.assignee_id else None
    return ActionOut(
        id=action.id, workspace_id=action.workspace_id,
        title=action.title, description=action.description,
        context_type=action.context_type.value if action.context_type else None,
        context_id=action.context_id,
        assignee_id=action.assignee_id, assignee_name=assignee_name,
        due_date=action.due_date, priority=action.priority.value,
        status=action.status.value, progress=action.progress,
        dependencies=action.dependencies, is_recurring=action.is_recurring,
        recurrence_rule=action.recurrence_rule, business_context=action.business_context,
        completed_at=action.completed_at, created_by=action.created_by,
        creator_name=creator_name, created_at=action.created_at, updated_at=action.updated_at,
    )


# ═══════════════════════════════════════════
# APPROVAL ENDPOINTS
# ═══════════════════════════════════════════

@router.post("/approval-workflows", status_code=201)
async def create_approval_workflow(
    data: ApprovalWorkflowCreate,
    current_user: User = Depends(get_current_user),
    svc: ApprovalService = Depends(get_approval_service),
):
    workflow = await svc.create_workflow(data, current_user.id)
    return ApprovalWorkflowOut(
        id=workflow.id, workspace_id=workflow.workspace_id,
        name=workflow.name, description=workflow.description,
        context_type=workflow.context_type.value if workflow.context_type else None,
        is_active=workflow.is_active, created_by=workflow.created_by,
        created_at=workflow.created_at, updated_at=workflow.updated_at,
    )


@router.get("/approval-workflows")
async def list_approval_workflows(
    workspace_id: int = Query(...),
    is_active: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    svc: ApprovalService = Depends(get_approval_service),
    pagination: tuple = Depends(pagination_params),
):
    page, page_size = pagination
    workflows, total = await svc.list_workflows(workspace_id, is_active=is_active, page=page, page_size=page_size)
    items = []
    for w in workflows:
        steps = await svc.get_steps(w.id)
        items.append(ApprovalWorkflowOut(
            id=w.id, workspace_id=w.workspace_id,
            name=w.name, description=w.description,
            context_type=w.context_type.value if w.context_type else None,
            is_active=w.is_active, created_by=w.created_by,
            steps=[{"id": s.id, "step_order": s.step_order, "name": s.name,
                    "approver_user_id": s.approver_user_id, "approver_role": s.approver_role} for s in steps],
            created_at=w.created_at, updated_at=w.updated_at,
        ))
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("/approval-workflows/{workflow_id}/steps")
async def add_approval_step(
    workflow_id: int,
    data: ApprovalWorkflowStepCreate,
    current_user: User = Depends(get_current_user),
    svc: ApprovalService = Depends(get_approval_service),
):
    step = await svc.add_step(workflow_id, data)
    if not step:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {"id": step.id, "workflow_id": step.workflow_id, "step_order": step.step_order,
            "name": step.name, "approver_user_id": step.approver_user_id,
            "approver_role": step.approver_role, "required_count": step.required_count,
            "timeout_hours": step.timeout_hours}


@router.post("/approval-requests", status_code=201)
async def submit_for_approval(
    data: ApprovalSubmit,
    current_user: User = Depends(get_current_user),
    svc: ApprovalService = Depends(get_approval_service),
):
    instance = await svc.submit_for_approval(data, current_user.id)
    if not instance:
        raise HTTPException(status_code=400, detail="Could not submit for approval")
    submitter_name = await get_user_name(instance.submitted_by, svc.db)
    return ApprovalInstanceOut(
        id=instance.id, workflow_id=instance.workflow_id,
        context_type=instance.context_type.value if instance.context_type else None,
        context_id=instance.context_id,
        status=instance.status.value, submitted_by=instance.submitted_by,
        submitter_name=submitter_name, submitted_at=instance.submitted_at,
        completed_at=instance.completed_at,
    )


@router.get("/approval-requests")
async def list_approval_requests(
    workflow_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    svc: ApprovalService = Depends(get_approval_service),
    pagination: tuple = Depends(pagination_params),
):
    page, page_size = pagination
    instances, total = await svc.list_instances(
        workflow_id=workflow_id, status=status, page=page, page_size=page_size,
    )
    items = []
    for inst in instances:
        submitter_name = await get_user_name(inst.submitted_by, svc.db)
        actions_result = await svc.db.execute(
            select(ApprovalAction).where(ApprovalAction.instance_id == inst.id)
        )
        actions = actions_result.scalars().all()
        items.append(ApprovalInstanceOut(
            id=inst.id, workflow_id=inst.workflow_id,
            context_type=inst.context_type.value if inst.context_type else None,
            context_id=inst.context_id,
            status=inst.status.value, submitted_by=inst.submitted_by,
            submitter_name=submitter_name, submitted_at=inst.submitted_at,
            completed_at=inst.completed_at,
            actions=[{"id": a.id, "step_id": a.step_id, "approver_id": a.approver_id,
                      "action": a.action.value, "comments": a.comments, "acted_at": a.acted_at}
                     for a in actions],
        ))
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("/approval-requests/{instance_id}/action")
async def process_approval_action(
    instance_id: int,
    data: ApprovalActionCreate,
    current_user: User = Depends(get_current_user),
    svc: ApprovalService = Depends(get_approval_service),
):
    instance = await svc.process_action(instance_id, data, current_user.id)
    if not instance:
        raise HTTPException(status_code=400, detail="Could not process approval action")
    submitter_name = await get_user_name(instance.submitted_by, svc.db)
    return ApprovalInstanceOut(
        id=instance.id, workflow_id=instance.workflow_id,
        context_type=instance.context_type.value if instance.context_type else None,
        context_id=instance.context_id,
        status=instance.status.value, submitted_by=instance.submitted_by,
        submitter_name=submitter_name, submitted_at=instance.submitted_at,
        completed_at=instance.completed_at,
    )


# ═══════════════════════════════════════════
# MEETING ENDPOINTS
# ═══════════════════════════════════════════

@router.post("/meeting-packs", status_code=201)
async def generate_meeting_pack(
    data: MeetingPackGenerate,
    current_user: User = Depends(get_current_user),
    svc: MeetingService = Depends(get_meeting_service),
):
    pack = await svc.generate_meeting_pack(data, current_user.id)
    if not pack:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return MeetingPackOut(
        id=pack.id, workspace_id=pack.workspace_id, title=pack.title,
        generated_for_date=pack.generated_for_date, content=pack.content,
        exported_formats=pack.exported_formats, created_by=pack.created_by,
        created_at=pack.created_at,
    )


@router.get("/meeting-packs")
async def list_meeting_packs(
    workspace_id: int = Query(...),
    current_user: User = Depends(get_current_user),
    svc: MeetingService = Depends(get_meeting_service),
    pagination: tuple = Depends(pagination_params),
):
    page, page_size = pagination
    packs, total = await svc.list_meeting_packs(workspace_id, page=page, page_size=page_size)
    items = [MeetingPackOut(
        id=p.id, workspace_id=p.workspace_id, title=p.title,
        generated_for_date=p.generated_for_date, content=p.content,
        exported_formats=p.exported_formats, created_by=p.created_by,
        created_at=p.created_at,
    ) for p in packs]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/meeting-packs/{pack_id}")
async def get_meeting_pack(
    pack_id: int,
    current_user: User = Depends(get_current_user),
    svc: MeetingService = Depends(get_meeting_service),
):
    pack = await svc.get_meeting_pack(pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail="Meeting pack not found")
    return MeetingPackOut(
        id=pack.id, workspace_id=pack.workspace_id, title=pack.title,
        generated_for_date=pack.generated_for_date, content=pack.content,
        exported_formats=pack.exported_formats, created_by=pack.created_by,
        created_at=pack.created_at,
    )


@router.post("/meeting-summaries", status_code=201)
async def create_meeting_summary(
    data: MeetingSummaryCreate,
    current_user: User = Depends(get_current_user),
    svc: MeetingService = Depends(get_meeting_service),
):
    summary = await svc.create_summary(data, current_user.id)
    creator_name = await get_user_name(summary.created_by, svc.db)
    return MeetingSummaryOut(
        id=summary.id, workspace_id=summary.workspace_id,
        title=summary.title, meeting_date=summary.meeting_date,
        agenda=summary.agenda, ai_generated_agenda=summary.ai_generated_agenda,
        discussion_summary=summary.discussion_summary,
        decisions_captured=summary.decisions_captured,
        action_items_extracted=summary.action_items_extracted,
        unresolved_issues=summary.unresolved_issues,
        follow_up_questions=summary.follow_up_questions,
        ai_generated=summary.ai_generated, is_edited=summary.is_edited,
        created_by=summary.created_by, creator_name=creator_name,
        created_at=summary.created_at, updated_at=summary.updated_at,
    )


@router.get("/meeting-summaries")
async def list_meeting_summaries(
    workspace_id: int = Query(...),
    current_user: User = Depends(get_current_user),
    svc: MeetingService = Depends(get_meeting_service),
    pagination: tuple = Depends(pagination_params),
):
    page, page_size = pagination
    summaries, total = await svc.list_summaries(workspace_id, page=page, page_size=page_size)
    items = []
    for s in summaries:
        creator_name = await get_user_name(s.created_by, svc.db)
        items.append(MeetingSummaryOut(
            id=s.id, workspace_id=s.workspace_id, title=s.title,
            meeting_date=s.meeting_date, agenda=s.agenda,
            ai_generated_agenda=s.ai_generated_agenda,
            discussion_summary=s.discussion_summary,
            decisions_captured=s.decisions_captured,
            action_items_extracted=s.action_items_extracted,
            unresolved_issues=s.unresolved_issues,
            follow_up_questions=s.follow_up_questions,
            ai_generated=s.ai_generated, is_edited=s.is_edited,
            created_by=s.created_by, creator_name=creator_name,
            created_at=s.created_at, updated_at=s.updated_at,
        ))
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.put("/meeting-summaries/{summary_id}")
async def update_meeting_summary(
    summary_id: int,
    data: MeetingSummaryUpdate,
    current_user: User = Depends(get_current_user),
    svc: MeetingService = Depends(get_meeting_service),
):
    summary = await svc.update_summary(summary_id, data)
    if not summary:
        raise HTTPException(status_code=404, detail="Meeting summary not found")
    creator_name = await get_user_name(summary.created_by, svc.db)
    return MeetingSummaryOut(
        id=summary.id, workspace_id=summary.workspace_id, title=summary.title,
        meeting_date=summary.meeting_date, agenda=summary.agenda,
        ai_generated_agenda=summary.ai_generated_agenda,
        discussion_summary=summary.discussion_summary,
        decisions_captured=summary.decisions_captured,
        action_items_extracted=summary.action_items_extracted,
        unresolved_issues=summary.unresolved_issues,
        follow_up_questions=summary.follow_up_questions,
        ai_generated=summary.ai_generated, is_edited=summary.is_edited,
        created_by=summary.created_by, creator_name=creator_name,
        created_at=summary.created_at, updated_at=summary.updated_at,
    )


# ═══════════════════════════════════════════
# AI ASSISTANT ENDPOINTS
# ═══════════════════════════════════════════

@router.post("/ai-assistant/agenda", response_model=AIAssistantAgendaOut)
async def generate_agenda(
    data: AIAssistantAgendaRequest,
    current_user: User = Depends(get_current_user),
    svc: AIAssistantService = Depends(get_ai_assistant_service),
):
    return await svc.generate_agenda(data)


@router.post("/ai-assistant/summarize", response_model=AIAssistantSummaryOut)
async def generate_summary(
    data: AIAssistantSummaryRequest,
    current_user: User = Depends(get_current_user),
    svc: AIAssistantService = Depends(get_ai_assistant_service),
):
    return await svc.generate_summary(data)


# ═══════════════════════════════════════════
# KNOWLEDGE ENDPOINTS
# ═══════════════════════════════════════════

@router.post("/knowledge-articles", status_code=201)
async def create_knowledge_article(
    data: KnowledgeArticleCreate,
    current_user: User = Depends(get_current_user),
    svc: KnowledgeService = Depends(get_knowledge_service),
):
    article = await svc.create_article(data, current_user.id)
    creator_name = await get_user_name(article.created_by, svc.db)
    return KnowledgeArticleOut(
        id=article.id, workspace_id=article.workspace_id, title=article.title,
        content=article.content, article_type=article.article_type.value,
        tags=article.tags, related_entities=article.related_entities,
        is_published=article.is_published, version=article.version,
        created_by=article.created_by, creator_name=creator_name,
        created_at=article.created_at, updated_at=article.updated_at,
    )


@router.get("/knowledge-articles", response_model=KnowledgeListOut)
async def list_knowledge_articles(
    workspace_id: int = Query(...),
    search: Optional[str] = Query(None),
    article_type: Optional[str] = Query(None),
    tags: Optional[str] = Query(None),
    is_published: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    svc: KnowledgeService = Depends(get_knowledge_service),
    pagination: tuple = Depends(pagination_params),
):
    page, page_size = pagination
    tag_list = tags.split(",") if tags else None
    articles, total = await svc.list_articles(
        workspace_id, search=search, article_type=article_type,
        tags=tag_list, is_published=is_published, page=page, page_size=page_size,
    )
    items = []
    for a in articles:
        creator_name = await get_user_name(a.created_by, svc.db)
        items.append(KnowledgeArticleOut(
            id=a.id, workspace_id=a.workspace_id, title=a.title, content=a.content,
            article_type=a.article_type.value, tags=a.tags, related_entities=a.related_entities,
            is_published=a.is_published, version=a.version,
            created_by=a.created_by, creator_name=creator_name,
            created_at=a.created_at, updated_at=a.updated_at,
        ))
    return KnowledgeListOut(items=items, total=total, page=page, page_size=page_size)


@router.get("/knowledge-articles/{article_id}")
async def get_knowledge_article(
    article_id: int,
    current_user: User = Depends(get_current_user),
    svc: KnowledgeService = Depends(get_knowledge_service),
):
    article = await svc.get_article(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    creator_name = await get_user_name(article.created_by, svc.db)
    return KnowledgeArticleOut(
        id=article.id, workspace_id=article.workspace_id, title=article.title,
        content=article.content, article_type=article.article_type.value,
        tags=article.tags, related_entities=article.related_entities,
        is_published=article.is_published, version=article.version,
        created_by=article.created_by, creator_name=creator_name,
        created_at=article.created_at, updated_at=article.updated_at,
    )


@router.put("/knowledge-articles/{article_id}")
async def update_knowledge_article(
    article_id: int,
    data: KnowledgeArticleUpdate,
    current_user: User = Depends(get_current_user),
    svc: KnowledgeService = Depends(get_knowledge_service),
):
    article = await svc.update_article(article_id, data, current_user.id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    creator_name = await get_user_name(article.created_by, svc.db)
    return KnowledgeArticleOut(
        id=article.id, workspace_id=article.workspace_id, title=article.title,
        content=article.content, article_type=article.article_type.value,
        tags=article.tags, related_entities=article.related_entities,
        is_published=article.is_published, version=article.version,
        created_by=article.created_by, creator_name=creator_name,
        created_at=article.created_at, updated_at=article.updated_at,
    )


@router.delete("/knowledge-articles/{article_id}")
async def delete_knowledge_article(
    article_id: int,
    current_user: User = Depends(get_current_user),
    svc: KnowledgeService = Depends(get_knowledge_service),
):
    success = await svc.delete_article(article_id)
    if not success:
        raise HTTPException(status_code=404, detail="Article not found")
    return {"message": "Article unpublished"}


@router.post("/knowledge-articles/search")
async def search_knowledge(
    data: KnowledgeSearchRequest,
    current_user: User = Depends(get_current_user),
    svc: KnowledgeService = Depends(get_knowledge_service),
):
    articles = await svc.semantic_search(data)
    items = []
    for a in articles:
        creator_name = await get_user_name(a.created_by, svc.db)
        items.append(KnowledgeArticleOut(
            id=a.id, workspace_id=a.workspace_id, title=a.title, content=a.content,
            article_type=a.article_type.value, tags=a.tags, related_entities=a.related_entities,
            is_published=a.is_published, version=a.version,
            created_by=a.created_by, creator_name=creator_name,
            created_at=a.created_at, updated_at=a.updated_at,
        ))
    return {"items": items, "total": len(items)}


# ═══════════════════════════════════════════
# NOTIFICATION ENDPOINTS
# ═══════════════════════════════════════════

@router.get("/notifications", response_model=NotificationListOut)
async def list_notifications(
    is_read: Optional[bool] = Query(None),
    notification_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    svc: NotificationService = Depends(get_notification_service),
    pagination: tuple = Depends(pagination_params),
):
    page, page_size = pagination
    notifications, total, unread_count = await svc.get_notifications(
        current_user.id, is_read=is_read, notification_type=notification_type,
        page=page, page_size=page_size,
    )
    items = [NotificationOut(
        id=n.id, user_id=n.user_id, notification_type=n.notification_type.value,
        title=n.title, message=n.message,
        context_type=n.context_type.value if n.context_type else None,
        context_id=n.context_id, is_read=n.is_read, read_at=n.read_at,
        created_at=n.created_at,
    ) for n in notifications]
    return NotificationListOut(items=items, total=total, unread_count=unread_count, page=page, page_size=page_size)


@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    svc: NotificationService = Depends(get_notification_service),
):
    success = await svc.mark_as_read(notification_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Marked as read"}


@router.put("/notifications/read-all")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    svc: NotificationService = Depends(get_notification_service),
):
    count = await svc.mark_all_as_read(current_user.id)
    return {"message": f"{count} notifications marked as read", "count": count}


@router.get("/notifications/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    svc: NotificationService = Depends(get_notification_service),
):
    count = await svc.get_unread_count(current_user.id)
    return {"unread_count": count}


@router.get("/notifications/preferences")
async def get_notification_preferences(
    current_user: User = Depends(get_current_user),
    svc: NotificationService = Depends(get_notification_service),
):
    prefs = await svc.get_preferences(current_user.id)
    return [NotificationPreferenceOut(
        id=p.id, user_id=p.user_id, notification_type=p.notification_type.value,
        channel=p.channel.value, enabled=p.enabled,
    ) for p in prefs]


@router.put("/notifications/preferences")
async def update_notification_preference(
    data: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    svc: NotificationService = Depends(get_notification_service),
):
    pref = await svc.update_preference(current_user.id, data)
    return NotificationPreferenceOut(
        id=pref.id, user_id=pref.user_id, notification_type=pref.notification_type.value,
        channel=pref.channel.value, enabled=pref.enabled,
    )


# ═══════════════════════════════════════════
# ANALYTICS ENDPOINTS
# ═══════════════════════════════════════════

@router.get("/analytics/dashboard", response_model=CollaborationAnalyticsDashboard)
async def get_collaboration_analytics(
    workspace_id: int = Query(...),
    current_user: User = Depends(get_current_user),
    svc: AnalyticsService = Depends(get_analytics_service),
):
    return await svc.compute_dashboard(workspace_id)


@router.get("/analytics/metrics")
async def get_collaboration_metrics(
    workspace_id: Optional[int] = Query(None),
    metric_name: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    svc: AnalyticsService = Depends(get_analytics_service),
    pagination: tuple = Depends(pagination_params),
):
    page, page_size = pagination
    query = CollaborationAnalyticsQuery(
        workspace_id=workspace_id,
        metric_name=metric_name,
        start_date=datetime.fromisoformat(start_date) if start_date else None,
        end_date=datetime.fromisoformat(end_date) if end_date else None,
    )
    metrics, total = await svc.get_metrics(query, page=page, page_size=page_size)
    items = [CollaborationMetricOut(
        id=m.id, workspace_id=m.workspace_id, metric_name=m.metric_name,
        metric_value=m.metric_value, dimension=m.dimension, recorded_at=m.recorded_at,
    ) for m in metrics]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


# ═══════════════════════════════════════════
# IMPACT TRACKING ENDPOINTS
# ═══════════════════════════════════════════

@router.post("/decision-impacts", status_code=201)
async def create_decision_impact(
    data: DecisionImpactCreate,
    current_user: User = Depends(get_current_user),
    svc: ImpactService = Depends(get_impact_service),
):
    impact = await svc.create_impact(data)
    if not impact:
        raise HTTPException(status_code=404, detail="Decision not found")
    return DecisionImpactOut(
        id=impact.id, decision_id=impact.decision_id,
        planned_result=impact.planned_result, actual_result=impact.actual_result,
        kpi_changes=impact.kpi_changes, financial_impact=impact.financial_impact,
        timeline=impact.timeline, lessons_learned=impact.lessons_learned,
        reviewed_at=impact.reviewed_at, reviewed_by=impact.reviewed_by,
        created_at=impact.created_at, updated_at=impact.updated_at,
    )


@router.get("/decision-impacts/{decision_id}")
async def get_decision_impact(
    decision_id: int,
    current_user: User = Depends(get_current_user),
    svc: ImpactService = Depends(get_impact_service),
):
    impact = await svc.get_impact(decision_id)
    if not impact:
        raise HTTPException(status_code=404, detail="Impact record not found")
    return DecisionImpactOut(
        id=impact.id, decision_id=impact.decision_id,
        planned_result=impact.planned_result, actual_result=impact.actual_result,
        kpi_changes=impact.kpi_changes, financial_impact=impact.financial_impact,
        timeline=impact.timeline, lessons_learned=impact.lessons_learned,
        reviewed_at=impact.reviewed_at, reviewed_by=impact.reviewed_by,
        created_at=impact.created_at, updated_at=impact.updated_at,
    )


@router.put("/decision-impacts/{decision_id}")
async def update_decision_impact(
    decision_id: int,
    data: DecisionImpactUpdate,
    current_user: User = Depends(get_current_user),
    svc: ImpactService = Depends(get_impact_service),
):
    impact = await svc.update_impact(decision_id, data, current_user.id)
    if not impact:
        raise HTTPException(status_code=404, detail="Impact record not found")
    return DecisionImpactOut(
        id=impact.id, decision_id=impact.decision_id,
        planned_result=impact.planned_result, actual_result=impact.actual_result,
        kpi_changes=impact.kpi_changes, financial_impact=impact.financial_impact,
        timeline=impact.timeline, lessons_learned=impact.lessons_learned,
        reviewed_at=impact.reviewed_at, reviewed_by=impact.reviewed_by,
        created_at=impact.created_at, updated_at=impact.updated_at,
    )


# ═══════════════════════════════════════════
# TIMELINE ENDPOINT
# ═══════════════════════════════════════════

@router.get("/timeline", response_model=TimelineOut)
async def get_timeline(
    workspace_id: int = Query(...),
    event_type: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    pagination: tuple = Depends(pagination_params),
):
    page, page_size = pagination
    events = []

    # Get decision history events
    decisions_query = select(DecisionHistory)
    if start_date:
        decisions_query = decisions_query.where(DecisionHistory.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        decisions_query = decisions_query.where(DecisionHistory.created_at <= datetime.fromisoformat(end_date))
    decisions_query = decisions_query.order_by(DecisionHistory.created_at.desc()).limit(page_size)
    result = await db.execute(decisions_query)
    decision_events = result.scalars().all()
    for h in decision_events:
        changer_name = await get_user_name(h.changed_by, db)
        events.append(TimelineEvent(
            event_type="decision_update",
            description=f"Decision field '{h.field_changed}' changed: {h.old_value or 'empty'} → {h.new_value or 'empty'}",
            user_name=changer_name,
            context_type="decision",
            context_id=h.decision_id,
            created_at=h.created_at,
        ))

    # Get recent completed actions
    actions_query = select(ActionItem).where(
        ActionItem.workspace_id == workspace_id,
        ActionItem.status == ActionStatus.completed,
    )
    if start_date:
        actions_query = actions_query.where(ActionItem.completed_at >= datetime.fromisoformat(start_date))
    if end_date:
        actions_query = actions_query.where(ActionItem.completed_at <= datetime.fromisoformat(end_date))
    actions_query = actions_query.order_by(ActionItem.completed_at.desc()).limit(page_size)
    result = await db.execute(actions_query)
    completed_actions = result.scalars().all()
    for a in completed_actions:
        user_name = await get_user_name(a.created_by, db)
        events.append(TimelineEvent(
            event_type="action_completed",
            description=f"Action completed: {a.title}",
            user_name=user_name,
            context_type="action",
            context_id=a.id,
            created_at=a.completed_at or a.updated_at,
        ))

    # Sort all events by timestamp descending
    events.sort(key=lambda e: e.created_at, reverse=True)
    total = len(events)
    paginated_events = events[(page - 1) * page_size: page * page_size]

    return TimelineOut(events=paginated_events, total=total, page=page, page_size=page_size)