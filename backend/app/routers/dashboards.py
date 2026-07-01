from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_user
from app.dashboard_schemas import (
    DashboardAIRecommendationOut,
    DashboardAIRecommendationsResponse,
    DashboardCreate,
    DashboardDetails,
    DashboardDraftRequest,
    DashboardDuplicateRequest,
    DashboardExportRequest,
    DashboardFilterCreate,
    DashboardFilterOut,
    DashboardFilterUpdate,
    DashboardGenerateRequest,
    DashboardListItem,
    DashboardListResponse,
    DashboardPermissionCreate,
    DashboardPermissionOut,
    DashboardPublishRequest,
    DashboardRecommendationOut,
    DashboardUpdate,
    DashboardUsageOut,
    DashboardVersionComparisonOut,
    DashboardVersionOut,
    DashboardWidgetCreate,
    DashboardWidgetOut,
    DashboardWidgetUpdate,
    DashboardWorkspaceSummaryOut,
)
from app.database import get_db
from app.models import (
    Dashboard,
    DashboardCreationMode,
    DashboardFilter,
    DashboardFilterScope,
    DashboardLayoutMetadata,
    DashboardPermission,
    DashboardPermissionRole,
    DashboardRecommendation,
    DashboardRecommendationType,
    DashboardStatus,
    DashboardTheme,
    DashboardUsage,
    DashboardVersion,
    DashboardVisibility,
    DashboardWidget,
    DashboardWidgetType,
    Dimension,
    KPI,
    SemanticModel,
    User,
)

router = APIRouter(prefix="/dashboards", tags=["dashboards"])


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _build_snapshot(dashboard: Dashboard) -> dict[str, Any]:
    return {
        "name": dashboard.name,
        "description": dashboard.description,
        "folder": dashboard.folder,
        "tags": dashboard.tags,
        "status": dashboard.status.value,
        "favourite": dashboard.is_favourite,
        "semantic_model_id": dashboard.semantic_model_id,
        "theme_id": dashboard.theme_id,
        "creation_mode": dashboard.creation_mode.value,
        "ai_prompt": dashboard.ai_prompt,
        "metadata": dashboard.metadata_json,
        "widgets": [
            {
                "id": widget.id,
                "widget_type": widget.widget_type.value,
                "title": widget.title,
                "subtitle": widget.subtitle,
                "description": widget.description,
                "data_source": widget.data_source,
                "dimensions": widget.dimensions,
                "measures": widget.measures,
                "filters": widget.filters,
                "colors": widget.colors,
                "number_formatting": widget.number_formatting,
                "conditional_formatting": widget.conditional_formatting,
                "legends": widget.legends,
                "labels": widget.labels,
                "tooltips": widget.tooltips,
                "drill_behavior": widget.drill_behavior,
                "config": widget.config,
                "position_x": widget.position_x,
                "position_y": widget.position_y,
                "width": widget.width,
                "height": widget.height,
                "z_index": widget.z_index,
                "is_locked": widget.is_locked,
                "group_key": widget.group_key,
                "alignment": widget.alignment,
                "snap_to_grid": widget.snap_to_grid,
            }
            for widget in dashboard.widgets
        ],
        "filters": [
            {
                "id": item.id,
                "scope": item.scope.value,
                "widget_id": item.widget_id,
                "name": item.name,
                "field": item.field,
                "operator": item.operator,
                "value": item.value,
                "is_saved": item.is_saved,
            }
            for item in dashboard.filters
        ],
        "permissions": [
            {
                "id": item.id,
                "visibility": item.visibility.value,
                "principal": item.principal,
                "role": item.role.value,
            }
            for item in dashboard.permissions
        ],
        "layout_metadata": [
            {
                "key": item.key,
                "value": item.value,
            }
            for item in dashboard.layout_metadata_entries
        ],
    }


async def _record_version(db: AsyncSession, dashboard: Dashboard, *, title: str, description: str, created_by: int) -> None:
    dashboard.current_version += 1
    db.add(
        DashboardVersion(
            dashboard_id=dashboard.id,
            version_number=dashboard.current_version,
            title=title,
            description=description,
            status=dashboard.status,
            snapshot=_build_snapshot(dashboard),
            created_by=created_by,
        )
    )


def _is_share_target(user: User, principal: str) -> bool:
    return principal in {user.email, user.company, user.role.value, "organisation", "team", "department"}


def _can_view(dashboard: Dashboard, user: User) -> bool:
    if dashboard.owner_id == user.id:
        return True
    for permission in dashboard.permissions:
        if _is_share_target(user, permission.principal):
            return True
    return False


def _can_edit(dashboard: Dashboard, user: User) -> bool:
    if dashboard.owner_id == user.id:
        return True
    for permission in dashboard.permissions:
        if _is_share_target(user, permission.principal) and permission.role in {
            DashboardPermissionRole.editor,
            DashboardPermissionRole.owner,
        }:
            return True
    return False


async def _get_dashboard_or_404(db: AsyncSession, dashboard_id: int) -> Dashboard:
    dashboard = await db.scalar(
        select(Dashboard)
        .where(Dashboard.id == dashboard_id, Dashboard.deleted_at.is_(None))
        .options(
            selectinload(Dashboard.owner),
            selectinload(Dashboard.semantic_model),
            selectinload(Dashboard.widgets),
            selectinload(Dashboard.filters),
            selectinload(Dashboard.permissions),
            selectinload(Dashboard.recommendations),
            selectinload(Dashboard.layout_metadata_entries),
            selectinload(Dashboard.usage_entries),
            selectinload(Dashboard.versions),
        )
    )
    if not dashboard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found")
    return dashboard


async def _seed_default_themes(db: AsyncSession) -> None:
    existing = await db.scalar(select(func.count()).select_from(DashboardTheme))
    if existing:
        return
    defaults = [
        DashboardTheme(name="Light", variant="light", is_default=True, brand_colors={"background": "#ffffff", "text": "#111827"}),
        DashboardTheme(name="Dark", variant="dark", is_default=True, brand_colors={"background": "#030712", "text": "#f9fafb"}),
        DashboardTheme(
            name="Corporate",
            variant="corporate",
            is_default=True,
            brand_colors={"primary": "#2563eb", "accent": "#0ea5e9", "background": "#0f172a"},
        ),
    ]
    db.add_all(defaults)
    await db.commit()


def _dashboard_to_list_item(dashboard: Dashboard) -> DashboardListItem:
    return DashboardListItem(
        id=dashboard.id,
        name=dashboard.name,
        description=dashboard.description,
        owner=dashboard.owner.full_name,
        folder=dashboard.folder,
        tags=dashboard.tags,
        status=dashboard.status,
        last_updated=dashboard.updated_at,
        created_date=dashboard.created_at,
        favourite=dashboard.is_favourite,
        shared_with=dashboard.shared_with,
        semantic_model=dashboard.semantic_model.name if dashboard.semantic_model else None,
        widgets_count=len(dashboard.widgets),
    )


def _dashboard_to_details(dashboard: Dashboard) -> DashboardDetails:
    list_item = _dashboard_to_list_item(dashboard)
    return DashboardDetails(
        **list_item.model_dump(),
        semantic_model_id=dashboard.semantic_model_id,
        theme_id=dashboard.theme_id,
        creation_mode=dashboard.creation_mode,
        ai_prompt=dashboard.ai_prompt,
        current_version=dashboard.current_version,
        auto_save_enabled=dashboard.auto_save_enabled,
        metadata=dashboard.metadata_json,
        widgets=[DashboardWidgetOut.model_validate(item) for item in dashboard.widgets],
        filters=[DashboardFilterOut.model_validate(item) for item in dashboard.filters],
        permissions=[DashboardPermissionOut.model_validate(item) for item in dashboard.permissions],
    )


async def _generate_visual_recommendations(db: AsyncSession, semantic_model_id: int, prompt: str) -> list[DashboardAIRecommendationOut]:
    dimensions = (
        await db.scalars(select(Dimension).where(Dimension.semantic_model_id == semantic_model_id).order_by(Dimension.display_name.asc()))
    ).all()
    kpis = (await db.scalars(select(KPI).where(KPI.semantic_model_id == semantic_model_id).order_by(KPI.name.asc()))).all()

    lower_prompt = prompt.lower()
    has_time_intent = any(token in lower_prompt for token in ["month", "year", "trend", "over time", "timeline"])
    has_compare_intent = any(token in lower_prompt for token in ["compare", "vs", "versus", "region", "segment"])
    has_distribution_intent = any(token in lower_prompt for token in ["distribution", "mix", "share", "breakdown"])
    has_correlation_intent = any(token in lower_prompt for token in ["correlation", "relationship", "impact"])

    top_dimensions = [item.display_name for item in dimensions[:3]]
    top_kpis = [item.name for item in kpis[:4]]

    recommendations: list[DashboardAIRecommendationOut] = []

    if top_kpis:
        recommendations.append(
            DashboardAIRecommendationOut(
                widget_type=DashboardWidgetType.kpi_card,
                title="Executive KPI Snapshot",
                reason="KPI cards provide immediate visibility into top business metrics for rapid decision-making.",
                confidence=0.94,
                measures=top_kpis[:3],
            )
        )

    if has_time_intent:
        recommendations.append(
            DashboardAIRecommendationOut(
                widget_type=DashboardWidgetType.line_chart,
                title="Trend Analysis",
                reason="Line charts are best suited for time series analysis and highlight directional movement over time.",
                confidence=0.93,
                dimensions=top_dimensions[:1],
                measures=top_kpis[:2],
            )
        )

    if has_compare_intent:
        recommendations.append(
            DashboardAIRecommendationOut(
                widget_type=DashboardWidgetType.bar_chart,
                title="Comparative Performance",
                reason="Bar charts are effective for comparing KPI values across business categories and regions.",
                confidence=0.9,
                dimensions=top_dimensions[:2],
                measures=top_kpis[:1],
            )
        )

    if has_distribution_intent:
        recommendations.append(
            DashboardAIRecommendationOut(
                widget_type=DashboardWidgetType.donut_chart,
                title="Contribution Mix",
                reason="Donut charts communicate proportional contribution across categories in a compact visual.",
                confidence=0.83,
                dimensions=top_dimensions[:1],
                measures=top_kpis[:1],
            )
        )

    if has_correlation_intent:
        recommendations.append(
            DashboardAIRecommendationOut(
                widget_type=DashboardWidgetType.scatter_chart,
                title="Correlation Overview",
                reason="Scatter plots help identify positive or negative relationships between two measurable variables.",
                confidence=0.82,
                dimensions=top_dimensions[:1],
                measures=top_kpis[:2],
            )
        )

    if not recommendations:
        recommendations = [
            DashboardAIRecommendationOut(
                widget_type=DashboardWidgetType.line_chart,
                title="Performance Trend",
                reason="Time-oriented trend analysis is usually the most actionable default for executive dashboards.",
                confidence=0.8,
                dimensions=top_dimensions[:1],
                measures=top_kpis[:1],
            ),
            DashboardAIRecommendationOut(
                widget_type=DashboardWidgetType.table,
                title="Detailed Data View",
                reason="A table complements summary charts and allows users to inspect precise values.",
                confidence=0.77,
                dimensions=top_dimensions[:2],
                measures=top_kpis[:2],
            ),
        ]

    return recommendations


async def _create_widgets_from_recommendations(
    db: AsyncSession,
    dashboard: Dashboard,
    recommendations: list[DashboardAIRecommendationOut],
) -> None:
    for index, recommendation in enumerate(recommendations):
        row = index // 3
        col = index % 3
        db.add(
            DashboardWidget(
                dashboard_id=dashboard.id,
                widget_type=recommendation.widget_type,
                title=recommendation.title,
                description=recommendation.reason,
                dimensions=recommendation.dimensions,
                measures=recommendation.measures,
                position_x=col * 4,
                position_y=row * 3,
                width=4,
                height=3,
                drill_behavior={"enabled": True, "breadcrumb": True},
            )
        )


@router.get("/workspace-summary", response_model=DashboardWorkspaceSummaryOut)
async def get_workspace_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total = await db.scalar(
        select(func.count())
        .select_from(Dashboard)
        .where(Dashboard.deleted_at.is_(None), Dashboard.owner_id == current_user.id)
    )
    draft = await db.scalar(
        select(func.count())
        .select_from(Dashboard)
        .where(Dashboard.deleted_at.is_(None), Dashboard.owner_id == current_user.id, Dashboard.status == DashboardStatus.draft)
    )
    published = await db.scalar(
        select(func.count())
        .select_from(Dashboard)
        .where(
            Dashboard.deleted_at.is_(None),
            Dashboard.owner_id == current_user.id,
            Dashboard.status == DashboardStatus.published,
        )
    )
    archived = await db.scalar(
        select(func.count())
        .select_from(Dashboard)
        .where(Dashboard.deleted_at.is_(None), Dashboard.owner_id == current_user.id, Dashboard.status == DashboardStatus.archived)
    )
    favourites = await db.scalar(
        select(func.count())
        .select_from(Dashboard)
        .where(Dashboard.deleted_at.is_(None), Dashboard.owner_id == current_user.id, Dashboard.is_favourite.is_(True))
    )
    return DashboardWorkspaceSummaryOut(
        total=total or 0,
        draft=draft or 0,
        published=published or 0,
        archived=archived or 0,
        favourites=favourites or 0,
    )


@router.get("/", response_model=DashboardListResponse)
async def list_dashboards(
    search: str | None = Query(default=None),
    status_filter: DashboardStatus | None = Query(default=None, alias="status"),
    favourite: bool | None = Query(default=None),
    folder: str | None = Query(default=None),
    semantic_model_id: int | None = Query(default=None),
    sort_by: str = Query(default="updated_at"),
    sort_order: str = Query(default="desc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filters = [Dashboard.deleted_at.is_(None), Dashboard.owner_id == current_user.id]

    if search:
        term = f"%{search.strip()}%"
        filters.append(or_(Dashboard.name.ilike(term), Dashboard.description.ilike(term), Dashboard.folder.ilike(term)))
    if status_filter:
        filters.append(Dashboard.status == status_filter)
    if favourite is not None:
        filters.append(Dashboard.is_favourite.is_(favourite))
    if folder:
        filters.append(Dashboard.folder == folder)
    if semantic_model_id:
        filters.append(Dashboard.semantic_model_id == semantic_model_id)

    query = (
        select(Dashboard)
        .where(and_(*filters))
        .options(selectinload(Dashboard.owner), selectinload(Dashboard.semantic_model), selectinload(Dashboard.widgets))
    )

    sort_map = {
        "name": Dashboard.name,
        "status": Dashboard.status,
        "updated_at": Dashboard.updated_at,
        "created_at": Dashboard.created_at,
    }
    sort_column = sort_map.get(sort_by, Dashboard.updated_at)
    if sort_order.lower() == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    total = await db.scalar(select(func.count()).select_from(Dashboard).where(and_(*filters)))
    query = query.offset((page - 1) * page_size).limit(page_size)
    dashboards = (await db.scalars(query)).all()

    return DashboardListResponse(
        items=[_dashboard_to_list_item(item) for item in dashboards],
        total=total or 0,
        page=page,
        page_size=page_size,
    )


@router.post("/", response_model=DashboardDetails, status_code=status.HTTP_201_CREATED)
async def create_dashboard(
    payload: DashboardCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _seed_default_themes(db)

    if payload.semantic_model_id:
        semantic_model = await db.get(SemanticModel, payload.semantic_model_id)
        if not semantic_model:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Semantic model not found")

    dashboard = Dashboard(
        name=payload.name.strip(),
        description=payload.description.strip(),
        owner_id=current_user.id,
        folder=payload.folder.strip(),
        tags=payload.tags,
        status=DashboardStatus.draft,
        semantic_model_id=payload.semantic_model_id,
        theme_id=payload.theme_id,
        creation_mode=payload.creation_mode,
        ai_prompt=payload.ai_prompt.strip(),
        metadata_json={
            "kpis_used": payload.kpis,
            "dimensions_used": payload.dimensions,
            "theme_variant": payload.theme_variant,
            "usage_statistics": {"views": 0, "exports": 0},
            "performance_metrics": {"avg_render_ms": 0, "widget_cache_hits": 0},
        },
    )
    db.add(dashboard)
    await db.flush()

    if payload.creation_mode == DashboardCreationMode.ai and payload.semantic_model_id and payload.ai_prompt.strip():
        recommendations = await _generate_visual_recommendations(db, payload.semantic_model_id, payload.ai_prompt.strip())
        await _create_widgets_from_recommendations(db, dashboard, recommendations)
        for recommendation in recommendations:
            db.add(
                DashboardRecommendation(
                    dashboard_id=dashboard.id,
                    recommendation_type=DashboardRecommendationType.better_chart,
                    title=recommendation.title,
                    description=recommendation.reason,
                    reason=recommendation.reason,
                    confidence=recommendation.confidence,
                    metadata_json={"dimensions": recommendation.dimensions, "measures": recommendation.measures},
                )
            )

    db.add(
        DashboardVersion(
            dashboard_id=dashboard.id,
            version_number=1,
            title="Initial draft",
            description=f"Created using {payload.creation_mode.value} mode",
            status=dashboard.status,
            snapshot=_build_snapshot(dashboard),
            created_by=current_user.id,
        )
    )

    await db.commit()
    dashboard = await _get_dashboard_or_404(db, dashboard.id)
    return _dashboard_to_details(dashboard)


@router.post("/generate-ai", response_model=DashboardDetails, status_code=status.HTTP_201_CREATED)
async def generate_ai_dashboard(
    payload: DashboardGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    semantic_model = await db.get(SemanticModel, payload.semantic_model_id)
    if not semantic_model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Semantic model not found")

    generated_name = payload.prompt.strip().title()[:80] + " Dashboard"
    create_payload = DashboardCreate(
        name=generated_name,
        description=f"AI-generated dashboard for: {payload.prompt.strip()}",
        folder="AI Generated",
        tags=["ai", "generated"],
        semantic_model_id=payload.semantic_model_id,
        creation_mode=DashboardCreationMode.ai,
        ai_prompt=payload.prompt,
        theme_variant=payload.theme_variant,
    )
    return await create_dashboard(create_payload, db, current_user)


@router.get("/{dashboard_id}", response_model=DashboardDetails)
async def get_dashboard(
    dashboard_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dashboard = await _get_dashboard_or_404(db, dashboard_id)
    if not _can_view(dashboard, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    dashboard.last_viewed_at = utcnow()
    db.add(
        DashboardUsage(
            dashboard_id=dashboard.id,
            user_id=current_user.id,
            render_time_ms=dashboard.metadata_json.get("performance_metrics", {}).get("avg_render_ms", 0),
            widget_count=len(dashboard.widgets),
            query_count=max(1, len(dashboard.widgets)),
            metadata_json={"source": "dashboard_open"},
        )
    )
    await db.commit()
    refreshed = await _get_dashboard_or_404(db, dashboard_id)
    return _dashboard_to_details(refreshed)


@router.patch("/{dashboard_id}", response_model=DashboardDetails)
async def update_dashboard(
    dashboard_id: int,
    payload: DashboardUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dashboard = await _get_dashboard_or_404(db, dashboard_id)
    if not _can_edit(dashboard, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(dashboard, key, value)

    if payload.status == DashboardStatus.archived:
        dashboard.archived_at = utcnow()
    if payload.status == DashboardStatus.published:
        dashboard.published_at = utcnow()

    await _record_version(db, dashboard, title="Dashboard update", description="Dashboard metadata updated", created_by=current_user.id)
    await db.commit()
    refreshed = await _get_dashboard_or_404(db, dashboard_id)
    return _dashboard_to_details(refreshed)


@router.delete("/{dashboard_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dashboard(
    dashboard_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dashboard = await _get_dashboard_or_404(db, dashboard_id)
    if dashboard.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can delete dashboard")
    dashboard.deleted_at = utcnow()
    await db.commit()


@router.post("/{dashboard_id}/duplicate", response_model=DashboardDetails, status_code=status.HTTP_201_CREATED)
async def duplicate_dashboard(
    dashboard_id: int,
    payload: DashboardDuplicateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    source = await _get_dashboard_or_404(db, dashboard_id)
    if not _can_view(source, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    duplicated = Dashboard(
        name=payload.name or f"{source.name} (Copy)",
        description=source.description,
        owner_id=current_user.id,
        folder=source.folder,
        tags=source.tags,
        status=DashboardStatus.draft,
        is_favourite=False,
        shared_with=[],
        semantic_model_id=source.semantic_model_id,
        theme_id=source.theme_id,
        creation_mode=source.creation_mode,
        ai_prompt=source.ai_prompt,
        metadata_json=source.metadata_json,
    )
    db.add(duplicated)
    await db.flush()

    for widget in source.widgets:
        db.add(
            DashboardWidget(
                dashboard_id=duplicated.id,
                widget_type=widget.widget_type,
                title=widget.title,
                subtitle=widget.subtitle,
                description=widget.description,
                data_source=widget.data_source,
                dimensions=widget.dimensions,
                measures=widget.measures,
                filters=widget.filters,
                colors=widget.colors,
                number_formatting=widget.number_formatting,
                conditional_formatting=widget.conditional_formatting,
                legends=widget.legends,
                labels=widget.labels,
                tooltips=widget.tooltips,
                drill_behavior=widget.drill_behavior,
                config=widget.config,
                position_x=widget.position_x,
                position_y=widget.position_y,
                width=widget.width,
                height=widget.height,
                z_index=widget.z_index,
                is_locked=widget.is_locked,
                group_key=widget.group_key,
                alignment=widget.alignment,
                snap_to_grid=widget.snap_to_grid,
            )
        )

    for item in source.filters:
        db.add(
            DashboardFilter(
                dashboard_id=duplicated.id,
                scope=item.scope,
                widget_id=None,
                name=item.name,
                field=item.field,
                operator=item.operator,
                value=item.value,
                is_saved=item.is_saved,
            )
        )

    db.add(
        DashboardVersion(
            dashboard_id=duplicated.id,
            version_number=1,
            title="Duplicated draft",
            description=f"Duplicated from dashboard {source.id}",
            status=DashboardStatus.draft,
            snapshot=_build_snapshot(duplicated),
            created_by=current_user.id,
        )
    )

    await db.commit()
    refreshed = await _get_dashboard_or_404(db, duplicated.id)
    return _dashboard_to_details(refreshed)


@router.post("/{dashboard_id}/archive", response_model=DashboardDetails)
async def archive_dashboard(
    dashboard_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dashboard = await _get_dashboard_or_404(db, dashboard_id)
    if not _can_edit(dashboard, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    dashboard.status = DashboardStatus.archived
    dashboard.archived_at = utcnow()
    await _record_version(db, dashboard, title="Archived", description="Dashboard archived", created_by=current_user.id)
    await db.commit()
    refreshed = await _get_dashboard_or_404(db, dashboard_id)
    return _dashboard_to_details(refreshed)


@router.post("/{dashboard_id}/save-draft", response_model=DashboardDetails)
async def save_dashboard_draft(
    dashboard_id: int,
    payload: DashboardDraftRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dashboard = await _get_dashboard_or_404(db, dashboard_id)
    if not _can_edit(dashboard, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    dashboard.status = DashboardStatus.draft
    await _record_version(
        db,
        dashboard,
        title="Draft save",
        description=payload.note or "Draft saved",
        created_by=current_user.id,
    )
    await db.commit()
    refreshed = await _get_dashboard_or_404(db, dashboard_id)
    return _dashboard_to_details(refreshed)


@router.post("/{dashboard_id}/publish", response_model=DashboardDetails)
async def publish_dashboard(
    dashboard_id: int,
    payload: DashboardPublishRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dashboard = await _get_dashboard_or_404(db, dashboard_id)
    if not _can_edit(dashboard, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    dashboard.status = DashboardStatus.published
    dashboard.published_at = utcnow()
    await _record_version(
        db,
        dashboard,
        title="Published",
        description=payload.note or "Dashboard published",
        created_by=current_user.id,
    )
    await db.commit()
    refreshed = await _get_dashboard_or_404(db, dashboard_id)
    return _dashboard_to_details(refreshed)


@router.get("/{dashboard_id}/versions", response_model=list[DashboardVersionOut])
async def list_dashboard_versions(
    dashboard_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dashboard = await _get_dashboard_or_404(db, dashboard_id)
    if not _can_view(dashboard, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    versions = (
        await db.scalars(
            select(DashboardVersion)
            .where(DashboardVersion.dashboard_id == dashboard_id)
            .order_by(DashboardVersion.version_number.desc())
        )
    ).all()
    return [DashboardVersionOut.model_validate(item) for item in versions]


@router.get("/{dashboard_id}/versions/compare", response_model=DashboardVersionComparisonOut)
async def compare_versions(
    dashboard_id: int,
    from_version: int = Query(..., ge=1),
    to_version: int = Query(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dashboard = await _get_dashboard_or_404(db, dashboard_id)
    if not _can_view(dashboard, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    versions = (
        await db.scalars(
            select(DashboardVersion).where(
                DashboardVersion.dashboard_id == dashboard_id,
                DashboardVersion.version_number.in_([from_version, to_version]),
            )
        )
    ).all()
    if len(versions) != 2:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requested versions not found")

    by_number = {version.version_number: version for version in versions}
    from_snapshot = by_number[from_version].snapshot
    to_snapshot = by_number[to_version].snapshot

    from_widgets = {item.get("id") for item in from_snapshot.get("widgets", [])}
    to_widgets = {item.get("id") for item in to_snapshot.get("widgets", [])}

    filters_changed = abs(len(from_snapshot.get("filters", [])) - len(to_snapshot.get("filters", [])))
    metadata_changes = {
        "name_changed": from_snapshot.get("name") != to_snapshot.get("name"),
        "description_changed": from_snapshot.get("description") != to_snapshot.get("description"),
        "theme_changed": from_snapshot.get("theme_id") != to_snapshot.get("theme_id"),
    }

    return DashboardVersionComparisonOut(
        from_version=from_version,
        to_version=to_version,
        widgets_added=len(to_widgets - from_widgets),
        widgets_removed=len(from_widgets - to_widgets),
        filters_changed=filters_changed,
        metadata_changes=metadata_changes,
    )


@router.post("/{dashboard_id}/restore/{version_id}", response_model=DashboardDetails)
async def restore_version(
    dashboard_id: int,
    version_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dashboard = await _get_dashboard_or_404(db, dashboard_id)
    if not _can_edit(dashboard, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    version = await db.scalar(
        select(DashboardVersion).where(DashboardVersion.dashboard_id == dashboard_id, DashboardVersion.id == version_id)
    )
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")

    snapshot = version.snapshot
    dashboard.name = snapshot.get("name", dashboard.name)
    dashboard.description = snapshot.get("description", dashboard.description)
    dashboard.folder = snapshot.get("folder", dashboard.folder)
    dashboard.tags = snapshot.get("tags", dashboard.tags)
    dashboard.theme_id = snapshot.get("theme_id", dashboard.theme_id)
    dashboard.semantic_model_id = snapshot.get("semantic_model_id", dashboard.semantic_model_id)
    dashboard.creation_mode = DashboardCreationMode(snapshot.get("creation_mode", dashboard.creation_mode.value))
    dashboard.ai_prompt = snapshot.get("ai_prompt", dashboard.ai_prompt)

    await db.execute(select(DashboardWidget).where(DashboardWidget.dashboard_id == dashboard.id).execution_options(synchronize_session="fetch"))
    for widget in list(dashboard.widgets):
        await db.delete(widget)

    for widget_data in snapshot.get("widgets", []):
        db.add(
            DashboardWidget(
                dashboard_id=dashboard.id,
                widget_type=DashboardWidgetType(widget_data.get("widget_type", DashboardWidgetType.table.value)),
                title=widget_data.get("title", ""),
                subtitle=widget_data.get("subtitle", ""),
                description=widget_data.get("description", ""),
                data_source=widget_data.get("data_source", ""),
                dimensions=widget_data.get("dimensions", []),
                measures=widget_data.get("measures", []),
                filters=widget_data.get("filters", {}),
                colors=widget_data.get("colors", {}),
                number_formatting=widget_data.get("number_formatting", {}),
                conditional_formatting=widget_data.get("conditional_formatting", {}),
                legends=widget_data.get("legends", {}),
                labels=widget_data.get("labels", {}),
                tooltips=widget_data.get("tooltips", {}),
                drill_behavior=widget_data.get("drill_behavior", {}),
                config=widget_data.get("config", {}),
                position_x=widget_data.get("position_x", 0),
                position_y=widget_data.get("position_y", 0),
                width=widget_data.get("width", 4),
                height=widget_data.get("height", 3),
                z_index=widget_data.get("z_index", 0),
                is_locked=widget_data.get("is_locked", False),
                group_key=widget_data.get("group_key", ""),
                alignment=widget_data.get("alignment", "start"),
                snap_to_grid=widget_data.get("snap_to_grid", True),
            )
        )

    await _record_version(
        db,
        dashboard,
        title="Restored",
        description=f"Restored from version {version.version_number}",
        created_by=current_user.id,
    )

    await db.commit()
    refreshed = await _get_dashboard_or_404(db, dashboard_id)
    return _dashboard_to_details(refreshed)


@router.post("/{dashboard_id}/export")
async def export_dashboard(
    dashboard_id: int,
    payload: DashboardExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dashboard = await _get_dashboard_or_404(db, dashboard_id)
    if not _can_view(dashboard, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    dashboard.metadata_json.setdefault("usage_statistics", {}).setdefault("exports", 0)
    dashboard.metadata_json["usage_statistics"]["exports"] += 1
    await db.commit()

    return {
        "dashboard_id": dashboard.id,
        "name": dashboard.name,
        "format": payload.format,
        "exported_at": utcnow().isoformat(),
        "layout": {
            "widgets": len(dashboard.widgets),
            "filters": len(dashboard.filters),
            "theme_id": dashboard.theme_id,
        },
    }


@router.get("/{dashboard_id}/widgets", response_model=list[DashboardWidgetOut])
async def list_widgets(
    dashboard_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dashboard = await _get_dashboard_or_404(db, dashboard_id)
    if not _can_view(dashboard, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return [DashboardWidgetOut.model_validate(item) for item in dashboard.widgets]


@router.post("/{dashboard_id}/widgets", response_model=DashboardWidgetOut, status_code=status.HTTP_201_CREATED)
async def create_widget(
    dashboard_id: int,
    payload: DashboardWidgetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dashboard = await _get_dashboard_or_404(db, dashboard_id)
    if not _can_edit(dashboard, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    widget = DashboardWidget(dashboard_id=dashboard_id, **payload.model_dump())
    db.add(widget)
    await db.flush()
    await _record_version(db, dashboard, title="Widget added", description=f"Widget {widget.title or widget.id} added", created_by=current_user.id)
    await db.commit()
    refreshed_widget = await db.get(DashboardWidget, widget.id)
    return DashboardWidgetOut.model_validate(refreshed_widget)


@router.patch("/{dashboard_id}/widgets/{widget_id}", response_model=DashboardWidgetOut)
async def update_widget(
    dashboard_id: int,
    widget_id: int,
    payload: DashboardWidgetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dashboard = await _get_dashboard_or_404(db, dashboard_id)
    if not _can_edit(dashboard, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    widget = await db.scalar(select(DashboardWidget).where(DashboardWidget.id == widget_id, DashboardWidget.dashboard_id == dashboard_id))
    if not widget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Widget not found")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(widget, key, value)

    await _record_version(db, dashboard, title="Widget updated", description=f"Widget {widget_id} updated", created_by=current_user.id)
    await db.commit()
    refreshed_widget = await db.get(DashboardWidget, widget_id)
    return DashboardWidgetOut.model_validate(refreshed_widget)


@router.delete("/{dashboard_id}/widgets/{widget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_widget(
    dashboard_id: int,
    widget_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dashboard = await _get_dashboard_or_404(db, dashboard_id)
    if not _can_edit(dashboard, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    widget = await db.scalar(select(DashboardWidget).where(DashboardWidget.id == widget_id, DashboardWidget.dashboard_id == dashboard_id))
    if not widget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Widget not found")

    await db.delete(widget)
    await _record_version(db, dashboard, title="Widget deleted", description=f"Widget {widget_id} deleted", created_by=current_user.id)
    await db.commit()


@router.get("/{dashboard_id}/filters", response_model=list[DashboardFilterOut])
async def list_filters(
    dashboard_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dashboard = await _get_dashboard_or_404(db, dashboard_id)
    if not _can_view(dashboard, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return [DashboardFilterOut.model_validate(item) for item in dashboard.filters]


@router.post("/{dashboard_id}/filters", response_model=DashboardFilterOut, status_code=status.HTTP_201_CREATED)
async def create_filter(
    dashboard_id: int,
    payload: DashboardFilterCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dashboard = await _get_dashboard_or_404(db, dashboard_id)
    if not _can_edit(dashboard, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if payload.scope == DashboardFilterScope.widget and not payload.widget_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="widget_id is required for widget-scope filters")

    filter_item = DashboardFilter(dashboard_id=dashboard_id, **payload.model_dump())
    db.add(filter_item)
    await db.flush()
    await _record_version(db, dashboard, title="Filter added", description=f"Filter {filter_item.name} added", created_by=current_user.id)
    await db.commit()
    refreshed_filter = await db.get(DashboardFilter, filter_item.id)
    return DashboardFilterOut.model_validate(refreshed_filter)


@router.patch("/{dashboard_id}/filters/{filter_id}", response_model=DashboardFilterOut)
async def update_filter(
    dashboard_id: int,
    filter_id: int,
    payload: DashboardFilterUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dashboard = await _get_dashboard_or_404(db, dashboard_id)
    if not _can_edit(dashboard, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    filter_item = await db.scalar(
        select(DashboardFilter).where(DashboardFilter.id == filter_id, DashboardFilter.dashboard_id == dashboard_id)
    )
    if not filter_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Filter not found")

    updates = payload.model_dump(exclude_unset=True)
    if updates.get("scope") == DashboardFilterScope.widget and not updates.get("widget_id") and not filter_item.widget_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="widget_id is required for widget-scope filters")
    for key, value in updates.items():
        setattr(filter_item, key, value)

    await _record_version(db, dashboard, title="Filter updated", description=f"Filter {filter_id} updated", created_by=current_user.id)
    await db.commit()
    refreshed_filter = await db.get(DashboardFilter, filter_id)
    return DashboardFilterOut.model_validate(refreshed_filter)


@router.delete("/{dashboard_id}/filters/{filter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_filter(
    dashboard_id: int,
    filter_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dashboard = await _get_dashboard_or_404(db, dashboard_id)
    if not _can_edit(dashboard, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    filter_item = await db.scalar(
        select(DashboardFilter).where(DashboardFilter.id == filter_id, DashboardFilter.dashboard_id == dashboard_id)
    )
    if not filter_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Filter not found")

    await db.delete(filter_item)
    await _record_version(db, dashboard, title="Filter deleted", description=f"Filter {filter_id} deleted", created_by=current_user.id)
    await db.commit()


@router.get("/{dashboard_id}/sharing", response_model=list[DashboardPermissionOut])
async def list_sharing(
    dashboard_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dashboard = await _get_dashboard_or_404(db, dashboard_id)
    if not _can_view(dashboard, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return [DashboardPermissionOut.model_validate(item) for item in dashboard.permissions]


@router.post("/{dashboard_id}/sharing", response_model=DashboardPermissionOut, status_code=status.HTTP_201_CREATED)
async def create_sharing_permission(
    dashboard_id: int,
    payload: DashboardPermissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dashboard = await _get_dashboard_or_404(db, dashboard_id)
    if dashboard.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can manage sharing")

    existing = await db.scalar(
        select(DashboardPermission).where(
            DashboardPermission.dashboard_id == dashboard_id,
            DashboardPermission.principal == payload.principal,
        )
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Permission already exists for this principal")

    permission = DashboardPermission(
        dashboard_id=dashboard_id,
        visibility=payload.visibility,
        principal=payload.principal,
        role=payload.role,
        granted_by=current_user.id,
    )
    db.add(permission)

    dashboard.shared_with = sorted({*dashboard.shared_with, payload.principal})
    await db.commit()
    refreshed = await db.get(DashboardPermission, permission.id)
    return DashboardPermissionOut.model_validate(refreshed)


@router.delete("/{dashboard_id}/sharing/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sharing_permission(
    dashboard_id: int,
    permission_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dashboard = await _get_dashboard_or_404(db, dashboard_id)
    if dashboard.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can manage sharing")

    permission = await db.scalar(
        select(DashboardPermission).where(
            DashboardPermission.dashboard_id == dashboard_id,
            DashboardPermission.id == permission_id,
        )
    )
    if not permission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")

    await db.delete(permission)
    await db.flush()
    dashboard.shared_with = [item.principal for item in dashboard.permissions if item.id != permission_id]
    await db.commit()


@router.get("/{dashboard_id}/ai-recommendations", response_model=DashboardAIRecommendationsResponse)
async def get_ai_recommendations(
    dashboard_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dashboard = await _get_dashboard_or_404(db, dashboard_id)
    if not _can_view(dashboard, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if not dashboard.semantic_model_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Dashboard is not linked to a semantic model")

    recommendations = await _generate_visual_recommendations(db, dashboard.semantic_model_id, dashboard.ai_prompt or dashboard.name)
    return DashboardAIRecommendationsResponse(dashboard_id=dashboard_id, recommendations=recommendations)


@router.post("/{dashboard_id}/optimize", response_model=list[DashboardRecommendationOut])
async def optimize_dashboard(
    dashboard_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dashboard = await _get_dashboard_or_404(db, dashboard_id)
    if not _can_edit(dashboard, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    await db.execute(
        DashboardRecommendation.__table__.delete().where(DashboardRecommendation.dashboard_id == dashboard_id)
    )

    chart_count = len([item for item in dashboard.widgets if item.widget_type not in {DashboardWidgetType.text_panel, DashboardWidgetType.image}])
    kpi_count = len([item for item in dashboard.widgets if item.widget_type == DashboardWidgetType.kpi_card])

    recommendations: list[DashboardRecommendation] = []
    if chart_count < 2:
        recommendations.append(
            DashboardRecommendation(
                dashboard_id=dashboard_id,
                recommendation_type=DashboardRecommendationType.missing_kpi,
                title="Add more comparative visuals",
                description="Dashboard has limited analytical depth. Add comparison and trend widgets.",
                reason="At least two analytical chart types improve insight quality.",
                confidence=0.88,
            )
        )
    if kpi_count == 0:
        recommendations.append(
            DashboardRecommendation(
                dashboard_id=dashboard_id,
                recommendation_type=DashboardRecommendationType.missing_kpi,
                title="Add KPI summary cards",
                description="No KPI cards detected. Add KPI cards to highlight performance at a glance.",
                reason="Executives need immediate KPI visibility before chart inspection.",
                confidence=0.91,
            )
        )
    if any(widget.width > 8 for widget in dashboard.widgets):
        recommendations.append(
            DashboardRecommendation(
                dashboard_id=dashboard_id,
                recommendation_type=DashboardRecommendationType.layout,
                title="Improve layout density",
                description="Some widgets are very wide. Consider balanced 4-6 column sections.",
                reason="Balanced layout improves scanability and reduces unused space.",
                confidence=0.79,
            )
        )
    if not dashboard.filters:
        recommendations.append(
            DashboardRecommendation(
                dashboard_id=dashboard_id,
                recommendation_type=DashboardRecommendationType.accessibility,
                title="Add quick filters",
                description="No filters configured. Add date/segment quick filters for exploratory analysis.",
                reason="Filter controls improve usability and reduce repetitive dashboard duplication.",
                confidence=0.76,
            )
        )

    if not recommendations:
        recommendations.append(
            DashboardRecommendation(
                dashboard_id=dashboard_id,
                recommendation_type=DashboardRecommendationType.performance,
                title="Dashboard is well balanced",
                description="No critical optimization issues were detected from current metadata.",
                reason="Widget composition and layout are within recommended thresholds.",
                confidence=0.72,
            )
        )

    db.add_all(recommendations)
    await db.commit()

    refreshed = (
        await db.scalars(
            select(DashboardRecommendation)
            .where(DashboardRecommendation.dashboard_id == dashboard_id)
            .order_by(DashboardRecommendation.created_at.desc())
        )
    ).all()
    return [
        DashboardRecommendationOut(
            id=item.id,
            recommendation_type=item.recommendation_type,
            title=item.title,
            description=item.description,
            reason=item.reason,
            confidence=item.confidence,
            metadata=item.metadata_json,
            created_at=item.created_at,
        )
        for item in refreshed
    ]


@router.get("/{dashboard_id}/recommendations", response_model=list[DashboardRecommendationOut])
async def list_dashboard_recommendations(
    dashboard_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dashboard = await _get_dashboard_or_404(db, dashboard_id)
    if not _can_view(dashboard, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return [
        DashboardRecommendationOut(
            id=item.id,
            recommendation_type=item.recommendation_type,
            title=item.title,
            description=item.description,
            reason=item.reason,
            confidence=item.confidence,
            metadata=item.metadata_json,
            created_at=item.created_at,
        )
        for item in dashboard.recommendations
    ]


@router.get("/{dashboard_id}/usage", response_model=DashboardUsageOut)
async def get_dashboard_usage(
    dashboard_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dashboard = await _get_dashboard_or_404(db, dashboard_id)
    if not _can_view(dashboard, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    seven_days_ago = utcnow() - timedelta(days=7)
    usage_entries = (
        await db.scalars(
            select(DashboardUsage)
            .where(DashboardUsage.dashboard_id == dashboard_id, DashboardUsage.viewed_at >= seven_days_ago)
            .order_by(DashboardUsage.viewed_at.desc())
        )
    ).all()

    if not usage_entries:
        return DashboardUsageOut(
            dashboard_id=dashboard_id,
            views_last_7_days=0,
            avg_render_time_ms=0,
            avg_widget_count=0,
            last_viewed_at=dashboard.last_viewed_at,
        )

    total_render = sum(item.render_time_ms for item in usage_entries)
    total_widgets = sum(item.widget_count for item in usage_entries)

    return DashboardUsageOut(
        dashboard_id=dashboard_id,
        views_last_7_days=len(usage_entries),
        avg_render_time_ms=round(total_render / len(usage_entries), 2),
        avg_widget_count=round(total_widgets / len(usage_entries), 2),
        last_viewed_at=usage_entries[0].viewed_at,
    )
