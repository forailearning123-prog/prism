from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.models import AgentPerformance, AIAgent
from app.agents.schemas import AgentPerformanceDashboard


class PerformanceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_metric(
        self,
        agent_id: int,
        metric_name: str,
        metric_value: float,
        dimension: Optional[str] = None,
    ) -> AgentPerformance:
        metric = AgentPerformance(
            agent_id=agent_id,
            metric_name=metric_name,
            metric_value=metric_value,
            dimension=dimension,
        )
        self.db.add(metric)
        await self.db.commit()
        await self.db.refresh(metric)
        return metric

    async def get_metrics(
        self,
        agent_id: int,
        metric_name: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[AgentPerformance], int]:
        query = select(AgentPerformance).where(AgentPerformance.agent_id == agent_id)

        if metric_name:
            query = query.where(AgentPerformance.metric_name == metric_name)
        if start_date:
            query = query.where(AgentPerformance.recorded_at >= start_date)
        if end_date:
            query = query.where(AgentPerformance.recorded_at <= end_date)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(AgentPerformance.recorded_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        metrics = result.scalars().all()
        return list(metrics), total

    async def get_dashboard(self, agent_id: int) -> AgentPerformanceDashboard:
        agent_result = await self.db.execute(
            select(AIAgent).where(AIAgent.id == agent_id)
        )
        agent = agent_result.scalar_one_or_none()
        if not agent:
            return AgentPerformanceDashboard()

        # Get task statistics
        from app.agents.models import AgentTask, TaskStatus
        completed_result = await self.db.execute(
            select(func.count()).select_from(AgentTask).where(
                AgentTask.agent_id == agent_id,
                AgentTask.status == TaskStatus.completed,
            )
        )
        tasks_completed = completed_result.scalar() or 0

        failed_result = await self.db.execute(
            select(func.count()).select_from(AgentTask).where(
                AgentTask.agent_id == agent_id,
                AgentTask.status == TaskStatus.failed,
            )
        )
        tasks_failed = failed_result.scalar() or 0

        total_tasks = tasks_completed + tasks_failed
        success_rate = (tasks_completed / total_tasks * 100) if total_tasks > 0 else 0.0

        # Get average execution time
        avg_time_result = await self.db.execute(
            select(func.avg(AgentPerformance.metric_value)).where(
                AgentPerformance.agent_id == agent_id,
                AgentPerformance.metric_name == "execution_time_ms",
            )
        )
        avg_execution_time_ms = int(avg_time_result.scalar() or 0)

        # Get average confidence score
        avg_confidence_result = await self.db.execute(
            select(func.avg(AgentPerformance.metric_value)).where(
                AgentPerformance.agent_id == agent_id,
                AgentPerformance.metric_name == "confidence_score",
            )
        )
        avg_confidence_score = float(avg_confidence_result.scalar() or 0.0)

        # Get recommendation statistics
        from app.agents.models import AgentRecommendation
        total_recs_result = await self.db.execute(
            select(func.count()).select_from(AgentRecommendation).where(
                AgentRecommendation.agent_id == agent_id,
            )
        )
        total_recommendations = total_recs_result.scalar() or 0

        actioned_recs_result = await self.db.execute(
            select(func.count()).select_from(AgentRecommendation).where(
                AgentRecommendation.agent_id == agent_id,
                AgentRecommendation.is_actioned == True,
            )
        )
        recommendations_actioned = actioned_recs_result.scalar() or 0

        recommendation_acceptance_rate = (recommendations_actioned / total_recommendations * 100) if total_recommendations > 0 else 0.0

        return AgentPerformanceDashboard(
            tasks_completed=tasks_completed,
            tasks_failed=tasks_failed,
            success_rate=round(success_rate, 2),
            avg_execution_time_ms=avg_execution_time_ms,
            avg_confidence_score=round(avg_confidence_score, 2),
            user_rating=agent.user_rating,
            total_recommendations=total_recommendations,
            recommendations_actioned=recommendations_actioned,
            recommendation_acceptance_rate=round(recommendation_acceptance_rate, 2),
        )

    async def get_agent_leaderboard(self, limit: int = 10) -> list[dict]:
        result = await self.db.execute(
            select(AIAgent)
            .where(AIAgent.is_active == True, AIAgent.archived_at == None)
            .order_by(AIAgent.user_rating.desc().nullslast(), AIAgent.tasks_completed.desc())
            .limit(limit)
        )
        agents = result.scalars().all()
        return [
            {
                "agent_id": agent.id,
                "name": agent.name,
                "display_name": agent.display_name,
                "agent_type": agent.agent_type.value,
                "tasks_completed": agent.tasks_completed,
                "tasks_failed": agent.tasks_failed,
                "user_rating": agent.user_rating,
                "avg_execution_time_ms": agent.avg_execution_time_ms,
            }
            for agent in agents
        ]