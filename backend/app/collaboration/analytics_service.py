from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.collaboration.models import (
    CollaborationMetric,
    DecisionRecord,
    DecisionStatus,
    ActionItem,
    ActionStatus,
    Workspace,
    WorkspaceMember,
    KnowledgeArticle,
    MeetingSummary,
    ApprovalInstance,
    ApprovalStatus,
)
from app.collaboration.schemas import (
    CollaborationAnalyticsQuery,
    CollaborationMetricOut,
    CollaborationAnalyticsDashboard,
)


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_metric(
        self, workspace_id: int, metric_name: str, metric_value: float, dimension: Optional[str] = None
    ) -> CollaborationMetric:
        metric = CollaborationMetric(
            workspace_id=workspace_id,
            metric_name=metric_name,
            metric_value=metric_value,
            dimension=dimension,
        )
        self.db.add(metric)
        await self.db.commit()
        await self.db.refresh(metric)
        return metric

    async def get_metrics(
        self, query: CollaborationAnalyticsQuery, page: int = 1, page_size: int = 50
    ) -> tuple[list[CollaborationMetric], int]:
        q = select(CollaborationMetric)

        if query.workspace_id:
            q = q.where(CollaborationMetric.workspace_id == query.workspace_id)
        if query.metric_name:
            q = q.where(CollaborationMetric.metric_name == query.metric_name)
        if query.start_date:
            q = q.where(CollaborationMetric.recorded_at >= query.start_date)
        if query.end_date:
            q = q.where(CollaborationMetric.recorded_at <= query.end_date)

        count_query = select(func.count()).select_from(q.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        q = q.order_by(CollaborationMetric.recorded_at.desc())
        q = q.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(q)
        metrics = result.scalars().all()
        return list(metrics), total

    async def compute_dashboard(self, workspace_id: int) -> CollaborationAnalyticsDashboard:
        # Average decision time (hours from creation to completion)
        decisions_result = await self.db.execute(
            select(DecisionRecord).where(
                DecisionRecord.workspace_id == workspace_id,
                DecisionRecord.status.in_([DecisionStatus.implemented, DecisionStatus.closed]),
                DecisionRecord.completed_at.isnot(None),
                DecisionRecord.created_at.isnot(None),
            )
        )
        completed_decisions = decisions_result.scalars().all()
        total_time_hours = 0
        for d in completed_decisions:
            if d.completed_at and d.created_at:
                delta = d.completed_at - d.created_at
                total_time_hours += delta.total_seconds() / 3600
        avg_decision_time = total_time_hours / len(completed_decisions) if completed_decisions else 0

        # Approval cycle time
        approval_result = await self.db.execute(
            select(ApprovalInstance).where(
                ApprovalInstance.status.in_([ApprovalStatus.approved, ApprovalStatus.rejected]),
                ApprovalInstance.completed_at.isnot(None),
            )
        )
        completed_approvals = approval_result.scalars().all()
        total_approval_time = 0
        for a in completed_approvals:
            if a.completed_at:
                delta = a.completed_at - a.submitted_at
                total_approval_time += delta.total_seconds() / 3600
        avg_approval_time = total_approval_time / len(completed_approvals) if completed_approvals else 0

        # Action completion rate
        total_actions_result = await self.db.execute(
            select(func.count()).select_from(ActionItem).where(ActionItem.workspace_id == workspace_id)
        )
        total_actions = total_actions_result.scalar() or 0
        completed_actions_result = await self.db.execute(
            select(func.count()).select_from(ActionItem).where(
                ActionItem.workspace_id == workspace_id,
                ActionItem.status == ActionStatus.completed,
            )
        )
        completed_actions = completed_actions_result.scalar() or 0
        action_completion_rate = (completed_actions / total_actions * 100) if total_actions > 0 else 0

        # Team participation
        members_result = await self.db.execute(
            select(func.count()).select_from(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id
            )
        )
        team_count = members_result.scalar() or 0

        # Decision counts
        open_decisions_result = await self.db.execute(
            select(func.count()).select_from(DecisionRecord).where(
                DecisionRecord.workspace_id == workspace_id,
                DecisionRecord.status.in_([DecisionStatus.draft, DecisionStatus.open, DecisionStatus.in_review]),
            )
        )
        open_decisions = open_decisions_result.scalar() or 0

        closed_decisions_result = await self.db.execute(
            select(func.count()).select_from(DecisionRecord).where(
                DecisionRecord.workspace_id == workspace_id,
                DecisionRecord.status.in_([DecisionStatus.implemented, DecisionStatus.closed, DecisionStatus.rejected]),
            )
        )
        closed_decisions = closed_decisions_result.scalar() or 0

        total_decisions = open_decisions + closed_decisions

        # Knowledge articles count
        articles_result = await self.db.execute(
            select(func.count()).select_from(KnowledgeArticle).where(
                KnowledgeArticle.workspace_id == workspace_id,
                KnowledgeArticle.is_published == True,
            )
        )
        articles_count = articles_result.scalar() or 0

        # Meeting count
        meetings_result = await self.db.execute(
            select(func.count()).select_from(MeetingSummary).where(
                MeetingSummary.workspace_id == workspace_id,
            )
        )
        meeting_count = meetings_result.scalar() or 0

        return CollaborationAnalyticsDashboard(
            avg_decision_time_hours=round(avg_decision_time, 1),
            approval_cycle_time_hours=round(avg_approval_time, 1),
            action_completion_rate=round(action_completion_rate, 1),
            team_participation_count=team_count,
            open_decisions=open_decisions,
            closed_decisions=closed_decisions,
            total_decisions=total_decisions,
            knowledge_articles_count=articles_count,
            meeting_count=meeting_count,
        )