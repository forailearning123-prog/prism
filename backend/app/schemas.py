from datetime import datetime
from enum import Enum
from typing import Any, Optional
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


# Auth schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    company: Optional[str] = ""
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    company: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# Executive schemas
class ExecutiveBase(BaseModel):
    id: str
    title: str
    role: str
    description: str
    focus_areas: list[str]
    status: str
    insights_count: int
    risk_level: str


# Insight schemas
class Insight(BaseModel):
    id: str
    executive_id: str
    executive_title: str
    category: str
    priority: str
    title: str
    summary: str
    impact: str
    recommendation: str
    confidence: int
    created_at: str


# Briefing schemas
class BriefingItem(BaseModel):
    category: str
    title: str
    detail: str
    impact: Optional[str] = None
    recommendation: Optional[str] = None
    probability: Optional[int] = None


class DailyBriefing(BaseModel):
    date: str
    company: str
    overall_health: str
    health_score: int
    items: list[BriefingItem]
    top_priority: str


class SourceTypeEnum(str, Enum):
    postgresql = "postgresql"
    mysql = "mysql"
    sqlserver = "sqlserver"
    csv = "csv"
    excel = "excel"
    rest_api = "rest_api"


class HealthStatusEnum(str, Enum):
    healthy = "healthy"
    warning = "warning"
    failed = "failed"
    disconnected = "disconnected"
    pending = "pending"


class PermissionRoleEnum(str, Enum):
    owner = "owner"
    admin = "admin"
    editor = "editor"
    viewer = "viewer"


class DataSourceBase(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    source_type: SourceTypeEnum
    description: str = Field(default="", max_length=500)
    schedule: str = Field(default="", max_length=100)
    tags: list[str] = Field(default_factory=list)
    host: Optional[str] = Field(default=None, max_length=255)
    port: Optional[int] = Field(default=None, ge=1, le=65535)
    username: Optional[str] = Field(default=None, max_length=255)
    password: Optional[str] = Field(default=None, max_length=255)
    database_name: Optional[str] = Field(default=None, max_length=255)
    base_url: Optional[str] = Field(default=None, max_length=500)
    authentication_type: Optional[str] = Field(default=None, max_length=100)
    headers: dict[str, str] = Field(default_factory=dict)
    file_name: Optional[str] = Field(default=None, max_length=255)
    file_content_base64: Optional[str] = None
    settings: dict[str, Any] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Source name is required")
        return cleaned

    @field_validator("host")
    @classmethod
    def validate_host(cls, value: Optional[str]) -> Optional[str]:
        if not value:
            return value
        if " " in value or value.startswith("-") or value.endswith("-"):
            raise ValueError("Enter a valid hostname")
        return value

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, value: Optional[str]) -> Optional[str]:
        if not value:
            return value
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Enter a valid URL (http/https)")
        return value

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value: list[str]) -> list[str]:
        cleaned = []
        seen = set()
        for tag in value:
            normalized = tag.strip()
            if not normalized:
                continue
            key = normalized.lower()
            if key not in seen:
                seen.add(key)
                cleaned.append(normalized[:100])
        return cleaned

    @model_validator(mode="after")
    def validate_type_specific_fields(self):
        if self.source_type in {SourceTypeEnum.postgresql, SourceTypeEnum.mysql, SourceTypeEnum.sqlserver}:
            required = {
                "host": self.host,
                "port": self.port,
                "username": self.username,
                "password": self.password,
                "database_name": self.database_name,
            }
            missing = [key for key, value in required.items() if value in (None, "")]
            if missing:
                raise ValueError(f"Missing required database fields: {', '.join(missing)}")
        elif self.source_type == SourceTypeEnum.rest_api:
            if not self.base_url:
                raise ValueError("Base URL is required for REST API connections")
        elif self.source_type in {SourceTypeEnum.csv, SourceTypeEnum.excel}:
            if not self.file_name or not self.file_content_base64:
                raise ValueError("File upload is required for CSV/Excel connections")
            if self.source_type == SourceTypeEnum.csv and not self.file_name.lower().endswith(".csv"):
                raise ValueError("Only .csv files are supported for CSV connector")
            if self.source_type == SourceTypeEnum.excel and not (
                self.file_name.lower().endswith(".xlsx") or self.file_name.lower().endswith(".xls")
            ):
                raise ValueError("Only .xlsx or .xls files are supported for Excel connector")
        return self


class DataSourceCreate(DataSourceBase):
    pass


class DataSourceUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    description: Optional[str] = Field(default=None, max_length=500)
    schedule: Optional[str] = Field(default=None, max_length=100)
    tags: Optional[list[str]] = None
    host: Optional[str] = Field(default=None, max_length=255)
    port: Optional[int] = Field(default=None, ge=1, le=65535)
    username: Optional[str] = Field(default=None, max_length=255)
    password: Optional[str] = Field(default=None, max_length=255)
    database_name: Optional[str] = Field(default=None, max_length=255)
    base_url: Optional[str] = Field(default=None, max_length=500)
    authentication_type: Optional[str] = Field(default=None, max_length=100)
    headers: Optional[dict[str, str]] = None
    file_name: Optional[str] = Field(default=None, max_length=255)
    file_content_base64: Optional[str] = None
    settings: Optional[dict[str, Any]] = None


class ConnectorCard(BaseModel):
    type: SourceTypeEnum
    title: str
    description: str


class MetadataColumn(BaseModel):
    object_name: str
    object_type: str
    column_name: str
    data_type: str
    is_nullable: bool
    sample_value: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SyncHistoryOut(BaseModel):
    id: int
    result: str
    duration_ms: int
    message: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConnectionLogOut(BaseModel):
    id: int
    action: str
    result: str
    duration_ms: int
    error_message: str
    user_id: Optional[int]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DataSourceListItem(BaseModel):
    id: int
    name: str
    source_type: SourceTypeEnum
    status: HealthStatusEnum
    owner: str
    last_sync_at: Optional[datetime]
    last_successful_refresh_at: Optional[datetime]
    created_at: datetime
    tags: list[str]


class DataSourceListResponse(BaseModel):
    items: list[DataSourceListItem]
    total: int
    page: int
    page_size: int


class DataSourceDetailsOut(BaseModel):
    id: int
    name: str
    source_type: SourceTypeEnum
    status: HealthStatusEnum
    owner: str
    description: str
    schedule: str
    host: Optional[str]
    port: Optional[int]
    database_name: Optional[str]
    base_url: Optional[str]
    authentication_type: Optional[str]
    created_at: datetime
    updated_at: datetime
    last_sync_at: Optional[datetime]
    last_successful_refresh_at: Optional[datetime]
    tags: list[str]
    metadata: list[MetadataColumn]
    recent_syncs: list[SyncHistoryOut]
    logs: list[ConnectionLogOut]
    usage_count: int
    recommendations: list[str]


class SourceHealthOut(BaseModel):
    source_id: int
    status: HealthStatusEnum
    reason: str


class ConnectionTestRequest(BaseModel):
    source_type: SourceTypeEnum
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    database_name: Optional[str] = None
    base_url: Optional[str] = None
    authentication_type: Optional[str] = None
    headers: dict[str, str] = Field(default_factory=dict)
    file_name: Optional[str] = None
    file_content_base64: Optional[str] = None


class ConnectionTestResponse(BaseModel):
    success: bool
    message: str
    duration_ms: int
    details: Optional[str] = None


class MetadataRefreshResponse(BaseModel):
    source_id: int
    status: str
    metadata_items: int
    message: str
