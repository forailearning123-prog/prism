from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.collaboration.models import (
    ActionItem,
    ActionStatus,
    ActionPriority,
    DiscussionContextType,
    Notification,
    NotificationType,
)
from app.collaboration.schemas import ActionCreate, ActionUpdate


class ActionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_action(self, data: ActionCreate, created_by: int) -> ActionItem:
        action = ActionItem(
            workspace_id=data.workspace_id,
            title=data.title,
            description=data.description,
            context_type=DiscussionContextType(data.context_type) if data.context_type else None,
            context_id=data.context_id,
            assignee_id=data.assignee_id,
            due_date=data.due_date,
            priority=ActionPriority(data.priority) if data.priority else ActionPriority.medium,
            status=ActionStatus.open,
            dependencies=data.dependencies,
            is_recurring=data.is_recurring,
            recurrence_rule=data.recurrence_rule,
            business_context=data.business_context,
            created_by=created_by,
        )
        self.db.add(action)
        await self.db.flush()

        # Notify assignee
        if data.assignee_id and data.assignee_id != created_by:
            notification = Notification(
                user_id=data.assignee_id,
                notification_type=NotificationType.action_assigned,
                title=f"New action assigned: {data.title}",
                message=data.description[:200] if data.description else "",
                context_type=DiscussionContextType.action,
                context_id=action.id,
            )
            self.db.add(notification)

        await self.db.commit()
        await self.db.refresh(action)
        return action

    async def get_action(self, action_id: int) -> Optional[ActionItem]:
        result = await self.db.execute(
            select(ActionItem).where(ActionItem.id == action_id)
        )
        return result.scalar_one_or_none()

    async def list_actions(
        self,
        workspace_id: int,
        search: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assignee_id: Optional[int] = None,
        context_type: Optional[str] = None,
        context_id: Optional[int] = None,
        due_before: Optional[datetime] = None,
        due_after: Optional[datetime] = None,
        is_recurring: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ActionItem], int]:
        query = select(ActionItem).where(ActionItem.workspace_id == workspace_id)

        if search:
            query = query.where(
                or_(
                    ActionItem.title.ilike(f"%{search}%"),
                    ActionItem.description.ilike(f"%{search}%"),
                )
            )
        if status:
            query = query.where(ActionItem.status == ActionStatus(status))
        if priority:
            query = query.where(ActionItem.priority == ActionPriority(priority))
        if assignee_id is not None:
            query = query.where(ActionItem.assignee_id == assignee_id)
        if context_type:
            query = query.where(ActionItem.context_type == DiscussionContextType(context_type))
        if context_id is not None:
            query = query.where(ActionItem.context_id == context_id)
        if due_before:
            query = query.where(ActionItem.due_date <= due_before)
        if due_after:
            query = query.where(ActionItem.due_date >= due_after)
        if is_recurring is not None:
            query = query.where(ActionItem.is_recurring == is_recurring)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(ActionItem.due_date.asc().nullslast(), ActionItem.priority.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        actions = result.scalars().all()

        return list(actions), total

    async def update_action(self, action_id: int, data: ActionUpdate) -> Optional[ActionItem]:
        action = await self.get_action(action_id)
        if not action:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None:
                if key == "priority":
                    setattr(action, key, ActionPriority(value))
                elif key == "status":
                    new_status = ActionStatus(value)
                    setattr(action, key, new_status)
                    if new_status == ActionStatus.completed:
                        action.completed_at = datetime.now(timezone.utc)
                        action.progress = 100
                    elif new_status == ActionStatus.open:
                        action.completed_at = None
                else:
                    setattr(action, key, value)

        action.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(action)
        return action

    async def complete_action(self, action_id: int) -> Optional[ActionItem]:
        return await self.update_action(
            action_id,
            ActionUpdate(status="completed"),
        )

    async def list_actions_by_due_date(
        self, workspace_id: int, start_date: datetime, end_date: datetime
    ) -> list[ActionItem]:
        query = select(ActionItem).where(
            ActionItem.workspace_id == workspace_id,
            ActionItem.due_date >= start_date,
            ActionItem.due_date <= end_date,
            ActionItem.status != ActionStatus.completed,
            ActionItem.status != ActionStatus.cancelled,
        ).order_by(ActionItem.due_date.asc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_action_counts_by_status(self, workspace_id: int) -> dict:
        statuses = list(ActionStatus)
        counts = {}
        for status in statuses:
            result = await self.db.execute(
                select(func.count()).select_from(ActionItem).where(
                    ActionItem.workspace_id == workspace_id,
                    ActionItem.status == status,
                )
            )
            counts[status.value] = result.scalar() or 0
        return counts