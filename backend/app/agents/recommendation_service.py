from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.models import AgentRecommendation, RecommendationType
from app.agents.schemas import AgentRecommendationListOut


class RecommendationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_recommendation(
        self,
        agent_id: int,
        recommendation_type: str,
        title: str,
        description: str,
        confidence_score: float,
        priority: str = "medium",
        context_data: Optional[dict] = None,
        related_entities: Optional[list[dict]] = None,
        suggested_actions: Optional[list[dict]] = None,
        requires_approval: bool = False,
        expires_at: Optional[datetime] = None,
    ) -> AgentRecommendation:
        recommendation = AgentRecommendation(
            agent_id=agent_id,
            recommendation_type=RecommendationType(recommendation_type) if recommendation_type else RecommendationType.insight,
            title=title,
            description=description,
            confidence_score=confidence_score,
            priority=priority,
            context_data=context_data,
            related_entities=related_entities,
            suggested_actions=suggested_actions,
            requires_approval=requires_approval,
            expires_at=expires_at,
        )
        self.db.add(recommendation)
        await self.db.commit()
        await self.db.refresh(recommendation)
        return recommendation

    async def get_recommendation(self, recommendation_id: int) -> Optional[AgentRecommendation]:
        result = await self.db.execute(
            select(AgentRecommendation).where(AgentRecommendation.id == recommendation_id)
        )
        return result.scalar_one_or_none()

    async def list_recommendations(
        self,
        agent_id: int,
        recommendation_type: Optional[str] = None,
        is_viewed: Optional[bool] = None,
        is_actioned: Optional[bool] = None,
        priority: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AgentRecommendation], int]:
        query = select(AgentRecommendation).where(AgentRecommendation.agent_id == agent_id)

        if recommendation_type:
            query = query.where(AgentRecommendation.recommendation_type == RecommendationType(recommendation_type))
        if is_viewed is not None:
            query = query.where(AgentRecommendation.is_viewed == is_viewed)
        if is_actioned is not None:
            query = query.where(AgentRecommendation.is_actioned == is_actioned)
        if priority:
            query = query.where(AgentRecommendation.priority == priority)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(AgentRecommendation.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        recommendations = result.scalars().all()
        return list(recommendations), total

    async def mark_as_viewed(self, recommendation_id: int) -> Optional[AgentRecommendation]:
        recommendation = await self.get_recommendation(recommendation_id)
        if not recommendation:
            return None
        recommendation.is_viewed = True
        recommendation.viewed_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(recommendation)
        return recommendation

    async def mark_as_actioned(self, recommendation_id: int) -> Optional[AgentRecommendation]:
        recommendation = await self.get_recommendation(recommendation_id)
        if not recommendation:
            return None
        recommendation.is_actioned = True
        recommendation.actioned_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(recommendation)
        return recommendation

    async def get_pending_recommendations(self, agent_id: int, limit: int = 20) -> list[AgentRecommendation]:
        result = await self.db.execute(
            select(AgentRecommendation)
            .where(
                AgentRecommendation.agent_id == agent_id,
                AgentRecommendation.is_actioned == False,
                AgentRecommendation.expires_at == None,
            )
            .order_by(AgentRecommendation.priority.desc(), AgentRecommendation.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())