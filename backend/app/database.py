from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings

settings = get_settings()

engine = create_async_engine(settings.database_url, echo=settings.debug)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


# Import all models to ensure they are registered with SQLAlchemy
from app.models import (
    User, DataSource, Tag, DataSourceTag, MetadataEntry, SyncHistory, ConnectionLog, DataSourcePermission,
    SemanticModel, SemanticModelDataSource, SemanticModelVersion, BusinessEntity, EntityRelationship,
    Dimension, Measure, CalculatedField, KPI, TimeIntelligenceDefinition, Hierarchy, HierarchyLevel,
    BusinessGlossaryTerm, ValidationResult, DocumentationMetadata, ImpactAnalysisSnapshot,
    Dashboard, DashboardVersion, DashboardWidget, DashboardFilter, DashboardTheme, DashboardPermission,
    DashboardLayoutMetadata, DashboardUsage, DashboardRecommendation,
    Conversation, AnalystMessage, ConversationBookmark, SavedInsight, UserFeedback, AnalystAuditLog,
    ReportDefinition,
    ForecastDefinition, ForecastResult, ScenarioPlan, WhatIfVariable, DriverAnalysis,
    RiskAssessment, OpportunityInsight, ForecastVersion, PredictionAlert, RecommendationHistory,
    Monitor, MonitorRule, AlertEvent, AlertComment, NotificationConfig, NotificationDelivery,
    AnomalyEvent, WorkflowDefinition, WorkflowStep, WorkflowExecution, WorkflowStepResult,
    EscalationPolicy, EscalationStep, ScheduledInsight, InsightDeliveryHistory, SLAMetric, SLABreachRecord,
    BusinessHealthScore, AuditRecord,
)

from app.collaboration.models import (
    Workspace, WorkspaceMember,
    Discussion, Comment,
    DecisionRecord, DecisionParticipant, DecisionHistory,
    ActionItem,
    ApprovalWorkflow, ApprovalWorkflowStep, ApprovalInstance, ApprovalAction,
    MeetingSummary, MeetingPack,
    KnowledgeArticle,
    Notification, NotificationPreference,
    CollaborationMetric,
    DecisionImpact,
)

from app.agents.models import (
    AIAgent, AgentTemplate,
    AgentMemory,
    AgentTask, AgentExecution,
    AgentRecommendation,
    AgentCollaboration,
    AgentApproval,
    AgentPerformance,
    AgentActivity,
    AgentPermission,
)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)