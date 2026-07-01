from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.collaboration.models import (
    ApprovalWorkflow,
    ApprovalWorkflowStep,
    ApprovalInstance,
    ApprovalAction,
    ApprovalStatus,
    ApprovalActionType,
    DiscussionContextType,
    Notification,
    NotificationType,
)
from app.collaboration.schemas import (
    ApprovalWorkflowCreate,
    ApprovalWorkflowUpdate,
    ApprovalWorkflowStepCreate,
    ApprovalSubmit,
    ApprovalActionCreate,
)


class ApprovalService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_workflow(self, data: ApprovalWorkflowCreate, created_by: int) -> ApprovalWorkflow:
        workflow = ApprovalWorkflow(
            workspace_id=data.workspace_id,
            name=data.name,
            description=data.description,
            context_type=DiscussionContextType(data.context_type) if data.context_type else None,
            created_by=created_by,
        )
        self.db.add(workflow)
        await self.db.commit()
        await self.db.refresh(workflow)
        return workflow

    async def get_workflow(self, workflow_id: int) -> Optional[ApprovalWorkflow]:
        result = await self.db.execute(
            select(ApprovalWorkflow).where(ApprovalWorkflow.id == workflow_id)
        )
        return result.scalar_one_or_none()

    async def list_workflows(
        self, workspace_id: int, is_active: Optional[bool] = None, page: int = 1, page_size: int = 20
    ) -> tuple[list[ApprovalWorkflow], int]:
        query = select(ApprovalWorkflow).where(ApprovalWorkflow.workspace_id == workspace_id)
        if is_active is not None:
            query = query.where(ApprovalWorkflow.is_active == is_active)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(ApprovalWorkflow.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        workflows = result.scalars().all()
        return list(workflows), total

    async def update_workflow(self, workflow_id: int, data: ApprovalWorkflowUpdate) -> Optional[ApprovalWorkflow]:
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None:
                setattr(workflow, key, value)
        workflow.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(workflow)
        return workflow

    async def add_step(self, workflow_id: int, data: ApprovalWorkflowStepCreate) -> Optional[ApprovalWorkflowStep]:
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            return None
        step = ApprovalWorkflowStep(
            workflow_id=workflow_id,
            step_order=data.step_order,
            name=data.name,
            approver_user_id=data.approver_user_id,
            approver_role=data.approver_role,
            required_count=data.required_count,
            timeout_hours=data.timeout_hours,
        )
        self.db.add(step)
        await self.db.commit()
        await self.db.refresh(step)
        return step

    async def get_steps(self, workflow_id: int) -> list[ApprovalWorkflowStep]:
        result = await self.db.execute(
            select(ApprovalWorkflowStep)
            .where(ApprovalWorkflowStep.workflow_id == workflow_id)
            .order_by(ApprovalWorkflowStep.step_order)
        )
        return list(result.scalars().all())

    async def submit_for_approval(self, data: ApprovalSubmit, submitted_by: int) -> Optional[ApprovalInstance]:
        workflow = await self.get_workflow(data.workflow_id)
        if not workflow or not workflow.is_active:
            return None

        steps = await self.get_steps(workflow.id)
        if not steps:
            return None

        instance = ApprovalInstance(
            workflow_id=data.workflow_id,
            context_type=DiscussionContextType(data.context_type) if data.context_type else None,
            context_id=data.context_id,
            status=ApprovalStatus.pending,
            submitted_by=submitted_by,
        )
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)

        # Notify first step approvers
        first_step = steps[0]
        if first_step.approver_user_id:
            notification = Notification(
                user_id=first_step.approver_user_id,
                notification_type=NotificationType.approval_request,
                title=f"Approval required: {workflow.name}",
                message=f"Please review and approve the submission.",
                context_type=DiscussionContextType.dashboard,
                context_id=instance.id,
            )
            self.db.add(notification)
            await self.db.commit()

        return instance

    async def get_instance(self, instance_id: int) -> Optional[ApprovalInstance]:
        result = await self.db.execute(
            select(ApprovalInstance).where(ApprovalInstance.id == instance_id)
        )
        return result.scalar_one_or_none()

    async def list_instances(
        self,
        workflow_id: Optional[int] = None,
        submitted_by: Optional[int] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ApprovalInstance], int]:
        query = select(ApprovalInstance)
        if workflow_id:
            query = query.where(ApprovalInstance.workflow_id == workflow_id)
        if submitted_by:
            query = query.where(ApprovalInstance.submitted_by == submitted_by)
        if status:
            query = query.where(ApprovalInstance.status == ApprovalStatus(status))

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(ApprovalInstance.submitted_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        instances = result.scalars().all()
        return list(instances), total

    async def process_action(
        self, instance_id: int, data: ApprovalActionCreate, approver_id: int
    ) -> Optional[ApprovalInstance]:
        instance = await self.get_instance(instance_id)
        if not instance or instance.status != ApprovalStatus.pending:
            return None

        steps = await self.get_steps(instance.workflow_id)
        if not steps:
            return None

        # Determine current step
        existing_actions_result = await self.db.execute(
            select(ApprovalAction).where(ApprovalAction.instance_id == instance_id)
        )
        existing_actions = list(existing_actions_result.scalars().all())
        current_step_idx = len(existing_actions)

        if current_step_idx >= len(steps):
            return None

        current_step = steps[current_step_idx]

        # Check if this user is an approver for this step
        if current_step.approver_user_id and current_step.approver_user_id != approver_id:
            return None

        action = ApprovalAction(
            instance_id=instance_id,
            step_id=current_step.id,
            approver_id=approver_id,
            action=ApprovalActionType(data.action),
            comments=data.comments,
        )
        self.db.add(action)

        if data.action == "rejected":
            instance.status = ApprovalStatus.rejected
            instance.completed_at = datetime.now(timezone.utc)
            # Notify submitter
            notification = Notification(
                user_id=instance.submitted_by,
                notification_type=NotificationType.approval_status,
                title=f"Approval rejected: {instance.workflow.name}",
                message=data.comments,
            )
            self.db.add(notification)
        elif data.action == "request_changes":
            instance.status = ApprovalStatus.pending  # Stays pending, but needs changes
        else:
            # Check if all steps are approved
            if current_step_idx + 1 >= len(steps):
                instance.status = ApprovalStatus.approved
                instance.completed_at = datetime.now(timezone.utc)
                # Notify submitter
                notification = Notification(
                    user_id=instance.submitted_by,
                    notification_type=NotificationType.approval_status,
                    title=f"Approval approved: {instance.workflow.name}",
                    message="All approvals have been obtained.",
                )
                self.db.add(notification)
            else:
                # Move to next step, notify next approver
                next_step = steps[current_step_idx + 1]
                if next_step.approver_user_id:
                    notification = Notification(
                        user_id=next_step.approver_user_id,
                        notification_type=NotificationType.approval_request,
                        title=f"Approval required: {instance.workflow.name}",
                        message="Previous step approved. Your review is needed.",
                        context_type=DiscussionContextType.dashboard,
                        context_id=instance.id,
                    )
                    self.db.add(notification)

        await self.db.commit()
        await self.db.refresh(instance)
        return instance