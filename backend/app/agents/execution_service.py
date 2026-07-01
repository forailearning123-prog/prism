from datetime import datetime, timezone
from typing import Optional
import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.models import AgentExecution, ExecutionStatus, AgentTask, TaskStatus
from app.agents.schemas import AgentExecuteRequest, AgentExecuteResponse


class ExecutionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def execute_agent_task(
        self,
        agent_id: int,
        task_id: int,
        request: AgentExecuteRequest,
        triggered_by: str = "system",
        triggered_by_user_id: Optional[int] = None,
    ) -> AgentExecution:
        execution_id = str(uuid.uuid4())
        execution = AgentExecution(
            agent_id=agent_id,
            task_id=task_id,
            execution_id=execution_id,
            status=ExecutionStatus.started,
            input_data=request.input_data,
            triggered_by=triggered_by,
            triggered_by_user_id=triggered_by_user_id,
        )
        self.db.add(execution)
        await self.db.commit()
        await self.db.refresh(execution)
        return execution

    async def update_execution(
        self,
        execution_id: str,
        status: str,
        output_data: Optional[dict] = None,
        error_details: Optional[dict] = None,
        model_used: Optional[str] = None,
        tokens_used: Optional[int] = None,
        confidence_score: Optional[float] = None,
    ) -> Optional[AgentExecution]:
        result = await self.db.execute(
            select(AgentExecution).where(AgentExecution.execution_id == execution_id)
        )
        execution = result.scalar_one_or_none()
        if not execution:
            return None

        execution.status = ExecutionStatus(status)
        execution.output_data = output_data
        execution.error_details = error_details
        execution.model_used = model_used
        execution.tokens_used = tokens_used
        execution.confidence_score = confidence_score
        execution.completed_at = datetime.now(timezone.utc)
        execution.duration_ms = int((execution.completed_at - execution.started_at).total_seconds() * 1000)

        await self.db.commit()
        await self.db.refresh(execution)
        return execution

    async def get_execution(self, execution_id: str) -> Optional[AgentExecution]:
        result = await self.db.execute(
            select(AgentExecution).where(AgentExecution.execution_id == execution_id)
        )
        return result.scalar_one_or_none()

    async def list_executions(
        self,
        agent_id: int,
        task_id: Optional[int] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AgentExecution], int]:
        query = select(AgentExecution).where(AgentExecution.agent_id == agent_id)

        if task_id:
            query = query.where(AgentExecution.task_id == task_id)
        if status:
            query = query.where(AgentExecution.status == ExecutionStatus(status))

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(AgentExecution.started_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        executions = result.scalars().all()
        return list(executions), total

    async def get_execution_history(self, agent_id: int, limit: int = 50) -> list[AgentExecution]:
        result = await self.db.execute(
            select(AgentExecution)
            .where(AgentExecution.agent_id == agent_id)
            .order_by(AgentExecution.started_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())