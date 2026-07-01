"""
Enterprise Integration Hub - Pydantic Schemas
Request/Response validation and serialization.
"""

from datetime import datetime
from typing import Any, Optional
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, HttpUrl
from pydantic_settings import BaseSettings


# ============================================================================
# Enums (mirroring models)
# ============================================================================

class ConnectorCategory(str, Enum):
    erp = "erp"
    crm = "crm"
    hr = "hr"
    productivity = "productivity"
    project_management = "project_management"
    itsm = "itsm"
    database = "database"
    storage = "storage"
    messaging = "messaging"
    custom = "custom"


class ConnectorType(str, Enum):
    source = "source"
    destination = "destination"
    both = "both"


class AuthType(str, Enum):
    none = "none"
    api_key = "api_key"
    bearer_token = "bearer_token"
    basic_auth = "basic_auth"
    oauth2 = "oauth2"
    oauth1 = "oauth1"
    certificate = "certificate"
    custom = "custom"


class IntegrationStatus(str, Enum):
    draft = "draft"
    active = "active"
    paused = "paused"
    error = "error"
    deprecated = "deprecated"


class SyncJobStatus(str, Enum):
    pending = "pending"
    running = "running"
    success = "success"
    failed = "failed"
    cancelled = "cancelled"
    retrying = "retrying"


class SyncMode(str, Enum):
    manual = "manual"
    scheduled = "scheduled"
    event_driven = "event_driven"
    incremental = "incremental"
    full_refresh = "full_refresh"
    bidirectional = "bidirectional"


class ConflictResolution(str, Enum):
    source_wins = "source_wins"
    destination_wins = "destination_wins"
    latest_wins = "latest_wins"
    manual = "manual"
    skip = "skip"


class EventType(str, Enum):
    created = "created"
    updated = "updated"
    deleted = "deleted"
    custom = "custom"


class LogLevel(str, Enum):
    debug = "debug"
    info = "info"
    warning = "warning"
    error = "error"
    critical = "critical"


class TransformationType(str, Enum):
    field_mapping = "field_mapping"
    lookup = "lookup"
    calculated = "calculated"
    validation = "validation"
    normalization = "normalization"
    conversion = "conversion"
    enrichment = "enrichment"


class TemplateStatus(str, Enum):
    draft = "draft"
    published = "published"
    deprecated = "deprecated"


class GovernanceAction(str, Enum):
    created = "created"
    updated = "updated"
    deleted = "deleted"
    deployed = "deployed"
    paused = "paused"
    resumed = "resumed"
    tested = "tested"


# ============================================================================
# Base Schemas
# ============================================================================

class TimestampMixin(BaseModel):
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Connector Schemas
# ============================================================================

class ConnectorCategoryBase(BaseModel):
    name: str
    display_name: str
    description: str = ""
    icon: str = ""
    sort_order: int = 0
    is_active: bool = True


class ConnectorCategoryCreate(ConnectorCategoryBase):
    pass


class ConnectorCategoryUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class ConnectorCategoryResponse(ConnectorCategoryBase, TimestampMixin):
    model_config = ConfigDict(from_attributes=True)
    
    id: int


class ConnectorBase(BaseModel):
    name: str
    display_name: str
    description: str = ""
    category_id: int
    connector_type: ConnectorType
    version: str = "1.0.0"
    icon: str = ""
    documentation_url: str = ""
    
    # Capabilities
    supports_incremental_sync: bool = False
    supports_bidirectional_sync: bool = False
    supports_events: bool = False
    supports_batch_operations: bool = False
    max_batch_size: int = 1000
    
    # Configuration schema
    config_schema: dict = Field(default_factory=dict)
    auth_schema: dict = Field(default_factory=dict)
    
    # Metadata
    tags: list[str] = Field(default_factory=list)
    sdk_version: str = "1.0.0"
    python_class_path: str = ""


class ConnectorCreate(ConnectorBase):
    pass


class ConnectorUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    connector_type: Optional[ConnectorType] = None
    version: Optional[str] = None
    icon: Optional[str] = None
    documentation_url: Optional[str] = None
    supports_incremental_sync: Optional[bool] = None
    supports_bidirectional_sync: Optional[bool] = None
    supports_events: Optional[bool] = None
    supports_batch_operations: Optional[bool] = None
    max_batch_size: Optional[int] = None
    config_schema: Optional[dict] = None
    auth_schema: Optional[dict] = None
    tags: Optional[list[str]] = None
    is_active: Optional[bool] = None


class ConnectorResponse(ConnectorBase, TimestampMixin):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_builtin: bool
    is_active: bool
    download_count: int
    rating: float


class ConnectorVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    connector_id: int
    version_number: str
    release_notes: str
    changelog: dict
    is_current: bool
    created_at: datetime


# ============================================================================
# Connector Configuration Schemas
# ============================================================================

class ConnectorConfigurationBase(BaseModel):
    connector_id: int
    name: str
    description: str = ""
    environment: str = "production"
    config: dict = Field(default_factory=dict)
    auth_type: AuthType
    timeout_seconds: int = 30
    retry_policy: dict = Field(default_factory=lambda: {"max_retries": 3, "backoff_strategy": "exponential"})
    rate_limit: Optional[dict] = None
    tags: list[str] = Field(default_factory=list)


class ConnectorConfigurationCreate(ConnectorConfigurationBase):
    encrypted_credentials: Optional[str] = None
    secrets_reference: Optional[str] = None


class ConnectorConfigurationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    environment: Optional[str] = None
    config: Optional[dict] = None
    auth_type: Optional[AuthType] = None
    encrypted_credentials: Optional[str] = None
    secrets_reference: Optional[str] = None
    timeout_seconds: Optional[int] = None
    retry_policy: Optional[dict] = None
    rate_limit: Optional[dict] = None
    status: Optional[str] = None
    tags: Optional[list[str]] = None


class ConnectorConfigurationResponse(ConnectorConfigurationBase, TimestampMixin):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    owner_id: int
    status: str
    last_health_check: Optional[datetime] = None
    health_status: str
    last_error: Optional[str] = None
    usage_count: int
    last_used_at: Optional[datetime] = None


class ConnectorHealthCheckResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    configuration_id: int
    status: str
    response_time_ms: int
    error_message: Optional[str] = None
    details: dict
    created_at: datetime


# ============================================================================
# Integration Flow Schemas
# ============================================================================

class IntegrationFlowBase(BaseModel):
    name: str
    description: str = ""
    source_configuration_id: int
    destination_configuration_id: int
    sync_mode: SyncMode = SyncMode.manual
    schedule_cron: Optional[str] = None
    conflict_resolution: ConflictResolution = ConflictResolution.source_wins
    batch_size: int = 1000
    max_retries: int = 3
    retry_delay_seconds: int = 60
    timeout_seconds: int = 300
    tags: list[str] = Field(default_factory=list)


class IntegrationFlowCreate(IntegrationFlowBase):
    pass


class IntegrationFlowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    source_configuration_id: Optional[int] = None
    destination_configuration_id: Optional[int] = None
    status: Optional[IntegrationStatus] = None
    sync_mode: Optional[SyncMode] = None
    schedule_cron: Optional[str] = None
    conflict_resolution: Optional[ConflictResolution] = None
    batch_size: Optional[int] = None
    max_retries: Optional[int] = None
    retry_delay_seconds: Optional[int] = None
    timeout_seconds: Optional[int] = None
    tags: Optional[list[str]] = None


class IntegrationFlowResponse(IntegrationFlowBase, TimestampMixin):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    owner_id: int
    status: IntegrationStatus
    total_runs: int
    successful_runs: int
    failed_runs: int
    last_run_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    last_error: Optional[str] = None


# ============================================================================
# Data Mapping Schemas
# ============================================================================

class DataMappingBase(BaseModel):
    integration_flow_id: int
    source_field: str
    source_type: str
    destination_field: str
    destination_type: str
    transformation_type: TransformationType
    transformation_config: dict = Field(default_factory=dict)
    is_required: bool = False
    validation_rules: dict = Field(default_factory=dict)
    default_value: Optional[str] = None
    description: str = ""
    sort_order: int = 0
    is_active: bool = True


class DataMappingCreate(DataMappingBase):
    pass


class DataMappingUpdate(BaseModel):
    source_field: Optional[str] = None
    source_type: Optional[str] = None
    destination_field: Optional[str] = None
    destination_type: Optional[str] = None
    transformation_type: Optional[TransformationType] = None
    transformation_config: Optional[dict] = None
    is_required: Optional[bool] = None
    validation_rules: Optional[dict] = None
    default_value: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class DataMappingResponse(DataMappingBase, TimestampMixin):
    model_config = ConfigDict(from_attributes=True)
    
    id: int


# ============================================================================
# Transformation Schemas
# ============================================================================

class TransformationBase(BaseModel):
    owner_id: int
    integration_flow_id: Optional[int] = None
    name: str
    description: str = ""
    transformation_type: TransformationType
    config: dict = Field(default_factory=dict)
    expression: Optional[str] = None
    version: int = 1
    is_versioned: bool = False
    tags: list[str] = Field(default_factory=list)
    is_shared: bool = False


class TransformationCreate(TransformationBase):
    pass


class TransformationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    transformation_type: Optional[TransformationType] = None
    config: Optional[dict] = None
    expression: Optional[str] = None
    version: Optional[int] = None
    is_versioned: Optional[bool] = None
    tags: Optional[list[str]] = None
    is_shared: Optional[bool] = None
    is_deleted: Optional[bool] = None


class TransformationResponse(TransformationBase, TimestampMixin):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    usage_count: int


# ============================================================================
# Sync Job Schemas
# ============================================================================

class SyncJobBase(BaseModel):
    integration_flow_id: int
    job_type: SyncMode
    scheduled_at: Optional[datetime] = None
    max_retries: int = 3
    triggered_by: Optional[int] = None
    trigger_event: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class SyncJobCreate(SyncJobBase):
    pass


class SyncJobUpdate(BaseModel):
    status: Optional[SyncJobStatus] = None
    scheduled_at: Optional[datetime] = None
    max_retries: Optional[int] = None


class SyncJobResponse(SyncJobBase, TimestampMixin):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    status: SyncJobStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    records_processed: int
    records_succeeded: int
    records_failed: int
    duration_ms: int
    error_message: Optional[str] = None
    error_details: Optional[dict] = None
    retry_count: int


class SyncJobRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    sync_job_id: int
    run_number: int
    status: SyncJobStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: int
    records_processed: int
    records_succeeded: int
    records_failed: int
    records_skipped: int
    records_per_second: Optional[float] = None
    bytes_processed: int
    error_count: int
    warning_count: int
    error_message: Optional[str] = None
    error_details: Optional[dict] = None
    metadata: dict
    created_at: datetime


# ============================================================================
# Event Schemas
# ============================================================================

class EventDefinitionBase(BaseModel):
    integration_flow_id: int
    event_name: str
    event_type: EventType
    description: str = ""
    event_schema: dict = Field(default_factory=dict)
    trigger_condition: Optional[dict] = None
    webhook_url: Optional[HttpUrl] = None
    webhook_secret: Optional[str] = None
    is_active: bool = True
    tags: list[str] = Field(default_factory=list)


class EventDefinitionCreate(EventDefinitionBase):
    pass


class EventDefinitionUpdate(BaseModel):
    event_name: Optional[str] = None
    event_type: Optional[EventType] = None
    description: Optional[str] = None
    event_schema: Optional[dict] = None
    trigger_condition: Optional[dict] = None
    webhook_url: Optional[HttpUrl] = None
    webhook_secret: Optional[str] = None
    is_active: Optional[bool] = None
    tags: Optional[list[str]] = None


class EventDefinitionResponse(EventDefinitionBase, TimestampMixin):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    trigger_count: int
    last_triggered_at: Optional[datetime] = None


# ============================================================================
# Log Schemas
# ============================================================================

class IntegrationLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    integration_flow_id: Optional[int] = None
    sync_job_id: Optional[int] = None
    sync_job_run_id: Optional[int] = None
    log_level: LogLevel
    message: str
    details: dict
    component: str
    operation: str
    record_id: Optional[str] = None
    is_error: bool
    stack_trace: Optional[str] = None
    metadata: dict
    created_at: datetime


# ============================================================================
# Template Schemas
# ============================================================================

class ConnectorTemplateBase(BaseModel):
    connector_id: int
    owner_id: Optional[int] = None
    name: str
    display_name: str
    description: str = ""
    category: ConnectorCategory
    template_config: dict = Field(default_factory=dict)
    data_mappings: list[dict] = Field(default_factory=list)
    transformations: list[dict] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class ConnectorTemplateCreate(ConnectorTemplateBase):
    pass


class ConnectorTemplateUpdate(BaseModel):
    name: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[ConnectorCategory] = None
    template_config: Optional[dict] = None
    data_mappings: Optional[list[dict]] = None
    transformations: Optional[list[dict]] = None
    status: Optional[TemplateStatus] = None
    is_featured: Optional[bool] = None
    tags: Optional[list[str]] = None


class ConnectorTemplateResponse(ConnectorTemplateBase, TimestampMixin):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    usage_count: int
    rating: float
    rating_count: int
    status: TemplateStatus
    is_featured: bool
    is_official: bool


# ============================================================================
# Governance Schemas
# ============================================================================

class IntegrationGovernanceLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    integration_flow_id: int
    user_id: int
    action: GovernanceAction
    description: str
    changes: Optional[dict] = None
    previous_version: Optional[int] = None
    new_version: Optional[int] = None
    requires_approval: bool
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    approval_notes: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: dict
    created_at: datetime


# ============================================================================
# Analytics Schemas
# ============================================================================

class IntegrationAnalyticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    integration_flow_id: int
    date: datetime
    total_records_processed: int
    successful_records: int
    failed_records: int
    bytes_transferred: int
    avg_latency_ms: Optional[float] = None
    min_latency_ms: Optional[int] = None
    max_latency_ms: Optional[int] = None
    avg_throughput_rps: Optional[float] = None
    success_rate: Optional[float] = None
    error_rate: Optional[float] = None
    uptime_percentage: Optional[float] = None
    total_jobs_run: int
    successful_jobs: int
    failed_jobs: int
    avg_job_duration_ms: Optional[float] = None
    api_calls_made: int
    api_errors: int
    metadata: dict
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Dead Letter Queue Schemas
# ============================================================================

class DeadLetterQueueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    integration_flow_id: int
    sync_job_run_id: Optional[int] = None
    payload: dict
    error_message: str
    error_type: str
    stack_trace: Optional[str] = None
    retry_count: int
    max_retries: int
    next_retry_at: Optional[datetime] = None
    status: str
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[int] = None
    resolution_notes: Optional[str] = None
    metadata: dict
    created_at: datetime
    updated_at: datetime


class DeadLetterQueueResolve(BaseModel):
    resolution_notes: str
    action: str = Field(..., pattern="^(retry|discard|resolve)$")  # retry, discard, or resolve


# ============================================================================
# Dashboard/Analytics Schemas
# ============================================================================

class IntegrationHubDashboard(BaseModel):
    """Dashboard summary for Integration Hub."""
    total_connectors: int
    active_integrations: int
    failed_jobs: int
    running_jobs: int
    recent_syncs: int
    api_usage_24h: int
    connector_statistics: dict[str, int]
    system_health: dict[str, Any]


class IntegrationHealthSummary(BaseModel):
    """Health summary for all integrations."""
    total_integrations: int
    healthy: int
    warning: int
    failed: int
    inactive: int
    avg_success_rate: float
    avg_latency_ms: float
    total_errors_24h: int


class ConnectorStatistics(BaseModel):
    """Statistics for a specific connector."""
    connector_id: int
    connector_name: str
    total_configurations: int
    active_configurations: int
    total_flows: int
    active_flows: int
    total_syncs_24h: int
    success_rate: float
    avg_latency_ms: float
    error_count: int


# ============================================================================
# SDK Schemas
# ============================================================================

class ConnectorSDKMetadata(BaseModel):
    """Metadata for the Connector SDK."""
    sdk_version: str
    min_python_version: str
    supported_auth_types: list[AuthType]
    connector_interface_version: str
    documentation_url: str
    example_connectors: list[str]
    capabilities: dict[str, Any]


class ConnectorSDKManifest(BaseModel):
    """Manifest for a connector plugin."""
    name: str
    version: str
    display_name: str
    description: str
    category: ConnectorCategory
    connector_type: ConnectorType
    author: str
    license: str
    python_class_path: str
    config_schema: dict
    auth_schema: dict
    dependencies: list[str]
    capabilities: dict[str, bool]