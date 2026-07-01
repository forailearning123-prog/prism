from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.collaboration.models import DecisionImpact, DecisionRecord, DecisionStatus
from app.collaboration.schemas import DecisionImpactCreate, DecisionImpactUpdate


class ImpactService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_impact(self, data: DecisionImpactCreate) -> Optional[DecisionImpact]:
        # Verify decision exists
        result = await self.db.execute(
            select(DecisionRecord).where(DecisionRecord.id == data.decision_id)
        )
        decision = result.scalar_one_or_none()
        if not decision:
            return None

        # Check if impact record already exists
        result = await self.db.execute(
            select(DecisionImpact).where(DecisionImpact.decision_id == data.decision_id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        impact = DecisionImpact(
            decision_id=data.decision_id,
            planned_result=data.planned_result,
            actual_result=data.actual_result,
            kpi_changes=data.kpi_changes,
            financial_impact=data.financial_impact,
            timeline=data.timeline,
            lessons_learned=data.lessons_learned,
        )
        self.db.add(impact)
        await self.db.commit()
        await self.db.refresh(impact)
        return impact

    async def get_impact(self, decision_id: int) -> Optional[DecisionImpact]:
        result = await self.db.execute(
            select(DecisionImpact).where(DecisionImpact.decision_id == decision_id)
        )
        return result.scalar_one_or_none()

    async def update_impact(self, decision_id: int, data: DecisionImpactUpdate, reviewed_by: int) -> Optional[DecisionImpact]:
        impact = await self.get_impact(decision_id)
        if not impact:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None:
                setattr(impact, key, value)

        impact.reviewed_by = reviewed_by
        impact.reviewed_at = datetime.now(timezone.utc)
        impact.updated_at = datetime.now(timezone.utc)

        # Update decision with actual outcome
        if data.actual_result:
            result = await self.db.execute(
                select(DecisionRecord).where(DecisionRecord.id == decision_id)
            )
            decision = result.scalar_one_or_none()
            if decision:
                decision.actual_outcome = data.actual_result
                if data.actual_result:
                    decision.status = DecisionStatus.implemented
                    decision.completed_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(impact)
        return impact