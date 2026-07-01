from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ── Agent Schemas ──


class AIAgentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    display_name: str = Field(min_length=1, max_length=255)
    description: str = Field(default="", max_length=1000)
    agent_type: str = Field(default="custom")
    personality: Optional[str] = None
    goals: Optional[list[str]] = None
    success_metrics: Optional[list[str]] = None
    allowed_actions: Optional[list[str]] = None
    knowledge_scope: Optional[list[str]] = None
    escalation_rules: Optional[dict] = None
    ai_provider: str = Field(default="openai")
    model_name: str = Field(default="gpt-4")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2000, ge=1, le=100000)
    system_prompt: Optional[str] = None
    permissions: Optional[dict] = None
    schedule_type: Optional[str] = None
    schedule_cron: Optional[str] = None
    schedule_timezone: str = Field(default="UTC")
    assigned_departments: Optional[list[str]] = None


class AIAgentUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    display_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    status: Optional[str] = None
    is_active: Optional[bool] = None
    personality: Optional[str] = None
    goals: Optional[list[str]] = None
    success_metrics: Optional[list[str]] = None
    allowed_actions: Optional[list[str]] = None
    knowledge_scope: Optional[list[str]] = None
    escalation_rules: Optional[dict] = None
    ai_provider: Optional[str] = None
    model_name: Optional[str] = None
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1, le=100000)
    system_prompt: Optional[str] = None
    permissions: Optional[dict] = None
    schedule_type: Optional[str] = None
    schedule_cron: Optional[str] = None
    schedule_timezone: Optional[str] = None
    assigned_departments: Optional[list[str]] = None


class AIAgentOut(BaseModel):
    id: int
    name: str
    display_name: str
    description: str
    agent_type: str
    status: str
    is_active: bool
    version: str
    owner_id: int
    assigned_departments: Optional[list[str]]
    personality: Optional[str]
    goals: Optional[list[str]]
    success_metrics: Optional[list[str]]
    allowed_actions: Optional[list[str]]
    knowledge_scope: Optional[list[str]]
    escalation_rules: Optional[dict]
    ai_provider: str
    model_name: str
    temperature: float
    max_tokens: int
    system_prompt: Optional[str]
    permissions: Optional[dict]
    schedule_type: Optional[str]
    schedule_cron: Optional[str]
    schedule_timezone: str
    last_executed_at: Optional[datetime]
    next_scheduled_at: Optional[datetime]
    tasks_completed: int
    tasks_failed: int
    avg_execution_time_ms: int
    user_rating: Optional[float]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AIAgentListOut(BaseModel):
    items: list[AIAgentOut]
    total: int
    page: int
    page_size: int


# ── Agent Template Schemas ──


class AgentTemplateOut(BaseModel):
    id: int
    name: str
    display_name: str
    description: str
    agent_type: str
    version: str
    is_active: bool
    is_system: bool
    personality: Optional[str]
    goals: Optional[list[str]]
    success_metrics: Optional[list[str]]
    allowed_actions: Optional[list[str]]
    knowledge_scope: Optional[list[str]]
    escalation_rules: Optional[dict]
    system_prompt: Optional[str]
    permissions_template: Optional[dict]
    deployment_count: int
    avg_rating: Optional[float]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AgentTemplateListOut(BaseModel):
    items: list[AgentTemplateOut]
    total: int
    page: int
    page_size: int


# ── Agent Task Schemas ──


class AgentTaskCreate(BaseModel):
    agent_id: int
    title: str = Field(min_length=1, max_length=500)
    description: str = Field(default="")
    task_type: str = Field(min_length=1, max_length=100)
    priority: str = Field(default="medium")
    input_data: Optional[dict] = None
    expected_output: Optional[str] = None
    context: Optional[dict] = None
    dependencies: Optional[list[int]] = None
    scheduled_at: Optional[datetime] = None
    requires_approval: bool = False


class AgentTaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=500)
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    input_data: Optional[dict] = None
    expected_output: Optional[str] = None
    context: Optional[dict] = None
    dependencies: Optional[list[int]] = None
    result: Optional[dict] = None
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None
    requires_approval: Optional[bool] = None


class AgentTaskOut(BaseModel):
    id: int
    agent_id: int
    title: str
    description: str
    task_type: str
    priority: str
    status: str
    input_data: Optional[dict]
    expected_output: Optional[str]
    context: Optional[dict]
    dependencies: Optional[list[int]]
    scheduled_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    result: Optional[dict]
    error_message: Optional[str]
    execution_time_ms: Optional[int]
    requires_approval: bool
    approved_by: Optional[int]
    approved_at: Optional[datetime]
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AgentTaskListOut(BaseModel):
    items: list[AgentTaskOut]
    total: int
    page: int
    page_size: int


# ── Agent Execution Schemas ──


class AgentExecutionOut(BaseModel):
    id: int
    agent_id: int
    task_id: Optional[int]
    execution_id: str
    status: str
    input_data: Optional[dict]
    output_data: Optional[dict]
    error_details: Optional[dict]
    started_at: datetime
    completed_at: Optional[datetime]
    duration_ms: Optional[int]
    model_used: Optional[str]
    tokens_used: Optional[int]
    confidence_score: Optional[float]
    triggered_by: Optional[str]
    triggered_by_user_id: Optional[int]

    model_config = {"from_attributes": True}


# ── Agent Recommendation Schemas ──


class AgentRecommendationOut(BaseModel):
    id: int
    agent_id: int
    recommendation_type: str
    title: str
    description: str
    confidence_score: float
    priority: str
    context_data: Optional[dict]
    related_entities: Optional[list[dict]]
    suggested_actions: Optional[list[dict]]
    requires_approval: bool
    is_viewed: bool
    is_actioned: bool
    viewed_at: Optional[datetime]
    actioned_at: Optional[datetime]
    created_at: datetime
    expires_at: Optional[datetime]

    model_config = {"from_attributes": True}


class AgentRecommendationListOut(BaseModel):
    items: list[AgentRecommendationOut]
    total: int
    page: int
    page_size: int


# ── Agent Collaboration Schemas ──


class AgentCollaborationCreate(BaseModel):
    to_agent_id: int
    subject: str = Field(min_length=1, max_length=500)
    content: str = Field(min_length=1)
    message_type: str = Field(default="request")
    payload: Optional[dict] = None
    response_to_id: Optional[int] = None


class AgentCollaborationOut(BaseModel):
    id: int
    from_agent_id: int
    to_agent_id: int
    message_type: str
    subject: str
    content: str
    payload: Optional[dict]
    response_to_id: Optional[int]
    is_read: bool
    read_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Agent Approval Schemas ──


class AgentApprovalCreate(BaseModel):
    agent_id: int
    task_id: Optional[int] = None
    recommendation_id: Optional[int] = None
    approval_type: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=500)
    description: str = Field(default="")
    expires_at: Optional[datetime] = None


class AgentApprovalOut(BaseModel):
    id: int
    agent_id: int
    task_id: Optional[int]
    recommendation_id: Optional[int]
    approval_type: str
    title: str
    description: str
    status: str
    requested_by: int
    approved_by: Optional[int]
    approval_notes: Optional[str]
    expires_at: Optional[datetime]
    created_at: datetime
    resolved_at: Optional[datetime]

    model_config = {"from_attributes": True}


class AgentApprovalAction(BaseModel):
    action: str = Field(pattern="^(approved|rejected)$")
    notes: Optional[str] = None


# ── Agent Memory Schemas ──


class AgentMemoryCreate(BaseModel):
    agent_id: int
    memory_type: str = Field(default="short_term")
    key: str = Field(min_length=1, max_length=255)
    value: str = Field(min_length=1)
    metadata: Optional[dict] = None
    context: Optional[dict] = None
    expires_at: Optional[datetime] = None


class AgentMemoryUpdate(BaseModel):
    value: Optional[str] = None
    metadata: Optional[dict] = None
    context: Optional[dict] = None
    expires_at: Optional[datetime] = None


class AgentMemoryOut(BaseModel):
    id: int
    agent_id: int
    memory_type: str
    key: str
    value: str
    metadata: Optional[dict]
    context: Optional[dict]
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Agent Performance Schemas ──


class AgentPerformanceOut(BaseModel):
    id: int
    agent_id: int
    metric_name: str
    metric_value: float
    dimension: Optional[str]
    recorded_at: datetime

    model_config = {"from_attributes": True}


class AgentPerformanceDashboard(BaseModel):
    tasks_completed: int = 0
    tasks_failed: int = 0
    success_rate: float = 0.0
    avg_execution_time_ms: int = 0
    avg_confidence_score: float = 0.0
    user_rating: Optional[float] = None
    total_recommendations: int = 0
    recommendations_actioned: int = 0
    recommendation_acceptance_rate: float = 0.0


# ── Agent Activity Schemas ──


class AgentActivityOut(BaseModel):
    id: int
    agent_id: int
    activity_type: str
    title: str
    description: str
    status: str
    metadata: Optional[dict]
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentActivityListOut(BaseModel):
    items: list[AgentActivityOut]
    total: int
    page: int
    page_size: int


# ── Agent Permission Schemas ──


class AgentPermissionCreate(BaseModel):
    agent_id: int
    permission_type: str = Field(min_length=1, max_length=100)
    resource_type: str = Field(min_length=1, max_length=100)
    resource_id: Optional[int] = None
    is_allowed: bool = True
    conditions: Optional[dict] = None


class AgentPermissionOut(BaseModel):
    id: int
    agent_id: int
    permission_type: str
    resource_type: str
    resource_id: Optional[int]
    is_allowed: bool
    conditions: Optional[dict]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Agent Execution Request Schemas ──


class AgentExecuteRequest(BaseModel):
    task_type: str = Field(min_length=1, max_length=100)
    input_data: Optional[dict] = None
    context: Optional[dict] = None
    priority: str = Field(default="medium")


class AgentExecuteResponse(BaseModel):
    execution_id: str
    agent_id: int
    task_id: int
    status: str
    result: Optional[dict] = None
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    confidence_score: Optional[float] = None


# ── Agent Schedule Schemas ──


class AgentScheduleUpdate(BaseModel):
    schedule_type: str = Field(min_length=1, max_length=50)
    schedule_cron: str = Field(min_length=1, max_length=100)
    schedule_timezone: str = Field(default="UTC")


# ── Error Response ──


class ErrorResponse(BaseModel):
    error: str
    detail: str