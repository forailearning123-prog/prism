from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.models import (
    DashboardCreationMode,
    DashboardFilterScope,
    DashboardPermissionRole,
    DashboardRecommendationType,
    DashboardStatus,
    DashboardVisibility,
    DashboardWidgetType,
)


class DashboardWidgetBase(BaseModel):
    widget_type: DashboardWidgetType
    title: str = Field(default="", max_length=255)
    subtitle: str = Field(default="", max_length=255)
    description: str = Field(default="", max_length=1000)
    data_source: str = Field(default="", max_length=255)
    dimensions: list[str] = Field(default_factory=list)
    measures: list[str] = Field(default_factory=list)
    filters: dict[str, Any] = Field(default_factory=dict)
    colors: dict[str, Any] = Field(default_factory=dict)
    number_formatting: dict[str, Any] = Field(default_factory=dict)
    conditional_formatting: dict[str, Any] = Field(default_factory=dict)
    legends: dict[str, Any] = Field(default_factory=dict)
    labels: dict[str, Any] = Field(default_factory=dict)
    tooltips: dict[str, Any] = Field(default_factory=dict)
    drill_behavior: dict[str, Any] = Field(default_factory=dict)
    config: dict[str, Any] = Field(default_factory=dict)
    position_x: int = Field(default=0, ge=0)
    position_y: int = Field(default=0, ge=0)
    width: int = Field(default=4, ge=1, le=24)
    height: int = Field(default=3, ge=1, le=24)
    z_index: int = Field(default=0, ge=0)
    is_locked: bool = False
    group_key: str = Field(default="", max_length=100)
    alignment: str = Field(default="start", max_length=50)
    snap_to_grid: bool = True


class DashboardWidgetCreate(DashboardWidgetBase):
    pass


class DashboardWidgetUpdate(BaseModel):
    widget_type: DashboardWidgetType | None = None
    title: str | None = Field(default=None, max_length=255)
    subtitle: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    data_source: str | None = Field(default=None, max_length=255)
    dimensions: list[str] | None = None
    measures: list[str] | None = None
    filters: dict[str, Any] | None = None
    colors: dict[str, Any] | None = None
    number_formatting: dict[str, Any] | None = None
    conditional_formatting: dict[str, Any] | None = None
    legends: dict[str, Any] | None = None
    labels: dict[str, Any] | None = None
    tooltips: dict[str, Any] | None = None
    drill_behavior: dict[str, Any] | None = None
    config: dict[str, Any] | None = None
    position_x: int | None = Field(default=None, ge=0)
    position_y: int | None = Field(default=None, ge=0)
    width: int | None = Field(default=None, ge=1, le=24)
    height: int | None = Field(default=None, ge=1, le=24)
    z_index: int | None = Field(default=None, ge=0)
    is_locked: bool | None = None
    group_key: str | None = Field(default=None, max_length=100)
    alignment: str | None = Field(default=None, max_length=50)
    snap_to_grid: bool | None = None


class DashboardWidgetOut(DashboardWidgetBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DashboardFilterBase(BaseModel):
    scope: DashboardFilterScope = DashboardFilterScope.dashboard
    widget_id: int | None = None
    name: str = Field(min_length=1, max_length=255)
    field: str = Field(min_length=1, max_length=255)
    operator: str = Field(default="equals", max_length=50)
    value: dict[str, Any] = Field(default_factory=dict)
    is_saved: bool = False


class DashboardFilterCreate(DashboardFilterBase):
    pass


class DashboardFilterUpdate(BaseModel):
    scope: DashboardFilterScope | None = None
    widget_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    field: str | None = Field(default=None, min_length=1, max_length=255)
    operator: str | None = Field(default=None, max_length=50)
    value: dict[str, Any] | None = None
    is_saved: bool | None = None


class DashboardFilterOut(DashboardFilterBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DashboardPermissionBase(BaseModel):
    visibility: DashboardVisibility = DashboardVisibility.private
    principal: str = Field(min_length=1, max_length=255)
    role: DashboardPermissionRole = DashboardPermissionRole.viewer


class DashboardPermissionCreate(DashboardPermissionBase):
    pass


class DashboardPermissionOut(DashboardPermissionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DashboardRecommendationOut(BaseModel):
    id: int
    recommendation_type: DashboardRecommendationType
    title: str
    description: str
    reason: str
    confidence: float
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    class Config:
        from_attributes = True


class DashboardVersionOut(BaseModel):
    id: int
    version_number: int
    title: str
    description: str
    status: DashboardStatus
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True


class DashboardBase(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: str = Field(default="", max_length=2000)
    folder: str = Field(default="", max_length=255)
    tags: list[str] = Field(default_factory=list)
    semantic_model_id: int | None = None
    theme_id: int | None = None
    auto_save_enabled: bool = True

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, value: list[str]) -> list[str]:
        deduped: list[str] = []
        seen: set[str] = set()
        for item in value:
            tag = item.strip()
            if not tag:
                continue
            key = tag.lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(tag[:100])
        return deduped


class DashboardCreate(DashboardBase):
    creation_mode: DashboardCreationMode = DashboardCreationMode.blank
    ai_prompt: str = Field(default="", max_length=2000)
    kpis: list[str] = Field(default_factory=list)
    dimensions: list[str] = Field(default_factory=list)
    theme_variant: str = Field(default="", max_length=50)


class DashboardUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    folder: str | None = Field(default=None, max_length=255)
    tags: list[str] | None = None
    status: DashboardStatus | None = None
    semantic_model_id: int | None = None
    theme_id: int | None = None
    auto_save_enabled: bool | None = None
    is_favourite: bool | None = None


class DashboardGenerateRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=2000)
    semantic_model_id: int
    theme_variant: str = Field(default="corporate", max_length=50)


class DashboardDraftRequest(BaseModel):
    note: str = Field(default="", max_length=500)


class DashboardPublishRequest(BaseModel):
    note: str = Field(default="", max_length=500)


class DashboardDuplicateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)


class DashboardExportRequest(BaseModel):
    format: str = Field(pattern="^(pdf|png|pptx|excel)$")


class DashboardVersionComparisonOut(BaseModel):
    from_version: int
    to_version: int
    widgets_added: int
    widgets_removed: int
    filters_changed: int
    metadata_changes: dict[str, Any] = Field(default_factory=dict)


class DashboardListItem(BaseModel):
    id: int
    name: str
    description: str
    owner: str
    folder: str
    tags: list[str]
    status: DashboardStatus
    last_updated: datetime
    created_date: datetime
    favourite: bool
    shared_with: list[str]
    semantic_model: str | None = None
    widgets_count: int


class DashboardListResponse(BaseModel):
    items: list[DashboardListItem]
    total: int
    page: int
    page_size: int


class DashboardDetails(DashboardListItem):
    semantic_model_id: int | None = None
    theme_id: int | None = None
    creation_mode: DashboardCreationMode
    ai_prompt: str
    current_version: int
    auto_save_enabled: bool
    metadata: dict[str, Any] = Field(default_factory=dict)
    widgets: list[DashboardWidgetOut] = Field(default_factory=list)
    filters: list[DashboardFilterOut] = Field(default_factory=list)
    permissions: list[DashboardPermissionOut] = Field(default_factory=list)


class DashboardAIRecommendationOut(BaseModel):
    widget_type: DashboardWidgetType
    title: str
    reason: str
    confidence: float
    dimensions: list[str] = Field(default_factory=list)
    measures: list[str] = Field(default_factory=list)


class DashboardAIRecommendationsResponse(BaseModel):
    dashboard_id: int
    recommendations: list[DashboardAIRecommendationOut]


class DashboardUsageOut(BaseModel):
    dashboard_id: int
    views_last_7_days: int
    avg_render_time_ms: float
    avg_widget_count: float
    last_viewed_at: datetime | None = None


class DashboardWorkspaceSummaryOut(BaseModel):
    total: int
    draft: int
    published: int
    archived: int
    favourites: int
