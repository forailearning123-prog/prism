from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.models import (
    AIAgent,
    AgentTask,
    AgentExecution,
    AgentRecommendation,
    AgentApproval,
    AgentActivity,
    TaskStatus,
    ExecutionStatus,
    ApprovalStatus,
)


class GovernanceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_activity(
        self,
        agent_id: int,
        activity_type: str,
        title: str,
        description: str,
        status: str,
        metadata: Optional[dict] = None,
    ) -> AgentActivity:
        activity = AgentActivity(
            agent_id=agent_id,
            activity_type=activity_type,
            title=title,
            description=description,
            status=status,
            metadata=metadata,
        )
        self.db.add(activity)
        await self.db.commit()
        await self.db.refresh(activity)
        return activity

    async def get_activity_feed(
        self,
        agent_id: int,
        activity_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AgentActivity], int]:
        query = select(AgentActivity).where(AgentActivity.agent_id == agent_id)

        if activity_type:
            query = query.where(AgentActivity.activity_type == activity_type)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(AgentActivity.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        activities = result.scalars().all()
        return list(activities), total

    async def get_audit_trail(
        self,
        agent_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[dict], int]:
        activities_query = select(AgentActivity).where(AgentActivity.agent_id == agent_id)
        executions_query = select(AgentExecution).where(AgentExecution.agent_id == agent_id)
        approvals_query = select(AgentApproval).where(AgentApproval.agent_id == agent_id)

        if start_date:
            activities_query = activities_query.where(AgentActivity.created_at >= start_date)
            executions_query = executions_query.where(AgentExecution.started_at >= start_date)
            approvals_query = approvals_query.where(AgentApproval.created_at >= start_date)
        if end_date:
            activities_query = activities_query.where(AgentActivity.created_at <= end_date)
            executions_query = executions_query.where(AgentExecution.started_at <= end_date)
            approvals_query = approvals_query.where(AgentApproval.created_at <= end_date)

        activities_result = await self.db.execute(activities_query)
        activities = activities_result.scalars().all()

        executions_result = await self.db.execute(executions_query)
        executions = executions_result.scalars().all()

        approvals_result = await self.db.execute(approvals_query)
        approvals = approvals_result.scalars().all()

        # Combine all audit events
        audit_events = []

        for activity in activities:
            audit_events.append({
                "event_type": "activity",
                "timestamp": activity.created_at,
                "title": activity.title,
                "description": activity.description,
                "status": activity.status,
                "metadata": activity.metadata,
            })

        for execution in executions:
            audit_events.append({
                "event_type": "execution",
                "timestamp": execution.started_at,
                "title": f"Execution {execution.execution_id}",
                "description": f"Task execution with status: {execution.status.value}",
                "status": execution.status.value,
                "metadata": {
                    "execution_id": execution.execution_id,
                    "task_id": execution.task_id,
                    "model_used": execution.model_used,
                    "tokens_used": execution.tokens_used,
                    "confidence_score": execution.confidence_score,
                    "duration_ms": execution.duration_ms,
                },
            })

        for approval in approvals:
            audit_events.append({
                "event_type": "approval",
                "timestamp": approval.created_at,
                "title": approval.title,
                "description": approval.description,
                "status": approval.status.value,
                "metadata": {
                    "approval_type": approval.approval_type,
                    "requested_by": approval.requested_by,
                    "approved_by": approval.approved_by,
                    "approval_notes": approval.approval_notes,
                },
            })

        # Sort by timestamp descending
        audit_events.sort(key=lambda x: x["timestamp"], reverse=True)
        total = len(audit_events)
        paginated_events = audit_events[(page - 1) * page_size: page * page_size]

        return paginated_events, total

    async def get_governance_summary(self, agent_id: int) -> dict:
        # Get task statistics
        from app.agents.models import AgentTask
        tasks_result = await self.db.execute(
            select(func.count()).select_from(AgentTask).where(AgentTask.agent_id == agent_id)
        )
        total_tasks = tasks_result.scalar() or 0

        # Get execution statistics
        executions_result = await self.db.execute(
            select(func.count()).select_from(AgentExecution).where(AgentExecution.agent_id == agent_id)
        )
        total_executions = executions_result.scalar() or 0

        # Get approval statistics
        approvals_result = await self.db.execute(
            select(func.count()).select_from(AgentApproval).where(AgentApproval.agent_id == agent_id)
        )
        total_approvals = approvals_result.scalar() or 0

        pending_approvals_result = await self.db.execute(
            select(func.count()).select_from(AgentApproval).where(
                AgentApproval.agent_id == agent_id,
                AgentApproval.status == ApprovalStatus.pending,
            )
        )
        pending_approvals = pending_approvals_result.scalar() or 0

        # Get recommendation statistics
        recs_result = await self.db.execute(
            select(func.count()).select_from(AgentRecommendation).where(AgentRecommendation.agent_id == agent_id)
        )
        total_recommendations = recs_result.scalar() or 0

        actioned_recs_result = await self.db.execute(
            select(func.count()).select_from(AgentRecommendation).where(
                AgentRecommendation.agent_id == agent_id,
                AgentRecommendation.is_actioned == True,
            )
        )
        actioned_recommendations = actioned_recs_result.scalar() or 0

        return {
            "total_tasks": total_tasks,
            "total_executions": total_executions,
            "total_approvals": total_approvals,
            "pending_approvals": pending_approvals,
            "total_recommendations": total_recommendations,
            "actioned_recommendations": actioned_recommendations,
            "approval_rate": round((total_approvals / total_executions * 100) if total_executions > 0 else 0, 2),
            "recommendation_acceptance_rate": round((actioned_recommendations / total_recommendations * 100) if total_recommendations > 0 else 0, 2),
        }