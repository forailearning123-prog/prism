from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.collaboration.models import (
    Discussion,
    DiscussionContextType,
    Comment,
    Notification,
    NotificationType,
)
from app.collaboration.schemas import (
    DiscussionCreate,
    DiscussionUpdate,
    CommentCreate,
    CommentUpdate,
    ReactionToggle,
)


class DiscussionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_discussion(self, data: DiscussionCreate, created_by: int) -> Discussion:
        discussion = Discussion(
            workspace_id=data.workspace_id,
            title=data.title,
            context_type=DiscussionContextType(data.context_type) if data.context_type else None,
            context_id=data.context_id,
            created_by=created_by,
        )
        self.db.add(discussion)
        await self.db.commit()
        await self.db.refresh(discussion)
        return discussion

    async def get_discussion(self, discussion_id: int) -> Optional[Discussion]:
        result = await self.db.execute(
            select(Discussion).where(Discussion.id == discussion_id, Discussion.is_archived == False)
        )
        return result.scalar_one_or_none()

    async def list_discussions(
        self,
        workspace_id: int,
        search: Optional[str] = None,
        context_type: Optional[str] = None,
        context_id: Optional[int] = None,
        is_pinned: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Discussion], int]:
        query = select(Discussion).where(
            Discussion.workspace_id == workspace_id,
            Discussion.is_archived == False,
        )

        if search:
            query = query.where(Discussion.title.ilike(f"%{search}%"))
        if context_type:
            query = query.where(Discussion.context_type == DiscussionContextType(context_type))
        if context_id is not None:
            query = query.where(Discussion.context_id == context_id)
        if is_pinned is not None:
            query = query.where(Discussion.is_pinned == is_pinned)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Discussion.is_pinned.desc(), Discussion.updated_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        discussions = result.scalars().all()

        return list(discussions), total

    async def update_discussion(self, discussion_id: int, data: DiscussionUpdate) -> Optional[Discussion]:
        discussion = await self.get_discussion(discussion_id)
        if not discussion:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None:
                setattr(discussion, key, value)

        discussion.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(discussion)
        return discussion

    async def archive_discussion(self, discussion_id: int) -> bool:
        discussion = await self.get_discussion(discussion_id)
        if not discussion:
            return False
        discussion.is_archived = True
        await self.db.commit()
        return True

    async def toggle_pin(self, discussion_id: int) -> Optional[Discussion]:
        discussion = await self.get_discussion(discussion_id)
        if not discussion:
            return None
        discussion.is_pinned = not discussion.is_pinned
        discussion.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(discussion)
        return discussion


class CommentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_comment(self, data: CommentCreate, created_by: int) -> Optional[Comment]:
        # Verify discussion exists
        result = await self.db.execute(
            select(Discussion).where(Discussion.id == data.discussion_id, Discussion.is_archived == False)
        )
        discussion = result.scalar_one_or_none()
        if not discussion:
            return None

        # If parent_id provided, verify it exists
        if data.parent_id:
            result = await self.db.execute(
                select(Comment).where(Comment.id == data.parent_id, Comment.is_deleted == False)
            )
            parent = result.scalar_one_or_none()
            if not parent:
                return None

        comment = Comment(
            discussion_id=data.discussion_id,
            parent_id=data.parent_id,
            content=data.content,
            content_rich_text=data.content_rich_text,
            mentions=data.mentions,
            attachments=data.attachments,
            created_by=created_by,
        )
        self.db.add(comment)

        # Update discussion comment count
        discussion.comment_count += 1
        discussion.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(comment)

        # Create notifications for mentions
        if data.mentions:
            for mentioned_user_id in data.mentions:
                if mentioned_user_id != created_by:
                    notification = Notification(
                        user_id=mentioned_user_id,
                        notification_type=NotificationType.mention,
                        title=f"You were mentioned in a comment",
                        message=data.content[:200],
                        context_type=DiscussionContextType.dashboard,
                        context_id=data.discussion_id,
                    )
                    self.db.add(notification)
            await self.db.commit()

        return comment

    async def get_comment(self, comment_id: int) -> Optional[Comment]:
        result = await self.db.execute(
            select(Comment).where(Comment.id == comment_id, Comment.is_deleted == False)
        )
        return result.scalar_one_or_none()

    async def get_comments(
        self, discussion_id: int, page: int = 1, page_size: int = 50
    ) -> tuple[list[Comment], int]:
        query = select(Comment).where(
            Comment.discussion_id == discussion_id,
            Comment.is_deleted == False,
            Comment.parent_id == None,  # Top-level comments only
        )

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Comment.created_at.asc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        comments = result.scalars().all()

        return list(comments), total

    async def get_replies(self, comment_id: int) -> list[Comment]:
        result = await self.db.execute(
            select(Comment).where(
                Comment.parent_id == comment_id,
                Comment.is_deleted == False,
            ).order_by(Comment.created_at.asc())
        )
        return list(result.scalars().all())

    async def update_comment(self, comment_id: int, data: CommentUpdate, user_id: int) -> Optional[Comment]:
        comment = await self.get_comment(comment_id)
        if not comment or comment.created_by != user_id:
            return None

        # Save edit history
        history_entry = {
            "previous_content": comment.content,
            "previous_rich_text": comment.content_rich_text,
            "edited_at": datetime.now(timezone.utc).isoformat(),
            "edited_by": user_id,
        }
        edit_history = comment.edit_history or []
        edit_history.append(history_entry)

        comment.edit_history = edit_history
        comment.content = data.content
        comment.content_rich_text = data.content_rich_text
        comment.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(comment)
        return comment

    async def delete_comment(self, comment_id: int, user_id: int) -> bool:
        comment = await self.db.execute(
            select(Comment).where(Comment.id == comment_id)
        )
        comment = comment.scalar_one_or_none()
        if not comment or comment.created_by != user_id:
            return False

        # Soft delete
        comment.is_deleted = True
        comment.content = "[deleted]"
        comment.content_rich_text = None

        # Update discussion comment count
        result = await self.db.execute(
            select(Discussion).where(Discussion.id == comment.discussion_id)
        )
        discussion = result.scalar_one_or_none()
        if discussion and discussion.comment_count > 0:
            discussion.comment_count -= 1

        await self.db.commit()
        return True

    async def toggle_reaction(self, comment_id: int, data: ReactionToggle, user_id: int) -> Optional[Comment]:
        comment = await self.get_comment(comment_id)
        if not comment:
            return None

        reactions = comment.reactions or {}
        emoji = data.reaction
        user_id_str = str(user_id)

        if emoji in reactions:
            if user_id_str in reactions[emoji]:
                reactions[emoji].remove(user_id_str)
                if not reactions[emoji]:
                    del reactions[emoji]
            else:
                reactions[emoji].append(user_id_str)
        else:
            reactions[emoji] = [user_id_str]

        comment.reactions = reactions
        await self.db.commit()
        await self.db.refresh(comment)
        return comment