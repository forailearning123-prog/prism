from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.collaboration.models import (
    MeetingSummary,
    MeetingPack,
    Workspace,
    DecisionRecord,
    ActionItem,
    KnowledgeArticle,
    Discussion,
    Comment,
)
from app.collaboration.schemas import (
    MeetingSummaryCreate,
    MeetingSummaryUpdate,
    MeetingPackGenerate,
    AIAssistantAgendaRequest,
    AIAssistantSummaryRequest,
    AIAssistantAgendaOut,
    AIAssistantSummaryOut,
)


class MeetingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_summary(self, data: MeetingSummaryCreate, created_by: int) -> MeetingSummary:
        summary = MeetingSummary(
            workspace_id=data.workspace_id,
            title=data.title,
            meeting_date=data.meeting_date or datetime.now(timezone.utc),
            agenda=data.agenda,
            discussion_summary=data.discussion_summary,
            decisions_captured=data.decisions_captured,
            action_items_extracted=data.action_items_extracted,
            unresolved_issues=data.unresolved_issues,
            created_by=created_by,
        )
        self.db.add(summary)
        await self.db.commit()
        await self.db.refresh(summary)
        return summary

    async def get_summary(self, summary_id: int) -> Optional[MeetingSummary]:
        result = await self.db.execute(
            select(MeetingSummary).where(MeetingSummary.id == summary_id)
        )
        return result.scalar_one_or_none()

    async def list_summaries(
        self, workspace_id: int, page: int = 1, page_size: int = 20
    ) -> tuple[list[MeetingSummary], int]:
        query = select(MeetingSummary).where(MeetingSummary.workspace_id == workspace_id)
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(MeetingSummary.meeting_date.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        summaries = result.scalars().all()
        return list(summaries), total

    async def update_summary(self, summary_id: int, data: MeetingSummaryUpdate) -> Optional[MeetingSummary]:
        summary = await self.get_summary(summary_id)
        if not summary:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None:
                setattr(summary, key, value)
        summary.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(summary)
        return summary

    async def generate_meeting_pack(self, data: MeetingPackGenerate, created_by: int) -> Optional[MeetingPack]:
        workspace = await self.db.execute(
            select(Workspace).where(Workspace.id == data.workspace_id)
        )
        workspace = workspace.scalar_one_or_none()
        if not workspace:
            return None

        # Gather data for the pack
        generated_date = data.generated_for_date or datetime.now(timezone.utc)

        # Get open decisions
        decisions_result = await self.db.execute(
            select(DecisionRecord).where(
                DecisionRecord.workspace_id == data.workspace_id,
                DecisionRecord.status.in_(["draft", "open", "in_review"]),
            ).order_by(DecisionRecord.priority.desc()).limit(10)
        )
        open_decisions = decisions_result.scalars().all()

        # Get outstanding actions
        actions_result = await self.db.execute(
            select(ActionItem).where(
                ActionItem.workspace_id == data.workspace_id,
                ActionItem.status.in_(["open", "in_progress", "blocked"]),
            ).order_by(ActionItem.due_date.asc()).limit(10)
        )
        outstanding_actions = actions_result.scalars().all()

        # Get recent discussions
        discussions_result = await self.db.execute(
            select(Discussion).where(
                Discussion.workspace_id == data.workspace_id,
                Discussion.is_archived == False,
            ).order_by(Discussion.updated_at.desc()).limit(5)
        )
        recent_discussions = discussions_result.scalars().all()

        content = {
            "generated_at": generated_date.isoformat(),
            "workspace_name": workspace.name,
            "kpi_summary": {},
            "business_highlights": [],
            "risks": [],
            "opportunities": [],
            "forecasts": [],
            "open_decisions": [
                {
                    "id": d.id,
                    "title": d.title,
                    "priority": d.priority.value,
                    "status": d.status.value,
                    "due_date": d.due_date.isoformat() if d.due_date else None,
                }
                for d in open_decisions
            ],
            "outstanding_actions": [
                {
                    "id": a.id,
                    "title": a.title,
                    "assignee_id": a.assignee_id,
                    "due_date": a.due_date.isoformat() if a.due_date else None,
                    "priority": a.priority.value,
                    "status": a.status.value,
                }
                for a in outstanding_actions
            ],
            "recent_discussions": [
                {
                    "id": d.id,
                    "title": d.title,
                    "comment_count": d.comment_count,
                    "updated_at": d.updated_at.isoformat(),
                }
                for d in recent_discussions
            ],
            "ai_recommendations": [],
        }

        pack = MeetingPack(
            workspace_id=data.workspace_id,
            title=data.title,
            generated_for_date=generated_date,
            content=content,
            created_by=created_by,
        )
        self.db.add(pack)
        await self.db.commit()
        await self.db.refresh(pack)
        return pack

    async def get_meeting_pack(self, pack_id: int) -> Optional[MeetingPack]:
        result = await self.db.execute(
            select(MeetingPack).where(MeetingPack.id == pack_id)
        )
        return result.scalar_one_or_none()

    async def list_meeting_packs(
        self, workspace_id: int, page: int = 1, page_size: int = 20
    ) -> tuple[list[MeetingPack], int]:
        query = select(MeetingPack).where(MeetingPack.workspace_id == workspace_id)
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(MeetingPack.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        packs = result.scalars().all()
        return list(packs), total


class AIAssistantService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_agenda(self, request: AIAssistantAgendaRequest) -> AIAssistantAgendaOut:
        # In production, this would call the LLM client
        # For now, generate structured agenda suggestions based on workspace context
        agenda_items = [
            {
                "topic": "Review of Key Metrics",
                "duration_minutes": 15,
                "description": "Review KPIs and performance against targets",
            },
            {
                "topic": "Open Decisions",
                "duration_minutes": 20,
                "description": "Review and update status of open decisions",
            },
            {
                "topic": "Action Items Review",
                "duration_minutes": 15,
                "description": "Review outstanding action items and progress",
            },
            {
                "topic": "Risks and Issues",
                "duration_minutes": 15,
                "description": "Discuss current risks and mitigation strategies",
            },
            {
                "topic": "Next Steps",
                "duration_minutes": 10,
                "description": "Assign new actions and set priorities",
            },
        ]

        if request.meeting_title:
            agenda_items.insert(0, {
                "topic": f"Context: {request.meeting_title}",
                "duration_minutes": 5,
                "description": "Set context for the meeting",
            })

        return AIAssistantAgendaOut(
            agenda_items=agenda_items,
            suggested_duration=75,
            focus_areas=["KPIs", "Decisions", "Actions", "Risks"],
        )

    async def generate_summary(self, request: AIAssistantSummaryRequest) -> AIAssistantSummaryOut:
        # In production, this would call the LLM client
        # For now, generate structured summary from transcript
        return AIAssistantSummaryOut(
            summary=f"Meeting summary for: {request.meeting_title or 'Untitled Meeting'}\n\n"
                    f"Key discussion points were identified from the meeting transcript.",
            decisions_captured=[
                {"title": "Decision identified from discussion", "status": "draft"},
            ],
            action_items=[
                {"title": "Action item extracted from meeting", "assignee": None, "due_date": None},
            ],
            unresolved_issues=["Issue requiring further discussion"],
            follow_up_questions=["What is the timeline for resolution?"],
        )