from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.tenants.schemas import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    OrganizationWithStats,
    OrganizationStats,
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
    InvitationAccept,
    AuditLogCreate,
    AuditLogResponse,
    AuditLogFilter,
    PaginatedResponse,
    TenantHealth,
)
from app.tenants.service import TenantService
from app.auth import get_current_user, get_current_active_user
from app.models import User

router = APIRouter(prefix="/api/v1/tenants", tags=["tenants"])


# ──────────────────────────────────────────────
# Organization Management
# ──────────────────────────────────────────────

@router.post("/organizations", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_data: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new organization."""
    try:
        service = TenantService(db)
        organization = await service.create_organization(org_data, current_user.id)
        return organization
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create organization")


@router.get("/organizations", response_model=PaginatedResponse)
async def list_organizations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List organizations with filtering."""
    try:
        from app.tenants.models import OrganizationStatus
        
        service = TenantService(db)
        status_filter = OrganizationStatus(status) if status else None
        organizations, total = await service.list_organizations(
            skip=skip,
            limit=limit,
            status=status_filter,
            search=search,
        )
        
        pages = (total + limit - 1) // limit
        
        return PaginatedResponse(
            items=[OrganizationResponse.model_validate(org) for org in organizations],
            total=total,
            page=skip // limit + 1,
            page_size=limit,
            pages=pages,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list organizations")


@router.get("/organizations/{organization_id}", response_model=OrganizationWithStats)
async def get_organization(
    organization_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get organization by ID with statistics."""
    service = TenantService(db)
    organization = await service.get_organization_with_stats(organization_id)
    if not organization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return organization


@router.put("/organizations/{organization_id}", response_model=OrganizationResponse)
async def update_organization(
    organization_id: int,
    org_data: OrganizationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update organization."""
    try:
        service = TenantService(db)
        organization = await service.update_organization(organization_id, org_data)
        if not organization:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
        return organization
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update organization")


@router.delete("/organizations/{organization_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    organization_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Archive organization (soft delete)."""
    service = TenantService(db)
    success = await service.delete_organization(organization_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return None


@router.post("/organizations/{organization_id}/suspend", response_model=OrganizationResponse)
async def suspend_organization(
    organization_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Suspend organization."""
    service = TenantService(db)
    success = await service.suspend_organization(organization_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    
    organization = await service.get_organization(organization_id)
    return organization


@router.get("/organizations/stats/overview", response_model=OrganizationStats)
async def get_organization_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get platform-wide organization statistics."""
    service = TenantService(db)
    stats = await service.get_organization_stats()
    return stats


# ──────────────────────────────────────────────
# Workspace Management
# ──────────────────────────────────────────────

@router.post("/workspaces", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    workspace_data: WorkspaceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new workspace."""
    try:
        service = TenantService(db)
        workspace = await service.create_workspace(workspace_data, current_user.id)
        return workspace
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create workspace")


@router.get("/organizations/{organization_id}/workspaces", response_model=PaginatedResponse)
async def list_workspaces(
    organization_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    workspace_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List workspaces for an organization."""
    try:
        from app.tenants.models import WorkspaceType
        
        service = TenantService(db)
        workspace_type_filter = WorkspaceType(workspace_type) if workspace_type else None
        workspaces, total = await service.list_workspaces(
            organization_id=organization_id,
            skip=skip,
            limit=limit,
            workspace_type=workspace_type_filter,
        )
        
        pages = (total + limit - 1) // limit
        
        return PaginatedResponse(
            items=[WorkspaceResponse.model_validate(ws) for ws in workspaces],
            total=total,
            page=skip // limit + 1,
            page_size=limit,
            pages=pages,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list workspaces")


@router.get("/workspaces/{workspace_id}", response_model=WorkspaceWithStats)
async def get_workspace(
    workspace_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get workspace by ID with statistics."""
    service = TenantService(db)
    workspace = await service.get_workspace_with_stats(workspace_id)
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return workspace


@router.put("/workspaces/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: int,
    workspace_data: WorkspaceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update workspace."""
    try:
        service = TenantService(db)
        workspace = await service.update_workspace(workspace_id, workspace_data)
        if not workspace:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
        return workspace
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update workspace")


@router.delete("/workspaces/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Archive workspace (soft delete)."""
    service = TenantService(db)
    try:
        success = await service.delete_workspace(workspace_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return None


# ──────────────────────────────────────────────
# Organization Member Management
# ──────────────────────────────────────────────

@router.post("/organizations/{organization_id}/members", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
async def add_organization_member(
    organization_id: int,
    member_data: MemberCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Add member to organization."""
    try:
        member_data.organization_id = organization_id
        service = TenantService(db)
        member = await service.add_organization_member(member_data)
        return member
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to add member")


@router.get("/organizations/{organization_id}/members", response_model=PaginatedResponse)
async def list_organization_members(
    organization_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List organization members."""
    try:
        service = TenantService(db)
        members, total = await service.list_organization_members(
            organization_id=organization_id,
            skip=skip,
            limit=limit,
        )
        
        pages = (total + limit - 1) // limit
        
        # Enrich with user details
        member_responses = []
        for member in members:
            member_dict = MemberResponse.model_validate(member).model_dump()
            member_dict["user_email"] = member.user.email if member.user else None
            member_dict["user_full_name"] = member.user.full_name if member.user else None
            member_responses.append(MemberResponse(**member_dict))
        
        return PaginatedResponse(
            items=member_responses,
            total=total,
            page=skip // limit + 1,
            page_size=limit,
            pages=pages,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list members")


@router.put("/organizations/{organization_id}/members/{user_id}", response_model=MemberResponse)
async def update_organization_member(
    organization_id: int,
    user_id: int,
    member_data: MemberUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update organization member."""
    service = TenantService(db)
    member = await service.update_organization_member(organization_id, user_id, member_data)
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    return member


@router.delete("/organizations/{organization_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_organization_member(
    organization_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Remove member from organization."""
    service = TenantService(db)
    success = await service.remove_organization_member(organization_id, user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    return None


# ──────────────────────────────────────────────
# Workspace Member Management
# ──────────────────────────────────────────────

@router.post("/workspaces/{workspace_id}/members", response_model=WorkspaceMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_workspace_member(
    workspace_id: int,
    member_data: WorkspaceMemberCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Add member to workspace."""
    try:
        member_data.workspace_id = workspace_id
        service = TenantService(db)
        member = await service.add_workspace_member(member_data)
        return member
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to add member")


@router.get("/workspaces/{workspace_id}/members", response_model=PaginatedResponse)
async def list_workspace_members(
    workspace_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List workspace members."""
    try:
        service = TenantService(db)
        members, total = await service.list_workspace_members(
            workspace_id=workspace_id,
            skip=skip,
            limit=limit,
        )
        
        pages = (total + limit - 1) // limit
        
        # Enrich with user details
        member_responses = []
        for member in members:
            member_dict = WorkspaceMemberResponse.model_validate(member).model_dump()
            member_dict["user_email"] = member.user.email if member.user else None
            member_dict["user_full_name"] = member.user.full_name if member.user else None
            member_responses.append(WorkspaceMemberResponse(**member_dict))
        
        return PaginatedResponse(
            items=member_responses,
            total=total,
            page=skip // limit + 1,
            page_size=limit,
            pages=pages,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list members")


@router.put("/workspaces/{workspace_id}/members/{user_id}", response_model=WorkspaceMemberResponse)
async def update_workspace_member(
    workspace_id: int,
    user_id: int,
    member_data: WorkspaceMemberUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update workspace member."""
    service = TenantService(db)
    member = await service.update_workspace_member(workspace_id, user_id, member_data)
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    return member


@router.delete("/workspaces/{workspace_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_workspace_member(
    workspace_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Remove member from workspace."""
    service = TenantService(db)
    success = await service.remove_workspace_member(workspace_id, user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    return None


# ──────────────────────────────────────────────
# Branding Management
# ──────────────────────────────────────────────

@router.get("/organizations/{organization_id}/branding", response_model=BrandingConfigResponse)
async def get_branding_config(
    organization_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get branding configuration for organization."""
    service = TenantService(db)
    branding = await service.get_branding_config(organization_id)
    if not branding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branding configuration not found")
    return branding


@router.post("/organizations/{organization_id}/branding", response_model=BrandingConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_branding_config(
    organization_id: int,
    branding_data: BrandingConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create branding configuration."""
    branding_data.organization_id = organization_id
    service = TenantService(db)
    branding = await service.create_branding_config(branding_data)
    return branding


@router.put("/organizations/{organization_id}/branding", response_model=BrandingConfigResponse)
async def update_branding_config(
    organization_id: int,
    branding_data: BrandingConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update branding configuration."""
    service = TenantService(db)
    branding = await service.update_branding_config(organization_id, branding_data)
    if not branding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branding configuration not found")
    return branding


# ──────────────────────────────────────────────
# Subscription Management
# ──────────────────────────────────────────────

@router.get("/organizations/{organization_id}/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    organization_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get subscription for organization."""
    service = TenantService(db)
    subscription = await service.get_subscription(organization_id)
    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    return subscription


@router.post("/organizations/{organization_id}/subscription", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    organization_id: int,
    subscription_data: SubscriptionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create subscription."""
    subscription_data.organization_id = organization_id
    service = TenantService(db)
    subscription = await service.create_subscription(subscription_data)
    return subscription


@router.put("/organizations/{organization_id}/subscription", response_model=SubscriptionResponse)
async def update_subscription(
    organization_id: int,
    subscription_data: SubscriptionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update subscription."""
    service = TenantService(db)
    subscription = await service.update_subscription(organization_id, subscription_data)
    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    return subscription


# ──────────────────────────────────────────────
# API Key Management
# ──────────────────────────────────────────────

@router.post("/organizations/{organization_id}/api-keys", response_model=APIKeyWithSecret, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    organization_id: int,
    api_key_data: APIKeyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create API key."""
    api_key_data.organization_id = organization_id
    api_key_data.user_id = current_user.id
    service = TenantService(db)
    api_key = await service.create_api_key(api_key_data)
    return api_key


@router.get("/organizations/{organization_id}/api-keys", response_model=PaginatedResponse)
async def list_api_keys(
    organization_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List API keys for organization."""
    try:
        service = TenantService(db)
        api_keys, total = await service.list_api_keys(
            organization_id=organization_id,
            skip=skip,
            limit=limit,
        )
        
        pages = (total + limit - 1) // limit
        
        return PaginatedResponse(
            items=[APIKeyResponse.model_validate(key) for key in api_keys],
            total=total,
            page=skip // limit + 1,
            page_size=limit,
            pages=pages,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list API keys")


@router.put("/api-keys/{api_key_id}", response_model=APIKeyResponse)
async def update_api_key(
    api_key_id: int,
    api_key_data: APIKeyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update API key."""
    service = TenantService(db)
    api_key = await service.update_api_key(api_key_id, api_key_data)
    if not api_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    return api_key


@router.post("/api-keys/{api_key_id}/revoke", response_model=APIKeyResponse)
async def revoke_api_key(
    api_key_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Revoke API key."""
    service = TenantService(db)
    success = await service.revoke_api_key(api_key_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    
    api_key = await service.get_api_key(api_key_id)
    return api_key


# ──────────────────────────────────────────────
# Feature Flag Management
# ──────────────────────────────────────────────

@router.post("/organizations/{organization_id}/feature-flags", response_model=FeatureFlagResponse, status_code=status.HTTP_201_CREATED)
async def create_feature_flag(
    organization_id: int,
    feature_flag_data: FeatureFlagCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create feature flag."""
    feature_flag_data.organization_id = organization_id
    service = TenantService(db)
    feature_flag = await service.create_feature_flag(feature_flag_data)
    return feature_flag


@router.get("/organizations/{organization_id}/feature-flags", response_model=PaginatedResponse)
async def list_feature_flags(
    organization_id: int,
    workspace_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List feature flags for organization."""
    try:
        service = TenantService(db)
        feature_flags, total = await service.list_feature_flags(
            organization_id=organization_id,
            workspace_id=workspace_id,
            skip=skip,
            limit=limit,
        )
        
        pages = (total + limit - 1) // limit
        
        return PaginatedResponse(
            items=[FeatureFlagResponse.model_validate(flag) for flag in feature_flags],
            total=total,
            page=skip // limit + 1,
            page_size=limit,
            pages=pages,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list feature flags")


@router.put("/feature-flags/{feature_flag_id}", response_model=FeatureFlagResponse)
async def update_feature_flag(
    feature_flag_id: int,
    feature_flag_data: FeatureFlagUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update feature flag."""
    service = TenantService(db)
    feature_flag = await service.update_feature_flag(feature_flag_id, feature_flag_data)
    if not feature_flag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feature flag not found")
    return feature_flag


@router.delete("/feature-flags/{feature_flag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_feature_flag(
    feature_flag_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete feature flag."""
    service = TenantService(db)
    success = await service.delete_feature_flag(feature_flag_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feature flag not found")
    return None


# ──────────────────────────────────────────────
# Invitation Management
# ──────────────────────────────────────────────

@router.post("/invitations", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
async def create_invitation(
    invitation_data: InvitationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create invitation."""
    service = TenantService(db)
    invitation = await service.create_invitation(invitation_data)
    return invitation


@router.post("/invitations/accept", response_model=InvitationResponse)
async def accept_invitation(
    invitation_data: InvitationAccept,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Accept invitation."""
    service = TenantService(db)
    invitation = await service.accept_invitation(invitation_data.token, current_user.id)
    if not invitation:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired invitation")
    return invitation


# ──────────────────────────────────────────────
# Audit Logs
# ──────────────────────────────────────────────

@router.post("/audit-logs", response_model=AuditLogResponse, status_code=status.HTTP_201_CREATED)
async def create_audit_log(
    audit_data: AuditLogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create audit log entry."""
    service = TenantService(db)
    audit_log = await service.create_audit_log(audit_data)
    return audit_log


@router.get("/organizations/{organization_id}/audit-logs", response_model=PaginatedResponse)
async def list_audit_logs(
    organization_id: int,
    user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[int] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List audit logs with filtering."""
    try:
        from datetime import datetime
        
        service = TenantService(db)
        
        # Parse dates if provided
        start_date_dt = datetime.fromisoformat(start_date) if start_date else None
        end_date_dt = datetime.fromisoformat(end_date) if end_date else None
        
        filter_data = AuditLogFilter(
            organization_id=organization_id,
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            start_date=start_date_dt,
            end_date=end_date_dt,
            limit=limit,
            offset=offset,
        )
        
        audit_logs, total = await service.list_audit_logs(filter_data)
        
        pages = (total + limit - 1) // limit
        
        return PaginatedResponse(
            items=[AuditLogResponse.model_validate(log) for log in audit_logs],
            total=total,
            page=offset // limit + 1,
            page_size=limit,
            pages=pages,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list audit logs")


# ──────────────────────────────────────────────
# Health Check
# ──────────────────────────────────────────────

@router.get("/organizations/{organization_id}/health", response_model=TenantHealth)
async def get_tenant_health(
    organization_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get tenant health metrics."""
    service = TenantService(db)
    health = await service.get_tenant_health(organization_id)
    if not health:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return health