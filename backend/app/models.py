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


class ConnectionType(str, enum.Enum):
    postgresql = "postgresql"
    mysql = "mysql"
    sqlserver = "sqlserver"
    csv = "csv"
    excel = "excel"
    rest_api = "rest_api"


class HealthStatus(str, enum.Enum):
    healthy = "healthy"
    warning = "warning"
    failed = "failed"
    disconnected = "disconnected"
    pending = "pending"


class SyncResult(str, enum.Enum):
    success = "success"
    failed = "failed"


class LogResult(str, enum.Enum):
    success = "success"
    failed = "failed"


class PermissionRole(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    editor = "editor"
    viewer = "viewer"


class AppUserRole(str, enum.Enum):
    admin = "admin"
    data_architect = "data_architect"
    business_analyst = "business_analyst"
    viewer = "viewer"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    company: Mapped[str] = mapped_column(String(255), default="")
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    role: Mapped[AppUserRole] = mapped_column(Enum(AppUserRole), default=AppUserRole.admin, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
    data_sources: Mapped[list["DataSource"]] = relationship(back_populates="owner")
    dashboards: Mapped[list["Dashboard"]] = relationship(back_populates="owner")


class DataSource(Base):
    __tablename__ = "data_sources"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name_normalized: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    source_type: Mapped[ConnectionType] = mapped_column(Enum(ConnectionType), index=True)
    status: Mapped[HealthStatus] = mapped_column(Enum(HealthStatus), default=HealthStatus.pending, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    description: Mapped[str] = mapped_column(String(500), default="")
    schedule: Mapped[str] = mapped_column(String(100), default="")
    host: Mapped[str | None] = mapped_column(String(255), nullable=True)
    port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    database_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    base_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    authentication_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    encrypted_credentials: Mapped[str | None] = mapped_column(Text, nullable=True)
    settings: Mapped[dict] = mapped_column(JSON, default=dict)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_successful_refresh_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    owner: Mapped["User"] = relationship(back_populates="data_sources")
    tags: Mapped[list["Tag"]] = relationship("Tag", secondary="data_source_tags", back_populates="data_sources")
    metadata_entries: Mapped[list["MetadataEntry"]] = relationship(back_populates="data_source", cascade="all, delete-orphan")
    sync_history: Mapped[list["SyncHistory"]] = relationship(back_populates="data_source", cascade="all, delete-orphan")
    connection_logs: Mapped[list["ConnectionLog"]] = relationship(back_populates="data_source", cascade="all, delete-orphan")
    permissions: Mapped[list["DataSourcePermission"]] = relationship(back_populates="data_source", cascade="all, delete-orphan")


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    data_sources: Mapped[list["DataSource"]] = relationship("DataSource", secondary="data_source_tags", back_populates="tags")


class DataSourceTag(Base):
    __tablename__ = "data_source_tags"

    data_source_id: Mapped[int] = mapped_column(ForeignKey("data_sources.id"), primary_key=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"), primary_key=True)


class MetadataEntry(Base):
    __tablename__ = "metadata_entries"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    data_source_id: Mapped[int] = mapped_column(ForeignKey("data_sources.id"), index=True)
    object_name: Mapped[str] = mapped_column(String(255), index=True)
    object_type: Mapped[str] = mapped_column(String(50), default="table")
    column_name: Mapped[str] = mapped_column(String(255))
    data_type: Mapped[str] = mapped_column(String(100), default="string")
    is_nullable: Mapped[bool] = mapped_column(Boolean, default=True)
    sample_value: Mapped[str | None] = mapped_column(String(500), nullable=True)
    relationship_info: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    data_source: Mapped["DataSource"] = relationship(back_populates="metadata_entries")


class SyncHistory(Base):
    __tablename__ = "sync_history"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    data_source_id: Mapped[int] = mapped_column(ForeignKey("data_sources.id"), index=True)
    result: Mapped[SyncResult] = mapped_column(Enum(SyncResult), index=True)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    message: Mapped[str] = mapped_column(String(500), default="")
    triggered_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    data_source: Mapped["DataSource"] = relationship(back_populates="sync_history")


class ConnectionLog(Base):
    __tablename__ = "connection_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    data_source_id: Mapped[int] = mapped_column(ForeignKey("data_sources.id"), index=True)
    action: Mapped[str] = mapped_column(String(100), index=True)
    result: Mapped[LogResult] = mapped_column(Enum(LogResult), index=True)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str] = mapped_column(String(500), default="")
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    data_source: Mapped["DataSource"] = relationship(back_populates="connection_logs")


class DataSourcePermission(Base):
    __tablename__ = "data_source_permissions"
    __table_args__ = (UniqueConstraint("data_source_id", "user_id", name="uq_data_source_user"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    data_source_id: Mapped[int] = mapped_column(ForeignKey("data_sources.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[PermissionRole] = mapped_column(Enum(PermissionRole), default=PermissionRole.viewer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    data_source: Mapped["DataSource"] = relationship(back_populates="permissions")


class SemanticModelStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    archived = "archived"


class RelationshipType(str, enum.Enum):
    one_to_one = "one_to_one"
    one_to_many = "one_to_many"
    many_to_one = "many_to_one"
    many_to_many = "many_to_many"


class ValidationSeverity(str, enum.Enum):
    error = "error"
    warning = "warning"


class TrendDirection(str, enum.Enum):
    up = "up"
    down = "down"
    neutral = "neutral"


class SemanticModel(Base):
    __tablename__ = "semantic_models"
    __table_args__ = (
        Index("ix_semantic_models_owner_status", "owner_id", "status"),
        Index("ix_semantic_models_updated_at", "updated_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[SemanticModelStatus] = mapped_column(Enum(SemanticModelStatus), default=SemanticModelStatus.draft, index=True)
    current_version: Mapped[int] = mapped_column(Integer, default=1)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    selected_tables: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    owner: Mapped["User"] = relationship()
    data_sources: Mapped[list["SemanticModelDataSource"]] = relationship(
        back_populates="semantic_model", cascade="all, delete-orphan"
    )
    versions: Mapped[list["SemanticModelVersion"]] = relationship(back_populates="semantic_model", cascade="all, delete-orphan")
    entities: Mapped[list["BusinessEntity"]] = relationship(back_populates="semantic_model", cascade="all, delete-orphan")
    relationships: Mapped[list["EntityRelationship"]] = relationship(
        back_populates="semantic_model", cascade="all, delete-orphan", foreign_keys="EntityRelationship.semantic_model_id"
    )
    dimensions: Mapped[list["Dimension"]] = relationship(back_populates="semantic_model", cascade="all, delete-orphan")
    measures: Mapped[list["Measure"]] = relationship(back_populates="semantic_model", cascade="all, delete-orphan")
    calculated_fields: Mapped[list["CalculatedField"]] = relationship(back_populates="semantic_model", cascade="all, delete-orphan")
    kpis: Mapped[list["KPI"]] = relationship(back_populates="semantic_model", cascade="all, delete-orphan")
    hierarchies: Mapped[list["Hierarchy"]] = relationship(back_populates="semantic_model", cascade="all, delete-orphan")
    glossary_terms: Mapped[list["BusinessGlossaryTerm"]] = relationship(
        back_populates="semantic_model", cascade="all, delete-orphan"
    )
    validation_results: Mapped[list["ValidationResult"]] = relationship(
        back_populates="semantic_model", cascade="all, delete-orphan"
    )
    documentation: Mapped["DocumentationMetadata"] = relationship(
        back_populates="semantic_model", cascade="all, delete-orphan", uselist=False
    )
    impact_analyses: Mapped[list["ImpactAnalysisSnapshot"]] = relationship(
        back_populates="semantic_model", cascade="all, delete-orphan"
    )
    time_intelligence_definitions: Mapped[list["TimeIntelligenceDefinition"]] = relationship(
        back_populates="semantic_model", cascade="all, delete-orphan"
    )


class SemanticModelDataSource(Base):
    __tablename__ = "semantic_model_data_sources"
    __table_args__ = (UniqueConstraint("semantic_model_id", "data_source_id", name="uq_model_data_source"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    semantic_model_id: Mapped[int] = mapped_column(ForeignKey("semantic_models.id"), index=True)
    data_source_id: Mapped[int] = mapped_column(ForeignKey("data_sources.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    semantic_model: Mapped["SemanticModel"] = relationship(back_populates="data_sources")
    data_source: Mapped["DataSource"] = relationship()


class SemanticModelVersion(Base):
    __tablename__ = "semantic_model_versions"
    __table_args__ = (
        UniqueConstraint("semantic_model_id", "version_number", name="uq_model_version"),
        Index("ix_model_versions_model_created", "semantic_model_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    semantic_model_id: Mapped[int] = mapped_column(ForeignKey("semantic_models.id"), index=True)
    version_number: Mapped[int] = mapped_column(Integer)
    status: Mapped[SemanticModelStatus] = mapped_column(Enum(SemanticModelStatus), default=SemanticModelStatus.draft)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    notes: Mapped[str] = mapped_column(String(500), default="")
    snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    is_rollback: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    semantic_model: Mapped["SemanticModel"] = relationship(back_populates="versions")


class BusinessEntity(Base):
    __tablename__ = "business_entities"
    __table_args__ = (UniqueConstraint("semantic_model_id", "display_name", name="uq_entity_display_name"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    semantic_model_id: Mapped[int] = mapped_column(ForeignKey("semantic_models.id"), index=True)
    display_name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    source_table: Mapped[str] = mapped_column(String(255), index=True)
    primary_key: Mapped[str] = mapped_column(String(255))
    business_owner: Mapped[str] = mapped_column(String(255), default="")
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    semantic_model: Mapped["SemanticModel"] = relationship(back_populates="entities")


class EntityRelationship(Base):
    __tablename__ = "entity_relationships"
    __table_args__ = (
        UniqueConstraint(
            "semantic_model_id",
            "from_entity_id",
            "to_entity_id",
            "from_field",
            "to_field",
            name="uq_entity_relationship_signature",
        ),
        Index("ix_entity_relationships_model", "semantic_model_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    semantic_model_id: Mapped[int] = mapped_column(ForeignKey("semantic_models.id"), index=True)
    name: Mapped[str] = mapped_column(String(255), default="")
    from_entity_id: Mapped[int] = mapped_column(ForeignKey("business_entities.id"), index=True)
    to_entity_id: Mapped[int] = mapped_column(ForeignKey("business_entities.id"), index=True)
    from_field: Mapped[str] = mapped_column(String(255))
    to_field: Mapped[str] = mapped_column(String(255))
    relationship_type: Mapped[RelationshipType] = mapped_column(Enum(RelationshipType), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    semantic_model: Mapped["SemanticModel"] = relationship(back_populates="relationships", foreign_keys=[semantic_model_id])
    from_entity: Mapped["BusinessEntity"] = relationship(foreign_keys=[from_entity_id])
    to_entity: Mapped["BusinessEntity"] = relationship(foreign_keys=[to_entity_id])


class Dimension(Base):
    __tablename__ = "dimensions"
    __table_args__ = (UniqueConstraint("semantic_model_id", "display_name", name="uq_dimension_display_name"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    semantic_model_id: Mapped[int] = mapped_column(ForeignKey("semantic_models.id"), index=True)
    entity_id: Mapped[int | None] = mapped_column(ForeignKey("business_entities.id"), nullable=True, index=True)
    display_name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    data_type: Mapped[str] = mapped_column(String(100), default="string")
    default_formatting: Mapped[str] = mapped_column(String(100), default="")
    visibility: Mapped[bool] = mapped_column(Boolean, default=True)
    grouping: Mapped[str] = mapped_column(String(100), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    semantic_model: Mapped["SemanticModel"] = relationship(back_populates="dimensions")


class Measure(Base):
    __tablename__ = "measures"
    __table_args__ = (UniqueConstraint("semantic_model_id", "display_name", name="uq_measure_display_name"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    semantic_model_id: Mapped[int] = mapped_column(ForeignKey("semantic_models.id"), index=True)
    entity_id: Mapped[int | None] = mapped_column(ForeignKey("business_entities.id"), nullable=True, index=True)
    display_name: Mapped[str] = mapped_column(String(255), index=True)
    aggregation_type: Mapped[str] = mapped_column(String(50), default="sum")
    formatting: Mapped[str] = mapped_column(String(100), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(100), default="")
    business_definition: Mapped[str] = mapped_column(Text, default="")
    expression: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    semantic_model: Mapped["SemanticModel"] = relationship(back_populates="measures")


class CalculatedField(Base):
    __tablename__ = "calculated_fields"
    __table_args__ = (UniqueConstraint("semantic_model_id", "display_name", name="uq_calculated_field_display_name"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    semantic_model_id: Mapped[int] = mapped_column(ForeignKey("semantic_models.id"), index=True)
    entity_id: Mapped[int | None] = mapped_column(ForeignKey("business_entities.id"), nullable=True, index=True)
    display_name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    data_type: Mapped[str] = mapped_column(String(100), default="string")
    expression: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    semantic_model: Mapped["SemanticModel"] = relationship(back_populates="calculated_fields")


class KPI(Base):
    __tablename__ = "kpis"
    __table_args__ = (UniqueConstraint("semantic_model_id", "name", name="uq_kpi_name"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    semantic_model_id: Mapped[int] = mapped_column(ForeignKey("semantic_models.id"), index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    business_description: Mapped[str] = mapped_column(Text, default="")
    formula: Mapped[str] = mapped_column(Text)
    target_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    warning_threshold: Mapped[float | None] = mapped_column(Float, nullable=True)
    critical_threshold: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str] = mapped_column(String(50), default="")
    trend_direction: Mapped[TrendDirection] = mapped_column(Enum(TrendDirection), default=TrendDirection.up)
    display_format: Mapped[str] = mapped_column(String(100), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    semantic_model: Mapped["SemanticModel"] = relationship(back_populates="kpis")


class TimeIntelligenceDefinition(Base):
    __tablename__ = "time_intelligence_definitions"
    __table_args__ = (UniqueConstraint("semantic_model_id", "name", name="uq_time_intelligence_name"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    semantic_model_id: Mapped[int] = mapped_column(ForeignKey("semantic_models.id"), index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    expression: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    semantic_model: Mapped["SemanticModel"] = relationship(back_populates="time_intelligence_definitions")


class Hierarchy(Base):
    __tablename__ = "hierarchies"
    __table_args__ = (UniqueConstraint("semantic_model_id", "name", name="uq_hierarchy_name"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    semantic_model_id: Mapped[int] = mapped_column(ForeignKey("semantic_models.id"), index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    semantic_model: Mapped["SemanticModel"] = relationship(back_populates="hierarchies")
    levels: Mapped[list["HierarchyLevel"]] = relationship(back_populates="hierarchy", cascade="all, delete-orphan")


class HierarchyLevel(Base):
    __tablename__ = "hierarchy_levels"
    __table_args__ = (
        UniqueConstraint("hierarchy_id", "level_order", name="uq_hierarchy_level_order"),
        Index("ix_hierarchy_levels_hierarchy_order", "hierarchy_id", "level_order"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    hierarchy_id: Mapped[int] = mapped_column(ForeignKey("hierarchies.id"), index=True)
    level_order: Mapped[int] = mapped_column(Integer)
    level_name: Mapped[str] = mapped_column(String(255))
    dimension_name: Mapped[str] = mapped_column(String(255))

    hierarchy: Mapped["Hierarchy"] = relationship(back_populates="levels")


class BusinessGlossaryTerm(Base):
    __tablename__ = "business_glossary_terms"
    __table_args__ = (UniqueConstraint("semantic_model_id", "business_name", name="uq_glossary_business_name"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    semantic_model_id: Mapped[int] = mapped_column(ForeignKey("semantic_models.id"), index=True)
    business_name: Mapped[str] = mapped_column(String(255), index=True)
    technical_name: Mapped[str] = mapped_column(String(255), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    business_owner: Mapped[str] = mapped_column(String(255), default="")
    synonyms: Mapped[list[str]] = mapped_column(JSON, default=list)
    related_metrics: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    semantic_model: Mapped["SemanticModel"] = relationship(back_populates="glossary_terms")


class ValidationResult(Base):
    __tablename__ = "validation_results"
    __table_args__ = (Index("ix_validation_results_model_version", "semantic_model_id", "version_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    semantic_model_id: Mapped[int] = mapped_column(ForeignKey("semantic_models.id"), index=True)
    version_id: Mapped[int | None] = mapped_column(ForeignKey("semantic_model_versions.id"), nullable=True, index=True)
    severity: Mapped[ValidationSeverity] = mapped_column(Enum(ValidationSeverity), index=True)
    code: Mapped[str] = mapped_column(String(100), index=True)
    message: Mapped[str] = mapped_column(String(500))
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    semantic_model: Mapped["SemanticModel"] = relationship(back_populates="validation_results")


class DocumentationMetadata(Base):
    __tablename__ = "documentation_metadata"
    __table_args__ = (UniqueConstraint("semantic_model_id", name="uq_documentation_model"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    semantic_model_id: Mapped[int] = mapped_column(ForeignKey("semantic_models.id"), index=True)
    generated_by: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    content: Mapped[dict] = mapped_column(JSON, default=dict)

    semantic_model: Mapped["SemanticModel"] = relationship(back_populates="documentation")


class ImpactAnalysisSnapshot(Base):
    __tablename__ = "impact_analysis_snapshots"
    __table_args__ = (Index("ix_impact_analysis_model_version", "semantic_model_id", "version_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    semantic_model_id: Mapped[int] = mapped_column(ForeignKey("semantic_models.id"), index=True)
    version_id: Mapped[int | None] = mapped_column(ForeignKey("semantic_model_versions.id"), nullable=True, index=True)
    dashboards_affected: Mapped[list[str]] = mapped_column(JSON, default=list)
    reports_affected: Mapped[list[str]] = mapped_column(JSON, default=list)
    kpis_affected: Mapped[list[str]] = mapped_column(JSON, default=list)
    ai_features_affected: Mapped[list[str]] = mapped_column(JSON, default=list)
    scheduled_jobs_affected: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    semantic_model: Mapped["SemanticModel"] = relationship(back_populates="impact_analyses")


class DashboardStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    archived = "archived"


class DashboardCreationMode(str, enum.Enum):
    ai = "ai"
    wizard = "wizard"
    blank = "blank"


class DashboardWidgetType(str, enum.Enum):
    kpi_card = "kpi_card"
    line_chart = "line_chart"
    bar_chart = "bar_chart"
    area_chart = "area_chart"
    pie_chart = "pie_chart"
    donut_chart = "donut_chart"
    scatter_chart = "scatter_chart"
    heat_map = "heat_map"
    tree_map = "tree_map"
    waterfall_chart = "waterfall_chart"
    funnel_chart = "funnel_chart"
    gauge_chart = "gauge_chart"
    table = "table"
    pivot_table = "pivot_table"
    map = "map"
    timeline = "timeline"
    text_panel = "text_panel"
    image = "image"
    embedded_content = "embedded_content"


class DashboardFilterScope(str, enum.Enum):
    global_ = "global"
    dashboard = "dashboard"
    widget = "widget"
    quick = "quick"
    advanced = "advanced"
    relative_date = "relative_date"
    saved = "saved"
    cross = "cross"


class DashboardVisibility(str, enum.Enum):
    private = "private"
    team = "team"
    department = "department"
    organisation = "organisation"
    public_link = "public_link"


class DashboardPermissionRole(str, enum.Enum):
    viewer = "viewer"
    editor = "editor"
    owner = "owner"


class DashboardRecommendationType(str, enum.Enum):
    better_chart = "better_chart"
    missing_kpi = "missing_kpi"
    redundant_visual = "redundant_visual"
    layout = "layout"
    accessibility = "accessibility"
    performance = "performance"


class Dashboard(Base):
    __tablename__ = "dashboards"
    __table_args__ = (
        Index("ix_dashboards_owner_status", "owner_id", "status"),
        Index("ix_dashboards_updated_status", "updated_at", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    folder: Mapped[str] = mapped_column(String(255), default="", index=True)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    status: Mapped[DashboardStatus] = mapped_column(Enum(DashboardStatus), default=DashboardStatus.draft, index=True)
    is_favourite: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    shared_with: Mapped[list[str]] = mapped_column(JSON, default=list)
    semantic_model_id: Mapped[int | None] = mapped_column(ForeignKey("semantic_models.id"), nullable=True, index=True)
    theme_id: Mapped[int | None] = mapped_column(ForeignKey("dashboard_themes.id"), nullable=True, index=True)
    creation_mode: Mapped[DashboardCreationMode] = mapped_column(
        Enum(DashboardCreationMode), default=DashboardCreationMode.blank, index=True
    )
    ai_prompt: Mapped[str] = mapped_column(Text, default="")
    last_viewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_version: Mapped[int] = mapped_column(Integer, default=1)
    auto_save_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    owner: Mapped["User"] = relationship(back_populates="dashboards")
    semantic_model: Mapped["SemanticModel"] = relationship()
    theme: Mapped["DashboardTheme"] = relationship(back_populates="dashboards")
    widgets: Mapped[list["DashboardWidget"]] = relationship(back_populates="dashboard", cascade="all, delete-orphan")
    filters: Mapped[list["DashboardFilter"]] = relationship(back_populates="dashboard", cascade="all, delete-orphan")
    versions: Mapped[list["DashboardVersion"]] = relationship(back_populates="dashboard", cascade="all, delete-orphan")
    permissions: Mapped[list["DashboardPermission"]] = relationship(back_populates="dashboard", cascade="all, delete-orphan")
    layout_metadata_entries: Mapped[list["DashboardLayoutMetadata"]] = relationship(
        back_populates="dashboard", cascade="all, delete-orphan"
    )
    usage_entries: Mapped[list["DashboardUsage"]] = relationship(back_populates="dashboard", cascade="all, delete-orphan")
    recommendations: Mapped[list["DashboardRecommendation"]] = relationship(
        back_populates="dashboard", cascade="all, delete-orphan"
    )


class DashboardVersion(Base):
    __tablename__ = "dashboard_versions"
    __table_args__ = (
        UniqueConstraint("dashboard_id", "version_number", name="uq_dashboard_version_number"),
        Index("ix_dashboard_versions_dashboard_created", "dashboard_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    dashboard_id: Mapped[int] = mapped_column(ForeignKey("dashboards.id"), index=True)
    version_number: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(255), default="")
    description: Mapped[str] = mapped_column(String(500), default="")
    status: Mapped[DashboardStatus] = mapped_column(Enum(DashboardStatus), default=DashboardStatus.draft)
    snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    dashboard: Mapped["Dashboard"] = relationship(back_populates="versions")


class DashboardWidget(Base):
    __tablename__ = "dashboard_widgets"
    __table_args__ = (Index("ix_dashboard_widgets_dashboard_position", "dashboard_id", "position_y", "position_x"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    dashboard_id: Mapped[int] = mapped_column(ForeignKey("dashboards.id"), index=True)
    widget_type: Mapped[DashboardWidgetType] = mapped_column(Enum(DashboardWidgetType), index=True)
    title: Mapped[str] = mapped_column(String(255), default="")
    subtitle: Mapped[str] = mapped_column(String(255), default="")
    description: Mapped[str] = mapped_column(String(1000), default="")
    data_source: Mapped[str] = mapped_column(String(255), default="")
    dimensions: Mapped[list[str]] = mapped_column(JSON, default=list)
    measures: Mapped[list[str]] = mapped_column(JSON, default=list)
    filters: Mapped[dict] = mapped_column(JSON, default=dict)
    colors: Mapped[dict] = mapped_column(JSON, default=dict)
    number_formatting: Mapped[dict] = mapped_column(JSON, default=dict)
    conditional_formatting: Mapped[dict] = mapped_column(JSON, default=dict)
    legends: Mapped[dict] = mapped_column(JSON, default=dict)
    labels: Mapped[dict] = mapped_column(JSON, default=dict)
    tooltips: Mapped[dict] = mapped_column(JSON, default=dict)
    drill_behavior: Mapped[dict] = mapped_column(JSON, default=dict)
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    position_x: Mapped[int] = mapped_column(Integer, default=0)
    position_y: Mapped[int] = mapped_column(Integer, default=0)
    width: Mapped[int] = mapped_column(Integer, default=4)
    height: Mapped[int] = mapped_column(Integer, default=3)
    z_index: Mapped[int] = mapped_column(Integer, default=0)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False)
    group_key: Mapped[str] = mapped_column(String(100), default="")
    alignment: Mapped[str] = mapped_column(String(50), default="start")
    snap_to_grid: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    dashboard: Mapped["Dashboard"] = relationship(back_populates="widgets")


class DashboardFilter(Base):
    __tablename__ = "dashboard_filters"
    __table_args__ = (Index("ix_dashboard_filters_dashboard_scope", "dashboard_id", "scope"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    dashboard_id: Mapped[int] = mapped_column(ForeignKey("dashboards.id"), index=True)
    widget_id: Mapped[int | None] = mapped_column(ForeignKey("dashboard_widgets.id"), nullable=True, index=True)
    scope: Mapped[DashboardFilterScope] = mapped_column(Enum(DashboardFilterScope), default=DashboardFilterScope.dashboard)
    name: Mapped[str] = mapped_column(String(255))
    field: Mapped[str] = mapped_column(String(255))
    operator: Mapped[str] = mapped_column(String(50), default="equals")
    value: Mapped[dict] = mapped_column(JSON, default=dict)
    is_saved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    dashboard: Mapped["Dashboard"] = relationship(back_populates="filters")


class DashboardTheme(Base):
    __tablename__ = "dashboard_themes"
    __table_args__ = (UniqueConstraint("name", "owner_id", name="uq_dashboard_theme_name_owner"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    variant: Mapped[str] = mapped_column(String(50), default="custom", index=True)
    brand_colors: Mapped[dict] = mapped_column(JSON, default=dict)
    typography: Mapped[dict] = mapped_column(JSON, default=dict)
    logo_url: Mapped[str] = mapped_column(String(500), default="")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    dashboards: Mapped[list["Dashboard"]] = relationship(back_populates="theme")


class DashboardPermission(Base):
    __tablename__ = "dashboard_permissions"
    __table_args__ = (UniqueConstraint("dashboard_id", "principal", name="uq_dashboard_permission_principal"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    dashboard_id: Mapped[int] = mapped_column(ForeignKey("dashboards.id"), index=True)
    visibility: Mapped[DashboardVisibility] = mapped_column(Enum(DashboardVisibility), default=DashboardVisibility.private)
    principal: Mapped[str] = mapped_column(String(255), index=True)
    role: Mapped[DashboardPermissionRole] = mapped_column(Enum(DashboardPermissionRole), default=DashboardPermissionRole.viewer)
    granted_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    dashboard: Mapped["Dashboard"] = relationship(back_populates="permissions")


class DashboardLayoutMetadata(Base):
    __tablename__ = "dashboard_layout_metadata"
    __table_args__ = (UniqueConstraint("dashboard_id", "key", name="uq_dashboard_layout_key"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    dashboard_id: Mapped[int] = mapped_column(ForeignKey("dashboards.id"), index=True)
    key: Mapped[str] = mapped_column(String(255))
    value: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    dashboard: Mapped["Dashboard"] = relationship(back_populates="layout_metadata_entries")


class DashboardUsage(Base):
    __tablename__ = "dashboard_usage"
    __table_args__ = (Index("ix_dashboard_usage_dashboard_viewed", "dashboard_id", "viewed_at"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    dashboard_id: Mapped[int] = mapped_column(ForeignKey("dashboards.id"), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    viewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    render_time_ms: Mapped[int] = mapped_column(Integer, default=0)
    widget_count: Mapped[int] = mapped_column(Integer, default=0)
    query_count: Mapped[int] = mapped_column(Integer, default=0)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)

    dashboard: Mapped["Dashboard"] = relationship(back_populates="usage_entries")


class DashboardRecommendation(Base):
    __tablename__ = "dashboard_recommendations"
    __table_args__ = (Index("ix_dashboard_recommendations_dashboard_created", "dashboard_id", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    dashboard_id: Mapped[int] = mapped_column(ForeignKey("dashboards.id"), index=True)
    recommendation_type: Mapped[DashboardRecommendationType] = mapped_column(Enum(DashboardRecommendationType), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String(1000), default="")
    reason: Mapped[str] = mapped_column(String(1000), default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    dashboard: Mapped["Dashboard"] = relationship(back_populates="recommendations")


# --- AI Analyst Models ---

class ConversationStatus(str, enum.Enum):
    active = "active"
    archived = "archived"
    deleted = "deleted"


class MessageRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"
    system = "system"


class FeedbackType(str, enum.Enum):
    rating = "rating"
    incorrect = "incorrect"
    misleading = "misleading"
    glossary_suggestion = "glossary_suggestion"


class ReportType(str, enum.Enum):
    executive_summary = "executive_summary"
    business_review = "business_review"
    department_report = "department_report"
    kpi_report = "kpi_report"
    operational_report = "operational_report"
    monthly_review = "monthly_review"
    quarterly_review = "quarterly_review"


class Conversation(Base):
    __tablename__ = "conversations"
    __table_args__ = (
        Index("ix_conversations_user_status", "user_id", "status"),
        Index("ix_conversations_updated_at", "updated_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(500), default="New Conversation")
    status: Mapped[ConversationStatus] = mapped_column(
        Enum(ConversationStatus), default=ConversationStatus.active, index=True
    )
    is_favourite: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    dashboard_context_id: Mapped[int | None] = mapped_column(ForeignKey("dashboards.id"), nullable=True)
    semantic_model_id: Mapped[int | None] = mapped_column(ForeignKey("semantic_models.id"), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User"] = relationship()
    messages: Mapped[list["AnalystMessage"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )
    bookmarks: Mapped[list["ConversationBookmark"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )
    insights: Mapped[list["SavedInsight"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )


class AnalystMessage(Base):
    __tablename__ = "analyst_messages"
    __table_args__ = (
        Index("ix_analyst_messages_conversation_created", "conversation_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), index=True)
    role: Mapped[MessageRole] = mapped_column(Enum(MessageRole), index=True)
    content: Mapped[str] = mapped_column(Text)
    executive_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_findings: Mapped[list | None] = mapped_column(JSON, nullable=True)
    supporting_evidence: Mapped[list | None] = mapped_column(JSON, nullable=True)
    business_interpretation: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    data_sources_used: Mapped[list | None] = mapped_column(JSON, nullable=True)
    visualizations: Mapped[list | None] = mapped_column(JSON, nullable=True)
    recommendations: Mapped[list | None] = mapped_column(JSON, nullable=True)
    suggested_questions: Mapped[list | None] = mapped_column(JSON, nullable=True)
    intent: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
    feedback: Mapped[list["UserFeedback"]] = relationship(
        back_populates="message", cascade="all, delete-orphan"
    )


class ConversationBookmark(Base):
    __tablename__ = "conversation_bookmarks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), index=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("analyst_messages.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    label: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    conversation: Mapped["Conversation"] = relationship(back_populates="bookmarks")
    message: Mapped["AnalystMessage"] = relationship()


class SavedInsight(Base):
    __tablename__ = "saved_insights"
    __table_args__ = (Index("ix_saved_insights_user_created", "user_id", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), index=True)
    message_id: Mapped[int | None] = mapped_column(
        ForeignKey("analyst_messages.id"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(Text)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    conversation: Mapped["Conversation"] = relationship(back_populates="insights")


class UserFeedback(Base):
    __tablename__ = "user_feedback"
    __table_args__ = (Index("ix_user_feedback_message", "message_id", "user_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), index=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("analyst_messages.id"), index=True)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    feedback_type: Mapped[FeedbackType] = mapped_column(
        Enum(FeedbackType), default=FeedbackType.rating
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    message: Mapped["AnalystMessage"] = relationship(back_populates="feedback")


class AnalystAuditLog(Base):
    __tablename__ = "analyst_audit_logs"
    __table_args__ = (Index("ix_analyst_audit_user_created", "user_id", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    conversation_id: Mapped[int | None] = mapped_column(
        ForeignKey("conversations.id"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(100), index=True)
    question: Mapped[str | None] = mapped_column(Text, nullable=True)
    intent: Mapped[str | None] = mapped_column(String(100), nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )


class ReportDefinition(Base):
    __tablename__ = "report_definitions"
    __table_args__ = (Index("ix_report_definitions_user_created", "user_id", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    conversation_id: Mapped[int | None] = mapped_column(ForeignKey("conversations.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(500))
    report_type: Mapped[ReportType] = mapped_column(Enum(ReportType), index=True)
    content: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
