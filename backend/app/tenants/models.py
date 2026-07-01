import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class OrganizationStatus(str, enum.Enum):
    active = "active"
    suspended = "suspended"
    archived = "archived"
    pending = "pending"


class SubscriptionTier(str, enum.Enum):
    trial = "trial"
    standard = "standard"
    professional = "professional"
    enterprise = "enterprise"
    custom = "custom"


class WorkspaceType(str, enum.Enum):
    general = "general"
    finance = "finance"
    hr = "hr"
    sales = "sales"
    operations = "operations"
    executive = "executive"
    data_science = "data_science"
    custom = "custom"


class MemberRole(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    member = "member"
    viewer = "viewer"


class Organization(Base):
    __tablename__ = "organizations"
    __table_args__ = (
        Index("ix_organizations_slug", "slug", unique=True),
        Index("ix_organizations_status", "status"),
        Index("ix_organizations_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    industry: Mapped[str] = mapped_column(String(100), default="")
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    locale: Mapped[str] = mapped_column(String(10), default="en-US")
    status: Mapped[OrganizationStatus] = mapped_column(Enum(OrganizationStatus), default=OrganizationStatus.active, index=True)
    subscription_tier: Mapped[SubscriptionTier] = mapped_column(Enum(SubscriptionTier), default=SubscriptionTier.trial, index=True)
    
    # Branding
    logo_url: Mapped[str] = mapped_column(String(500), default="")
    primary_color: Mapped[str] = mapped_column(String(7), default="#007bff")
    secondary_color: Mapped[str] = mapped_column(String(7), default="#6c757d")
    custom_domain: Mapped[str] = mapped_column(String(255), default="")
    
    # Limits and quotas
    max_users: Mapped[int] = mapped_column(Integer, default=10)
    max_workspaces: Mapped[int] = mapped_column(Integer, default=5)
    max_storage_gb: Mapped[float] = mapped_column(Float, default=10.0)
    max_ai_requests_per_month: Mapped[int] = mapped_column(Integer, default=1000)
    max_api_calls_per_month: Mapped[int] = mapped_column(Integer, default=10000)
    
    # Settings
    settings: Mapped[dict] = mapped_column(JSON, default=dict)
    feature_flags: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Metadata
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    workspaces: Mapped[list["Workspace"]] = relationship(back_populates="organization", cascade="all, delete-orphan")
    members: Mapped[list["OrganizationMember"]] = relationship(back_populates="organization", cascade="all, delete-orphan")
    branding_config: Mapped["BrandingConfig | None"] = relationship(back_populates="organization", cascade="all, delete-orphan", uselist=False)
    subscription: Mapped["Subscription | None"] = relationship(back_populates="organization", cascade="all, delete-orphan", uselist=False)
    api_keys: Mapped[list["APIKey"]] = relationship(back_populates="organization", cascade="all, delete-orphan")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="organization", cascade="all, delete-orphan")
    usage_metrics: Mapped[list["UsageMetric"]] = relationship(back_populates="organization", cascade="all, delete-orphan")


class Workspace(Base):
    __tablename__ = "workspaces"
    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_workspace_org_name"),
        Index("ix_workspaces_org_id", "organization_id"),
        Index("ix_workspaces_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    workspace_type: Mapped[WorkspaceType] = mapped_column(Enum(WorkspaceType), default=WorkspaceType.general, index=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    
    # Settings
    settings: Mapped[dict] = mapped_column(JSON, default=dict)
    feature_flags: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Metadata
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="workspaces")
    members: Mapped[list["WorkspaceMember"]] = relationship(back_populates="workspace", cascade="all, delete-orphan")
    dashboards: Mapped[list["Dashboard"]] = relationship(back_populates="workspace")
    semantic_models: Mapped[list["SemanticModel"]] = relationship(back_populates="workspace")


class OrganizationMember(Base):
    __tablename__ = "organization_members"
    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_org_member_user"),
        Index("ix_org_members_org_user", "organization_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[MemberRole] = mapped_column(Enum(MemberRole), default=MemberRole.member, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    
    # Metadata
    invited_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(foreign_keys=[user_id])
    inviter: Mapped["User | None"] = relationship(foreign_keys=[invited_by])


class WorkspaceMember(Base):
    __tablename__ = "workspace_members"
    __table_args__ = (
        UniqueConstraint("workspace_id", "user_id", name="uq_workspace_member_user"),
        Index("ix_workspace_members_workspace_user", "workspace_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[MemberRole] = mapped_column(Enum(MemberRole), default=MemberRole.member, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    
    # Metadata
    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    workspace: Mapped["Workspace"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship()


class BrandingConfig(Base):
    __tablename__ = "branding_configs"
    __table_args__ = (UniqueConstraint("organization_id", name="uq_branding_org"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    
    # Logo and images
    logo_url: Mapped[str] = mapped_column(String(500), default="")
    logo_dark_url: Mapped[str] = mapped_column(String(500), default="")
    favicon_url: Mapped[str] = mapped_column(String(500), default="")
    background_image_url: Mapped[str] = mapped_column(String(500), default="")
    
    # Colors
    primary_color: Mapped[str] = mapped_column(String(7), default="#007bff")
    secondary_color: Mapped[str] = mapped_column(String(7), default="#6c757d")
    accent_color: Mapped[str] = mapped_column(String(7), default="#28a745")
    background_color: Mapped[str] = mapped_column(String(7), default="#ffffff")
    text_color: Mapped[str] = mapped_column(String(7), default="#212529")
    
    # Typography
    font_family: Mapped[str] = mapped_column(String(100), default="Inter, sans-serif")
    heading_font_family: Mapped[str] = mapped_column(String(100), default="Inter, sans-serif")
    
    # Login screen
    login_page_title: Mapped[str] = mapped_column(String(255), default="")
    login_page_description: Mapped[str] = mapped_column(Text, default="")
    login_background_image: Mapped[str] = mapped_column(String(500), default="")
    
    # Email templates
    email_header_logo: Mapped[str] = mapped_column(String(500), default="")
    email_footer_text: Mapped[str] = mapped_column(Text, default="")
    
    # Advanced
    custom_css: Mapped[str] = mapped_column(Text, default="")
    css_variables: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="branding_config")


class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        Index("ix_subscriptions_org_id", "organization_id"),
        Index("ix_subscriptions_status", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    plan_id: Mapped[int | None] = mapped_column(ForeignKey("subscription_plans.id"), nullable=True, index=True)
    
    # Subscription details
    status: Mapped[str] = mapped_column(String(50), default="active", index=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Billing
    billing_cycle: Mapped[str] = mapped_column(String(50), default="monthly")
    amount: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    
    # Metadata
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="subscription")
    plan: Mapped["SubscriptionPlan | None"] = relationship()


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"
    __table_args__ = (
        Index("ix_subscription_plans_tier", "tier"),
        Index("ix_subscription_plans_is_active", "is_active"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    tier: Mapped[SubscriptionTier] = mapped_column(Enum(SubscriptionTier), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    
    # Limits
    max_users: Mapped[int] = mapped_column(Integer, default=10)
    max_workspaces: Mapped[int] = mapped_column(Integer, default=5)
    max_storage_gb: Mapped[float] = mapped_column(Float, default=10.0)
    max_ai_requests_per_month: Mapped[int] = mapped_column(Integer, default=1000)
    max_api_calls_per_month: Mapped[int] = mapped_column(Integer, default=10000)
    max_scheduled_jobs: Mapped[int] = mapped_column(Integer, default=10)
    
    # Features
    features: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Pricing
    price_monthly: Mapped[float] = mapped_column(Float, default=0.0)
    price_annual: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    
    # Metadata
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class APIKey(Base):
    __tablename__ = "api_keys"
    __table_args__ = (
        Index("ix_api_keys_org_id", "organization_id"),
        Index("ix_api_keys_key_hash", "key_hash", unique=True),
        Index("ix_api_keys_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    
    # Key details
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    key_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    key_prefix: Mapped[str] = mapped_column(String(20), index=True)
    
    # Permissions
    scopes: Mapped[list[str]] = mapped_column(JSON, default=list)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="api_keys")
    user: Mapped["User"] = relationship()
    usage_logs: Mapped[list["APIUsageLog"]] = relationship(back_populates="api_key", cascade="all, delete-orphan")


class APIUsageLog(Base):
    __tablename__ = "api_usage_logs"
    __table_args__ = (
        Index("ix_api_usage_logs_api_key_id", "api_key_id"),
        Index("ix_api_usage_logs_created_at", "created_at"),
        Index("ix_api_usage_logs_org_created", "organization_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    api_key_id: Mapped[int] = mapped_column(ForeignKey("api_keys.id"), index=True)
    
    # Request details
    endpoint: Mapped[str] = mapped_column(String(255), index=True)
    method: Mapped[str] = mapped_column(String(10), index=True)
    status_code: Mapped[int] = mapped_column(Integer, index=True)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    
    # Request metadata
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    request_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    
    # Relationships
    api_key: Mapped["APIKey"] = relationship(back_populates="usage_logs")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_org_created", "organization_id", "created_at"),
        Index("ix_audit_logs_user_id", "user_id"),
        Index("ix_audit_logs_entity", "entity_type", "entity_id"),
        Index("ix_audit_logs_action", "action"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    
    # Action details
    action: Mapped[str] = mapped_column(String(100), index=True)
    entity_type: Mapped[str] = mapped_column(String(100), index=True)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    
    # Changes
    changes: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    old_values: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    new_values: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    # Context
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    session_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Metadata
    metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    
    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="audit_logs")
    user: Mapped["User | None"] = relationship()


class UsageMetric(Base):
    __tablename__ = "usage_metrics"
    __table_args__ = (
        Index("ix_usage_metrics_org_type", "organization_id", "metric_type"),
        Index("ix_usage_metrics_recorded_at", "recorded_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    
    # Metric details
    metric_type: Mapped[str] = mapped_column(String(50), index=True)
    value: Mapped[float] = mapped_column(Float, default=0.0)
    unit: Mapped[str] = mapped_column(String(50), default="")
    
    # Period
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    
    # Metadata
    metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    
    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="usage_metrics")


class FeatureFlag(Base):
    __tablename__ = "feature_flags"
    __table_args__ = (
        UniqueConstraint("organization_id", "workspace_id", "feature_key", name="uq_feature_flag"),
        Index("ix_feature_flags_org_workspace", "organization_id", "workspace_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    workspace_id: Mapped[int | None] = mapped_column(ForeignKey("workspaces.id"), nullable=True, index=True)
    
    # Feature details
    feature_key: Mapped[str] = mapped_column(String(100), index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    
    # Conditions
    conditions: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    
    # Metadata
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    organization: Mapped["Organization"] = relationship()
    workspace: Mapped["Workspace | None"] = relationship()


class Invitation(Base):
    __tablename__ = "invitations"
    __table_args__ = (
        Index("ix_invitations_email", "email"),
        Index("ix_invitations_token", "token", unique=True),
        Index("ix_invitations_org_id", "organization_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    workspace_id: Mapped[int | None] = mapped_column(ForeignKey("workspaces.id"), nullable=True, index=True)
    
    # Invitation details
    email: Mapped[str] = mapped_column(String(255), index=True)
    token: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    role: Mapped[MemberRole] = mapped_column(Enum(MemberRole), default=MemberRole.member)
    
    # Status
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    invited_by: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    organization: Mapped["Organization"] = relationship()
    workspace: Mapped["Workspace | None"] = relationship()
    inviter: Mapped["User"] = relationship(foreign_keys=[invited_by])