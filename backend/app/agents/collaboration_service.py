from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.models import AgentCollaboration, CollaborationMessageType
from app.agents.schemas import AgentCollaborationCreate


class CollaborationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def send_message(self, data: AgentCollaborationCreate) -> AgentCollaboration:
        message = AgentCollaboration(
            from_agent_id=data.from_agent_id,
            to_agent_id=data.to_agent_id,
            message_type=CollaborationMessageType(data.message_type) if data.message_type else CollaborationMessageType.request,
            subject=data.subject,
            content=data.content,
            payload=data.payload,
            response_to_id=data.response_to_id,
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def get_message(self, message_id: int) -> Optional[AgentCollaboration]:
        result = await self.db.execute(
            select(AgentCollaboration).where(AgentCollaboration.id == message_id)
        )
        return result.scalar_one_or_none()

    async def list_messages(
        self,
        agent_id: int,
        message_type: Optional[str] = None,
        is_read: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AgentCollaboration], int]:
        query = select(AgentCollaboration).where(
            (AgentCollaboration.from_agent_id == agent_id) | (AgentCollaboration.to_agent_id == agent_id)
        )

        if message_type:
            query = query.where(AgentCollaboration.message_type == CollaborationMessageType(message_type))
        if is_read is not None:
            query = query.where(AgentCollaboration.is_read == is_read)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(AgentCollaboration.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        messages = result.scalars().all()
        return list(messages), total

    async def mark_as_read(self, message_id: int) -> Optional[AgentCollaboration]:
        message = await self.get_message(message_id)
        if not message:
            return None
        message.is_read = True
        message.read_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def get_conversation(self, agent1_id: int, agent2_id: int, limit: int = 50) -> list[AgentCollaboration]:
        result = await self.db.execute(
            select(AgentCollaboration)
            .where(
                ((AgentCollaboration.from_agent_id == agent1_id) & (AgentCollaboration.to_agent_id == agent2_id))
                | ((AgentCollaboration.from_agent_id == agent2_id) & (AgentCollaboration.to_agent_id == agent1_id))
            )
            .order_by(AgentCollaboration.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())