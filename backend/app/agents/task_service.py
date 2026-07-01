from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.models import AgentTask, TaskStatus, TaskPriority
from app.agents.schemas import AgentTaskCreate, AgentTaskUpdate


class TaskService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_task(self, data: AgentTaskCreate, created_by: int) -> AgentTask:
        task = AgentTask(
            agent_id=data.agent_id,
            title=data.title,
            description=data.description,
            task_type=data.task_type,
            priority=TaskPriority(data.priority) if data.priority else TaskPriority.medium,
            input_data=data.input_data,
            expected_output=data.expected_output,
            context=data.context,
            dependencies=data.dependencies,
            scheduled_at=data.scheduled_at,
            requires_approval=data.requires_approval,
            created_by=created_by,
        )
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def get_task(self, task_id: int) -> Optional[AgentTask]:
        result = await self.db.execute(
            select(AgentTask).where(AgentTask.id == task_id)
        )
        return result.scalar_one_or_none()

    async def list_tasks(
        self,
        agent_id: int,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        task_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AgentTask], int]:
        query = select(AgentTask).where(AgentTask.agent_id == agent_id)

        if status:
            query = query.where(AgentTask.status == TaskStatus(status))
        if priority:
            query = query.where(AgentTask.priority == TaskPriority(priority))
        if task_type:
            query = query.where(AgentTask.task_type == task_type)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(AgentTask.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        tasks = result.scalars().all()
        return list(tasks), total

    async def update_task(self, task_id: int, data: AgentTaskUpdate) -> Optional[AgentTask]:
        task = await self.get_task(task_id)
        if not task:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None:
                if key == "status" and value:
                    setattr(task, key, TaskStatus(value))
                elif key == "priority" and value:
                    setattr(task, key, TaskPriority(value))
                else:
                    setattr(task, key, value)

        task.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def start_task(self, task_id: int) -> Optional[AgentTask]:
        task = await self.get_task(task_id)
        if not task:
            return None
        task.status = TaskStatus.running
        task.started_at = datetime.now(timezone.utc)
        task.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def complete_task(self, task_id: int, result: dict, execution_time_ms: int) -> Optional[AgentTask]:
        task = await self.get_task(task_id)
        if not task:
            return None
        task.status = TaskStatus.completed
        task.completed_at = datetime.now(timezone.utc)
        task.result = result
        task.execution_time_ms = execution_time_ms
        task.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def fail_task(self, task_id: int, error_message: str) -> Optional[AgentTask]:
        task = await self.get_task(task_id)
        if not task:
            return None
        task.status = TaskStatus.failed
        task.completed_at = datetime.now(timezone.utc)
        task.error_message = error_message
        task.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def cancel_task(self, task_id: int) -> Optional[AgentTask]:
        task = await self.get_task(task_id)
        if not task:
            return None
        task.status = TaskStatus.cancelled
        task.completed_at = datetime.now(timezone.utc)
        task.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def get_pending_tasks(self, agent_id: int, limit: int = 10) -> list[AgentTask]:
        result = await self.db.execute(
            select(AgentTask)
            .where(
                AgentTask.agent_id == agent_id,
                AgentTask.status == TaskStatus.pending,
                AgentTask.scheduled_at <= datetime.now(timezone.utc),
            )
            .order_by(AgentTask.priority.desc(), AgentTask.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_scheduled_tasks(self, limit: int = 100) -> list[AgentTask]:
        result = await self.db.execute(
            select(AgentTask)
            .where(
                AgentTask.status == TaskStatus.pending,
                AgentTask.scheduled_at != None,
                AgentTask.scheduled_at <= datetime.now(timezone.utc),
            )
            .order_by(AgentTask.scheduled_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())