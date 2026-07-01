from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.models import AIAgent, AgentTemplate, AgentStatus, AgentType
from app.agents.schemas import AIAgentCreate, AIAgentUpdate


class AgentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_agent(self, data: AIAgentCreate, owner_id: int) -> AIAgent:
        agent = AIAgent(
            name=data.name,
            display_name=data.display_name,
            description=data.description,
            agent_type=AgentType(data.agent_type) if data.agent_type else AgentType.custom,
            personality=data.personality,
            goals=data.goals,
            success_metrics=data.success_metrics,
            allowed_actions=data.allowed_actions,
            knowledge_scope=data.knowledge_scope,
            escalation_rules=data.escalation_rules,
            ai_provider=data.ai_provider,
            model_name=data.model_name,
            temperature=data.temperature,
            max_tokens=data.max_tokens,
            system_prompt=data.system_prompt,
            permissions=data.permissions,
            schedule_type=data.schedule_type,
            schedule_cron=data.schedule_cron,
            schedule_timezone=data.schedule_timezone,
            assigned_departments=data.assigned_departments,
            owner_id=owner_id,
        )
        self.db.add(agent)
        await self.db.commit()
        await self.db.refresh(agent)
        return agent

    async def get_agent(self, agent_id: int) -> Optional[AIAgent]:
        result = await self.db.execute(
            select(AIAgent).where(AIAgent.id == agent_id, AIAgent.archived_at == None)
        )
        return result.scalar_one_or_none()

    async def list_agents(
        self,
        owner_id: int,
        agent_type: Optional[str] = None,
        status: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AIAgent], int]:
        query = select(AIAgent).where(AIAgent.owner_id == owner_id, AIAgent.archived_at == None)

        if agent_type:
            query = query.where(AIAgent.agent_type == AgentType(agent_type))
        if status:
            query = query.where(AIAgent.status == AgentStatus(status))
        if is_active is not None:
            query = query.where(AIAgent.is_active == is_active)
        if search:
            query = query.where(
                AIAgent.name.ilike(f"%{search}%") | AIAgent.display_name.ilike(f"%{search}%")
            )

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(AIAgent.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        agents = result.scalars().all()
        return list(agents), total

    async def update_agent(self, agent_id: int, data: AIAgentUpdate) -> Optional[AIAgent]:
        agent = await self.get_agent(agent_id)
        if not agent:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None:
                if key == "agent_type" and value:
                    setattr(agent, key, AgentType(value))
                elif key == "status" and value:
                    setattr(agent, key, AgentStatus(value))
                else:
                    setattr(agent, key, value)

        agent.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(agent)
        return agent

    async def archive_agent(self, agent_id: int) -> bool:
        agent = await self.get_agent(agent_id)
        if not agent:
            return False
        agent.archived_at = datetime.now(timezone.utc)
        agent.is_active = False
        await self.db.commit()
        return True

    async def enable_agent(self, agent_id: int) -> Optional[AIAgent]:
        agent = await self.get_agent(agent_id)
        if not agent:
            return None
        agent.status = AgentStatus.active
        agent.is_active = True
        agent.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(agent)
        return agent

    async def disable_agent(self, agent_id: int) -> Optional[AIAgent]:
        agent = await self.get_agent(agent_id)
        if not agent:
            return None
        agent.status = AgentStatus.inactive
        agent.is_active = False
        agent.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(agent)
        return agent

    async def get_templates(
        self, agent_type: Optional[str] = None, page: int = 1, page_size: int = 20
    ) -> tuple[list[AgentTemplate], int]:
        query = select(AgentTemplate).where(AgentTemplate.is_active == True)

        if agent_type:
            query = query.where(AgentTemplate.agent_type == AgentType(agent_type))

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(AgentTemplate.deployment_count.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        templates = result.scalars().all()
        return list(templates), total

    async def get_template(self, template_id: int) -> Optional[AgentTemplate]:
        result = await self.db.execute(
            select(AgentTemplate).where(AgentTemplate.id == template_id, AgentTemplate.is_active == True)
        )
        return result.scalar_one_or_none()

    async def deploy_from_template(self, template_id: int, owner_id: int, name: str, display_name: str) -> Optional[AIAgent]:
        template = await self.get_template(template_id)
        if not template:
            return None

        agent = AIAgent(
            name=name,
            display_name=display_name,
            description=template.description,
            agent_type=template.agent_type,
            personality=template.personality,
            goals=template.goals,
            success_metrics=template.success_metrics,
            allowed_actions=template.allowed_actions,
            knowledge_scope=template.knowledge_scope,
            escalation_rules=template.escalation_rules,
            system_prompt=template.system_prompt,
            permissions=template.permissions_template,
            owner_id=owner_id,
        )
        self.db.add(agent)

        # Update template deployment count
        template.deployment_count += 1

        await self.db.commit()
        await self.db.refresh(agent)
        return agent