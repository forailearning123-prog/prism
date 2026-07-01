from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class MonitorFrequencyEnum(str, Enum):
    realtime = "realtime"
    every_minute = "every_minute"
    every_5_minutes = "every_5_minutes"
    every_15_minutes = "every_15_minutes"
    every_hour = "every_hour"
    every_6_hours = "every_6_hours"
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"


class MonitorSeverityEnum(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"
    informational = "informational"


class MonitorStatusEnum(str, Enum):
    active = "active"
    inactive = "inactive"
    archived = "archived"


class RuleTypeEnum(str, Enum):
    threshold = "threshold"
    trend = "trend"
    percentage_change = "percentage_change"
    comparison = "comparison"
    multi_condition = "multi_condition"
    time_based = "time_based"
    composite = "composite"


class RuleOperatorEnum(str, Enum):
    lt = "lt"
    lte = "lte"
    gt = "gt"
    gte = "gte"
    eq = "eq"
    neq = "neq"
    between = "between"
    outside = "outside"


class AlertStatusEnum(str, Enum):
    open = "open"
    acknowledged = "acknowledged"
    resolved = "resolved"
    dismissed = "dismissed"


class WorkflowTriggerTypeEnum(str, Enum):
    alert = "alert"
    schedule = "schedule"
    anomaly = "anomaly"
    sla_breach = "sla_breach"
    webhook = "webhook"


class WorkflowStepTypeEnum(str, Enum):
    send_notification = "send_notification"
    generate_report = "generate_report"
    refresh_dashboard = "refresh_dashboard"
    refresh_semantic_model = "refresh_semantic_model"
    trigger_webhook = "trigger_webhook"
    create_task = "create_task"
    invoke_analyst = "invoke_analyst"
    execute_workflow = "execute_workflow"
    wait = "wait"


class EscalationLevelEnum(str, Enum):
    first = "first"
    second = "second"
    third = "third"
    executive = "executive"


class NotificationChannelTypeEnum(str, Enum):
    in_app = "in_app"
    email = "email"
    slack = "slack"
    teams = "teams"
    webhook = "webhook"


class AnomalyCategoryEnum(str, Enum):
    revenue = "revenue"
    cost = "cost"
    sales = "sales"
    inventory = "inventory"
    workforce = "workforce"
    operational = "operational"
    financial = "financial"


# ── Monitor ──

class RuleDefinition(BaseModel):
    name: str = Field(default="", max_length=255)
    rule_type: RuleTypeEnum = RuleTypeEnum.threshold
    operator: RuleOperatorEnum = RuleOperatorEnum.gt
    threshold_value: Optional[float] = None
    threshold_high: Optional[float] = None
    threshold_low: Optional[float] = None
    percentage: Optional[float] = None
    comparison_monitor_id: Optional[int] = None
    trend_window: Optional[int] = None
    trend_direction: Optional[str] = None
    time_field: Optional[str] = None
    time_value: Optional[int] = None
    time_unit: Optional[str] = None
    condition_logic: Optional[dict] = None
    priority: int = 0


class MonitorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = ""
    semantic_model_id: Optional[int] = None
    kpi_id: Optional[int] = None
    measure_name: str = ""
    frequency: MonitorFrequencyEnum = MonitorFrequencyEnum.daily
    severity: MonitorSeverityEnum = MonitorSeverityEnum.medium
    business_owner: str = ""
    tags: list[str] = Field(default_factory=list)
    template_id: Optional[str] = None
    rules: list[RuleDefinition] = Field(default_factory=list)


class MonitorUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    semantic_model_id: Optional[int] = None
    kpi_id: Optional[int] = None
    measure_name: Optional[str] = None
    frequency: Optional[MonitorFrequencyEnum] = None
    severity: Optional[MonitorSeverityEnum] = None
    business_owner: Optional[str] = None
    tags: Optional[list[str]] = None


class MonitorOut(BaseModel):
    id: int
    name: str
    description: str
    semantic_model_id: Optional[int]
    kpi_id: Optional[int]
    measure_name: str
    frequency: MonitorFrequencyEnum
    severity: MonitorSeverityEnum
    status: MonitorStatusEnum
    owner_id: int
    business_owner: str
    tags: list[str]
    template_id: Optional[str]
    last_evaluated_at: Optional[datetime]
    last_alerted_at: Optional[datetime]
    evaluation_count: int
    alert_count: int
    created_at: datetime
    updated_at: datetime
    rules: list["RuleOut"] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class RuleOut(BaseModel):
    id: int
    monitor_id: int
    name: str
    rule_type: RuleTypeEnum
    operator: RuleOperatorEnum
    threshold_value: Optional[float]
    threshold_high: Optional[float]
    threshold_low: Optional[float]
    percentage: Optional[float]
    comparison_monitor_id: Optional[int]
    trend_window: Optional[int]
    trend_direction: Optional[str]
    time_field: Optional[str]
    time_value: Optional[int]
    time_unit: Optional[str]
    condition_logic: Optional[dict]
    priority: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class MonitorListResponse(BaseModel):
    items: list[MonitorOut]
    total: int
    page: int
    page_size: int


# ── Alert ──

class AlertOut(BaseModel):
    id: int
    monitor_id: int
    rule_id: Optional[int]
    title: str
    message: str
    severity: MonitorSeverityEnum
    status: AlertStatusEnum
    source: str
    kpi_value: Optional[float]
    threshold_value: Optional[float]
    anomaly_score: Optional[float]
    confidence: Optional[float]
    anomaly_category: Optional[AnomalyCategoryEnum]
    possible_causes: list[str]
    suggested_actions: list[str]
    ai_explanation: Optional[str]
    root_cause: Optional[str]
    assigned_to: Optional[int]
    acknowledged_by: Optional[int]
    acknowledged_at: Optional[datetime]
    resolved_by: Optional[int]
    resolved_at: Optional[datetime]
    resolution_notes: str
    escalation_level: Optional[EscalationLevelEnum]
    escalation_count: int
    is_read: bool
    created_at: datetime
    comments: list["AlertCommentOut"] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class AlertCommentCreate(BaseModel):
    content: str = Field(min_length=1)


class AlertCommentOut(BaseModel):
    id: int
    alert_id: int
    user_id: int
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertListResponse(BaseModel):
    items: list[AlertOut]
    total: int
    page: int
    page_size: int


class AlertAcknowledge(BaseModel):
    pass


class AlertResolve(BaseModel):
    resolution_notes: str = ""


class AlertAssign(BaseModel):
    assigned_to: int


# ── Anomaly ──

class AnomalyOut(BaseModel):
    id: int
    monitor_id: Optional[int]
    semantic_model_id: Optional[int]
    category: AnomalyCategoryEnum
    severity: MonitorSeverityEnum
    metric_name: str
    metric_value: float
    expected_value: Optional[float]
    deviation: Optional[float]
    confidence: float
    anomaly_score: float
    possible_causes: list[str]
    suggested_actions: list[str]
    affected_kpis: list[str]
    ai_explanation: Optional[str]
    is_resolved: bool
    detected_at: datetime

    model_config = {"from_attributes": True}


class AnomalyListResponse(BaseModel):
    items: list[AnomalyOut]
    total: int
    page: int
    page_size: int


# ── Workflow ──

class WorkflowStepDefinition(BaseModel):
    name: str = ""
    step_type: WorkflowStepTypeEnum
    order: int = 0
    config: dict = Field(default_factory=dict)
    condition: Optional[dict] = None
    timeout_seconds: int = 300
    is_parallel: bool = False


class WorkflowCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = ""
    trigger_type: WorkflowTriggerTypeEnum = WorkflowTriggerTypeEnum.alert
    trigger_config: dict = Field(default_factory=dict)
    template_id: Optional[str] = None
    steps: list[WorkflowStepDefinition] = Field(default_factory=list)


class WorkflowOut(BaseModel):
    id: int
    name: str
    description: str
    trigger_type: WorkflowTriggerTypeEnum
    trigger_config: dict
    is_active: bool
    owner_id: int
    template_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    steps: list["WorkflowStepOut"] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class WorkflowStepOut(BaseModel):
    id: int
    workflow_id: int
    name: str
    step_type: WorkflowStepTypeEnum
    order: int
    config: dict
    condition: Optional[dict]
    timeout_seconds: int
    is_parallel: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class WorkflowListResponse(BaseModel):
    items: list[WorkflowOut]
    total: int
    page: int
    page_size: int


class WorkflowExecutionOut(BaseModel):
    id: int
    workflow_id: int
    alert_id: Optional[int]
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    result: Optional[dict]
    created_at: datetime

    model_config = {"from_attributes": True}


class WorkflowExecutionListResponse(BaseModel):
    items: list[WorkflowExecutionOut]
    total: int
    page: int
    page_size: int


# ── Notification ──

class NotificationConfigCreate(BaseModel):
    channel: NotificationChannelTypeEnum = NotificationChannelTypeEnum.in_app
    enabled: bool = True
    config: dict = Field(default_factory=dict)
    min_severity: MonitorSeverityEnum = MonitorSeverityEnum.medium
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None


class NotificationConfigOut(BaseModel):
    id: int
    user_id: int
    channel: NotificationChannelTypeEnum
    enabled: bool
    config: dict
    min_severity: MonitorSeverityEnum
    quiet_hours_start: Optional[str]
    quiet_hours_end: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationDeliveryOut(BaseModel):
    id: int
    alert_id: int
    user_id: int
    channel: NotificationChannelTypeEnum
    status: str
    error_message: Optional[str]
    delivered_at: Optional[datetime]
    read_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Escalation ──

class EscalationStepDefinition(BaseModel):
    level_order: int = 0
    level: EscalationLevelEnum = EscalationLevelEnum.first
    notify_user_id: Optional[int] = None
    notify_role: Optional[str] = None
    delay_minutes: int = 15
    notify_channels: list[str] = Field(default_factory=list)
    message_template: str = ""


class EscalationPolicyCreate(BaseModel):
    monitor_id: Optional[int] = None
    name: str = Field(min_length=1, max_length=255)
    steps: list[EscalationStepDefinition] = Field(default_factory=list)


class EscalationPolicyOut(BaseModel):
    id: int
    monitor_id: Optional[int]
    name: str
    is_active: bool
    created_at: datetime
    steps: list["EscalationStepOut"] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class EscalationStepOut(BaseModel):
    id: int
    policy_id: int
    level_order: int
    level: EscalationLevelEnum
    notify_user_id: Optional[int]
    notify_role: Optional[str]
    delay_minutes: int
    notify_channels: list[str]
    message_template: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Scheduled Insight ──

class ScheduledInsightCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = ""
    schedule_cron: str = Field(min_length=1, max_length=100)
    timezone: str = "UTC"
    format: str = "email"
    recipients: list[str] = Field(default_factory=list)
    included_kpis: list[str] = Field(default_factory=list)
    monitor_ids: list[int] = Field(default_factory=list)
    filters: dict = Field(default_factory=dict)


class ScheduledInsightOut(BaseModel):
    id: int
    name: str
    description: str
    owner_id: int
    schedule_cron: str
    timezone: str
    format: str
    recipients: list[str]
    included_kpis: list[str]
    monitor_ids: list[int]
    filters: dict
    is_active: bool
    last_generated_at: Optional[datetime]
    next_run_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class ScheduledInsightListResponse(BaseModel):
    items: list[ScheduledInsightOut]
    total: int
    page: int
    page_size: int


# ── SLA ──

class SLAMetricCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = ""
    target_value: float
    target_unit: str = "hours"
    breach_threshold: Optional[float] = None
    measurement_period: str = "daily"


class SLAMetricOut(BaseModel):
    id: int
    name: str
    description: str
    owner_id: int
    target_value: float
    target_unit: str
    current_value: Optional[float]
    status: str
    breach_threshold: Optional[float]
    measurement_period: str
    last_measured_at: Optional[datetime]
    breaches: int
    trend: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SLAMetricListResponse(BaseModel):
    items: list[SLAMetricOut]
    total: int
    page: int
    page_size: int


# ── Business Health Score ──

class BusinessHealthScoreOut(BaseModel):
    id: int
    overall_score: float
    kpi_performance: float
    forecast_confidence: float
    active_risks: float
    open_alerts: float
    data_quality: float
    operational_efficiency: float
    details: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class BusinessHealthScoreListResponse(BaseModel):
    items: list[BusinessHealthScoreOut]
    total: int
    page: int
    page_size: int


# ── Audit ──

class AuditRecordOut(BaseModel):
    id: int
    entity_type: str
    entity_id: Optional[int]
    action: str
    user_id: Optional[int]
    changes: Optional[dict]
    metadata: Optional[dict]
    ip_address: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditRecordListResponse(BaseModel):
    items: list[AuditRecordOut]
    total: int
    page: int
    page_size: int


# ── Dashboard ──

class MonitorStats(BaseModel):
    total_monitors: int
    active_monitors: int
    total_alerts: int
    open_alerts: int
    critical_alerts: int
    recent_anomalies: int
    health_score: Optional[float]