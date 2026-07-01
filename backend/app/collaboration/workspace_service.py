from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.collaboration.models import (
    Workspace,
    WorkspaceMember,
    WorkspaceMemberRole,
    WorkspaceType,
    Discussion,
    DecisionRecord,
    ActionItem,
)
from app.collaboration.schemas import WorkspaceCreate, WorkspaceUpdate, WorkspaceMemberAdd, WorkspaceMemberUpdate


class WorkspaceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_workspace(self, data: WorkspaceCreate, owner_id: int) -> Workspace:
        workspace = Workspace(
            name=data.name,
            description=data.description,
            workspace_type=WorkspaceType(data.workspace_type) if data.workspace_type else WorkspaceType.team,
            owner_id=owner_id,
        )
        self.db.add(workspace)
        await self.db.flush()

        # Add owner as admin member
        member = WorkspaceMember(
            workspace_id=workspace.id,
            user_id=owner_id,
            role=WorkspaceMemberRole.admin,
        )
        self.db.add(member)
        await self.db.commit()
        await self.db.refresh(workspace)
        return workspace

    async def get_workspace(self, workspace_id: int) -> Optional[Workspace]:
        result = await self.db.execute(
            select(Workspace).where(Workspace.id == workspace_id, Workspace.is_archived == False)
        )
        return result.scalar_one_or_none()

    async def list_workspaces(
        self,
        user_id: int,
        search: Optional[str] = None,
        workspace_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Workspace], int]:
        query = (
            select(Workspace)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
            .where(WorkspaceMember.user_id == user_id, Workspace.is_archived == False)
        )

        if search:
            query = query.where(Workspace.name.ilike(f"%{search}%"))
        if workspace_type:
            query = query.where(Workspace.workspace_type == WorkspaceType(workspace_type))

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Workspace.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        workspaces = result.scalars().all()

        return list(workspaces), total

    async def update_workspace(self, workspace_id: int, data: WorkspaceUpdate) -> Optional[Workspace]:
        workspace = await self.get_workspace(workspace_id)
        if not workspace:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if key == "workspace_type" and value:
                setattr(workspace, key, WorkspaceType(value))
            elif value is not None:
                setattr(workspace, key, value)

        workspace.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(workspace)
        return workspace

    async def archive_workspace(self, workspace_id: int) -> bool:
        workspace = await self.get_workspace(workspace_id)
        if not workspace:
            return False
        workspace.is_archived = True
        workspace.archived_at = datetime.now(timezone.utc)
        await self.db.commit()
        return True

    async def add_member(self, workspace_id: int, data: WorkspaceMemberAdd) -> Optional[WorkspaceMember]:
        workspace = await self.get_workspace(workspace_id)
        if not workspace:
            return None

        # Check if already a member
        result = await self.db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == data.user_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        member = WorkspaceMember(
            workspace_id=workspace_id,
            user_id=data.user_id,
            role=WorkspaceMemberRole(data.role) if data.role else WorkspaceMemberRole.member,
        )
        self.db.add(member)
        await self.db.commit()
        await self.db.refresh(member)
        return member

    async def update_member_role(self, workspace_id: int, user_id: int, data: WorkspaceMemberUpdate) -> Optional[WorkspaceMember]:
        result = await self.db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
            )
        )
        member = result.scalar_one_or_none()
        if not member:
            return None
        member.role = WorkspaceMemberRole(data.role)
        await self.db.commit()
        await self.db.refresh(member)
        return member

    async def remove_member(self, workspace_id: int, user_id: int) -> bool:
        result = await self.db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
            )
        )
        member = result.scalar_one_or_none()
        if not member:
            return False
        await self.db.delete(member)
        await self.db.commit()
        return True

    async def get_members(self, workspace_id: int) -> list[WorkspaceMember]:
        result = await self.db.execute(
            select(WorkspaceMember)
            .where(WorkspaceMember.workspace_id == workspace_id)
            .options(selectinload(WorkspaceMember.user))
        )
        return list(result.scalars().all())

    async def get_workspace_counts(self, workspace_id: int) -> dict:
        # Discussion count
        result = await self.db.execute(
            select(func.count()).select_from(Discussion).where(
                Discussion.workspace_id == workspace_id,
                Discussion.is_archived == False,
            )
        )
        discussion_count = result.scalar() or 0

        # Decision count
        result = await self.db.execute(
            select(func.count()).select_from(DecisionRecord).where(
                DecisionRecord.workspace_id == workspace_id,
            )
        )
        decision_count = result.scalar() or 0

        # Action count
        result = await self.db.execute(
            select(func.count()).select_from(ActionItem).where(
                ActionItem.workspace_id == workspace_id,
                ActionItem.status != "cancelled",
            )
        )
        action_count = result.scalar() or 0

        # Member count
        result = await self.db.execute(
            select(func.count()).select_from(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id,
            )
        )
        member_count = result.scalar() or 0

        return {
            "member_count": member_count,
            "discussion_count": discussion_count,
            "decision_count": decision_count,
            "action_count": action_count,
        }