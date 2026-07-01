import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditRecord

logger = logging.getLogger(__name__)


class AuditService:
    """Provides immutable audit logging for monitoring operations."""

    async def log(
        self,
        entity_type: str,
        entity_id: Optional[int],
        action: str,
        user_id: Optional[int],
        changes: Optional[dict] = None,
        metadata: Optional[dict] = None,
        ip_address: Optional[str] = None,
        db: Optional[AsyncSession] = None,
    ):
        """Record an audit log entry."""
        try:
            record = AuditRecord(
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                user_id=user_id,
                changes=changes,
                metadata=metadata,
                ip_address=ip_address,
            )
            db.add(record)
            await db.commit()
        except Exception as e:
            logger.error(f"Error writing audit log: {e}")

    async def get_records(
        self,
        db: AsyncSession,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        action: Optional[str] = None,
        user_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[AuditRecord], int]:
        """Query audit records with filtering and pagination."""
        query = select(AuditRecord)

        if entity_type:
            query = query.where(AuditRecord.entity_type == entity_type)
        if entity_id:
            query = query.where(AuditRecord.entity_id == entity_id)
        if action:
            query = query.where(AuditRecord.action == action)
        if user_id:
            query = query.where(AuditRecord.user_id == user_id)

        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query) or 0

        query = query.order_by(desc(AuditRecord.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        items = list(result.scalars().all())

        return items, total