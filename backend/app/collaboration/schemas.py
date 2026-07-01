from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ── Workspace Schemas ──


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = Field(default="", max_length=1000)
    workspace_type: str = Field(default="team")


class WorkspaceUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    workspace_type: Optional[str] = None


class WorkspaceMemberAdd(BaseModel):
    user_id: int
    role: str = Field(default="member")


class WorkspaceMemberUpdate(BaseModel):
    role: str


class WorkspaceMemberOut(BaseModel):
    id: int
    workspace_id: int
    user_id: int
    role: str
    joined_at: datetime

    model_config = {"from_attributes": True}


class WorkspaceOut(BaseModel):
    id: int
    name: str
    description: str
    workspace_type: str
    owner_id: int
    is_archived: bool
    member_count: int = 0
    discussion_count: int = 0
    decision_count: int = 0
    action_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WorkspaceListOut(BaseModel):
    items: list[WorkspaceOut]
    total: int
    page: int
    page_size: int


# ── Discussion & Comment Schemas ──


class DiscussionCreate(BaseModel):
    workspace_id: int
    title: str = Field(min_length=1, max_length=500)
    context_type: Optional[str] = None
    context_id: Optional[int] = None


class DiscussionUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=500)
    is_pinned: Optional[bool] = None
    is_archived: Optional[bool] = None


class DiscussionOut(BaseModel):
    id: int
    workspace_id: int
    title: str
    context_type: Optional[str]
    context_id: Optional[int]
    is_pinned: bool
    is_archived: bool
    comment_count: int
    created_by: int
    creator_name: str = ""
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DiscussionListOut(BaseModel):
    items: list[DiscussionOut]
    total: int
    page: int
    page_size: int


class CommentCreate(BaseModel):
    discussion_id: int
    parent_id: Optional[int] = None
    content: str = Field(min_length=1)
    content_rich_text: Optional[str] = None
    mentions: Optional[list[int]] = None
    attachments: Optional[list[dict]] = None


class CommentUpdate(BaseModel):
    content: str = Field(min_length=1)
    content_rich_text: Optional[str] = None


class CommentOut(BaseModel):
    id: int
    discussion_id: int
    parent_id: Optional[int]
    content: str
    content_rich_text: Optional[str]
    mentions: Optional[list[int]]
    attachments: Optional[list[dict]]
    reactions: Optional[dict]
    is_deleted: bool
    created_by: int
    creator_name: str = ""
    created_at: datetime
    updated_at: datetime
    reply_count: int = 0

    model_config = {"from_attributes": True}


class ReactionToggle(BaseModel):
    reaction: str = Field(min_length=1, max_length=100)


# ── Decision Schemas ──


class DecisionCreate(BaseModel):
    workspace_id: int
    title: str = Field(min_length=1, max_length=500)
    description: str = Field(default="")
    context_type: Optional[str] = None
    context_id: Optional[int] = None
    owner_id: int
    priority: str = Field(default="medium")
    business_rationale: str = Field(default="")
    expected_outcome: str = Field(default="")
    due_date: Optional[datetime] = None


class DecisionUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=500)
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    business_rationale: Optional[str] = None
    expected_outcome: Optional[str] = None
    actual_outcome: Optional[str] = None
    due_date: Optional[datetime] = None


class DecisionParticipantAdd(BaseModel):
    user_id: int
    role: str = Field(default="participant")


class DecisionHistoryOut(BaseModel):
    id: int
    decision_id: int
    field_changed: str
    old_value: Optional[str]
    new_value: Optional[str]
    changed_by: int
    changer_name: str = ""
    created_at: datetime

    model_config = {"from_attributes": True}


class DecisionOut(BaseModel):
    id: int
    workspace_id: int
    title: str
    description: str
    context_type: Optional[str]
    context_id: Optional[int]
    owner_id: int
    owner_name: str = ""
    priority: str
    status: str
    business_rationale: str
    expected_outcome: str
    actual_outcome: Optional[str]
    due_date: Optional[datetime]
    completed_at: Optional[datetime]
    created_by: int
    creator_name: str = ""
    participant_count: int = 0
    history_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DecisionListOut(BaseModel):
    items: list[DecisionOut]
    total: int
    page: int
    page_size: int


# ── Action Item Schemas ──


class ActionCreate(BaseModel):
    workspace_id: int
    title: str = Field(min_length=1, max_length=500)
    description: str = Field(default="")
    context_type: Optional[str] = None
    context_id: Optional[int] = None
    assignee_id: Optional[int] = None
    due_date: Optional[datetime] = None
    priority: str = Field(default="medium")
    dependencies: Optional[list[int]] = None
    is_recurring: bool = False
    recurrence_rule: Optional[str] = None
    business_context: Optional[dict] = None


class ActionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assignee_id: Optional[int] = None
    due_date: Optional[datetime] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    progress: Optional[int] = Field(default=None, ge=0, le=100)
    dependencies: Optional[list[int]] = None


class ActionOut(BaseModel):
    id: int
    workspace_id: int
    title: str
    description: str
    context_type: Optional[str]
    context_id: Optional[int]
    assignee_id: Optional[int]
    assignee_name: Optional[str] = ""
    due_date: Optional[datetime]
    priority: str
    status: str
    progress: int
    dependencies: Optional[list[int]]
    is_recurring: bool
    recurrence_rule: Optional[str]
    business_context: Optional[dict]
    completed_at: Optional[datetime]
    created_by: int
    creator_name: str = ""
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ActionListOut(BaseModel):
    items: list[ActionOut]
    total: int
    page: int
    page_size: int


# ── Approval Schemas ──


class ApprovalWorkflowCreate(BaseModel):
    workspace_id: int
    name: str = Field(min_length=1, max_length=255)
    description: str = Field(default="")
    context_type: Optional[str] = None


class ApprovalWorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ApprovalWorkflowStepCreate(BaseModel):
    step_order: int
    name: str = Field(default="")
    approver_user_id: Optional[int] = None
    approver_role: Optional[str] = None
    required_count: int = 1
    timeout_hours: Optional[int] = None


class ApprovalWorkflowOut(BaseModel):
    id: int
    workspace_id: int
    name: str
    description: str
    context_type: Optional[str]
    is_active: bool
    created_by: int
    steps: list[dict] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ApprovalSubmit(BaseModel):
    workflow_id: int
    context_type: Optional[str] = None
    context_id: Optional[int] = None


class ApprovalActionCreate(BaseModel):
    action: str = Field(pattern="^(approved|rejected|request_changes)$")
    comments: str = Field(default="")


class ApprovalInstanceOut(BaseModel):
    id: int
    workflow_id: int
    context_type: Optional[str]
    context_id: Optional[int]
    status: str
    submitted_by: int
    submitter_name: str = ""
    submitted_at: datetime
    completed_at: Optional[datetime]
    actions: list[dict] = []

    model_config = {"from_attributes": True}


# ── Meeting Schemas ──


class MeetingSummaryCreate(BaseModel):
    workspace_id: int
    title: str = Field(min_length=1, max_length=500)
    meeting_date: Optional[datetime] = None
    agenda: Optional[list[dict]] = None
    discussion_summary: Optional[str] = None
    decisions_captured: Optional[list[dict]] = None
    action_items_extracted: Optional[list[dict]] = None
    unresolved_issues: Optional[list[str]] = None


class MeetingSummaryUpdate(BaseModel):
    title: Optional[str] = None
    discussion_summary: Optional[str] = None
    decisions_captured: Optional[list[dict]] = None
    action_items_extracted: Optional[list[dict]] = None
    unresolved_issues: Optional[list[str]] = None
    follow_up_questions: Optional[list[str]] = None
    is_edited: bool = True


class MeetingSummaryOut(BaseModel):
    id: int
    workspace_id: int
    title: str
    meeting_date: datetime
    agenda: Optional[list[dict]]
    ai_generated_agenda: Optional[list[dict]]
    discussion_summary: Optional[str]
    decisions_captured: Optional[list[dict]]
    action_items_extracted: Optional[list[dict]]
    unresolved_issues: Optional[list[str]]
    follow_up_questions: Optional[list[str]]
    ai_generated: bool
    is_edited: bool
    created_by: int
    creator_name: str = ""
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MeetingPackGenerate(BaseModel):
    workspace_id: int
    title: str = Field(default="Executive Briefing Pack")
    generated_for_date: Optional[datetime] = None


class MeetingPackOut(BaseModel):
    id: int
    workspace_id: int
    title: str
    generated_for_date: datetime
    content: dict
    exported_formats: Optional[list[str]]
    created_by: int
    created_at: datetime

    model_config = {"from_attributes": True}


class AIAssistantAgendaRequest(BaseModel):
    workspace_id: int
    context: str = Field(default="")
    meeting_title: str = Field(default="")


class AIAssistantSummaryRequest(BaseModel):
    workspace_id: int
    transcript: str = Field(min_length=1)
    meeting_title: str = Field(default="")


class AIAssistantAgendaOut(BaseModel):
    agenda_items: list[dict]
    suggested_duration: Optional[int] = None
    focus_areas: list[str] = []


class AIAssistantSummaryOut(BaseModel):
    summary: str
    decisions_captured: list[dict]
    action_items: list[dict]
    unresolved_issues: list[str]
    follow_up_questions: list[str]


# ── Knowledge Article Schemas ──


class KnowledgeArticleCreate(BaseModel):
    workspace_id: int
    title: str = Field(min_length=1, max_length=500)
    content: str = Field(min_length=1)
    article_type: str = Field(default="best_practice")
    tags: Optional[list[str]] = None
    related_entities: Optional[list[dict]] = None


class KnowledgeArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    article_type: Optional[str] = None
    tags: Optional[list[str]] = None
    related_entities: Optional[list[dict]] = None
    is_published: Optional[bool] = None


class KnowledgeArticleOut(BaseModel):
    id: int
    workspace_id: int
    title: str
    content: str
    article_type: str
    tags: Optional[list[str]]
    related_entities: Optional[list[dict]]
    is_published: bool
    version: int
    created_by: int
    creator_name: str = ""
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    workspace_id: Optional[int] = None
    article_type: Optional[str] = None
    tags: Optional[list[str]] = None


class KnowledgeListOut(BaseModel):
    items: list[KnowledgeArticleOut]
    total: int
    page: int
    page_size: int


# ── Notification Schemas ──


class NotificationOut(BaseModel):
    id: int
    user_id: int
    notification_type: str
    title: str
    message: str
    context_type: Optional[str]
    context_id: Optional[int]
    is_read: bool
    read_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListOut(BaseModel):
    items: list[NotificationOut]
    total: int
    unread_count: int
    page: int
    page_size: int


class NotificationPreferenceUpdate(BaseModel):
    notification_type: str
    channel: str = Field(default="in_app")
    enabled: bool


class NotificationPreferenceOut(BaseModel):
    id: int
    user_id: int
    notification_type: str
    channel: str
    enabled: bool

    model_config = {"from_attributes": True}


# ── Collaboration Analytics Schemas ──


class CollaborationAnalyticsQuery(BaseModel):
    workspace_id: Optional[int] = None
    metric_name: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class CollaborationMetricOut(BaseModel):
    id: int
    workspace_id: int
    metric_name: str
    metric_value: float
    dimension: Optional[str]
    recorded_at: datetime

    model_config = {"from_attributes": True}


class CollaborationAnalyticsDashboard(BaseModel):
    avg_decision_time_hours: float = 0
    approval_cycle_time_hours: float = 0
    action_completion_rate: float = 0
    team_participation_count: int = 0
    open_decisions: int = 0
    closed_decisions: int = 0
    total_decisions: int = 0
    knowledge_articles_count: int = 0
    meeting_count: int = 0
    metrics_by_workspace: list[dict] = []


# ── Impact Tracking Schemas ──


class DecisionImpactCreate(BaseModel):
    decision_id: int
    planned_result: str = Field(default="")
    actual_result: Optional[str] = None
    kpi_changes: Optional[list[dict]] = None
    financial_impact: Optional[dict] = None
    timeline: Optional[list[dict]] = None
    lessons_learned: Optional[str] = None


class DecisionImpactUpdate(BaseModel):
    actual_result: Optional[str] = None
    kpi_changes: Optional[list[dict]] = None
    financial_impact: Optional[dict] = None
    timeline: Optional[list[dict]] = None
    lessons_learned: Optional[str] = None


class DecisionImpactOut(BaseModel):
    id: int
    decision_id: int
    planned_result: str
    actual_result: Optional[str]
    kpi_changes: Optional[list[dict]]
    financial_impact: Optional[dict]
    timeline: Optional[list[dict]]
    lessons_learned: Optional[str]
    reviewed_at: Optional[datetime]
    reviewed_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Timeline Schemas ──


class TimelineEvent(BaseModel):
    event_type: str
    description: str
    user_name: str = ""
    context_type: Optional[str] = None
    context_id: Optional[int] = None
    created_at: datetime


class TimelineOut(BaseModel):
    events: list[TimelineEvent]
    total: int
    page: int
    page_size: int


# ── Error Response ──


class ErrorResponse(BaseModel):
    error: str
    detail: str