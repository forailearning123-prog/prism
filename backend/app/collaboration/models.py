import enum
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# ── Enums ──


class WorkspaceType(str, enum.Enum):
    organization = "organization"
    department = "department"
    project = "project"
    team = "team"


class WorkspaceMemberRole(str, enum.Enum):
    admin = "admin"
    moderator = "moderator"
    member = "member"
    viewer = "viewer"


class DiscussionContextType(str, enum.Enum):
    dashboard = "dashboard"
    widget = "widget"
    kpi = "kpi"
    forecast = "forecast"
    alert = "alert"
    report = "report"
    insight = "insight"
    glossary = "glossary"
    decision = "decision"
    action = "action"


class DecisionPriority(str, enum.Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"


class DecisionStatus(str, enum.Enum):
    draft = "draft"
    open = "open"
    in_review = "in_review"
    approved = "approved"
    implemented = "implemented"
    closed = "closed"
    rejected = "rejected"


class DecisionParticipantRole(str, enum.Enum):
    owner = "owner"
    participant = "participant"
    reviewer = "reviewer"
    approver = "approver"


class ActionPriority(str, enum.Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"


class ActionStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    blocked = "blocked"
    completed = "completed"
    cancelled = "cancelled"


class ApprovalStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    escalated = "escalated"
    cancelled = "cancelled"


class ApprovalActionType(str, enum.Enum):
    approved = "approved"
    rejected = "rejected"
    request_changes = "request_changes"


class NotificationType(str, enum.Enum):
    mention = "mention"
    action_assigned = "action_assigned"
    approval_request = "approval_request"
    decision_update = "decision_update"
    comment_reply = "comment_reply"
    due_date_reminder = "due_date_reminder"
    workspace_invite = "workspace_invite"
    approval_status = "approval_status"
    action_completed = "action_completed"


class NotificationChannel(str, enum.Enum):
    in_app = "in_app"
    email = "email"


class KnowledgeArticleType(str, enum.Enum):
    best_practice = "best_practice"
    lesson_learned = "lesson_learned"
    sop = "sop"
    faq = "faq"
    business_definition = "business_definition"
    decision_history = "decision_history"


# ── Workspace Models ──


class Workspace(Base):
    __tablename__ = "workspaces"
    __table_args__ = (
        Index("ix_workspaces_owner_type", "owner_id", "workspace_type"),
        Index("ix_workspaces_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    workspace_type: Mapped[WorkspaceType] = mapped_column(
        Enum(WorkspaceType), default=WorkspaceType.team, index=True
    )
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    owner: Mapped["User"] = relationship()
    members: Mapped[list["WorkspaceMember"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )
    discussions: Mapped[list["Discussion"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )
    decisions: Mapped[list["DecisionRecord"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )
    actions: Mapped[list["ActionItem"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )
    approval_workflows: Mapped[list["ApprovalWorkflow"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )
    meeting_summaries: Mapped[list["MeetingSummary"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )
    meeting_packs: Mapped[list["MeetingPack"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )
    knowledge_articles: Mapped[list["KnowledgeArticle"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )


class WorkspaceMember(Base):
    __tablename__ = "workspace_members"
    __table_args__ = (
        UniqueConstraint("workspace_id", "user_id", name="uq_workspace_member"),
        Index("ix_workspace_members_user", "user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[WorkspaceMemberRole] = mapped_column(
        Enum(WorkspaceMemberRole), default=WorkspaceMemberRole.member
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    workspace: Mapped["Workspace"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship()


# ── Discussion & Comment Models ──


class Discussion(Base):
    __tablename__ = "discussions"
    __table_args__ = (
        Index("ix_discussions_workspace_pinned", "workspace_id", "is_pinned"),
        Index("ix_discussions_context", "context_type", "context_id"),
        Index("ix_discussions_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"), index=True)
    title: Mapped[str] = mapped_column(String(500))
    context_type: Mapped[DiscussionContextType | None] = mapped_column(
        Enum(DiscussionContextType), nullable=True, index=True
    )
    context_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    comment_count: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    workspace: Mapped["Workspace"] = relationship(back_populates="discussions")
    creator: Mapped["User"] = relationship()
    comments: Mapped[list["Comment"]] = relationship(
        back_populates="discussion", cascade="all, delete-orphan"
    )


class Comment(Base):
    __tablename__ = "comments"
    __table_args__ = (
        Index("ix_comments_discussion_created", "discussion_id", "created_at"),
        Index("ix_comments_parent", "parent_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    discussion_id: Mapped[int] = mapped_column(ForeignKey("discussions.id"), index=True)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("comments.id"), nullable=True, index=True
    )
    content: Mapped[str] = mapped_column(Text)
    content_rich_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    mentions: Mapped[list[int] | None] = mapped_column(JSON, nullable=True)
    attachments: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    reactions: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    edit_history: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    discussion: Mapped["Discussion"] = relationship(back_populates="comments")
    parent: Mapped["Comment | None"] = relationship(
        remote_side="Comment.id", backref="replies"
    )
    creator: Mapped["User"] = relationship()


# ── Decision Models ──


class DecisionRecord(Base):
    __tablename__ = "decision_records"
    __table_args__ = (
        Index("ix_decision_records_workspace_status", "workspace_id", "status"),
        Index("ix_decision_records_owner", "owner_id"),
        Index("ix_decision_records_due_date", "due_date"),
        Index("ix_decision_records_context", "context_type", "context_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"), index=True)
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text, default="")
    context_type: Mapped[DiscussionContextType | None] = mapped_column(
        Enum(DiscussionContextType), nullable=True, index=True
    )
    context_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    priority: Mapped[DecisionPriority] = mapped_column(
        Enum(DecisionPriority), default=DecisionPriority.medium, index=True
    )
    status: Mapped[DecisionStatus] = mapped_column(
        Enum(DecisionStatus), default=DecisionStatus.draft, index=True
    )
    business_rationale: Mapped[str] = mapped_column(Text, default="")
    expected_outcome: Mapped[str] = mapped_column(Text, default="")
    actual_outcome: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    workspace: Mapped["Workspace"] = relationship(back_populates="decisions")
    owner: Mapped["User"] = relationship(foreign_keys=[owner_id])
    creator: Mapped["User"] = relationship(foreign_keys=[created_by])
    participants: Mapped[list["DecisionParticipant"]] = relationship(
        back_populates="decision", cascade="all, delete-orphan"
    )
    history: Mapped[list["DecisionHistory"]] = relationship(
        back_populates="decision", cascade="all, delete-orphan"
    )


class DecisionParticipant(Base):
    __tablename__ = "decision_participants"
    __table_args__ = (
        UniqueConstraint("decision_id", "user_id", name="uq_decision_participant"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    decision_id: Mapped[int] = mapped_column(ForeignKey("decision_records.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[DecisionParticipantRole] = mapped_column(
        Enum(DecisionParticipantRole), default=DecisionParticipantRole.participant
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    decision: Mapped["DecisionRecord"] = relationship(back_populates="participants")
    user: Mapped["User"] = relationship()


class DecisionHistory(Base):
    __tablename__ = "decision_history"
    __table_args__ = (
        Index("ix_decision_history_decision_created", "decision_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    decision_id: Mapped[int] = mapped_column(ForeignKey("decision_records.id"), index=True)
    field_changed: Mapped[str] = mapped_column(String(100))
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_by: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

    decision: Mapped["DecisionRecord"] = relationship(back_populates="history")
    changer: Mapped["User"] = relationship()


# ── Action Item Models ──


class ActionItem(Base):
    __tablename__ = "action_items"
    __table_args__ = (
        Index("ix_action_items_workspace_status", "workspace_id", "status"),
        Index("ix_action_items_assignee_status", "assignee_id", "status"),
        Index("ix_action_items_due_date", "due_date"),
        Index("ix_action_items_context", "context_type", "context_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"), index=True)
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text, default="")
    context_type: Mapped[DiscussionContextType | None] = mapped_column(
        Enum(DiscussionContextType), nullable=True, index=True
    )
    context_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    assignee_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    priority: Mapped[ActionPriority] = mapped_column(
        Enum(ActionPriority), default=ActionPriority.medium, index=True
    )
    status: Mapped[ActionStatus] = mapped_column(
        Enum(ActionStatus), default=ActionStatus.open, index=True
    )
    progress: Mapped[int] = mapped_column(Integer, default=0)
    dependencies: Mapped[list[int] | None] = mapped_column(JSON, nullable=True)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    recurrence_rule: Mapped[str | None] = mapped_column(String(255), nullable=True)
    business_context: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    workspace: Mapped["Workspace"] = relationship(back_populates="actions")
    assignee: Mapped["User | None"] = relationship(foreign_keys=[assignee_id])
    creator: Mapped["User"] = relationship(foreign_keys=[created_by])


# ── Approval Workflow Models ──


class ApprovalWorkflow(Base):
    __tablename__ = "approval_workflows"
    __table_args__ = (
        Index("ix_approval_workflows_workspace", "workspace_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    context_type: Mapped[DiscussionContextType | None] = mapped_column(
        Enum(DiscussionContextType), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    workspace: Mapped["Workspace"] = relationship(back_populates="approval_workflows")
    steps: Mapped[list["ApprovalWorkflowStep"]] = relationship(
        back_populates="workflow", cascade="all, delete-orphan", order_by="ApprovalWorkflowStep.step_order"
    )
    instances: Mapped[list["ApprovalInstance"]] = relationship(
        back_populates="workflow", cascade="all, delete-orphan"
    )


class ApprovalWorkflowStep(Base):
    __tablename__ = "approval_workflow_steps"
    __table_args__ = (
        UniqueConstraint("workflow_id", "step_order", name="uq_workflow_step_order"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    workflow_id: Mapped[int] = mapped_column(ForeignKey("approval_workflows.id"), index=True)
    step_order: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(255), default="")
    approver_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    approver_role: Mapped[str | None] = mapped_column(String(100), nullable=True)
    required_count: Mapped[int] = mapped_column(Integer, default=1)
    timeout_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)

    workflow: Mapped["ApprovalWorkflow"] = relationship(back_populates="steps")


class ApprovalInstance(Base):
    __tablename__ = "approval_instances"
    __table_args__ = (
        Index("ix_approval_instances_workflow_status", "workflow_id", "status"),
        Index("ix_approval_instances_context", "context_type", "context_id"),
        Index("ix_approval_instances_submitted_by", "submitted_by"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    workflow_id: Mapped[int] = mapped_column(ForeignKey("approval_workflows.id"), index=True)
    context_type: Mapped[DiscussionContextType | None] = mapped_column(
        Enum(DiscussionContextType), nullable=True
    )
    context_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus), default=ApprovalStatus.pending, index=True
    )
    submitted_by: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    workflow: Mapped["ApprovalWorkflow"] = relationship(back_populates="instances")
    actions: Mapped[list["ApprovalAction"]] = relationship(
        back_populates="instance", cascade="all, delete-orphan"
    )


class ApprovalAction(Base):
    __tablename__ = "approval_actions"
    __table_args__ = (
        Index("ix_approval_actions_instance_step", "instance_id", "step_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    instance_id: Mapped[int] = mapped_column(ForeignKey("approval_instances.id"), index=True)
    step_id: Mapped[int] = mapped_column(ForeignKey("approval_workflow_steps.id"), index=True)
    approver_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[ApprovalActionType] = mapped_column(Enum(ApprovalActionType))
    comments: Mapped[str] = mapped_column(Text, default="")
    acted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    instance: Mapped["ApprovalInstance"] = relationship(back_populates="actions")


# ── Meeting Models ──


class MeetingSummary(Base):
    __tablename__ = "meeting_summaries"
    __table_args__ = (
        Index("ix_meeting_summaries_workspace_date", "workspace_id", "meeting_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"), index=True)
    title: Mapped[str] = mapped_column(String(500))
    meeting_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    agenda: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    ai_generated_agenda: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    discussion_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    decisions_captured: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    action_items_extracted: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    unresolved_issues: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    follow_up_questions: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    workspace: Mapped["Workspace"] = relationship(back_populates="meeting_summaries")


class MeetingPack(Base):
    __tablename__ = "meeting_packs"
    __table_args__ = (
        Index("ix_meeting_packs_workspace_date", "workspace_id", "generated_for_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"), index=True)
    title: Mapped[str] = mapped_column(String(500))
    generated_for_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    content: Mapped[dict] = mapped_column(JSON, default=dict)
    exported_formats: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

    workspace: Mapped["Workspace"] = relationship(back_populates="meeting_packs")


# ── Knowledge Article Models ──


class KnowledgeArticle(Base):
    __tablename__ = "knowledge_articles"
    __table_args__ = (
        Index("ix_knowledge_articles_workspace_type", "workspace_id", "article_type"),
        Index("ix_knowledge_articles_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"), index=True)
    title: Mapped[str] = mapped_column(String(500), index=True)
    content: Mapped[str] = mapped_column(Text)
    article_type: Mapped[KnowledgeArticleType] = mapped_column(
        Enum(KnowledgeArticleType), default=KnowledgeArticleType.best_practice, index=True
    )
    tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    related_entities: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    workspace: Mapped["Workspace"] = relationship(back_populates="knowledge_articles")


# ── Notification Models ──


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_read", "user_id", "is_read"),
        Index("ix_notifications_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    notification_type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType), index=True
    )
    title: Mapped[str] = mapped_column(String(500))
    message: Mapped[str] = mapped_column(Text, default="")
    context_type: Mapped[DiscussionContextType | None] = mapped_column(
        Enum(DiscussionContextType), nullable=True
    )
    context_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"
    __table_args__ = (
        UniqueConstraint("user_id", "notification_type", "channel", name="uq_user_notification_pref"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    notification_type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType), index=True
    )
    channel: Mapped[NotificationChannel] = mapped_column(
        Enum(NotificationChannel), default=NotificationChannel.in_app
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


# ── Collaboration Analytics Models ──


class CollaborationMetric(Base):
    __tablename__ = "collaboration_metrics"
    __table_args__ = (
        Index("ix_collab_metrics_workspace_name", "workspace_id", "metric_name"),
        Index("ix_collab_metrics_recorded_at", "recorded_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"), index=True)
    metric_name: Mapped[str] = mapped_column(String(100), index=True)
    metric_value: Mapped[float] = mapped_column(Float)
    dimension: Mapped[str | None] = mapped_column(String(100), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )


# ── Decision Impact Tracking ──


class DecisionImpact(Base):
    __tablename__ = "decision_impacts"
    __table_args__ = (
        Index("ix_decision_impacts_decision", "decision_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    decision_id: Mapped[int] = mapped_column(
        ForeignKey("decision_records.id"), index=True, unique=True
    )
    planned_result: Mapped[str] = mapped_column(Text, default="")
    actual_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    kpi_changes: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    financial_impact: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    timeline: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    lessons_learned: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    decision: Mapped["DecisionRecord"] = relationship()