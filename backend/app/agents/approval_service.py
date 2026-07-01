from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.models import AgentApproval, ApprovalStatus
from app.agents.schemas import AgentApprovalCreate, AgentApprovalAction


class ApprovalService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_approval(self, data: AgentApprovalCreate, requested_by: int) -> AgentApproval:
        approval = AgentApproval(
            agent_id=data.agent_id,
            task_id=data.task_id,
            recommendation_id=data.recommendation_id,
            approval_type=data.approval_type,
            title=data.title,
            description=data.description,
            status=ApprovalStatus.pending,
            requested_by=requested_by,
            expires_at=data.expires_at,
        )
        self.db.add(approval)
        await self.db.commit()
        await self.db.refresh(approval)
        return approval

    async def get_approval(self, approval_id: int) -> Optional[AgentApproval]:
        result = await self.db.execute(
            select(AgentApproval).where(AgentApproval.id == approval_id)
        )
        return result.scalar_one_or_none()

    async def list_approvals(
        self,
        agent_id: int,
        status: Optional[str] = None,
        approval_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AgentApproval], int]:
        query = select(AgentApproval).where(AgentApproval.agent_id == agent_id)

        if status:
            query = query.where(AgentApproval.status == ApprovalStatus(status))
        if approval_type:
            query = query.where(AgentApproval.approval_type == approval_type)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(AgentApproval.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        approvals = result.scalars().all()
        return list(approvals), total

    async def process_approval(self, approval_id: int, action_data: AgentApprovalAction, approved_by: int) -> Optional[AgentApproval]:
        approval = await self.get_approval(approval_id)
        if not approval:
            return None

        if approval.status != ApprovalStatus.pending:
            return None

        if action_data.action == "approved":
            approval.status = ApprovalStatus.approved
        else:
            approval.status = ApprovalStatus.rejected

        approval.approved_by = approved_by
        approval.approval_notes = action_data.notes
        approval.resolved_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(approval)
        return approval

    async def get_pending_approvals(self, agent_id: int, limit: int = 20) -> list[AgentApproval]:
        result = await self.db.execute(
            select(AgentApproval)
            .where(
                AgentApproval.agent_id == agent_id,
                AgentApproval.status == ApprovalStatus.pending,
            )
            .order_by(AgentApproval.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())