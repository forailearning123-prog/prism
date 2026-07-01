"""
Enterprise Integration Hub - Database Models
Production-ready schema for connectors, integrations, sync jobs, and governance.
"""

import enum
from datetime import datetime, timezone
from typing import Any

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
    Column,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# ============================================================================
# Enums
# ============================================================================

class ConnectorCategory(str, enum.Enum):
    """Categories for organizing connectors in the marketplace."""
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


class ConnectorType(str, enum.Enum):
    """Types of connectors."""
    source = "source"
    destination = "destination"
    both = "both"


class AuthType(str, enum.Enum):
    """Authentication types supported by connectors."""
    none = "none"
    api_key = "api_key"
    bearer_token = "bearer_token"
    basic_auth = "basic_auth"
    oauth2 = "oauth2"
    oauth1 = "oauth1"
    certificate = "certificate"
    custom = "custom"


class IntegrationStatus(str, enum.Enum):
    """Status of integration flows."""
    draft = "draft"
    active = "active"
    paused = "paused"
    error = "error"
    deprecated = "deprecated"


class SyncJobStatus(str, enum.Enum):
    """Status of synchronization jobs."""
    pending = "pending"
    running = "running"
    success = "success"
    failed = "failed"
    cancelled = "cancelled"
    retrying = "retrying"


class SyncMode(str, enum.Enum):
    """Synchronization modes."""
    manual = "manual"
    scheduled = "scheduled"
    event_driven = "event_driven"
    incremental = "incremental"
    full_refresh = "full_refresh"
    bidirectional = "bidirectional"


class ConflictResolution(str, enum.Enum):
    """Strategies for resolving sync conflicts."""
    source_wins = "source_wins"
    destination_wins = "destination_wins"
    latest_wins = "latest_wins"
    manual = "manual"
    skip = "skip"


class EventType(str, enum.Enum):
    """Types of integration events."""
    created = "created"
    updated = "updated"
    deleted = "deleted"
    custom = "custom"


class LogLevel(str, enum.Enum):
    """Log severity levels."""
    debug = "debug"
    info = "info"
    warning = "warning"
    error = "error"
    critical = "critical"


class TransformationType(str, enum.Enum):
    """Types of transformations."""
    field_mapping = "field_mapping"
    lookup = "lookup"
    calculated = "calculated"
    validation = "validation"
    normalization = "normalization"
    conversion = "conversion"
    enrichment = "enrichment"


class TemplateStatus(str, enum.Enum):
    """Status of integration templates."""
    draft = "draft"
    published = "published"
    deprecated = "deprecated"


class GovernanceAction(str, enum.Enum):
    """Types of governance actions."""
    created = "created"
    updated = "updated"
    deleted = "deleted"
    deployed = "deployed"
    paused = "paused"
    resumed = "resumed"
    tested = "tested"


# ============================================================================
# Connector Models
# ============================================================================

class ConnectorCategory(Base):
    """Categories for organizing connectors in the marketplace."""
    __tablename__ = "connector_categories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    icon: Mapped[str] = mapped_column(String(100), default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    connectors: Mapped[list["Connector"]] = relationship(back_populates="category")


class Connector(Base):
    """
    Registry of available connectors in the marketplace.
    Defines metadata, capabilities, and configuration schema for each connector type.
    """
    __tablename__ = "connectors"
    __table_args__ = (
        Index("ix_connectors_category_active", "category_id", "is_active"),
        Index("ix_connectors_name", "name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    category_id: Mapped[int] = mapped_column(ForeignKey("connector_categories.id"), index=True)
    connector_type: Mapped[ConnectorType] = mapped_column(Enum(ConnectorType), index=True)
    version: Mapped[str] = mapped_column(String(50), default="1.0.0")
    icon: Mapped[str] = mapped_column(String(500), default="")
    documentation_url: Mapped[str] = mapped_column(String(500), default="")
    
    # Capabilities
    supports_incremental_sync: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_bidirectional_sync: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_events: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_batch_operations: Mapped[bool] = mapped_column(Boolean, default=False)
    max_batch_size: Mapped[int] = mapped_column(Integer, default=1000)
    
    # Configuration schema (JSON Schema for validation)
    config_schema: Mapped[dict] = mapped_column(JSON, default=dict)
    auth_schema: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Metadata
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    download_count: Mapped[int] = mapped_column(Integer, default=0)
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    
    # SDK metadata
    sdk_version: Mapped[str] = mapped_column(String(50), default="1.0.0")
    python_class_path: Mapped[str] = mapped_column(String(500), default="")
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    category: Mapped["ConnectorCategory"] = relationship(back_populates="connectors")
    configurations: Mapped[list["ConnectorConfiguration"]] = relationship(back_populates="connector", cascade="all, delete-orphan")
    templates: Mapped[list["ConnectorTemplate"]] = relationship(back_populates="connector", cascade="all, delete-orphan")
    versions: Mapped[list["ConnectorVersion"]] = relationship(back_populates="connector", cascade="all, delete-orphan")


class ConnectorVersion(Base):
    """Version history for connectors."""
    __tablename__ = "connector_versions"
    __table_args__ = (
        UniqueConstraint("connector_id", "version_number", name="uq_connector_version"),
        Index("ix_connector_versions_connector_created", "connector_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    connector_id: Mapped[int] = mapped_column(ForeignKey("connectors.id"), index=True)
    version_number: Mapped[str] = mapped_column(String(50))
    release_notes: Mapped[str] = mapped_column(Text, default="")
    changelog: Mapped[dict] = mapped_column(JSON, default=dict)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    connector: Mapped["Connector"] = relationship(back_populates="versions")


class ConnectorConfiguration(Base):
    """
    Instance-specific configuration for a connector.
    Each tenant/user can have multiple configurations of the same connector type.
    """
    __tablename__ = "connector_configurations"
    __table_args__ = (
        Index("ix_connector_configs_connector_owner", "connector_id", "owner_id"),
        Index("ix_connector_configs_status", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    connector_id: Mapped[int] = mapped_column(ForeignKey("connectors.id"), index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    
    # Configuration
    environment: Mapped[str] = mapped_column(String(50), default="production", index=True)  # dev, staging, production
    config: Mapped[dict] = mapped_column(JSON, default=dict)  # Provider-specific configuration
    
    # Authentication (encrypted)
    auth_type: Mapped[AuthType] = mapped_column(Enum(AuthType), index=True)
    encrypted_credentials: Mapped[str | None] = mapped_column(Text, nullable=True)  # Encrypted JSON
    secrets_reference: Mapped[str | None] = mapped_column(String(500), nullable=True)  # Reference to secrets manager
    
    # Connection settings
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=30)
    retry_policy: Mapped[dict] = mapped_column(JSON, default=dict)  # {max_retries, backoff_strategy, etc.}
    rate_limit: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # {requests_per_minute, etc.}
    
    # Health and status
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)  # pending, connected, error, disabled
    last_health_check: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    health_status: Mapped[str] = mapped_column(String(50), default="unknown")  # healthy, warning, failed
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Usage tracking
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    connector: Mapped["Connector"] = relationship(back_populates="configurations")
    integration_flows: Mapped[list["IntegrationFlow"]] = relationship(back_populates="source_configuration")
    destination_flows: Mapped[list["IntegrationFlow"]] = relationship(back_populates="destination_configuration", foreign_keys="IntegrationFlow.destination_configuration_id")
    health_checks: Mapped[list["ConnectorHealthCheck"]] = relationship(back_populates="configuration", cascade="all, delete-orphan")


class ConnectorHealthCheck(Base):
    """Historical health check records for connector configurations."""
    __tablename__ = "connector_health_checks"
    __table_args__ = (
        Index("ix_health_checks_config_created", "configuration_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    configuration_id: Mapped[int] = mapped_column(ForeignKey("connector_configurations.id"), index=True)
    status: Mapped[str] = mapped_column(String(50), index=True)  # healthy, warning, failed
    response_time_ms: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    configuration: Mapped["ConnectorConfiguration"] = relationship(back_populates="health_checks")


# ============================================================================
# Integration Flow Models
# ============================================================================

class IntegrationFlow(Base):
    """
    End-to-end integration definition.
    Defines source, destination, mappings, transformations, and scheduling.
    """
    __tablename__ = "integration_flows"
    __table_args__ = (
        Index("ix_integration_flows_owner_status", "owner_id", "status"),
        Index("ix_integration_flows_created", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    
    # Source and Destination
    source_configuration_id: Mapped[int] = mapped_column(ForeignKey("connector_configurations.id"), index=True)
    destination_configuration_id: Mapped[int] = mapped_column(ForeignKey("connector_configurations.id"), index=True)
    
    # Status and scheduling
    status: Mapped[IntegrationStatus] = mapped_column(Enum(IntegrationStatus), default=IntegrationStatus.draft, index=True)
    sync_mode: Mapped[SyncMode] = mapped_column(Enum(SyncMode), default=SyncMode.manual, index=True)
    schedule_cron: Mapped[str | None] = mapped_column(String(100), nullable=True)  # Cron expression
    conflict_resolution: Mapped[ConflictResolution] = mapped_column(Enum(ConflictResolution), default=ConflictResolution.source_wins)
    
    # Configuration
    batch_size: Mapped[int] = mapped_column(Integer, default=1000)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    retry_delay_seconds: Mapped[int] = mapped_column(Integer, default=60)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=300)
    
    # Statistics
    total_runs: Mapped[int] = mapped_column(Integer, default=0)
    successful_runs: Mapped[int] = mapped_column(Integer, default=0)
    failed_runs: Mapped[int] = mapped_column(Integer, default=0)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Metadata
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    owner: Mapped["User"] = relationship()
    source_configuration: Mapped["ConnectorConfiguration"] = relationship(foreign_keys=[source_configuration_id], back_populates="integration_flows")
    destination_configuration: Mapped["ConnectorConfiguration"] = relationship(foreign_keys=[destination_configuration_id], back_populates="destination_flows")
    data_mappings: Mapped[list["DataMapping"]] = relationship(back_populates="integration_flow", cascade="all, delete-orphan")
    transformations: Mapped[list["Transformation"]] = relationship(back_populates="integration_flow", cascade="all, delete-orphan")
    sync_jobs: Mapped[list["SyncJob"]] = relationship(back_populates="integration_flow", cascade="all, delete-orphan")
    event_definitions: Mapped[list["EventDefinition"]] = relationship(back_populates="integration_flow", cascade="all, delete-orphan")
    analytics: Mapped[list["IntegrationAnalytics"]] = relationship(back_populates="integration_flow", cascade="all, delete-orphan")
    governance_logs: Mapped[list["IntegrationGovernanceLog"]] = relationship(back_populates="integration_flow", cascade="all, delete-orphan")


# ============================================================================
# Data Mapping Models
# ============================================================================

class DataMapping(Base):
    """
    Field-level mapping between source and destination systems.
    Supports lookups, calculated values, and validation rules.
    """
    __tablename__ = "data_mappings"
    __table_args__ = (
        Index("ix_data_mappings_flow_order", "integration_flow_id", "sort_order"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    integration_flow_id: Mapped[int] = mapped_column(ForeignKey("integration_flows.id"), index=True)
    
    # Field mapping
    source_field: Mapped[str] = mapped_column(String(255))
    source_type: Mapped[str] = mapped_column(String(100))  # string, number, date, boolean, etc.
    destination_field: Mapped[str] = mapped_column(String(255))
    destination_type: Mapped[str] = mapped_column(String(100))
    
    # Transformation
    transformation_type: Mapped[TransformationType] = mapped_column(Enum(TransformationType), index=True)
    transformation_config: Mapped[dict] = mapped_column(JSON, default=dict)  # Lookup table, formula, etc.
    
    # Validation
    is_required: Mapped[bool] = mapped_column(Boolean, default=False)
    validation_rules: Mapped[dict] = mapped_column(JSON, default=dict)  # {min, max, pattern, etc.}
    default_value: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    # Metadata
    description: Mapped[str] = mapped_column(Text, default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    integration_flow: Mapped["IntegrationFlow"] = relationship(back_populates="data_mappings")


# ============================================================================
# Transformation Models
# ============================================================================

class Transformation(Base):
    """
    Reusable transformation rules.
    Can be versioned and shared across multiple integration flows.
    """
    __tablename__ = "transformations"
    __table_args__ = (
        Index("ix_transformations_owner_type", "owner_id", "transformation_type"),
        UniqueConstraint("owner_id", "name", name="uq_transformation_name_owner"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    integration_flow_id: Mapped[int | None] = mapped_column(ForeignKey("integration_flows.id"), nullable=True, index=True)
    
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    transformation_type: Mapped[TransformationType] = mapped_column(Enum(TransformationType), index=True)
    
    # Transformation logic
    config: Mapped[dict] = mapped_column(JSON, default=dict)  # Type-specific configuration
    expression: Mapped[str | None] = mapped_column(Text, nullable=True)  # For calculated fields
    
    # Versioning
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_versioned: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Usage tracking
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Metadata
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    is_shared: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    integration_flow: Mapped["IntegrationFlow"] = relationship(back_populates="transformations")


# ============================================================================
# Synchronization Models
# ============================================================================

class SyncJob(Base):
    """
    Scheduled or triggered synchronization job.
    Represents a recurring or one-time sync operation.
    """
    __tablename__ = "sync_jobs"
    __table_args__ = (
        Index("ix_sync_jobs_flow_status", "integration_flow_id", "status"),
        Index("ix_sync_jobs_scheduled", "scheduled_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    integration_flow_id: Mapped[int] = mapped_column(ForeignKey("integration_flows.id"), index=True)
    
    # Job details
    job_type: Mapped[SyncMode] = mapped_column(Enum(SyncMode), index=True)
    status: Mapped[SyncJobStatus] = mapped_column(Enum(SyncJobStatus), default=SyncJobStatus.pending, index=True)
    
    # Scheduling
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Execution details
    records_processed: Mapped[int] = mapped_column(Integer, default=0)
    records_succeeded: Mapped[int] = mapped_column(Integer, default=0)
    records_failed: Mapped[int] = mapped_column(Integer, default=0)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    
    # Error handling
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    
    # Metadata
    triggered_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    trigger_event: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Event that triggered this job
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    integration_flow: Mapped["IntegrationFlow"] = relationship(back_populates="sync_jobs")
    runs: Mapped[list["SyncJobRun"]] = relationship(back_populates="sync_job", cascade="all, delete-orphan")
    error_logs: Mapped[list["IntegrationLog"]] = relationship(back_populates="sync_job", cascade="all, delete-orphan")


class SyncJobRun(Base):
    """
    Individual execution run of a sync job.
    Tracks detailed metrics and status for each run.
    """
    __tablename__ = "sync_job_runs"
    __table_args__ = (
        Index("ix_sync_job_runs_job_created", "sync_job_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    sync_job_id: Mapped[int] = mapped_column(ForeignKey("sync_jobs.id"), index=True)
    
    # Run details
    run_number: Mapped[int] = mapped_column(Integer)  # Sequential run number for this job
    status: Mapped[SyncJobStatus] = mapped_column(Enum(SyncJobStatus), index=True)
    
    # Timing
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    
    # Metrics
    records_processed: Mapped[int] = mapped_column(Integer, default=0)
    records_succeeded: Mapped[int] = mapped_column(Integer, default=0)
    records_failed: Mapped[int] = mapped_column(Integer, default=0)
    records_skipped: Mapped[int] = mapped_column(Integer, default=0)
    
    # Throughput
    records_per_second: Mapped[float | None] = mapped_column(Float, nullable=True)
    bytes_processed: Mapped[int] = mapped_column(Integer, default=0)
    
    # Error tracking
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    warning_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    # Metadata
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    sync_job: Mapped["SyncJob"] = relationship(back_populates="runs")
    error_logs: Mapped[list["IntegrationLog"]] = relationship(back_populates="sync_job_run")


# ============================================================================
# Event Models
# ============================================================================

class EventDefinition(Base):
    """
    Event-driven integration trigger.
    Defines events that can trigger integration flows.
    """
    __tablename__ = "event_definitions"
    __table_args__ = (
        Index("ix_event_definitions_flow", "integration_flow_id"),
        Index("ix_event_definitions_event_type", "event_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    integration_flow_id: Mapped[int] = mapped_column(ForeignKey("integration_flows.id"), index=True)
    
    # Event details
    event_name: Mapped[str] = mapped_column(String(255), index=True)
    event_type: Mapped[EventType] = mapped_column(Enum(EventType), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    
    # Event schema
    event_schema: Mapped[dict] = mapped_column(JSON, default=dict)  # JSON schema for event payload
    
    # Trigger configuration
    trigger_condition: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # Filter conditions
    webhook_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    webhook_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    trigger_count: Mapped[int] = mapped_column(Integer, default=0)
    last_triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    integration_flow: Mapped["IntegrationFlow"] = relationship(back_populates="event_definitions")


# ============================================================================
# Logging and Monitoring Models
# ============================================================================

class IntegrationLog(Base):
    """
    Detailed integration logs for debugging and auditing.
    """
    __tablename__ = "integration_logs"
    __table_args__ = (
        Index("ix_integration_logs_flow_created", "integration_flow_id", "created_at"),
        Index("ix_integration_logs_level", "log_level"),
        Index("ix_integration_logs_sync_job", "sync_job_id"),
        Index("ix_integration_logs_sync_run", "sync_job_run_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    integration_flow_id: Mapped[int | None] = mapped_column(ForeignKey("integration_flows.id"), nullable=True, index=True)
    sync_job_id: Mapped[int | None] = mapped_column(ForeignKey("sync_jobs.id"), nullable=True, index=True)
    sync_job_run_id: Mapped[int | None] = mapped_column(ForeignKey("sync_job_runs.id"), nullable=True, index=True)
    
    # Log details
    log_level: Mapped[LogLevel] = mapped_column(Enum(LogLevel), index=True)
    message: Mapped[str] = mapped_column(Text)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Context
    component: Mapped[str] = mapped_column(String(100), index=True)  # connector, transformer, sync, etc.
    operation: Mapped[str] = mapped_column(String(100), index=True)  # connect, read, write, transform, etc.
    record_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    
    # Error tracking
    is_error: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    stack_trace: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Metadata
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)


# ============================================================================
# Template Models
# ============================================================================

class ConnectorTemplate(Base):
    """
    Pre-built integration templates for common scenarios.
    Users can clone and customize templates.
    """
    __tablename__ = "connector_templates"
    __table_args__ = (
        Index("ix_connector_templates_category_status", "category", "status"),
        Index("ix_connector_templates_featured", "is_featured", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    connector_id: Mapped[int] = mapped_column(ForeignKey("connectors.id"), index=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    
    # Template details
    name: Mapped[str] = mapped_column(String(255), index=True)
    display_name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[ConnectorCategory] = mapped_column(Enum(ConnectorCategory), index=True)
    
    # Template configuration
    template_config: Mapped[dict] = mapped_column(JSON, default=dict)  # Full integration flow config
    data_mappings: Mapped[list[dict]] = mapped_column(JSON, default=list)
    transformations: Mapped[list[dict]] = mapped_column(JSON, default=list)
    
    # Usage and ratings
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Status
    status: Mapped[TemplateStatus] = mapped_column(Enum(TemplateStatus), default=TemplateStatus.draft, index=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_official: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    
    # Metadata
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    connector: Mapped["Connector"] = relationship(back_populates="templates")


# ============================================================================
# Governance Models
# ============================================================================

class IntegrationGovernanceLog(Base):
    """
    Audit trail for all integration changes.
    Ensures compliance and traceability.
    """
    __tablename__ = "integration_governance_logs"
    __table_args__ = (
        Index("ix_governance_logs_flow_created", "integration_flow_id", "created_at"),
        Index("ix_governance_logs_user_action", "user_id", "action"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    integration_flow_id: Mapped[int] = mapped_column(ForeignKey("integration_flows.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    
    # Action details
    action: Mapped[GovernanceAction] = mapped_column(Enum(GovernanceAction), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    
    # Change tracking
    changes: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # Before/after snapshot
    previous_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    new_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Approval workflow
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approval_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Metadata
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    integration_flow: Mapped["IntegrationFlow"] = relationship(back_populates="governance_logs")


# ============================================================================
# Analytics Models
# ============================================================================

class IntegrationAnalytics(Base):
    """
    Operational metrics and analytics for integrations.
    """
    __tablename__ = "integration_analytics"
    __table_args__ = (
        Index("ix_integration_analytics_flow_date", "integration_flow_id", "date"),
        Index("ix_integration_analytics_date", "date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    integration_flow_id: Mapped[int] = mapped_column(ForeignKey("integration_flows.id"), index=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0), index=True)
    
    # Volume metrics
    total_records_processed: Mapped[int] = mapped_column(Integer, default=0)
    successful_records: Mapped[int] = mapped_column(Integer, default=0)
    failed_records: Mapped[int] = mapped_column(Integer, default=0)
    bytes_transferred: Mapped[int] = mapped_column(Integer, default=0)
    
    # Performance metrics
    avg_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    min_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    avg_throughput_rps: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Reliability metrics
    success_rate: Mapped[float | None] = mapped_column(Float, nullable=True)  # Percentage
    error_rate: Mapped[float | None] = mapped_column(Float, nullable=True)  # Percentage
    uptime_percentage: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Job metrics
    total_jobs_run: Mapped[int] = mapped_column(Integer, default=0)
    successful_jobs: Mapped[int] = mapped_column(Integer, default=0)
    failed_jobs: Mapped[int] = mapped_column(Integer, default=0)
    avg_job_duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # API consumption
    api_calls_made: Mapped[int] = mapped_column(Integer, default=0)
    api_errors: Mapped[int] = mapped_column(Integer, default=0)
    
    # Metadata
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    integration_flow: Mapped["IntegrationFlow"] = relationship(back_populates="analytics")


# ============================================================================
# Dead Letter Queue Models
# ============================================================================

class DeadLetterQueue(Base):
    """
    Failed messages that couldn't be processed.
    Supports replay and manual recovery.
    """
    __tablename__ = "dead_letter_queue"
    __table_args__ = (
        Index("ix_dlq_flow_created", "integration_flow_id", "created_at"),
        Index("ix_dlq_status", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    integration_flow_id: Mapped[int] = mapped_column(ForeignKey("integration_flows.id"), index=True)
    sync_job_run_id: Mapped[int | None] = mapped_column(ForeignKey("sync_job_runs.id"), nullable=True, index=True)
    
    # Failed message
    payload: Mapped[dict] = mapped_column(JSON)
    error_message: Mapped[str] = mapped_column(Text)
    error_type: Mapped[str] = mapped_column(String(100), index=True)
    stack_trace: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Retry tracking
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    
    # Status
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)  # pending, retrying, resolved, discarded
    
    # Resolution
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Metadata
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    integration_flow: Mapped["IntegrationFlow"] = relationship()