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


class AgentStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    paused = "paused"
    error = "error"
    training = "training"


class AgentType(str, enum.Enum):
    cfo = "cfo"
    sales_director = "sales_director"
    hr_business_partner = "hr_business_partner"
    operations_manager = "operations_manager"
    procurement = "procurement"
    customer_success = "customer_success"
    executive_strategy = "executive_strategy"
    supply_chain = "supply_chain"
    risk_compliance = "risk_compliance"
    custom = "custom"


class TaskStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"
    awaiting_approval = "awaiting_approval"


class TaskPriority(str, enum.Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"


class ExecutionStatus(str, enum.Enum):
    started = "started"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"
    timeout = "timeout"
    cancelled = "cancelled"


class ApprovalStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    expired = "expired"


class MemoryType(str, enum.Enum):
    short_term = "short_term"
    long_term = "long_term"
    user_preference = "user_preference"
    business_context = "business_context"
    department_context = "department_context"


class RecommendationType(str, enum.Enum):
    action = "action"
    insight = "insight"
    alert = "alert"
    optimization = "optimization"
    forecast = "forecast"
    anomaly = "anomaly"


class CollaborationMessageType(str, enum.Enum):
    request = "request"
    response = "response"
    broadcast = "broadcast"
    handoff = "handoff"


class AIProvider(str, enum.Enum):
    openai = "openai"
    anthropic = "anthropic"
    azure_openai = "azure_openai"
    google_vertex = "google_vertex"
    custom = "custom"


# ── Agent Models ──


class AIAgent(Base):
    __tablename__ = "ai_agents"
    __table_args__ = (
        Index("ix_ai_agents_owner_status", "owner_id", "status"),
        Index("ix_ai_agents_type_active", "agent_type", "is_active"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    display_name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    agent_type: Mapped[AgentType] = mapped_column(Enum(AgentType), index=True)
    status: Mapped[AgentStatus] = mapped_column(Enum(AgentStatus), default=AgentStatus.inactive, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    version: Mapped[str] = mapped_column(String(50), default="1.0.0")
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    assigned_departments: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    
    # Agent Configuration
    personality: Mapped[str | None] = mapped_column(Text, nullable=True)
    goals: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    success_metrics: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    allowed_actions: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    knowledge_scope: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    escalation_rules: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    # AI Configuration
    ai_provider: Mapped[AIProvider] = mapped_column(Enum(AIProvider), default=AIProvider.openai)
    model_name: Mapped[str] = mapped_column(String(100), default="gpt-4")
    temperature: Mapped[float] = mapped_column(Float, default=0.7)
    max_tokens: Mapped[int] = mapped_column(Integer, default=2000)
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Permissions
    permissions: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    # Scheduling
    schedule_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    schedule_cron: Mapped[str | None] = mapped_column(String(100), nullable=True)
    schedule_timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    last_executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Statistics
    tasks_completed: Mapped[int] = mapped_column(Integer, default=0)
    tasks_failed: Mapped[int] = mapped_column(Integer, default=0)
    avg_execution_time_ms: Mapped[int] = mapped_column(Integer, default=0)
    user_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    owner: Mapped["User"] = relationship()
    tasks: Mapped[list["AgentTask"]] = relationship(back_populates="agent", cascade="all, delete-orphan")
    executions: Mapped[list["AgentExecution"]] = relationship(back_populates="agent", cascade="all, delete-orphan")
    memories: Mapped[list["AgentMemory"]] = relationship(back_populates="agent", cascade="all, delete-orphan")
    recommendations: Mapped[list["AgentRecommendation"]] = relationship(back_populates="agent", cascade="all, delete-orphan")
    collaborations: Mapped[list["AgentCollaboration"]] = relationship(back_populates="agent", cascade="all, delete-orphan")
    approvals: Mapped[list["AgentApproval"]] = relationship(back_populates="agent", cascade="all, delete-orphan")
    performance_metrics: Mapped[list["AgentPerformance"]] = relationship(back_populates="agent", cascade="all, delete-orphan")
    activities: Mapped[list["AgentActivity"]] = relationship(back_populates="agent", cascade="all, delete-orphan")


class AgentTemplate(Base):
    __tablename__ = "agent_templates"
    __table_args__ = (
        Index("ix_agent_templates_type_active", "agent_type", "is_active"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    display_name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    agent_type: Mapped[AgentType] = mapped_column(Enum(AgentType), index=True)
    version: Mapped[str] = mapped_column(String(50), default="1.0.0")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Template Configuration
    personality: Mapped[str | None] = mapped_column(Text, nullable=True)
    goals: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    success_metrics: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    allowed_actions: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    knowledge_scope: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    escalation_rules: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    permissions_template: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    # Usage Statistics
    deployment_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


# ── Agent Memory Models ──


class AgentMemory(Base):
    __tablename__ = "agent_memories"
    __table_args__ = (
        Index("ix_agent_memories_agent_type", "agent_id", "memory_type"),
        Index("ix_agent_memories_expires", "expires_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("ai_agents.id"), index=True)
    memory_type: Mapped[MemoryType] = mapped_column(Enum(MemoryType), index=True)
    key: Mapped[str] = mapped_column(String(255), index=True)
    value: Mapped[str] = mapped_column(Text)
    metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    context: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    agent: Mapped["AIAgent"] = relationship(back_populates="memories")


# ── Agent Task Models ──


class AgentTask(Base):
    __tablename__ = "agent_tasks"
    __table_args__ = (
        Index("ix_agent_tasks_agent_status", "agent_id", "status"),
        Index("ix_agent_tasks_scheduled", "scheduled_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("ai_agents.id"), index=True)
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text, default="")
    task_type: Mapped[str] = mapped_column(String(100), index=True)
    priority: Mapped[TaskPriority] = mapped_column(Enum(TaskPriority), default=TaskPriority.medium, index=True)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.pending, index=True)
    
    # Task Configuration
    input_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    expected_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    context: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    dependencies: Mapped[list[int] | None] = mapped_column(JSON, nullable=True)
    
    # Scheduling
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Results
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Approval
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    agent: Mapped["AIAgent"] = relationship(back_populates="tasks")
    executions: Mapped[list["AgentExecution"]] = relationship(back_populates="task", cascade="all, delete-orphan")


class AgentExecution(Base):
    __tablename__ = "agent_executions"
    __table_args__ = (
        Index("ix_agent_executions_agent_task", "agent_id", "task_id"),
        Index("ix_agent_executions_status", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("ai_agents.id"), index=True)
    task_id: Mapped[int | None] = mapped_column(ForeignKey("agent_tasks.id"), nullable=True, index=True)
    execution_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    status: Mapped[ExecutionStatus] = mapped_column(Enum(ExecutionStatus), default=ExecutionStatus.started, index=True)
    
    # Execution Details
    input_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    output_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    # Timing
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # AI Details
    model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Audit
    triggered_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    triggered_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    agent: Mapped["AIAgent"] = relationship(back_populates="executions")
    task: Mapped["AgentTask | None"] = relationship(back_populates="executions")


# ── Agent Recommendation Models ──


class AgentRecommendation(Base):
    __tablename__ = "agent_recommendations"
    __table_args__ = (
        Index("ix_agent_recommendations_agent_type", "agent_id", "recommendation_type"),
        Index("ix_agent_recommendations_created", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("ai_agents.id"), index=True)
    recommendation_type: Mapped[RecommendationType] = mapped_column(Enum(RecommendationType), index=True)
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text, default="")
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    priority: Mapped[str] = mapped_column(String(50), default="medium")
    
    # Context
    context_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    related_entities: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    
    # Actions
    suggested_actions: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Status
    is_viewed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_actioned: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    viewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actioned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    agent: Mapped["AIAgent"] = relationship(back_populates="recommendations")


# ── Agent Collaboration Models ──


class AgentCollaboration(Base):
    __tablename__ = "agent_collaborations"
    __table_args__ = (
        Index("ix_agent_collaborations_from_to", "from_agent_id", "to_agent_id"),
        Index("ix_agent_collaborations_created", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    from_agent_id: Mapped[int] = mapped_column(ForeignKey("ai_agents.id"), index=True)
    to_agent_id: Mapped[int] = mapped_column(ForeignKey("ai_agents.id"), index=True)
    message_type: Mapped[CollaborationMessageType] = mapped_column(Enum(CollaborationMessageType), index=True)
    subject: Mapped[str] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    response_to_id: Mapped[int | None] = mapped_column(ForeignKey("agent_collaborations.id"), nullable=True, index=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    from_agent: Mapped["AIAgent"] = relationship(foreign_keys=[from_agent_id])
    to_agent: Mapped["AIAgent"] = relationship(foreign_keys=[to_agent_id])


# ── Agent Approval Models ──


class AgentApproval(Base):
    __tablename__ = "agent_approvals"
    __table_args__ = (
        Index("ix_agent_approvals_agent_status", "agent_id", "status"),
        Index("ix_agent_approvals_created", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("ai_agents.id"), index=True)
    task_id: Mapped[int | None] = mapped_column(ForeignKey("agent_tasks.id"), nullable=True, index=True)
    recommendation_id: Mapped[int | None] = mapped_column(ForeignKey("agent_recommendations.id"), nullable=True, index=True)
    approval_type: Mapped[str] = mapped_column(String(100), index=True)
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[ApprovalStatus] = mapped_column(Enum(ApprovalStatus), default=ApprovalStatus.pending, index=True)
    requested_by: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    approval_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    agent: Mapped["AIAgent"] = relationship(back_populates="approvals")


# ── Agent Performance Models ──


class AgentPerformance(Base):
    __tablename__ = "agent_performance"
    __table_args__ = (
        Index("ix_agent_performance_agent_date", "agent_id", "recorded_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("ai_agents.id"), index=True)
    metric_name: Mapped[str] = mapped_column(String(100), index=True)
    metric_value: Mapped[float] = mapped_column(Float)
    dimension: Mapped[str | None] = mapped_column(String(100), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    agent: Mapped["AIAgent"] = relationship(back_populates="performance_metrics")


# ── Agent Activity Models ──


class AgentActivity(Base):
    __tablename__ = "agent_activities"
    __table_args__ = (
        Index("ix_agent_activities_agent_created", "agent_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("ai_agents.id"), index=True)
    activity_type: Mapped[str] = mapped_column(String(100), index=True)
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(50), index=True)
    metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    agent: Mapped["AIAgent"] = relationship(back_populates="activities")


# ── Agent Permission Models ──


class AgentPermission(Base):
    __tablename__ = "agent_permissions"
    __table_args__ = (
        UniqueConstraint("agent_id", "permission_type", "resource_type", "resource_id", name="uq_agent_permission"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("ai_agents.id"), index=True)
    permission_type: Mapped[str] = mapped_column(String(100), index=True)
    resource_type: Mapped[str] = mapped_column(String(100), index=True)
    resource_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    is_allowed: Mapped[bool] = mapped_column(Boolean, default=True)
    conditions: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))