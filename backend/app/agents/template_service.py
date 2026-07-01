from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.models import AgentTemplate, AgentType
from app.agents.schemas import AgentTemplateListOut


class TemplateService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_templates(
        self,
        agent_type: Optional[str] = None,
        is_active: bool = True,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AgentTemplate], int]:
        query = select(AgentTemplate).where(AgentTemplate.is_active == is_active)

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

    async def get_template_by_name(self, name: str) -> Optional[AgentTemplate]:
        result = await self.db.execute(
            select(AgentTemplate).where(AgentTemplate.name == name, AgentTemplate.is_active == True)
        )
        return result.scalar_one_or_none()

    async def create_template(
        self,
        name: str,
        display_name: str,
        description: str,
        agent_type: str,
        **kwargs,
    ) -> AgentTemplate:
        template = AgentTemplate(
            name=name,
            display_name=display_name,
            description=description,
            agent_type=AgentType(agent_type) if agent_type else AgentType.custom,
            **kwargs,
        )
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def update_template(self, template_id: int, **kwargs) -> Optional[AgentTemplate]:
        template = await self.get_template(template_id)
        if not template:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(template, key):
                setattr(template, key, value)

        template.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def get_popular_templates(self, limit: int = 10) -> list[AgentTemplate]:
        result = await self.db.execute(
            select(AgentTemplate)
            .where(AgentTemplate.is_active == True)
            .order_by(AgentTemplate.deployment_count.desc())
            .limit(limit)
        )
        return list(result.scalars().all())