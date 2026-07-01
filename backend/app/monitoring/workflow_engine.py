import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    AlertEvent, WorkflowDefinition, WorkflowExecution, WorkflowStep,
    WorkflowStepResult, WorkflowStepType, WorkflowTriggerType,
)

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """Executes automation workflows triggered by alerts or schedules."""

    async def trigger_for_alert(self, alert: AlertEvent, db: AsyncSession):
        """Trigger workflows that match the alert's conditions."""
        result = await db.execute(
            select(WorkflowDefinition)
            .where(
                WorkflowDefinition.is_active == True,
                WorkflowDefinition.trigger_type.in_([
                    WorkflowTriggerType.alert,
                    WorkflowTriggerType.anomaly,
                ]),
            )
            .options(selectinload(WorkflowDefinition.steps))
        )
        workflows = result.scalars().all()

        for workflow in workflows:
            if self._matches_trigger(workflow, alert):
                await self.execute(workflow, alert.id, db)

    async def execute(
        self,
        workflow: WorkflowDefinition,
        alert_id: Optional[int] = None,
        db: Optional[AsyncSession] = None,
    ) -> WorkflowExecution:
        """Execute a workflow and its steps."""
        execution = WorkflowExecution(
            workflow_id=workflow.id,
            alert_id=alert_id,
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        db.add(execution)
        await db.commit()
        await db.refresh(execution)

        try:
            sorted_steps = sorted(workflow.steps, key=lambda s: s.order)
            for step in sorted_steps:
                step_result = await self._execute_step(step, execution, db)
                if step_result.status == "failed" and not step.is_parallel:
                    execution.status = "failed"
                    execution.error_message = f"Step '{step.name}' failed"
                    break

            if execution.status != "failed":
                execution.status = "completed"
            execution.completed_at = datetime.now(timezone.utc)
            await db.commit()
            await db.refresh(execution)

        except Exception as e:
            execution.status = "failed"
            execution.error_message = str(e)
            execution.completed_at = datetime.now(timezone.utc)
            await db.commit()

        return execution

    async def _execute_step(self, step: WorkflowStep, execution: WorkflowExecution, db: AsyncSession) -> WorkflowStepResult:
        """Execute a single workflow step."""
        step_result = WorkflowStepResult(
            execution_id=execution.id,
            step_id=step.id,
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        db.add(step_result)
        await db.commit()

        try:
            output = None
            step_type = step.step_type

            if step_type == WorkflowStepType.send_notification:
                output = await self._send_notification_step(step, execution)
            elif step_type == WorkflowStepType.generate_report:
                output = await self._generate_report_step(step, execution)
            elif step_type == WorkflowStepType.refresh_dashboard:
                output = await self._refresh_dashboard_step(step, execution)
            elif step_type == WorkflowStepType.refresh_semantic_model:
                output = await self._refresh_semantic_model_step(step, execution)
            elif step_type == WorkflowStepType.trigger_webhook:
                output = await self._trigger_webhook_step(step, execution)
            elif step_type == WorkflowStepType.create_task:
                output = await self._create_task_step(step, execution)
            elif step_type == WorkflowStepType.invoke_analyst:
                output = await self._invoke_analyst_step(step, execution)
            elif step_type == WorkflowStepType.wait:
                output = await self._wait_step(step, execution)

            step_result.status = "completed"
            step_result.output = output or {}
            step_result.completed_at = datetime.now(timezone.utc)

        except Exception as e:
            step_result.status = "failed"
            step_result.error_message = str(e)
            step_result.completed_at = datetime.now(timezone.utc)
            logger.error(f"Workflow step {step.id} failed: {e}")

        await db.commit()
        return step_result

    async def _send_notification_step(self, step: WorkflowStep, execution: WorkflowExecution) -> dict:
        channel = step.config.get("channel", "in_app")
        message = step.config.get("message", "")
        logger.info(f"Workflow step: send {channel} notification: {message}")
        return {"channel": channel, "message_preview": message[:100]}

    async def _generate_report_step(self, step: WorkflowStep, execution: WorkflowExecution) -> dict:
        report_type = step.config.get("report_type", "summary")
        logger.info(f"Workflow step: generate {report_type} report")
        return {"report_type": report_type, "status": "generated"}

    async def _refresh_dashboard_step(self, step: WorkflowStep, execution: WorkflowExecution) -> dict:
        dashboard_id = step.config.get("dashboard_id")
        logger.info(f"Workflow step: refresh dashboard {dashboard_id}")
        return {"dashboard_id": dashboard_id, "status": "refreshed"}

    async def _refresh_semantic_model_step(self, step: WorkflowStep, execution: WorkflowExecution) -> dict:
        model_id = step.config.get("semantic_model_id")
        logger.info(f"Workflow step: refresh semantic model {model_id}")
        return {"semantic_model_id": model_id, "status": "refreshed"}

    async def _trigger_webhook_step(self, step: WorkflowStep, execution: WorkflowExecution) -> dict:
        url = step.config.get("url", "")
        payload = step.config.get("payload", {})
        logger.info(f"Workflow step: trigger webhook {url}")
        return {"url": url, "status": "triggered"}

    async def _create_task_step(self, step: WorkflowStep, execution: WorkflowExecution) -> dict:
        title = step.config.get("title", "Follow-up task")
        assignee = step.config.get("assignee")
        logger.info(f"Workflow step: create task '{title}' for {assignee}")
        return {"title": title, "assignee": assignee, "status": "created"}

    async def _invoke_analyst_step(self, step: WorkflowStep, execution: WorkflowExecution) -> dict:
        query = step.config.get("query", "Analyze current situation")
        logger.info(f"Workflow step: invoke AI analyst: {query}")
        return {"query": query, "status": "invoked"}

    async def _wait_step(self, step: WorkflowStep, execution: WorkflowExecution) -> dict:
        duration = step.config.get("duration_seconds", 60)
        logger.info(f"Workflow step: wait {duration}s")
        return {"duration": duration, "status": "completed"}

    def _matches_trigger(self, workflow: WorkflowDefinition, alert: AlertEvent) -> bool:
        """Check if a workflow's trigger config matches the alert."""
        trigger_config = workflow.trigger_config
        if not trigger_config:
            return True

        if "severity" in trigger_config:
            allowed = trigger_config["severity"]
            if isinstance(allowed, list) and alert.severity.value not in allowed:
                return False
            if isinstance(allowed, str) and alert.severity.value != allowed:
                return False

        if "monitor_id" in trigger_config:
            if alert.monitor_id != trigger_config["monitor_id"]:
                return False

        return True

    async def get_executions(
        self,
        db: AsyncSession,
        workflow_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[WorkflowExecution], int]:
        """Get workflow executions with pagination."""
        query = select(WorkflowExecution)
        if workflow_id:
            query = query.where(WorkflowExecution.workflow_id == workflow_id)
        query = query.order_by(desc(WorkflowExecution.created_at))

        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query) or 0

        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        items = list(result.scalars().all())
        return items, total