from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.collaboration.models import KnowledgeArticle, KnowledgeArticleType
from app.collaboration.schemas import (
    KnowledgeArticleCreate,
    KnowledgeArticleUpdate,
    KnowledgeSearchRequest,
)


class KnowledgeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_article(self, data: KnowledgeArticleCreate, created_by: int) -> KnowledgeArticle:
        article = KnowledgeArticle(
            workspace_id=data.workspace_id,
            title=data.title,
            content=data.content,
            article_type=KnowledgeArticleType(data.article_type) if data.article_type else KnowledgeArticleType.best_practice,
            tags=data.tags,
            related_entities=data.related_entities,
            created_by=created_by,
        )
        self.db.add(article)
        await self.db.commit()
        await self.db.refresh(article)
        return article

    async def get_article(self, article_id: int) -> Optional[KnowledgeArticle]:
        result = await self.db.execute(
            select(KnowledgeArticle).where(KnowledgeArticle.id == article_id)
        )
        return result.scalar_one_or_none()

    async def list_articles(
        self,
        workspace_id: int,
        search: Optional[str] = None,
        article_type: Optional[str] = None,
        tags: Optional[list[str]] = None,
        is_published: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[KnowledgeArticle], int]:
        query = select(KnowledgeArticle).where(KnowledgeArticle.workspace_id == workspace_id)

        if search:
            query = query.where(
                or_(
                    KnowledgeArticle.title.ilike(f"%{search}%"),
                    KnowledgeArticle.content.ilike(f"%{search}%"),
                )
            )
        if article_type:
            query = query.where(KnowledgeArticle.article_type == KnowledgeArticleType(article_type))
        if tags:
            query = query.where(KnowledgeArticle.tags.comparator.contains(tags))
        if is_published is not None:
            query = query.where(KnowledgeArticle.is_published == is_published)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(KnowledgeArticle.updated_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        articles = result.scalars().all()
        return list(articles), total

    async def update_article(self, article_id: int, data: KnowledgeArticleUpdate, user_id: int) -> Optional[KnowledgeArticle]:
        article = await self.get_article(article_id)
        if not article:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None:
                if key == "article_type":
                    setattr(article, key, KnowledgeArticleType(value))
                else:
                    setattr(article, key, value)

        article.version += 1
        article.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(article)
        return article

    async def delete_article(self, article_id: int) -> bool:
        article = await self.get_article(article_id)
        if not article:
            return False
        article.is_published = False
        await self.db.commit()
        return True

    async def semantic_search(self, request: KnowledgeSearchRequest) -> list[KnowledgeArticle]:
        query = select(KnowledgeArticle).where(KnowledgeArticle.is_published == True)

        if request.workspace_id:
            query = query.where(KnowledgeArticle.workspace_id == request.workspace_id)
        if request.article_type:
            query = query.where(KnowledgeArticle.article_type == KnowledgeArticleType(request.article_type))
        if request.tags:
            query = query.where(KnowledgeArticle.tags.comparator.contains(request.tags))

        # Simple keyword search across title and content
        if request.query:
            search_term = f"%{request.query}%"
            query = query.where(
                or_(
                    KnowledgeArticle.title.ilike(search_term),
                    KnowledgeArticle.content.ilike(search_term),
                )
            )

        query = query.order_by(KnowledgeArticle.updated_at.desc()).limit(20)
        result = await self.db.execute(query)
        return list(result.scalars().all())