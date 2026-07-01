from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from enum import Enum


# Enums
class OrganizationStatus(str, Enum):
    active = "active"
    suspended = "suspended"
    archived = "archived"
    pending = "pending"


class SubscriptionTier(str, Enum):
    trial = "trial"
    standard = "standard"
    professional = "professional"
    enterprise = "enterprise"
    custom = "custom"


class WorkspaceType(str, Enum):
    general = "general"
    finance = "finance"
    hr = "hr"
    sales = "sales"
    operations = "operations"
    executive = "executive"
    data_science = "data_science"
    custom = "custom"


class MemberRole(str, Enum):
    owner = "owner"
    admin = "admin"
    member = "member"
    viewer = "viewer"


# Organization Schemas
class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100, pattern="^[a-z0-9-]+$")
    description: str = Field(default="", max_length=5000)
    industry: str = Field(default="", max_length=100)
    timezone: str = Field(default="UTC", max_length=50)
    locale: str = Field(default="en-US", max_length=10)
    subscription_tier: SubscriptionTier = Field(default=SubscriptionTier.trial)
    logo_url: str = Field(default="", max_length=500)
    primary_color: str = Field(default="#007bff", max_length=7)
    secondary_color: str = Field(default="#6c757d", max_length=7)
    custom_domain: str = Field(default="", max_length=255)
    max_users: int = Field(default=10, ge=1)
    max_workspaces: int = Field(default=5, ge=1)
    max_storage_gb: float = Field(default=10.0, ge=0.1)
    max_ai_requests_per_month: int = Field(default=1000, ge=0)
    max_api_calls_per_month: int = Field(default=10000, ge=0)
    settings: Dict[str, Any] = Field(default_factory=dict)
    feature_flags: Dict[str, Any] = Field(default_factory=dict)


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    industry: Optional[str] = Field(None, max_length=100)
    timezone: Optional[str] = Field(None, max_length=50)
    locale: Optional[str] = Field(None, max_length=10)
    subscription_tier: Optional[SubscriptionTier] = None
    logo_url: Optional[str] = Field(None, max_length=500)
    primary_color: Optional[str] = Field(None, max_length=7)
    secondary_color: Optional[str] = Field(None, max_length=7)
    custom_domain: Optional[str] = Field(None, max_length=255)
    max_users: Optional[int] = Field(None, ge=1)
    max_workspaces: Optional[int] = Field(None, ge=1)
    max_storage_gb: Optional[float] = Field(None, ge=0.1)
    max_ai_requests_per_month: Optional[int] = Field(None, ge=0)
    max_api_calls_per_month: Optional[int] = Field(None, ge=0)
    settings: Optional[Dict[str, Any]] = None
    feature_flags: Optional[Dict[str, Any]] = None
    status: Optional[OrganizationStatus] = None


class OrganizationResponse(OrganizationBase):
    id: int
    status: OrganizationStatus
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime
    archived_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


class OrganizationWithStats(OrganizationResponse):
    user_count: int = 0
    workspace_count: int = 0
    active_user_count: int = 0
    storage_used_gb: float = 0.0
    ai_requests_this_month: int = 0
    api_calls_this_month: int = 0


# Workspace Schemas
class WorkspaceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(default="", max_length=5000)
    workspace_type: WorkspaceType = Field(default=WorkspaceType.general)
    is_default: bool = Field(default=False)
    is_public: bool = Field(default=False)
    settings: Dict[str, Any] = Field(default_factory=dict)
    feature_flags: Dict[str, Any] = Field(default_factory=dict)


class WorkspaceCreate(WorkspaceBase):
    organization_id: int


class WorkspaceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    workspace_type: Optional[WorkspaceType] = None
    is_default: Optional[bool] = None
    is_public: Optional[bool] = None
    settings: Optional[Dict[str, Any]] = None
    feature_flags: Optional[Dict[str, Any]] = None
    archived_at: Optional[datetime] = None


class WorkspaceResponse(WorkspaceBase):
    id: int
    organization_id: int
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime
    archived_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


class WorkspaceWithStats(WorkspaceResponse):
    member_count: int = 0
    dashboard_count: int = 0
    semantic_model_count: int = 0


# Member Schemas
class MemberBase(BaseModel):
    user_id: int
    role: MemberRole = Field(default=MemberRole.member)
    is_active: bool = Field(default=True)


class MemberCreate(MemberBase):
    organization_id: int
    invited_by: Optional[int] = None


class MemberUpdate(BaseModel):
    role: Optional[MemberRole] = None
    is_active: Optional[bool] = None


class MemberResponse(MemberBase):
    id: int
    organization_id: int
    user_id: int
    invited_by: Optional[int]
    joined_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    # User details
    user_email: Optional[str] = None
    user_full_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class WorkspaceMemberBase(BaseModel):
    user_id: int
    role: MemberRole = Field(default=MemberRole.member)
    is_active: bool = Field(default=True)


class WorkspaceMemberCreate(WorkspaceMemberBase):
    workspace_id: int


class WorkspaceMemberUpdate(BaseModel):
    role: Optional[MemberRole] = None
    is_active: Optional[bool] = None


class WorkspaceMemberResponse(WorkspaceMemberBase):
    id: int
    workspace_id: int
    user_id: int
    joined_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    # User details
    user_email: Optional[str] = None
    user_full_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


# Branding Schemas
class BrandingConfigBase(BaseModel):
    logo_url: str = Field(default="", max_length=500)
    logo_dark_url: str = Field(default="", max_length=500)
    favicon_url: str = Field(default="", max_length=500)
    background_image_url: str = Field(default="", max_length=500)
    primary_color: str = Field(default="#007bff", max_length=7)
    secondary_color: str = Field(default="#6c757d", max_length=7)
    accent_color: str = Field(default="#28a745", max_length=7)
    background_color: str = Field(default="#ffffff", max_length=7)
    text_color: str = Field(default="#212529", max_length=7)
    font_family: str = Field(default="Inter, sans-serif", max_length=100)
    heading_font_family: str = Field(default="Inter, sans-serif", max_length=100)
    login_page_title: str = Field(default="", max_length=255)
    login_page_description: str = Field(default="", max_length=1000)
    login_background_image: str = Field(default="", max_length=500)
    email_header_logo: str = Field(default="", max_length=500)
    email_footer_text: str = Field(default="", max_length=2000)
    custom_css: str = Field(default="", max_length=10000)
    css_variables: Dict[str, Any] = Field(default_factory=dict)


class BrandingConfigCreate(BrandingConfigBase):
    organization_id: int


class BrandingConfigUpdate(BaseModel):
    logo_url: Optional[str] = Field(None, max_length=500)
    logo_dark_url: Optional[str] = Field(None, max_length=500)
    favicon_url: Optional[str] = Field(None, max_length=500)
    background_image_url: Optional[str] = Field(None, max_length=500)
    primary_color: Optional[str] = Field(None, max_length=7)
    secondary_color: Optional[str] = Field(None, max_length=7)
    accent_color: Optional[str] = Field(None, max_length=7)
    background_color: Optional[str] = Field(None, max_length=7)
    text_color: Optional[str] = Field(None, max_length=7)
    font_family: Optional[str] = Field(None, max_length=100)
    heading_font_family: Optional[str] = Field(None, max_length=100)
    login_page_title: Optional[str] = Field(None, max_length=255)
    login_page_description: Optional[str] = Field(None, max_length=1000)
    login_background_image: Optional[str] = Field(None, max_length=500)
    email_header_logo: Optional[str] = Field(None, max_length=500)
    email_footer_text: Optional[str] = Field(None, max_length=2000)
    custom_css: Optional[str] = Field(None, max_length=10000)
    css_variables: Optional[Dict[str, Any]] = None


class BrandingConfigResponse(BrandingConfigBase):
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Subscription Schemas
class SubscriptionPlanBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    tier: SubscriptionTier
    description: str = Field(default="", max_length=5000)
    max_users: int = Field(default=10, ge=1)
    max_workspaces: int = Field(default=5, ge=1)
    max_storage_gb: float = Field(default=10.0, ge=0.1)
    max_ai_requests_per_month: int = Field(default=1000, ge=0)
    max_api_calls_per_month: int = Field(default=10000, ge=0)
    max_scheduled_jobs: int = Field(default=10, ge=0)
    features: Dict[str, Any] = Field(default_factory=dict)
    price_monthly: float = Field(default=0.0, ge=0)
    price_annual: float = Field(default=0.0, ge=0)
    currency: str = Field(default="USD", max_length=3)
    is_active: bool = Field(default=True)
    is_public: bool = Field(default=True)


class SubscriptionPlanCreate(SubscriptionPlanBase):
    pass


class SubscriptionPlanUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    max_users: Optional[int] = Field(None, ge=1)
    max_workspaces: Optional[int] = Field(None, ge=1)
    max_storage_gb: Optional[float] = Field(None, ge=0.1)
    max_ai_requests_per_month: Optional[int] = Field(None, ge=0)
    max_api_calls_per_month: Optional[int] = Field(None, ge=0)
    max_scheduled_jobs: Optional[int] = Field(None, ge=0)
    features: Optional[Dict[str, Any]] = None
    price_monthly: Optional[float] = Field(None, ge=0)
    price_annual: Optional[float] = Field(None, ge=0)
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None


class SubscriptionPlanResponse(SubscriptionPlanBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class SubscriptionBase(BaseModel):
    organization_id: int
    plan_id: Optional[int] = None
    status: str = Field(default="active", max_length=50)
    starts_at: datetime
    expires_at: Optional[datetime] = None
    billing_cycle: str = Field(default="monthly", max_length=50)
    amount: float = Field(default=0.0)
    currency: str = Field(default="USD", max_length=3)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SubscriptionCreate(SubscriptionBase):
    pass


class SubscriptionUpdate(BaseModel):
    plan_id: Optional[int] = None
    status: Optional[str] = Field(None, max_length=50)
    expires_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    billing_cycle: Optional[str] = Field(None, max_length=50)
    amount: Optional[float] = Field(None, ge=0)
    metadata: Optional[Dict[str, Any]] = None


class SubscriptionResponse(SubscriptionBase):
    id: int
    cancelled_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# API Key Schemas
class APIKeyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(default="", max_length=1000)
    scopes: List[str] = Field(default_factory=list)
    expires_at: Optional[datetime] = None


class APIKeyCreate(APIKeyBase):
    organization_id: int
    user_id: int


class APIKeyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    scopes: Optional[List[str]] = None
    is_active: Optional[bool] = None
    expires_at: Optional[datetime] = None


class APIKeyResponse(APIKeyBase):
    id: int
    organization_id: int
    user_id: int
    key_prefix: str
    is_active: bool
    last_used_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    revoked_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


class APIKeyWithSecret(APIKeyResponse):
    secret: str  # Only shown once during creation


# Feature Flag Schemas
class FeatureFlagBase(BaseModel):
    feature_key: str = Field(..., min_length=1, max_length=100)
    enabled: bool = Field(default=False)
    description: str = Field(default="", max_length=1000)
    conditions: Optional[Dict[str, Any]] = None
    expires_at: Optional[datetime] = None


class FeatureFlagCreate(FeatureFlagBase):
    organization_id: int
    workspace_id: Optional[int] = None


class FeatureFlagUpdate(BaseModel):
    enabled: Optional[bool] = None
    description: Optional[str] = Field(None, max_length=1000)
    conditions: Optional[Dict[str, Any]] = None
    expires_at: Optional[datetime] = None


class FeatureFlagResponse(FeatureFlagBase):
    id: int
    organization_id: int
    workspace_id: Optional[int]
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Invitation Schemas
class InvitationBase(BaseModel):
    email: EmailStr
    role: MemberRole = Field(default=MemberRole.member)
    workspace_id: Optional[int] = None


class InvitationCreate(InvitationBase):
    organization_id: int


class InvitationResponse(InvitationBase):
    id: int
    organization_id: int
    token: str
    status: str
    expires_at: datetime
    accepted_at: Optional[datetime]
    invited_by: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class InvitationAccept(BaseModel):
    token: str


# Usage Metric Schemas
class UsageMetricBase(BaseModel):
    metric_type: str = Field(..., min_length=1, max_length=50)
    value: float = Field(default=0.0)
    unit: str = Field(default="", max_length=50)
    period_start: datetime
    period_end: datetime
    metadata: Optional[Dict[str, Any]] = None


class UsageMetricCreate(UsageMetricBase):
    organization_id: int


class UsageMetricResponse(UsageMetricBase):
    id: int
    organization_id: int
    recorded_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Audit Log Schemas
class AuditLogBase(BaseModel):
    action: str = Field(..., min_length=1, max_length=100)
    entity_type: str = Field(..., min_length=1, max_length=100)
    entity_id: Optional[int] = None
    changes: Optional[Dict[str, Any]] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = Field(None, max_length=50)
    user_agent: Optional[str] = Field(None, max_length=500)
    session_id: Optional[str] = Field(None, max_length=255)
    metadata: Optional[Dict[str, Any]] = None


class AuditLogCreate(AuditLogBase):
    organization_id: int
    user_id: Optional[int] = None


class AuditLogResponse(AuditLogBase):
    id: int
    organization_id: int
    user_id: Optional[int]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class AuditLogFilter(BaseModel):
    organization_id: Optional[int] = None
    user_id: Optional[int] = None
    action: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


# Pagination
class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    pages: int


# Statistics
class OrganizationStats(BaseModel):
    total_organizations: int
    active_organizations: int
    suspended_organizations: int
    archived_organizations: int
    total_users: int
    total_workspaces: int
    total_storage_gb: float
    total_api_calls_today: int
    total_ai_requests_today: int


class TenantHealth(BaseModel):
    organization_id: int
    organization_name: str
    status: OrganizationStatus
    user_count: int
    workspace_count: int
    storage_used_gb: float
    api_calls_this_month: int
    ai_requests_this_month: int
    subscription_status: str
    health_score: float
    last_activity: Optional[datetime]