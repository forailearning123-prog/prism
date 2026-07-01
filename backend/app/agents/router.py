from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import get_current_user
from app.models import User
from app.agents.schemas import (
    AIAgentCreate,
    AIAgentUpdate,
    AIAgentOut,
    AIAgentListOut,
    AgentTemplateOut,
    AgentTemplateListOut,
    AgentTaskCreate,
    AgentTaskUpdate,
    AgentTaskOut,
    AgentTaskListOut,
    AgentExecutionOut,
    AgentExecuteRequest,
    AgentExecuteResponse,
    AgentRecommendationOut,
    AgentRecommendationListOut,
    AgentCollaborationCreate,
    AgentCollaborationOut,
    AgentApprovalCreate,
    AgentApprovalOut,
    AgentApprovalAction,
    AgentMemoryCreate,
    AgentMemoryUpdate,
    AgentMemoryOut,
    AgentPerformanceOut,
    AgentPerformanceDashboard,
    AgentActivityOut,
    AgentActivityListOut,
    AgentPermissionCreate,
    AgentPermissionOut,
    AgentScheduleUpdate,
    ErrorResponse,
)
from app.agents import (
    agent_service,
    memory_service,
    task_service,
    execution_service,
    collaboration_service,
    recommendation_service,
    approval_service,
    performance_service,
    template_service,
    governance_service,
)
from app.agents.models import (
    AIAgent,
    AgentStatus,
    AgentType,
    TaskStatus,
    TaskPriority,
    ExecutionStatus,
    ApprovalStatus,
    MemoryType,
    RecommendationType,
    CollaborationMessageType,
)

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


# ── Agent CRUD ──


@router.post("", response_model=AIAgentOut)
async def create_agent(
    data: AIAgentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = agent_service.AgentService(db)
    agent = await svc.create_agent(data, owner_id=current_user.id)
    return agent


@router.get("", response_model=AIAgentListOut)
async def list_agents(
    agent_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = agent_service.AgentService(db)
    agents, total = await svc.list_agents(
        owner_id=current_user.id,
        agent_type=agent_type,
        status=status,
        is_active=is_active,
        search=search,
        page=page,
        page_size=page_size,
    )
    return AIAgentListOut(items=agents, total=total, page=page, page_size=page_size)


@router.get("/{agent_id}", response_model=AIAgentOut)
async def get_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = agent_service.AgentService(db)
    agent = await svc.get_agent(agent_id)
    if not agent or agent.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.put("/{agent_id}", response_model=AIAgentOut)
async def update_agent(
    agent_id: int,
    data: AIAgentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = agent_service.AgentService(db)
    agent = await svc.get_agent(agent_id)
    if not agent or agent.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Agent not found")
    updated = await svc.update_agent(agent_id, data)
    if not updated:
        raise HTTPException(status_code=400, detail="Failed to update agent")
    return updated


@router.delete("/{agent_id}")
async def archive_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = agent_service.AgentService(db)
    agent = await svc.get_agent(agent_id)
    if not agent or agent.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Agent not found")
    success = await svc.archive_agent(agent_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to archive agent")
    return {"message": "Agent archived successfully"}


@router.post("/{agent_id}/enable", response_model=AIAgentOut)
async def enable_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = agent_service.AgentService(db)
    agent = await svc.get_agent(agent_id)
    if not agent or agent.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Agent not found")
    updated = await svc.enable_agent(agent_id)
    if not updated:
        raise HTTPException(status_code=400, detail="Failed to enable agent")
    return updated


@router.post("/{agent_id}/disable", response_model=AIAgentOut)
async def disable_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = agent_service.AgentService(db)
    agent = await svc.get_agent(agent_id)
    if not agent or agent.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Agent not found")
    updated = await svc.disable_agent(agent_id)
    if not updated:
        raise HTTPException(status_code=400, detail="Failed to disable agent")
    return updated


# ── Agent Templates ──


@router.get("/templates", response_model=AgentTemplateListOut)
async def list_templates(
    agent_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = template_service.TemplateService(db)
    templates, total = await svc.list_templates(agent_type=agent_type, page=page, page_size=page_size)
    return AgentTemplateListOut(items=templates, total=total, page=page, page_size=page_size)


@router.get("/templates/{template_id}", response_model=AgentTemplateOut)
async def get_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = template_service.TemplateService(db)
    template = await svc.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.post("/templates/{template_id}/deploy", response_model=AIAgentOut)
async def deploy_template(
    template_id: int,
    name: str = Query(..., min_length=1, max_length=255),
    display_name: str = Query(..., min_length=1, max_length=255),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = agent_service.AgentService(db)
    agent = await svc.deploy_from_template(template_id, current_user.id, name, display_name)
    if not agent:
        raise HTTPException(status_code=404, detail="Template not found")
    return agent


# ── Agent Tasks ──


@router.post("/{agent_id}/tasks", response_model=AgentTaskOut)
async def create_task(
    agent_id: int,
    data: AgentTaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = agent_service.AgentService(db)
    agent = await svc.get_agent(agent_id)
    if not agent or agent.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    task_svc = task_service.TaskService(db)
    task = await task_svc.create_task(data, created_by=current_user.id)
    return task


@router.get("/{agent_id}/tasks", response_model=AgentTaskListOut)
async def list_tasks(
    agent_id: int,
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    task_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = agent_service.AgentService(db)
    agent = await svc.get_agent(agent_id)
    if not agent or agent.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    task_svc = task_service.TaskService(db)
    tasks, total = await task_svc.list_tasks(
        agent_id=agent_id,
        status=status,
        priority=priority,
        task_type=task_type,
        page=page,
        page_size=page_size,
    )
    return AgentTaskListOut(items=tasks, total=total, page=page, page_size=page_size)


@router.get("/{agent_id}/tasks/{task_id}", response_model=AgentTaskOut)
async def get_task(
    agent_id: int,
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = agent_service.AgentService(db)
    agent = await svc.get_agent(agent_id)
    if not agent or agent.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    task_svc = task_service.TaskService(db)
    task = await task_svc.get_task(task_id)
    if not task or task.agent_id != agent_id:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{agent_id}/tasks/{task_id}", response_model=AgentTaskOut)
async def update_task(
    agent_id: int,
    task_id: int,
    data: AgentTaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = agent_service.AgentService(db)
    agent = await svc.get_agent(agent_id)
    if not agent or agent.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    task_svc = task_service.TaskService(db)
    task = await task_svc.get_task(task_id)
    if not task or task.agent_id != agent_id:
        raise HTTPException(status_code=404, detail="Task not found")
    
    updated = await task_svc.update_task(task_id, data)
    if not updated:
        raise HTTPException(status_code=400, detail="Failed to update task")
    return updated


# ── Agent Execution ──


@router.post("/{agent_id}/execute", response_model=AgentExecuteResponse)
async def execute_agent(
    agent_id: int,
    request: AgentExecuteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = agent_service.AgentService(db)
    agent = await svc.get_agent(agent_id)
    if not agent or agent.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Create task
    task_svc = task_service.TaskService(db)
    task = await task_svc.create_task(
        AgentTaskCreate(
            agent_id=agent_id,
            title=request.task_type,
            description=f"Execute {request.task_type}",
            task_type=request.task_type,
            priority=request.priority,
            input_data=request.input_data,
            context=request.context,
        ),
        created_by=current_user.id,
    )
    
    # Start execution
    exec_svc = execution_service.ExecutionService(db)
    execution = await exec_svc.execute_agent_task(
        agent_id=agent_id,
        task_id=task.id,
        request=request,
        triggered_by="user",
        triggered_by_user_id=current_user.id,
    )
    
    # Update task status
    await task_svc.start_task(task.id)
    
    # Log activity
    gov_svc = governance_service.GovernanceService(db)
    await gov_svc.log_activity(
        agent_id=agent_id,
        activity_type="task_execution",
        title=f"Executed task: {task.title}",
        description=f"Task {task.id} started by user {current_user.id}",
        status="started",
        metadata={"task_id": task.id, "execution_id": execution.execution_id},
    )
    
    return AgentExecuteResponse(
        execution_id=execution.execution_id,
        agent_id=agent_id,
        task_id=task.id,
        status=execution.status.value,
        started_at=execution.started_at,
    )


@router.get("/{agent_id}/executions", response_model=list[AgentExecutionOut])
async def list_executions(
    agent_id: int,
    task_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = agent_service.AgentService(db)
    agent = await svc.get_agent(agent_id)
    if not agent or agent.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    exec_svc = execution_service.ExecutionService(db)
    executions, _ = await exec_svc.list_executions(
        agent_id=agent_id,
        task_id=task_id,
        status=status,
        page=page,
        page_size=page_size,
    )
    return executions


# ── Agent Memory ──


@router.post("/{agent_id}/memory", response_model=AgentMemoryOut)
async def create_memory(
    agent_id: int,
    data: AgentMemoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = agent_service.AgentService(db)
    agent = await svc.get_agent(agent_id)
    if not agent or agent.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    mem_svc = memory_service.MemoryService(db)
    memory = await mem_svc.create_memory(data)
    return memory


@router.get("/{agent_id}/memory", response_model=list[AgentMemoryOut])
async def list_memories(
    agent_id: int,
    memory_type: Optional[str] = Query(None),
    key: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = agent_service.AgentService(db)
    agent = await svc.get_agent(agent_id)
    if not agent or agent.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    mem_svc = memory_service.MemoryService(db)
    memories, _ = await mem_svc.get_memories(
        agent_id=agent_id,
        memory_type=memory_type,
        key=key,
        page=page,
        page_size=page_size,
    )
    return memories


@router.put("/{agent_id}/memory/{memory_id}", response_model=AgentMemoryOut)
async def update_memory(
    agent_id: int,
    memory_id: int,
    data: AgentMemoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = agent_service.AgentService(db)
    agent = await svc.get_agent(agent_id)
    if not agent or agent.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    mem_svc = memory_service.MemoryService(db)
    memory = await mem_svc.update_memory(memory_id, data)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    return memory


# ── Agent Recommendations ──


@router.get("/{agent_id}/recommendations", response_model=AgentRecommendationListOut)
async def list_recommendations(
    agent_id: int,
    recommendation_type: Optional[str] = Query(None),
    is_viewed: Optional[bool] = Query(None),
    is_actioned: Optional[bool] = Query(None),
    priority: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = agent_service.AgentService(db)
    agent = await svc.get_agent(agent_id)
    if not agent or agent.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    rec_svc = recommendation_service.RecommendationService(db)
    recommendations, total = await rec_svc.list_recommendations(
        agent_id=agent_id,
        recommendation_type=recommendation_type,
        is_viewed=is_viewed,
        is_actioned=is_actioned,
        priority=priority,
        page=page,
        page_size=page_size,
    )
    return AgentRecommendationListOut(items=recommendations, total=total, page=page, page_size=page_size)


@router.post("/{agent_id}/recommendations/{recommendation_id}/view")
async def mark_recommendation_viewed(
    agent_id: int,
    recommendation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = agent_service.AgentService(db)
    agent = await svc.get_agent(agent_id)
    if not agent or agent.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    rec_svc = recommendation_service.RecommendationService(db)
    recommendation = await rec_svc.mark_as_viewed(recommendation_id)
    if not recommendation:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return {"message": "Recommendation marked as viewed"}


@router.post("/{agent_id}/recommendations/{recommendation_id}/action")
async def mark_recommendation_actioned(
    agent_id: int,
    recommendation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = agent_service.AgentService(db)
    agent = await svc.get_agent(agent_id)
    if not agent or agent.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    rec_svc = recommendation_service.RecommendationService(db)
    recommendation = await rec_svc.mark_as_actioned(recommendation_id)
    if not recommendation:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return {"message": "Recommendation marked as actioned"}


# ── Agent Collaboration ──


@router.post("/{agent_id}/collaborate", response_model=AgentCollaborationOut)
async def send_collaboration_message(
    agent_id: int,
    data: AgentCollaborationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = agent_service.AgentService(db)
    agent = await svc.get_agent(agent_id)
    if not agent or agent.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    collab_svc = collaboration_service.CollaborationService(db)
    message = await collab_svc.send_message(data)
    return message


@router.get("/{agent_id}/messages", response_model=list[AgentCollaborationOut])
async def list_messages(
    agent_id: int,
    message_type: Optional[str] = Query(None),
    is_read: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = agent_service.AgentService(db)
    agent = await svc.get_agent(agent_id)
    if not agent or agent.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    collab_svc = collaboration_service.CollaborationService(db)
    messages, _ = await collab_svc.list_messages(
        agent_id=agent_id,
        message_type=message_type,
        is_read=is_read,
        page=page,
        page_size=page_size,
    )
    return messages


# ── Agent Approvals ──


@router.post("/{agent_id}/approvals", response_model=AgentApprovalOut)
async def create_approval(
    agent_id: int,
    data: AgentApprovalCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = agent_service.AgentService(db)
    agent = await svc.get_agent(agent_id)
    if not agent or agent.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    approval_svc = approval_service.ApprovalService(db)
    approval = await approval_svc.create_approval(data, requested_by=current_user.id)
    return approval


@router.get("/{agent_id}/approvals", response_model=list[AgentApprovalOut])
async def list_approvals(
    agent_id: int,
    status: Optional[str] = Query(None),
    approval_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = agent_service.AgentService(db)
    agent = await svc.get_agent(agent_id)
    if not agent or agent.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    approval_svc = approval_service.ApprovalService(db)
    approvals, _ = await approval_svc.list_approvals(
        agent_id=agent_id,
        status=status,
        approval_type=approval_type,
        page=page,
        page_size=page_size,
    )
    return approvals


@router.post("/{agent_id}/approvals/{approval_id}/action", response_model=AgentApprovalOut)
async def process_approval(
    agent_id: int,
    approval_id: int,
    action_data: AgentApprovalAction,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = agent_service.AgentService(db)
    agent = await svc.get_agent(agent_id)
    if not agent or agent.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    approval_svc = approval_service.ApprovalService(db)
    approval = await approval_svc.process_approval(approval_id, action_data, approved_by=current_user.id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found or already processed")
    return approval


# ── Agent Performance ──


@router.get("/{agent_id}/performance", response_model=AgentPerformanceDashboard)
async def get_performance_dashboard(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = agent_service.AgentService(db)
    agent = await svc.get_agent(agent_id)
    if not agent or agent.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    perf_svc = performance_service.PerformanceService(db)
    dashboard = await perf_svc.get_dashboard(agent_id)
    return dashboard


@router.get("/{agent_id}/metrics", response_model=list[AgentPerformanceOut])
async def list_metrics(
    agent_id: int,
    metric_name: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = agent_service.AgentService(db)
    agent = await svc.get_agent(agent_id)
    if not agent or agent.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    perf_svc = performance_service.PerformanceService(db)
    metrics, _ = await perf_svc.get_metrics(
        agent_id=agent_id,
        metric_name=metric_name,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )
    return metrics


# ── Agent Activity ──


@router.get("/{agent_id}/activity", response_model=AgentActivityListOut)
async def get_activity_feed(
    agent_id: int,
    activity_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = agent_service.AgentService(db)
    agent = await svc.get_agent(agent_id)
    if not agent or agent.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    gov_svc = governance_service.GovernanceService(db)
    activities, total = await gov_svc.get_activity_feed(
        agent_id=agent_id,
        activity_type=activity_type,
        page=page,
        page_size=page_size,
    )
    return AgentActivityListOut(items=activities, total=total, page=page, page_size=page_size)


# ── Agent Permissions ──


@router.post("/{agent_id}/permissions", response_model=AgentPermissionOut)
async def create_permission(
    agent_id: int,
    data: AgentPermissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = agent_service.AgentService(db)
    agent = await svc.get_agent(agent_id)
    if not agent or agent.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    from app.agents.models import AgentPermission
    permission = AgentPermission(
        agent_id=agent_id,
        permission_type=data.permission_type,
        resource_type=data.resource_type,
        resource_id=data.resource_id,
        is_allowed=data.is_allowed,
        conditions=data.conditions,
    )
    db.add(permission)
    await db.commit()
    await db.refresh(permission)
    return permission


# ── Agent Scheduling ──


@router.put("/{agent_id}/schedule", response_model=AIAgentOut)
async def update_schedule(
    agent_id: int,
    data: AgentScheduleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = agent_service.AgentService(db)
    agent = await svc.get_agent(agent_id)
    if not agent or agent.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent.schedule_type = data.schedule_type
    agent.schedule_cron = data.schedule_cron
    agent.schedule_timezone = data.schedule_timezone
    agent.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(agent)
    return agent


# ── Agent Governance ──


@router.get("/{agent_id}/audit-trail")
async def get_audit_trail(
    agent_id: int,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = agent_service.AgentService(db)
    agent = await svc.get_agent(agent_id)
    if not agent or agent.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    gov_svc = governance_service.GovernanceService(db)
    events, total = await gov_svc.get_audit_trail(
        agent_id=agent_id,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )
    return {"items": events, "total": total, "page": page, "page_size": page_size}


@router.get("/{agent_id}/governance")
async def get_governance_summary(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = agent_service.AgentService(db)
    agent = await svc.get_agent(agent_id)
    if not agent or agent.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    gov_svc = governance_service.GovernanceService(db)
    summary = await gov_svc.get_governance_summary(agent_id)
    return summary


# ── Agent Leaderboard ──


@router.get("/leaderboard/top")
async def get_leaderboard(
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    perf_svc = performance_service.PerformanceService(db)
    leaderboard = await perf_svc.get_agent_leaderboard(limit=limit)
    return {"items": leaderboard, "total": len(leaderboard)}