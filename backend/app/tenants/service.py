import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.tenants.models import (
    Organization,
    Workspace,
    OrganizationMember,
    WorkspaceMember,
    BrandingConfig,
    Subscription,
    APIKey,
    AuditLog,
    UsageMetric,
    FeatureFlag,
    Invitation,
    OrganizationStatus,
    SubscriptionTier,
    WorkspaceType,
    MemberRole,
)
from app.tenants.schemas import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    OrganizationWithStats,
    WorkspaceCreate,
    WorkspaceUpdate,
    WorkspaceResponse,
    WorkspaceWithStats,
    MemberCreate,
    MemberUpdate,
    MemberResponse,
    WorkspaceMemberCreate,
    WorkspaceMemberUpdate,
    WorkspaceMemberResponse,
    BrandingConfigCreate,
    BrandingConfigUpdate,
    BrandingConfigResponse,
    SubscriptionCreate,
    SubscriptionUpdate,
    SubscriptionResponse,
    APIKeyCreate,
    APIKeyUpdate,
    APIKeyResponse,
    APIKeyWithSecret,
    FeatureFlagCreate,
    FeatureFlagUpdate,
    FeatureFlagResponse,
    InvitationCreate,
    InvitationResponse,
    UsageMetricCreate,
    UsageMetricResponse,
    AuditLogCreate,
    AuditLogResponse,
    AuditLogFilter,
    PaginatedResponse,
    OrganizationStats,
    TenantHealth,
)
from app.models import User


class TenantService:
    """Service layer for tenant management operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ──────────────────────────────────────────────
    # Organization Management
    # ──────────────────────────────────────────────
    
    async def create_organization(
        self,
        org_data: OrganizationCreate,
        created_by: int,
    ) -> Organization:
        """Create a new organization."""
        # Check if slug already exists
        existing = await self.get_organization_by_slug(org_data.slug)
        if existing:
            raise ValueError(f"Organization with slug '{org_data.slug}' already exists")
        
        organization = Organization(
            **org_data.model_dump(),
            created_by=created_by,
        )
        self.db.add(organization)
        await self.db.flush()
        
        # Create default workspace
        await self.create_workspace(
            WorkspaceCreate(
                organization_id=organization.id,
                name="General",
                description="Default workspace",
                workspace_type=WorkspaceType.general,
                is_default=True,
            ),
            created_by=created_by,
        )
        
        # Create branding config
        branding = BrandingConfig(organization_id=organization.id)
        self.db.add(branding)
        
        # Create subscription
        subscription = Subscription(organization_id=organization.id)
        self.db.add(subscription)
        
        await self.db.commit()
        await self.db.refresh(organization)
        
        return organization
    
    async def get_organization(self, organization_id: int) -> Optional[Organization]:
        """Get organization by ID."""
        result = await self.db.execute(
            select(Organization).where(Organization.id == organization_id)
        )
        return result.scalar_one_or_none()
    
    async def get_organization_by_slug(self, slug: str) -> Optional[Organization]:
        """Get organization by slug."""
        result = await self.db.execute(
            select(Organization).where(Organization.slug == slug)
        )
        return result.scalar_one_or_none()
    
    async def list_organizations(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[OrganizationStatus] = None,
        search: Optional[str] = None,
    ) -> tuple[List[Organization], int]:
        """List organizations with filtering."""
        query = select(Organization)
        
        if status:
            query = query.where(Organization.status == status)
        
        if search:
            query = query.where(
                or_(
                    Organization.name.ilike(f"%{search}%"),
                    Organization.slug.ilike(f"%{search}%"),
                )
            )
        
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()
        
        # Get paginated results
        query = query.order_by(Organization.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        organizations = result.scalars().all()
        
        return list(organizations), total
    
    async def update_organization(
        self,
        organization_id: int,
        org_data: OrganizationUpdate,
    ) -> Optional[Organization]:
        """Update organization."""
        organization = await self.get_organization(organization_id)
        if not organization:
            return None
        
        update_data = org_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(organization, field, value)
        
        await self.db.commit()
        await self.db.refresh(organization)
        
        return organization
    
    async def delete_organization(self, organization_id: int) -> bool:
        """Archive organization (soft delete)."""
        organization = await self.get_organization(organization_id)
        if not organization:
            return False
        
        organization.status = OrganizationStatus.archived
        organization.archived_at = datetime.now(timezone.utc)
        
        await self.db.commit()
        return True
    
    async def suspend_organization(self, organization_id: int) -> bool:
        """Suspend organization."""
        organization = await self.get_organization(organization_id)
        if not organization:
            return False
        
        organization.status = OrganizationStatus.suspended
        await self.db.commit()
        return True
    
    async def get_organization_with_stats(
        self,
        organization_id: int,
    ) -> Optional[OrganizationWithStats]:
        """Get organization with statistics."""
        organization = await self.get_organization(organization_id)
        if not organization:
            return None
        
        # Get member count
        member_count_result = await self.db.execute(
            select(func.count(OrganizationMember.id))
            .where(OrganizationMember.organization_id == organization_id)
            .where(OrganizationMember.is_active == True)
        )
        member_count = member_count_result.scalar_one()
        
        # Get workspace count
        workspace_count_result = await self.db.execute(
            select(func.count(Workspace.id))
            .where(Workspace.organization_id == organization_id)
            .where(Workspace.archived_at.is_(None))
        )
        workspace_count = workspace_count_result.scalar_one()
        
        # Get usage metrics
        storage_result = await self.db.execute(
            select(func.sum(UsageMetric.value))
            .where(UsageMetric.organization_id == organization_id)
            .where(UsageMetric.metric_type == "storage_gb")
        )
        storage_used_gb = storage_result.scalar_one() or 0.0
        
        return OrganizationWithStats(
            **organization.__dict__,
            user_count=member_count,
            workspace_count=workspace_count,
            active_user_count=member_count,
            storage_used_gb=storage_used_gb,
        )
    
    async def get_organization_stats(self) -> OrganizationStats:
        """Get platform-wide organization statistics."""
        # Total organizations
        total_result = await self.db.execute(select(func.count(Organization.id)))
        total_organizations = total_result.scalar_one()
        
        # Active organizations
        active_result = await self.db.execute(
            select(func.count(Organization.id)).where(Organization.status == OrganizationStatus.active)
        )
        active_organizations = active_result.scalar_one()
        
        # Suspended organizations
        suspended_result = await self.db.execute(
            select(func.count(Organization.id)).where(Organization.status == OrganizationStatus.suspended)
        )
        suspended_organizations = suspended_result.scalar_one()
        
        # Archived organizations
        archived_result = await self.db.execute(
            select(func.count(Organization.id)).where(Organization.status == OrganizationStatus.archived)
        )
        archived_organizations = archived_result.scalar_one()
        
        # Total users (unique across all orgs)
        users_result = await self.db.execute(select(func.count(User.id)))
        total_users = users_result.scalar_one()
        
        # Total workspaces
        workspaces_result = await self.db.execute(select(func.count(Workspace.id)))
        total_workspaces = workspaces_result.scalar_one()
        
        # Total storage
        storage_result = await self.db.execute(
            select(func.sum(UsageMetric.value))
            .where(UsageMetric.metric_type == "storage_gb")
        )
        total_storage_gb = storage_result.scalar_one() or 0.0
        
        # Today's API calls
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        api_calls_result = await self.db.execute(
            select(func.count(APIUsageLog.id))
            .where(APIUsageLog.created_at >= today_start)
        )
        total_api_calls_today = api_calls_result.scalar_one()
        
        # Today's AI requests
        ai_requests_result = await self.db.execute(
            select(func.sum(UsageMetric.value))
            .where(UsageMetric.metric_type == "ai_requests")
            .where(UsageMetric.period_start >= today_start)
        )
        total_ai_requests_today = int(ai_requests_result.scalar_one() or 0)
        
        return OrganizationStats(
            total_organizations=total_organizations,
            active_organizations=active_organizations,
            suspended_organizations=suspended_organizations,
            archived_organizations=archived_organizations,
            total_users=total_users,
            total_workspaces=total_workspaces,
            total_storage_gb=total_storage_gb,
            total_api_calls_today=total_api_calls_today,
            total_ai_requests_today=total_ai_requests_today,
        )
    
    # ──────────────────────────────────────────────
    # Workspace Management
    # ──────────────────────────────────────────────
    
    async def create_workspace(
        self,
        workspace_data: WorkspaceCreate,
        created_by: int,
    ) -> Workspace:
        """Create a new workspace."""
        # Check if organization exists
        organization = await self.get_organization(workspace_data.organization_id)
        if not organization:
            raise ValueError("Organization not found")
        
        # Check workspace limit
        workspace_count_result = await self.db.execute(
            select(func.count(Workspace.id))
            .where(Workspace.organization_id == workspace_data.organization_id)
            .where(Workspace.archived_at.is_(None))
        )
        current_count = workspace_count_result.scalar_one()
        if current_count >= organization.max_workspaces:
            raise ValueError(f"Workspace limit reached ({organization.max_workspaces})")
        
        # Check if name already exists in organization
        existing = await self.db.execute(
            select(Workspace)
            .where(Workspace.organization_id == workspace_data.organization_id)
            .where(Workspace.name == workspace_data.name)
            .where(Workspace.archived_at.is_(None))
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Workspace with name '{workspace_data.name}' already exists")
        
        workspace = Workspace(
            **workspace_data.model_dump(),
            created_by=created_by,
        )
        self.db.add(workspace)
        await self.db.flush()
        
        await self.db.commit()
        await self.db.refresh(workspace)
        
        return workspace
    
    async def get_workspace(self, workspace_id: int) -> Optional[Workspace]:
        """Get workspace by ID."""
        result = await self.db.execute(
            select(Workspace).where(Workspace.id == workspace_id)
        )
        return result.scalar_one_or_none()
    
    async def list_workspaces(
        self,
        organization_id: int,
        skip: int = 0,
        limit: int = 100,
        workspace_type: Optional[WorkspaceType] = None,
    ) -> tuple[List[Workspace], int]:
        """List workspaces for an organization."""
        query = select(Workspace).where(Workspace.organization_id == organization_id)
        
        if workspace_type:
            query = query.where(Workspace.workspace_type == workspace_type)
        
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()
        
        # Get paginated results
        query = query.order_by(Workspace.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        workspaces = result.scalars().all()
        
        return list(workspaces), total
    
    async def update_workspace(
        self,
        workspace_id: int,
        workspace_data: WorkspaceUpdate,
    ) -> Optional[Workspace]:
        """Update workspace."""
        workspace = await self.get_workspace(workspace_id)
        if not workspace:
            return None
        
        update_data = workspace_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(workspace, field, value)
        
        await self.db.commit()
        await self.db.refresh(workspace)
        
        return workspace
    
    async def delete_workspace(self, workspace_id: int) -> bool:
        """Archive workspace (soft delete)."""
        workspace = await self.get_workspace(workspace_id)
        if not workspace:
            return False
        
        if workspace.is_default:
            raise ValueError("Cannot delete default workspace")
        
        workspace.archived_at = datetime.now(timezone.utc)
        await self.db.commit()
        return True
    
    async def get_workspace_with_stats(
        self,
        workspace_id: int,
    ) -> Optional[WorkspaceWithStats]:
        """Get workspace with statistics."""
        workspace = await self.get_workspace(workspace_id)
        if not workspace:
            return None
        
        # Get member count
        member_count_result = await self.db.execute(
            select(func.count(WorkspaceMember.id))
            .where(WorkspaceMember.workspace_id == workspace_id)
            .where(WorkspaceMember.is_active == True)
        )
        member_count = member_count_result.scalar_one()
        
        return WorkspaceWithStats(
            **workspace.__dict__,
            member_count=member_count,
        )
    
    # ──────────────────────────────────────────────
    # Organization Member Management
    # ──────────────────────────────────────────────
    
    async def add_organization_member(
        self,
        member_data: MemberCreate,
    ) -> OrganizationMember:
        """Add member to organization."""
        # Check if organization exists
        organization = await self.get_organization(member_data.organization_id)
        if not organization:
            raise ValueError("Organization not found")
        
        # Check if user exists
        user_result = await self.db.execute(
            select(User).where(User.id == member_data.user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")
        
        # Check if already a member
        existing = await self.db.execute(
            select(OrganizationMember)
            .where(OrganizationMember.organization_id == member_data.organization_id)
            .where(OrganizationMember.user_id == member_data.user_id)
        )
        if existing.scalar_one_or_none():
            raise ValueError("User is already a member of this organization")
        
        # Check user limit
        member_count_result = await self.db.execute(
            select(func.count(OrganizationMember.id))
            .where(OrganizationMember.organization_id == member_data.organization_id)
            .where(OrganizationMember.is_active == True)
        )
        current_count = member_count_result.scalar_one()
        if current_count >= organization.max_users:
            raise ValueError(f"User limit reached ({organization.max_users})")
        
        member = OrganizationMember(
            **member_data.model_dump(),
            joined_at=datetime.now(timezone.utc),
        )
        self.db.add(member)
        await self.db.commit()
        await self.db.refresh(member)
        
        return member
    
    async def update_organization_member(
        self,
        organization_id: int,
        user_id: int,
        member_data: MemberUpdate,
    ) -> Optional[OrganizationMember]:
        """Update organization member."""
        result = await self.db.execute(
            select(OrganizationMember)
            .where(OrganizationMember.organization_id == organization_id)
            .where(OrganizationMember.user_id == user_id)
        )
        member = result.scalar_one_or_none()
        if not member:
            return None
        
        update_data = member_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(member, field, value)
        
        await self.db.commit()
        await self.db.refresh(member)
        
        return member
    
    async def remove_organization_member(
        self,
        organization_id: int,
        user_id: int,
    ) -> bool:
        """Remove member from organization."""
        result = await self.db.execute(
            select(OrganizationMember)
            .where(OrganizationMember.organization_id == organization_id)
            .where(OrganizationMember.user_id == user_id)
        )
        member = result.scalar_one_or_none()
        if not member:
            return False
        
        member.is_active = False
        await self.db.commit()
        return True
    
    async def list_organization_members(
        self,
        organization_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[List[OrganizationMember], int]:
        """List organization members."""
        query = select(OrganizationMember).where(
            OrganizationMember.organization_id == organization_id
        )
        
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()
        
        # Get paginated results with user details
        query = (
            query.options(selectinload(OrganizationMember.user))
            .order_by(OrganizationMember.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        members = result.scalars().all()
        
        return list(members), total
    
    # ──────────────────────────────────────────────
    # Workspace Member Management
    # ──────────────────────────────────────────────
    
    async def add_workspace_member(
        self,
        member_data: WorkspaceMemberCreate,
    ) -> WorkspaceMember:
        """Add member to workspace."""
        # Check if workspace exists
        workspace = await self.get_workspace(member_data.workspace_id)
        if not workspace:
            raise ValueError("Workspace not found")
        
        # Check if user exists
        user_result = await self.db.execute(
            select(User).where(User.id == member_data.user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")
        
        # Check if already a member
        existing = await self.db.execute(
            select(WorkspaceMember)
            .where(WorkspaceMember.workspace_id == member_data.workspace_id)
            .where(WorkspaceMember.user_id == member_data.user_id)
        )
        if existing.scalar_one_or_none():
            raise ValueError("User is already a member of this workspace")
        
        member = WorkspaceMember(
            **member_data.model_dump(),
            joined_at=datetime.now(timezone.utc),
        )
        self.db.add(member)
        await self.db.commit()
        await self.db.refresh(member)
        
        return member
    
    async def update_workspace_member(
        self,
        workspace_id: int,
        user_id: int,
        member_data: WorkspaceMemberUpdate,
    ) -> Optional[WorkspaceMember]:
        """Update workspace member."""
        result = await self.db.execute(
            select(WorkspaceMember)
            .where(WorkspaceMember.workspace_id == workspace_id)
            .where(WorkspaceMember.user_id == user_id)
        )
        member = result.scalar_one_or_none()
        if not member:
            return None
        
        update_data = member_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(member, field, value)
        
        await self.db.commit()
        await self.db.refresh(member)
        
        return member
    
    async def remove_workspace_member(
        self,
        workspace_id: int,
        user_id: int,
    ) -> bool:
        """Remove member from workspace."""
        result = await self.db.execute(
            select(WorkspaceMember)
            .where(WorkspaceMember.workspace_id == workspace_id)
            .where(WorkspaceMember.user_id == user_id)
        )
        member = result.scalar_one_or_none()
        if not member:
            return False
        
        member.is_active = False
        await self.db.commit()
        return True
    
    async def list_workspace_members(
        self,
        workspace_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[List[WorkspaceMember], int]:
        """List workspace members."""
        query = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id
        )
        
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()
        
        # Get paginated results with user details
        query = (
            query.options(selectinload(WorkspaceMember.user))
            .order_by(WorkspaceMember.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        members = result.scalars().all()
        
        return list(members), total
    
    # ──────────────────────────────────────────────
    # Branding Management
    # ──────────────────────────────────────────────
    
    async def get_branding_config(
        self,
        organization_id: int,
    ) -> Optional[BrandingConfig]:
        """Get branding configuration for organization."""
        result = await self.db.execute(
            select(BrandingConfig).where(BrandingConfig.organization_id == organization_id)
        )
        return result.scalar_one_or_none()
    
    async def create_branding_config(
        self,
        branding_data: BrandingConfigCreate,
    ) -> BrandingConfig:
        """Create branding configuration."""
        branding = BrandingConfig(**branding_data.model_dump())
        self.db.add(branding)
        await self.db.commit()
        await self.db.refresh(branding)
        
        return branding
    
    async def update_branding_config(
        self,
        organization_id: int,
        branding_data: BrandingConfigUpdate,
    ) -> Optional[BrandingConfig]:
        """Update branding configuration."""
        branding = await self.get_branding_config(organization_id)
        if not branding:
            return None
        
        update_data = branding_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(branding, field, value)
        
        await self.db.commit()
        await self.db.refresh(branding)
        
        return branding
    
    # ──────────────────────────────────────────────
    # Subscription Management
    # ──────────────────────────────────────────────
    
    async def get_subscription(
        self,
        organization_id: int,
    ) -> Optional[Subscription]:
        """Get subscription for organization."""
        result = await self.db.execute(
            select(Subscription).where(Subscription.organization_id == organization_id)
        )
        return result.scalar_one_or_none()
    
    async def create_subscription(
        self,
        subscription_data: SubscriptionCreate,
    ) -> Subscription:
        """Create subscription."""
        subscription = Subscription(**subscription_data.model_dump())
        self.db.add(subscription)
        await self.db.commit()
        await self.db.refresh(subscription)
        
        return subscription
    
    async def update_subscription(
        self,
        organization_id: int,
        subscription_data: SubscriptionUpdate,
    ) -> Optional[Subscription]:
        """Update subscription."""
        subscription = await self.get_subscription(organization_id)
        if not subscription:
            return None
        
        update_data = subscription_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(subscription, field, value)
        
        await self.db.commit()
        await self.db.refresh(subscription)
        
        return subscription
    
    # ──────────────────────────────────────────────
    # API Key Management
    # ──────────────────────────────────────────────
    
    async def create_api_key(
        self,
        api_key_data: APIKeyCreate,
    ) -> APIKeyWithSecret:
        """Create API key."""
        # Generate secure random key
        secret = self._generate_api_key()
        key_hash = self._hash_api_key(secret)
        key_prefix = secret[:8]
        
        api_key = APIKey(
            **api_key_data.model_dump(),
            key_hash=key_hash,
            key_prefix=key_prefix,
        )
        self.db.add(api_key)
        await self.db.commit()
        await self.db.refresh(api_key)
        
        return APIKeyWithSecret(
            **api_key.__dict__,
            secret=secret,
        )
    
    async def get_api_key(self, api_key_id: int) -> Optional[APIKey]:
        """Get API key by ID."""
        result = await self.db.execute(
            select(APIKey).where(APIKey.id == api_key_id)
        )
        return result.scalar_one_or_none()
    
    async def get_api_key_by_hash(self, key_hash: str) -> Optional[APIKey]:
        """Get API key by hash."""
        result = await self.db.execute(
            select(APIKey).where(APIKey.key_hash == key_hash)
        )
        return result.scalar_one_or_none()
    
    async def list_api_keys(
        self,
        organization_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[List[APIKey], int]:
        """List API keys for organization."""
        query = select(APIKey).where(APIKey.organization_id == organization_id)
        
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()
        
        # Get paginated results
        query = query.order_by(APIKey.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        api_keys = result.scalars().all()
        
        return list(api_keys), total
    
    async def update_api_key(
        self,
        api_key_id: int,
        api_key_data: APIKeyUpdate,
    ) -> Optional[APIKey]:
        """Update API key."""
        api_key = await self.get_api_key(api_key_id)
        if not api_key:
            return None
        
        update_data = api_key_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(api_key, field, value)
        
        await self.db.commit()
        await self.db.refresh(api_key)
        
        return api_key
    
    async def revoke_api_key(self, api_key_id: int) -> bool:
        """Revoke API key."""
        api_key = await self.get_api_key(api_key_id)
        if not api_key:
            return False
        
        api_key.is_active = False
        api_key.revoked_at = datetime.now(timezone.utc)
        
        await self.db.commit()
        return True
    
    def _generate_api_key(self) -> str:
        """Generate secure API key."""
        alphabet = string.ascii_letters + string.digits
        return "prism_" + "".join(secrets.choice(alphabet) for _ in range(32))
    
    def _hash_api_key(self, key: str) -> str:
        """Hash API key for storage."""
        # In production, use proper hashing like bcrypt
        import hashlib
        return hashlib.sha256(key.encode()).hexdigest()
    
    # ──────────────────────────────────────────────
    # Feature Flag Management
    # ──────────────────────────────────────────────
    
    async def create_feature_flag(
        self,
        feature_flag_data: FeatureFlagCreate,
    ) -> FeatureFlag:
        """Create feature flag."""
        feature_flag = FeatureFlag(**feature_flag_data.model_dump())
        self.db.add(feature_flag)
        await self.db.commit()
        await self.db.refresh(feature_flag)
        
        return feature_flag
    
    async def get_feature_flag(
        self,
        organization_id: int,
        feature_key: str,
        workspace_id: Optional[int] = None,
    ) -> Optional[FeatureFlag]:
        """Get feature flag."""
        query = select(FeatureFlag).where(
            FeatureFlag.organization_id == organization_id,
            FeatureFlag.feature_key == feature_key,
        )
        
        if workspace_id:
            query = query.where(FeatureFlag.workspace_id == workspace_id)
        else:
            query = query.where(FeatureFlag.workspace_id.is_(None))
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def list_feature_flags(
        self,
        organization_id: int,
        workspace_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[List[FeatureFlag], int]:
        """List feature flags."""
        query = select(FeatureFlag).where(FeatureFlag.organization_id == organization_id)
        
        if workspace_id:
            query = query.where(FeatureFlag.workspace_id == workspace_id)
        else:
            query = query.where(FeatureFlag.workspace_id.is_(None))
        
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()
        
        # Get paginated results
        query = query.order_by(FeatureFlag.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        feature_flags = result.scalars().all()
        
        return list(feature_flags), total
    
    async def update_feature_flag(
        self,
        feature_flag_id: int,
        feature_flag_data: FeatureFlagUpdate,
    ) -> Optional[FeatureFlag]:
        """Update feature flag."""
        result = await self.db.execute(
            select(FeatureFlag).where(FeatureFlag.id == feature_flag_id)
        )
        feature_flag = result.scalar_one_or_none()
        if not feature_flag:
            return None
        
        update_data = feature_flag_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(feature_flag, field, value)
        
        await self.db.commit()
        await self.db.refresh(feature_flag)
        
        return feature_flag
    
    async def delete_feature_flag(self, feature_flag_id: int) -> bool:
        """Delete feature flag."""
        result = await self.db.execute(
            select(FeatureFlag).where(FeatureFlag.id == feature_flag_id)
        )
        feature_flag = result.scalar_one_or_none()
        if not feature_flag:
            return False
        
        await self.db.delete(feature_flag)
        await self.db.commit()
        return True
    
    async def is_feature_enabled(
        self,
        organization_id: int,
        feature_key: str,
        workspace_id: Optional[int] = None,
    ) -> bool:
        """Check if feature is enabled."""
        # Check workspace-level flag first
        if workspace_id:
            workspace_flag = await self.get_feature_flag(organization_id, feature_key, workspace_id)
            if workspace_flag:
                if workspace_flag.expires_at and workspace_flag.expires_at < datetime.now(timezone.utc):
                    return False
                return workspace_flag.enabled
        
        # Check organization-level flag
        org_flag = await self.get_feature_flag(organization_id, feature_key, None)
        if org_flag:
            if org_flag.expires_at and org_flag.expires_at < datetime.now(timezone.utc):
                return False
            return org_flag.enabled
        
        return False
    
    # ──────────────────────────────────────────────
    # Invitation Management
    # ──────────────────────────────────────────────
    
    async def create_invitation(
        self,
        invitation_data: InvitationCreate,
    ) -> Invitation:
        """Create invitation."""
        # Generate secure token
        token = self._generate_invitation_token()
        
        # Set expiration (7 days from now)
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        invitation = Invitation(
            **invitation_data.model_dump(),
            token=token,
            expires_at=expires_at,
        )
        self.db.add(invitation)
        await self.db.commit()
        await self.db.refresh(invitation)
        
        return invitation
    
    async def get_invitation_by_token(self, token: str) -> Optional[Invitation]:
        """Get invitation by token."""
        result = await self.db.execute(
            select(Invitation).where(Invitation.token == token)
        )
        return result.scalar_one_or_none()
    
    async def accept_invitation(self, token: str, user_id: int) -> Optional[Invitation]:
        """Accept invitation."""
        invitation = await self.get_invitation_by_token(token)
        if not invitation:
            return None
        
        if invitation.status != "pending":
            return None
        
        if invitation.expires_at < datetime.now(timezone.utc):
            return None
        
        invitation.status = "accepted"
        invitation.accepted_at = datetime.now(timezone.utc)
        
        await self.db.commit()
        await self.db.refresh(invitation)
        
        return invitation
    
    def _generate_invitation_token(self) -> str:
        """Generate secure invitation token."""
        return secrets.token_urlsafe(32)
    
    # ──────────────────────────────────────────────
    # Audit Logging
    # ──────────────────────────────────────────────
    
    async def create_audit_log(
        self,
        audit_data: AuditLogCreate,
    ) -> AuditLog:
        """Create audit log entry."""
        audit_log = AuditLog(**audit_data.model_dump())
        self.db.add(audit_log)
        await self.db.commit()
        await self.db.refresh(audit_log)
        
        return audit_log
    
    async def list_audit_logs(
        self,
        filter_data: AuditLogFilter,
    ) -> tuple[List[AuditLog], int]:
        """List audit logs with filtering."""
        query = select(AuditLog)
        
        if filter_data.organization_id:
            query = query.where(AuditLog.organization_id == filter_data.organization_id)
        
        if filter_data.user_id:
            query = query.where(AuditLog.user_id == filter_data.user_id)
        
        if filter_data.action:
            query = query.where(AuditLog.action == filter_data.action)
        
        if filter_data.entity_type:
            query = query.where(AuditLog.entity_type == filter_data.entity_type)
        
        if filter_data.entity_id:
            query = query.where(AuditLog.entity_id == filter_data.entity_id)
        
        if filter_data.start_date:
            query = query.where(AuditLog.created_at >= filter_data.start_date)
        
        if filter_data.end_date:
            query = query.where(AuditLog.created_at <= filter_data.end_date)
        
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()
        
        # Get paginated results
        query = query.order_by(AuditLog.created_at.desc()).offset(filter_data.offset).limit(filter_data.limit)
        result = await self.db.execute(query)
        audit_logs = result.scalars().all()
        
        return list(audit_logs), total
    
    # ──────────────────────────────────────────────
    # Usage Metrics
    # ──────────────────────────────────────────────
    
    async def record_usage_metric(
        self,
        metric_data: UsageMetricCreate,
    ) -> UsageMetric:
        """Record usage metric."""
        metric = UsageMetric(**metric_data.model_dump())
        self.db.add(metric)
        await self.db.commit()
        await self.db.refresh(metric)
        
        return metric
    
    async def get_usage_metrics(
        self,
        organization_id: int,
        metric_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[UsageMetric]:
        """Get usage metrics for organization."""
        query = select(UsageMetric).where(UsageMetric.organization_id == organization_id)
        
        if metric_type:
            query = query.where(UsageMetric.metric_type == metric_type)
        
        if start_date:
            query = query.where(UsageMetric.period_start >= start_date)
        
        if end_date:
            query = query.where(UsageMetric.period_end <= end_date)
        
        query = query.order_by(UsageMetric.period_start.desc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    # ──────────────────────────────────────────────
    # Health Check
    # ──────────────────────────────────────────────
    
    async def get_tenant_health(
        self,
        organization_id: int,
    ) -> Optional[TenantHealth]:
        """Get tenant health metrics."""
        organization = await self.get_organization(organization_id)
        if not organization:
            return None
        
        # Get member count
        member_count_result = await self.db.execute(
            select(func.count(OrganizationMember.id))
            .where(OrganizationMember.organization_id == organization_id)
            .where(OrganizationMember.is_active == True)
        )
        user_count = member_count_result.scalar_one()
        
        # Get workspace count
        workspace_count_result = await self.db.execute(
            select(func.count(Workspace.id))
            .where(Workspace.organization_id == organization_id)
            .where(Workspace.archived_at.is_(None))
        )
        workspace_count = workspace_count_result.scalar_one()
        
        # Get storage usage
        storage_result = await self.db.execute(
            select(func.sum(UsageMetric.value))
            .where(UsageMetric.organization_id == organization_id)
            .where(UsageMetric.metric_type == "storage_gb")
        )
        storage_used_gb = storage_result.scalar_one() or 0.0
        
        # Get API calls this month
        month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        api_calls_result = await self.db.execute(
            select(func.count(APIUsageLog.id))
            .where(APIUsageLog.organization_id == organization_id)
            .where(APIUsageLog.created_at >= month_start)
        )
        api_calls_this_month = api_calls_result.scalar_one()
        
        # Get AI requests this month
        ai_requests_result = await self.db.execute(
            select(func.sum(UsageMetric.value))
            .where(UsageMetric.organization_id == organization_id)
            .where(UsageMetric.metric_type == "ai_requests")
            .where(UsageMetric.period_start >= month_start)
        )
        ai_requests_this_month = int(ai_requests_result.scalar_one() or 0)
        
        # Get subscription status
        subscription = await self.get_subscription(organization_id)
        subscription_status = subscription.status if subscription else "none"
        
        # Calculate health score (simple algorithm)
        health_score = 100.0
        
        # Deduct points for quota usage
        if storage_used_gb > 0:
            storage_percentage = (storage_used_gb / organization.max_storage_gb) * 100
            if storage_percentage > 80:
                health_score -= 10
        
        if api_calls_this_month > 0:
            api_percentage = (api_calls_this_month / organization.max_api_calls_per_month) * 100
            if api_percentage > 80:
                health_score -= 10
        
        if ai_requests_this_month > 0:
            ai_percentage = (ai_requests_this_month / organization.max_ai_requests_per_month) * 100
            if ai_percentage > 80:
                health_score -= 10
        
        # Deduct for status
        if organization.status == OrganizationStatus.suspended:
            health_score = 0.0
        elif organization.status == OrganizationStatus.archived:
            health_score = 0.0
        
        # Get last activity
        last_activity_result = await self.db.execute(
            select(AuditLog.created_at)
            .where(AuditLog.organization_id == organization_id)
            .order_by(AuditLog.created_at.desc())
            .limit(1)
        )
        last_activity = last_activity_result.scalar_one_or_none()
        
        return TenantHealth(
            organization_id=organization_id,
            organization_name=organization.name,
            status=organization.status,
            user_count=user_count,
            workspace_count=workspace_count,
            storage_used_gb=storage_used_gb,
            api_calls_this_month=api_calls_this_month,
            ai_requests_this_month=ai_requests_this_month,
            subscription_status=subscription_status,
            health_score=health_score,
            last_activity=last_activity,
        )