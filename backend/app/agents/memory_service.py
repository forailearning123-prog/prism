from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.models import AgentMemory, MemoryType
from app.agents.schemas import AgentMemoryCreate, AgentMemoryUpdate


class MemoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_memory(self, data: AgentMemoryCreate) -> AgentMemory:
        memory = AgentMemory(
            agent_id=data.agent_id,
            memory_type=MemoryType(data.memory_type) if data.memory_type else MemoryType.short_term,
            key=data.key,
            value=data.value,
            metadata=data.metadata,
            context=data.context,
            expires_at=data.expires_at,
        )
        self.db.add(memory)
        await self.db.commit()
        await self.db.refresh(memory)
        return memory

    async def get_memory(self, memory_id: int) -> Optional[AgentMemory]:
        result = await self.db.execute(
            select(AgentMemory).where(AgentMemory.id == memory_id)
        )
        return result.scalar_one_or_none()

    async def get_memories(
        self,
        agent_id: int,
        memory_type: Optional[str] = None,
        key: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[AgentMemory], int]:
        query = select(AgentMemory).where(AgentMemory.agent_id == agent_id)

        if memory_type:
            query = query.where(AgentMemory.memory_type == MemoryType(memory_type))
        if key:
            query = query.where(AgentMemory.key.ilike(f"%{key}%"))

        # Filter out expired memories
        query = query.where(
            (AgentMemory.expires_at == None) | (AgentMemory.expires_at > datetime.now(timezone.utc))
        )

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(AgentMemory.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        memories = result.scalars().all()
        return list(memories), total

    async def update_memory(self, memory_id: int, data: AgentMemoryUpdate) -> Optional[AgentMemory]:
        memory = await self.get_memory(memory_id)
        if not memory:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None:
                setattr(memory, key, value)

        memory.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(memory)
        return memory

    async def delete_memory(self, memory_id: int) -> bool:
        memory = await self.get_memory(memory_id)
        if not memory:
            return False
        await self.db.delete(memory)
        await self.db.commit()
        return True

    async def clear_expired_memories(self, agent_id: int) -> int:
        result = await self.db.execute(
            select(AgentMemory).where(
                AgentMemory.agent_id == agent_id,
                AgentMemory.expires_at != None,
                AgentMemory.expires_at <= datetime.now(timezone.utc),
            )
        )
        expired_memories = result.scalars().all()
        count = 0
        for memory in expired_memories:
            await self.db.delete(memory)
            count += 1
        await self.db.commit()
        return count

    async def get_memory_by_key(self, agent_id: int, key: str, memory_type: Optional[str] = None) -> Optional[AgentMemory]:
        query = select(AgentMemory).where(
            AgentMemory.agent_id == agent_id,
            AgentMemory.key == key,
        )
        if memory_type:
            query = query.where(AgentMemory.memory_type == MemoryType(memory_type))
        query = query.where(
            (AgentMemory.expires_at == None) | (AgentMemory.expires_at > datetime.now(timezone.utc))
        )
        query = query.order_by(AgentMemory.created_at.desc()).limit(1)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()