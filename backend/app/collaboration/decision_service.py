from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.collaboration.models import (
    DecisionRecord,
    DecisionParticipant,
    DecisionHistory,
    DecisionStatus,
    DecisionPriority,
    DecisionParticipantRole,
    DiscussionContextType,
    Notification,
    NotificationType,
)
from app.collaboration.schemas import (
    DecisionCreate,
    DecisionUpdate,
    DecisionParticipantAdd,
)


class DecisionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_decision(self, data: DecisionCreate, created_by: int) -> DecisionRecord:
        decision = DecisionRecord(
            workspace_id=data.workspace_id,
            title=data.title,
            description=data.description,
            context_type=DiscussionContextType(data.context_type) if data.context_type else None,
            context_id=data.context_id,
            owner_id=data.owner_id,
            priority=DecisionPriority(data.priority) if data.priority else DecisionPriority.medium,
            status=DecisionStatus.draft,
            business_rationale=data.business_rationale,
            expected_outcome=data.expected_outcome,
            due_date=data.due_date,
            created_by=created_by,
        )
        self.db.add(decision)
        await self.db.flush()

        # Add creator as owner participant
        participant = DecisionParticipant(
            decision_id=decision.id,
            user_id=created_by,
            role=DecisionParticipantRole.owner,
        )
        self.db.add(participant)

        # Add specified owner as participant if different
        if data.owner_id != created_by:
            owner_participant = DecisionParticipant(
                decision_id=decision.id,
                user_id=data.owner_id,
                role=DecisionParticipantRole.owner,
            )
            self.db.add(owner_participant)

        # Record creation in history
        history = DecisionHistory(
            decision_id=decision.id,
            field_changed="status",
            old_value=None,
            new_value=DecisionStatus.draft.value,
            changed_by=created_by,
        )
        self.db.add(history)

        await self.db.commit()
        await self.db.refresh(decision)
        return decision

    async def get_decision(self, decision_id: int) -> Optional[DecisionRecord]:
        result = await self.db.execute(
            select(DecisionRecord).where(DecisionRecord.id == decision_id)
        )
        return result.scalar_one_or_none()

    async def list_decisions(
        self,
        workspace_id: int,
        search: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        owner_id: Optional[int] = None,
        context_type: Optional[str] = None,
        context_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[DecisionRecord], int]:
        query = select(DecisionRecord).where(DecisionRecord.workspace_id == workspace_id)

        if search:
            query = query.where(
                or_(
                    DecisionRecord.title.ilike(f"%{search}%"),
                    DecisionRecord.description.ilike(f"%{search}%"),
                )
            )
        if status:
            query = query.where(DecisionRecord.status == DecisionStatus(status))
        if priority:
            query = query.where(DecisionRecord.priority == DecisionPriority(priority))
        if owner_id is not None:
            query = query.where(DecisionRecord.owner_id == owner_id)
        if context_type:
            query = query.where(DecisionRecord.context_type == DiscussionContextType(context_type))
        if context_id is not None:
            query = query.where(DecisionRecord.context_id == context_id)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(DecisionRecord.updated_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        decisions = result.scalars().all()

        return list(decisions), total

    async def update_decision(self, decision_id: int, data: DecisionUpdate, changed_by: int) -> Optional[DecisionRecord]:
        decision = await self.get_decision(decision_id)
        if not decision:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None:
                old_value = getattr(decision, key, None)
                if key == "priority":
                    setattr(decision, key, DecisionPriority(value))
                elif key == "status":
                    new_status = DecisionStatus(value)
                    setattr(decision, key, new_status)
                    if new_status == DecisionStatus.completed or new_status == DecisionStatus.implemented:
                        decision.completed_at = datetime.now(timezone.utc)
                else:
                    setattr(decision, key, value)

                # Record history for significant fields
                if key in ("status", "priority", "owner_id", "title", "description"):
                    history = DecisionHistory(
                        decision_id=decision.id,
                        field_changed=key,
                        old_value=str(old_value) if old_value else None,
                        new_value=str(value) if value else None,
                        changed_by=changed_by,
                    )
                    self.db.add(history)

        decision.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(decision)
        return decision

    async def add_participant(self, decision_id: int, data: DecisionParticipantAdd) -> Optional[DecisionParticipant]:
        decision = await self.get_decision(decision_id)
        if not decision:
            return None

        # Check if already a participant
        result = await self.db.execute(
            select(DecisionParticipant).where(
                DecisionParticipant.decision_id == decision_id,
                DecisionParticipant.user_id == data.user_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        participant = DecisionParticipant(
            decision_id=decision_id,
            user_id=data.user_id,
            role=DecisionParticipantRole(data.role) if data.role else DecisionParticipantRole.participant,
        )
        self.db.add(participant)
        await self.db.commit()
        await self.db.refresh(participant)
        return participant

    async def remove_participant(self, decision_id: int, user_id: int) -> bool:
        result = await self.db.execute(
            select(DecisionParticipant).where(
                DecisionParticipant.decision_id == decision_id,
                DecisionParticipant.user_id == user_id,
            )
        )
        participant = result.scalar_one_or_none()
        if not participant:
            return False
        await self.db.delete(participant)
        await self.db.commit()
        return True

    async def get_participants(self, decision_id: int) -> list[DecisionParticipant]:
        result = await self.db.execute(
            select(DecisionParticipant).where(DecisionParticipant.decision_id == decision_id)
        )
        return list(result.scalars().all())

    async def get_history(self, decision_id: int) -> list[DecisionHistory]:
        result = await self.db.execute(
            select(DecisionHistory)
            .where(DecisionHistory.decision_id == decision_id)
            .order_by(DecisionHistory.created_at.desc())
        )
        return list(result.scalars().all())