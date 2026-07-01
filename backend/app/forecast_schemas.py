from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import ForecastHorizon, ForecastStatus, RiskLevel, ScenarioStatus, TrendDirection


class ForecastSchemaModel(BaseModel):
    model_config = ConfigDict(protected_namespaces=())


class ForecastBase(ForecastSchemaModel):
    name: str = Field(min_length=2, max_length=255)
    description: str = Field(default="", max_length=2000)
    business_domain: str = Field(default="", max_length=255)
    semantic_model_id: int | None = None
    target_metric: str = Field(min_length=2, max_length=255)
    horizon: ForecastHorizon = ForecastHorizon.monthly
    confidence_level: float = Field(default=0.95, ge=0.5, le=0.99)
    variables: list[str] = Field(default_factory=list)

    @field_validator("variables")
    @classmethod
    def normalize_variables(cls, value: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for item in value:
            label = item.strip()
            if not label:
                continue
            key = label.lower()
            if key in seen:
                continue
            seen.add(key)
            normalized.append(label[:255])
        return normalized


class ForecastCreate(ForecastBase):
    pass


class ForecastUpdate(ForecastSchemaModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    business_domain: str | None = Field(default=None, max_length=255)
    semantic_model_id: int | None = None
    target_metric: str | None = Field(default=None, min_length=2, max_length=255)
    horizon: ForecastHorizon | None = None
    confidence_level: float | None = Field(default=None, ge=0.5, le=0.99)
    variables: list[str] | None = None
    status: ForecastStatus | None = None
    model_metadata: dict[str, Any] | None = None


class WhatIfVariableInput(ForecastSchemaModel):
    name: str = Field(min_length=1, max_length=255)
    variable_type: str = Field(default="percentage", max_length=100)
    base_value: float = 0.0
    adjusted_value: float = 0.0
    unit: str = Field(default="%", max_length=50)
    impact_direction: str = Field(default="neutral", max_length=20)


class WhatIfVariableOut(WhatIfVariableInput):
    id: int
    scenario_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ForecastResultOut(ForecastSchemaModel):
    id: int
    forecast_id: int
    version_number: int
    historical_data: list[dict[str, Any]] = Field(default_factory=list)
    forecast_data: list[dict[str, Any]] = Field(default_factory=list)
    confidence_upper: list[dict[str, Any]] = Field(default_factory=list)
    confidence_lower: list[dict[str, Any]] = Field(default_factory=list)
    accuracy_score: float | None = None
    trend_direction: TrendDirection
    executive_summary: str
    key_factors: list[Any] = Field(default_factory=list)
    assumptions: list[Any] = Field(default_factory=list)
    recommendations: list[Any] = Field(default_factory=list)
    model_used: str
    generated_by: int
    created_at: datetime

    class Config:
        from_attributes = True


class ScenarioCreate(ForecastSchemaModel):
    name: str = Field(min_length=2, max_length=255)
    description: str = Field(default="", max_length=2000)
    variables: list[WhatIfVariableInput] = Field(default_factory=list)


class ScenarioUpdate(ForecastSchemaModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    status: ScenarioStatus | None = None
    variables: list[WhatIfVariableInput] | None = None


class ScenarioOut(ForecastSchemaModel):
    id: int
    name: str
    description: str
    forecast_id: int | None = None
    status: ScenarioStatus
    owner_id: int
    variables: list[WhatIfVariableOut] = Field(default_factory=list)
    estimated_impact: dict[str, Any] = Field(default_factory=dict)
    result_summary: str
    created_at: datetime
    updated_at: datetime


class DriverAnalysisOut(ForecastSchemaModel):
    id: int
    forecast_id: int
    target_kpi: str
    drivers: list[dict[str, Any]] = Field(default_factory=list)
    analysis_summary: str
    generated_by: int
    created_at: datetime

    class Config:
        from_attributes = True


class RiskAssessmentCreate(ForecastSchemaModel):
    name: str = Field(min_length=2, max_length=255)
    risk_type: str = Field(min_length=2, max_length=100)
    forecast_id: int | None = None
    risk_level: RiskLevel = RiskLevel.medium
    probability: float = Field(default=0.5, ge=0, le=1)
    business_impact: str = Field(default="", max_length=2000)
    recommended_actions: list[str] = Field(default_factory=list)
    is_active: bool = True


class RiskAssessmentOut(ForecastSchemaModel):
    id: int
    name: str
    risk_type: str
    forecast_id: int | None = None
    owner_id: int
    risk_level: RiskLevel
    probability: float
    business_impact: str
    recommended_actions: list[str] = Field(default_factory=list)
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OpportunityInsightOut(ForecastSchemaModel):
    id: int
    name: str
    opportunity_type: str
    owner_id: int
    expected_value: float | None = None
    confidence_score: float
    description: str
    recommended_actions: list[str] = Field(default_factory=list)
    priority_rank: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ForecastVersionOut(ForecastSchemaModel):
    id: int
    forecast_id: int
    version_number: int
    result_id: int | None = None
    notes: str
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True


class PredictionAlertOut(ForecastSchemaModel):
    id: int
    forecast_id: int
    alert_type: str
    severity: RiskLevel
    title: str
    message: str
    is_read: bool
    owner_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class RecommendationOut(ForecastSchemaModel):
    id: int
    forecast_id: int | None = None
    owner_id: int
    business_objective: str
    expected_impact: str
    confidence: float
    dependencies: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    source_type: str
    is_actioned: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ForecastListItem(ForecastSchemaModel):
    id: int
    name: str
    description: str
    business_domain: str
    semantic_model_id: int | None = None
    target_metric: str
    horizon: ForecastHorizon
    confidence_level: float
    variables: list[str] = Field(default_factory=list)
    status: ForecastStatus
    owner_id: int
    last_generated_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    result_count: int = 0


class ForecastListResponse(ForecastSchemaModel):
    items: list[ForecastListItem]
    total: int
    skip: int
    limit: int


class ForecastDetail(ForecastListItem):
    model_metadata: dict[str, Any] = Field(default_factory=dict)
    latest_result: ForecastResultOut | None = None
    scenarios: list[ScenarioOut] = Field(default_factory=list)
    driver_analysis: DriverAnalysisOut | None = None
    risks: list[RiskAssessmentOut] = Field(default_factory=list)
    versions: list[ForecastVersionOut] = Field(default_factory=list)
    alerts: list[PredictionAlertOut] = Field(default_factory=list)
    recommendations: list[RecommendationOut] = Field(default_factory=list)


class WhatIfAdjustment(ForecastSchemaModel):
    name: str = Field(min_length=1, max_length=255)
    adjustment_percent: float = Field(ge=-100, le=100)
    weight: float | None = Field(default=None, ge=0, le=1)


class WhatIfRequest(ForecastSchemaModel):
    variables: list[WhatIfAdjustment] = Field(default_factory=list)


class WhatIfResult(ForecastSchemaModel):
    baseline_value: float
    projected_value: float
    percentage_change: float
    impact_breakdown: list[dict[str, Any]] = Field(default_factory=list)
    summary: str


class ForecastCompareRequest(ForecastSchemaModel):
    primary_forecast_id: int
    comparison_forecast_id: int


class ForecastCompareOut(ForecastSchemaModel):
    primary_forecast_id: int
    comparison_forecast_id: int
    primary_metric: str
    comparison_metric: str
    primary_latest_value: float
    comparison_latest_value: float
    delta_percentage: float
    accuracy_difference: float | None = None
    summary: str


class ForecastWorkspaceSummaryOut(ForecastSchemaModel):
    total_forecasts: int
    ready_forecasts: int
    in_progress_forecasts: int
    failed_forecasts: int
    archived_forecasts: int
    status_breakdown: dict[str, int] = Field(default_factory=dict)
    recent_activity: list[ForecastListItem] = Field(default_factory=list)


class ForecastExportRequest(ForecastSchemaModel):
    export_format: str = Field(default="json", max_length=50)
