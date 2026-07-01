import enum
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
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


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    company: Mapped[str] = mapped_column(String(255), default="")
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
    data_sources: Mapped[list["DataSource"]] = relationship(back_populates="owner")


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
