import hashlib
import math
import random
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_user
from app.database import get_db
from app.forecast_schemas import (
    DriverAnalysisOut,
    ForecastCompareOut,
    ForecastCompareRequest,
    ForecastCreate,
    ForecastDetail,
    ForecastExportRequest,
    ForecastListItem,
    ForecastListResponse,
    ForecastResultOut,
    ForecastUpdate,
    ForecastVersionOut,
    ForecastWorkspaceSummaryOut,
    OpportunityInsightOut,
    PredictionAlertOut,
    RecommendationOut,
    RiskAssessmentCreate,
    RiskAssessmentOut,
    ScenarioCreate,
    ScenarioOut,
    ScenarioUpdate,
    WhatIfRequest,
    WhatIfResult,
    WhatIfVariableInput,
    WhatIfVariableOut,
)
from app.models import (
    DriverAnalysis,
    ForecastDefinition,
    ForecastHorizon,
    ForecastResult,
    ForecastStatus,
    ForecastVersion,
    OpportunityInsight,
    PredictionAlert,
    RecommendationHistory,
    RiskAssessment,
    RiskLevel,
    ScenarioPlan,
    ScenarioStatus,
    SemanticModel,
    TrendDirection,
    User,
    WhatIfVariable,
)

router = APIRouter(prefix="/forecasting", tags=["forecasting"])


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _status_counts() -> dict[str, int]:
    return {item.value: 0 for item in ForecastStatus}


def _seed_for(*parts: Any) -> int:
    raw = "::".join(str(part) for part in parts)
    return int(hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16], 16)


def _period_step_days(horizon: ForecastHorizon) -> int:
    return {
        ForecastHorizon.daily: 1,
        ForecastHorizon.weekly: 7,
        ForecastHorizon.monthly: 30,
        ForecastHorizon.quarterly: 91,
        ForecastHorizon.yearly: 365,
    }[horizon]


def _format_period(dt: datetime, horizon: ForecastHorizon) -> str:
    if horizon == ForecastHorizon.daily:
        return dt.strftime("%d %b")
    if horizon == ForecastHorizon.weekly:
        return f"W{dt.isocalendar().week} {dt.year}"
    if horizon == ForecastHorizon.monthly:
        return dt.strftime("%b %Y")
    if horizon == ForecastHorizon.quarterly:
        return f"Q{((dt.month - 1) // 3) + 1} {dt.year}"
    return str(dt.year)


def _metric_profile(metric: str) -> dict[str, Any]:
    lower = metric.lower()
    if "revenue" in lower or "sales" in lower or "cash" in lower:
        return {"base": (90000, 240000), "trend": (0.01, 0.035), "seasonality": 0.08, "noise": 0.03, "min": 1000}
    if "expense" in lower or "cost" in lower:
        return {"base": (40000, 120000), "trend": (-0.01, 0.02), "seasonality": 0.05, "noise": 0.025, "min": 500}
    if "profit" in lower:
        return {"base": (15000, 80000), "trend": (0.005, 0.03), "seasonality": 0.07, "noise": 0.04, "min": 500}
    if "employee" in lower or "headcount" in lower:
        return {"base": (120, 1200), "trend": (0.002, 0.015), "seasonality": 0.02, "noise": 0.015, "min": 5}
    if "churn" in lower:
        return {"base": (3.0, 12.0), "trend": (-0.02, 0.01), "seasonality": 0.06, "noise": 0.035, "min": 0.5, "max": 40}
    if "inventory" in lower:
        return {"base": (800, 5000), "trend": (-0.005, 0.02), "seasonality": 0.1, "noise": 0.03, "min": 50}
    return {"base": (1000, 10000), "trend": (0.005, 0.025), "seasonality": 0.05, "noise": 0.03, "min": 50}


def _round_value(metric: str, value: float) -> float:
    lower = metric.lower()
    if any(token in lower for token in ("churn", "margin", "rate", "%")):
        return round(value, 2)
    if value >= 1000:
        return round(value, 0)
    return round(value, 2)


def _latest_value(result: ForecastResult | None) -> float | None:
    if not result:
        return None
    if result.forecast_data:
        return float(result.forecast_data[-1].get("value", 0))
    if result.historical_data:
        return float(result.historical_data[-1].get("value", 0))
    return None


def _serialize_variable_map(variables: list[WhatIfVariableInput]) -> dict[str, Any]:
    return {
        item.name: {
            "variable_type": item.variable_type,
            "base_value": item.base_value,
            "adjusted_value": item.adjusted_value,
            "unit": item.unit,
            "impact_direction": item.impact_direction,
        }
        for item in variables
    }


def _forecast_to_list_item(forecast: ForecastDefinition) -> ForecastListItem:
    return ForecastListItem(
        id=forecast.id,
        name=forecast.name,
        description=forecast.description,
        business_domain=forecast.business_domain,
        semantic_model_id=forecast.semantic_model_id,
        target_metric=forecast.target_metric,
        horizon=forecast.horizon,
        confidence_level=forecast.confidence_level,
        variables=list(forecast.variables or []),
        status=forecast.status,
        owner_id=forecast.owner_id,
        last_generated_at=forecast.last_generated_at,
        created_at=forecast.created_at,
        updated_at=forecast.updated_at,
        result_count=len(forecast.results or []),
    )


def _scenario_to_out(scenario: ScenarioPlan) -> ScenarioOut:
    return ScenarioOut(
        id=scenario.id,
        name=scenario.name,
        description=scenario.description,
        forecast_id=scenario.forecast_id,
        status=scenario.status,
        owner_id=scenario.owner_id,
        variables=[WhatIfVariableOut.model_validate(item) for item in sorted(scenario.what_if_variables, key=lambda value: value.id)],
        estimated_impact=scenario.estimated_impact or {},
        result_summary=scenario.result_summary or "",
        created_at=scenario.created_at,
        updated_at=scenario.updated_at,
    )


def _forecast_to_detail(
    forecast: ForecastDefinition,
    recommendations: list[RecommendationHistory] | None = None,
) -> ForecastDetail:
    latest_result = max(forecast.results, key=lambda item: item.version_number) if forecast.results else None
    latest_driver = max(forecast.driver_analyses, key=lambda item: item.created_at) if forecast.driver_analyses else None
    recommendation_items = recommendations or []
    return ForecastDetail(
        **_forecast_to_list_item(forecast).model_dump(),
        model_metadata=forecast.model_metadata or {},
        latest_result=ForecastResultOut.model_validate(latest_result) if latest_result else None,
        scenarios=[_scenario_to_out(item) for item in sorted(forecast.scenarios, key=lambda value: value.updated_at, reverse=True)],
        driver_analysis=DriverAnalysisOut.model_validate(latest_driver) if latest_driver else None,
        risks=[RiskAssessmentOut.model_validate(item) for item in sorted(forecast.risk_assessments, key=lambda value: value.updated_at, reverse=True)],
        versions=[ForecastVersionOut.model_validate(item) for item in sorted(forecast.versions, key=lambda value: value.version_number, reverse=True)],
        alerts=[PredictionAlertOut.model_validate(item) for item in sorted(forecast.alerts, key=lambda value: value.created_at, reverse=True)],
        recommendations=[RecommendationOut.model_validate(item) for item in sorted(recommendation_items, key=lambda value: value.created_at, reverse=True)],
    )


async def _get_forecast_or_404(db: AsyncSession, forecast_id: int, user_id: int, *, load_related: bool = True) -> ForecastDefinition:
    query = select(ForecastDefinition).where(ForecastDefinition.id == forecast_id, ForecastDefinition.owner_id == user_id)
    if load_related:
        query = query.options(
            selectinload(ForecastDefinition.results),
            selectinload(ForecastDefinition.scenarios).selectinload(ScenarioPlan.what_if_variables),
            selectinload(ForecastDefinition.driver_analyses),
            selectinload(ForecastDefinition.risk_assessments),
            selectinload(ForecastDefinition.versions),
            selectinload(ForecastDefinition.alerts),
        )
    forecast = await db.scalar(query)
    if not forecast:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Forecast not found")
    return forecast


async def _get_scenario_or_404(db: AsyncSession, forecast_id: int, scenario_id: int, user_id: int) -> ScenarioPlan:
    scenario = await db.scalar(
        select(ScenarioPlan)
        .where(
            ScenarioPlan.id == scenario_id,
            ScenarioPlan.forecast_id == forecast_id,
            ScenarioPlan.owner_id == user_id,
        )
        .options(selectinload(ScenarioPlan.what_if_variables))
    )
    if not scenario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scenario not found")
    return scenario


async def _get_latest_result_or_404(forecast: ForecastDefinition) -> ForecastResult:
    if not forecast.results:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No forecast results available")
    return max(forecast.results, key=lambda item: item.version_number)


def _build_forecast_series(forecast: ForecastDefinition, version_number: int) -> dict[str, Any]:
    profile = _metric_profile(forecast.target_metric)
    rng = random.Random(_seed_for(forecast.id, forecast.target_metric, forecast.horizon.value, version_number))
    base_value = rng.uniform(*profile["base"])
    trend_low, trend_high = profile["trend"]
    trend = rng.uniform(trend_low, trend_high)
    seasonal_strength = profile["seasonality"]
    noise = profile["noise"]
    seasonal_period = 4 if forecast.horizon in {ForecastHorizon.monthly, ForecastHorizon.quarterly} else 6
    points: list[dict[str, Any]] = []
    now = utcnow()
    start = now - timedelta(days=_period_step_days(forecast.horizon) * 11)
    for index in range(18):
        current_dt = start + timedelta(days=_period_step_days(forecast.horizon) * index)
        drift = 1 + (trend * index)
        seasonal = 1 + math.sin((index / seasonal_period) * math.pi * 2) * seasonal_strength
        random_adj = 1 + rng.uniform(-noise, noise)
        raw_value = max(profile.get("min", 0.1), base_value * drift * seasonal * random_adj)
        if "max" in profile:
            raw_value = min(profile["max"], raw_value)
        value = _round_value(forecast.target_metric, raw_value)
        points.append({"period": _format_period(current_dt, forecast.horizon), "value": value, "timestamp": current_dt.isoformat()})
    historical = points[:12]
    projected = points[12:]
    confidence_step = max(0.03, 1 - forecast.confidence_level)
    upper: list[dict[str, Any]] = []
    lower: list[dict[str, Any]] = []
    for index, point in enumerate(projected, start=1):
        margin = abs(float(point["value"])) * (0.05 + confidence_step + index * 0.01)
        upper.append({"period": point["period"], "value": _round_value(forecast.target_metric, float(point["value"]) + margin)})
        lower.append({"period": point["period"], "value": _round_value(forecast.target_metric, max(profile.get("min", 0.1), float(point["value"]) - margin))})
    trend_direction = TrendDirection.up if projected[-1]["value"] > historical[-1]["value"] else TrendDirection.down
    if abs(projected[-1]["value"] - historical[-1]["value"]) / max(abs(historical[-1]["value"]), 1) < 0.01:
        trend_direction = TrendDirection.neutral
    accuracy_score = round(0.85 + rng.random() * 0.1, 3)
    factors = list(forecast.variables or [])[:3] or ["Pricing", "Demand", "Operational capacity"]
    key_factors = [f"{factor} is expected to materially influence {forecast.target_metric.lower()}." for factor in factors]
    assumptions = [
        f"Historical {forecast.target_metric.lower()} seasonality remains directionally consistent.",
        f"No material disruption changes the current {forecast.business_domain.lower() or 'business'} operating baseline.",
        f"Input variables remain within a ±10% planning range over the {forecast.horizon.value} horizon.",
    ]
    recommendations = [
        f"Monitor {factors[0]} weekly to validate the {forecast.target_metric.lower()} trajectory.",
        f"Prepare a contingency scenario if {forecast.target_metric.lower()} deviates by more than 5% from plan.",
        f"Review leading indicators before the next {forecast.horizon.value} planning cycle.",
    ]
    executive_summary = (
        f"{forecast.name} projects {forecast.target_metric.lower()} on a {forecast.horizon.value} basis with "
        f"a {forecast.confidence_level:.0%} confidence setting. The synthetic baseline indicates a "
        f"{trend_direction.value} trend driven by {', '.join(factors[:2])}."
    )
    return {
        "historical": historical,
        "forecast": projected,
        "upper": upper,
        "lower": lower,
        "accuracy_score": accuracy_score,
        "trend_direction": trend_direction,
        "executive_summary": executive_summary,
        "key_factors": key_factors,
        "assumptions": assumptions,
        "recommendations": recommendations,
        "model_used": "Prism Synthetic Forecast Engine v1",
        "metadata": {
            "seed": _seed_for(forecast.id, forecast.target_metric, forecast.horizon.value, version_number),
            "base_value": _round_value(forecast.target_metric, base_value),
            "trend_rate": round(trend, 4),
            "seasonality": round(seasonal_strength, 4),
            "noise": round(noise, 4),
        },
    }


async def _generate_driver_analysis_record(forecast: ForecastDefinition, user_id: int) -> DriverAnalysis:
    rng = random.Random(_seed_for("drivers", forecast.id, forecast.target_metric, forecast.horizon.value))
    pool = list(dict.fromkeys((forecast.variables or []) + [
        "Pricing strategy",
        "Demand generation",
        "Sales conversion",
        "Operational throughput",
        "Retention rate",
        "Channel mix",
    ]))
    count = min(max(4, len(pool[:6])), 6)
    selected = pool[:count]
    raw_weights = [rng.uniform(0.08, 0.26) for _ in selected]
    total_weight = sum(raw_weights) or 1
    remaining = 1.0
    drivers: list[dict[str, Any]] = []
    for index, (name, raw_weight) in enumerate(zip(selected, raw_weights)):
        if index == len(selected) - 1:
            weight = round(max(0.05, remaining), 3)
        else:
            weight = round(raw_weight / total_weight, 3)
            remaining -= weight
        direction = rng.choice(["positive", "negative"]) if name.lower() not in forecast.target_metric.lower() else "positive"
        drivers.append(
            {
                "name": name,
                "weight": weight,
                "direction": direction,
                "description": f"{name} has a measurable {direction} relationship to {forecast.target_metric.lower()} over the planning horizon.",
            }
        )
    normalized_total = sum(item["weight"] for item in drivers) or 1
    for item in drivers:
        item["weight"] = round(item["weight"] / normalized_total, 3)
    return DriverAnalysis(
        forecast_id=forecast.id,
        target_kpi=forecast.target_metric,
        drivers=drivers,
        analysis_summary=f"Top drivers for {forecast.target_metric.lower()} concentrate around commercial momentum, operational execution, and controllable planning inputs.",
        generated_by=user_id,
    )


async def _generate_recommendation_records(forecast: ForecastDefinition, user_id: int, latest_result: ForecastResult) -> list[RecommendationHistory]:
    latest_value = _latest_value(latest_result) or 0
    recommendations = [
        RecommendationHistory(
            forecast_id=forecast.id,
            owner_id=user_id,
            business_objective=f"Protect {forecast.target_metric.lower()} forecast accuracy",
            expected_impact=f"Maintain forecast variance within 3% around a projected value of {latest_value:,.2f}.",
            confidence=0.83,
            dependencies=["Weekly KPI review", "Business stakeholder sign-off"],
            next_steps=["Validate assumptions with finance", "Track leading indicators every planning cycle"],
            source_type="forecast",
        ),
        RecommendationHistory(
            forecast_id=forecast.id,
            owner_id=user_id,
            business_objective=f"Improve downside resilience for {forecast.business_domain or 'core'} operations",
            expected_impact="Reduce downside exposure through scenario triggers and early-warning alerts.",
            confidence=0.79,
            dependencies=["Scenario threshold definition", "Alert routing"],
            next_steps=["Run best/base/worst case scenarios", "Publish trigger thresholds to stakeholders"],
            source_type="forecast",
        ),
        RecommendationHistory(
            forecast_id=forecast.id,
            owner_id=user_id,
            business_objective=f"Prioritize high-impact drivers affecting {forecast.target_metric.lower()}",
            expected_impact="Concentrate operating reviews on the variables with the strongest modeled influence.",
            confidence=0.81,
            dependencies=["Driver analysis", "Department owner alignment"],
            next_steps=["Assign owners to top drivers", "Add driver review to monthly cadence"],
            source_type="forecast",
        ),
    ]
    return recommendations


@router.get("/", response_model=ForecastListResponse)
async def list_forecasts(
    search: str | None = Query(default=None),
    forecast_status: ForecastStatus | None = Query(default=None, alias="status"),
    horizon: ForecastHorizon | None = Query(default=None),
    domain: str | None = Query(default=None),
    sort_by: str = Query(default="updated_at"),
    sort_order: str = Query(default="desc"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    filters = [ForecastDefinition.owner_id == current_user.id]
    if search:
        term = f"%{search.strip()}%"
        filters.append(
            or_(
                ForecastDefinition.name.ilike(term),
                ForecastDefinition.description.ilike(term),
                ForecastDefinition.target_metric.ilike(term),
                ForecastDefinition.business_domain.ilike(term),
            )
        )
    if forecast_status:
        filters.append(ForecastDefinition.status == forecast_status)
    if horizon:
        filters.append(ForecastDefinition.horizon == horizon)
    if domain:
        filters.append(ForecastDefinition.business_domain.ilike(f"%{domain.strip()}%"))

    sort_map = {
        "name": ForecastDefinition.name,
        "created_at": ForecastDefinition.created_at,
        "updated_at": ForecastDefinition.updated_at,
        "status": ForecastDefinition.status,
        "horizon": ForecastDefinition.horizon,
        "last_generated_at": ForecastDefinition.last_generated_at,
    }
    order_column = sort_map.get(sort_by, ForecastDefinition.updated_at)
    order_fn = asc if sort_order.lower() == "asc" else desc

    total = await db.scalar(select(func.count()).select_from(ForecastDefinition).where(*filters)) or 0
    forecasts = (
        await db.scalars(
            select(ForecastDefinition)
            .where(*filters)
            .options(selectinload(ForecastDefinition.results))
            .order_by(order_fn(order_column), desc(ForecastDefinition.id))
            .offset(skip)
            .limit(limit)
        )
    ).all()
    return ForecastListResponse(items=[_forecast_to_list_item(item) for item in forecasts], total=total, skip=skip, limit=limit)


@router.post("/", response_model=ForecastDetail, status_code=status.HTTP_201_CREATED)
async def create_forecast(
    payload: ForecastCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    semantic_model_id = payload.semantic_model_id
    if semantic_model_id is not None:
        model_exists = await db.scalar(
            select(SemanticModel.id).where(SemanticModel.id == semantic_model_id, SemanticModel.owner_id == current_user.id)
        )
        if not model_exists:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Semantic model not found")
    forecast = ForecastDefinition(
        name=payload.name,
        description=payload.description,
        business_domain=payload.business_domain,
        semantic_model_id=payload.semantic_model_id,
        target_metric=payload.target_metric,
        horizon=payload.horizon,
        confidence_level=payload.confidence_level,
        variables=payload.variables,
        owner_id=current_user.id,
        status=ForecastStatus.draft,
        model_metadata={"created_from": "forecasting_workspace"},
    )
    db.add(forecast)
    await db.commit()
    forecast = await _get_forecast_or_404(db, forecast.id, current_user.id)
    return _forecast_to_detail(forecast, recommendations=[])


@router.get("/workspace", response_model=ForecastWorkspaceSummaryOut)
async def get_workspace_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    forecasts = (
        await db.scalars(
            select(ForecastDefinition)
            .where(ForecastDefinition.owner_id == current_user.id)
            .options(selectinload(ForecastDefinition.results))
            .order_by(desc(ForecastDefinition.updated_at))
        )
    ).all()
    breakdown = _status_counts()
    for item in forecasts:
        breakdown[item.status.value] += 1
    return ForecastWorkspaceSummaryOut(
        total_forecasts=len(forecasts),
        ready_forecasts=breakdown[ForecastStatus.ready.value],
        in_progress_forecasts=breakdown[ForecastStatus.generating.value] + breakdown[ForecastStatus.draft.value],
        failed_forecasts=breakdown[ForecastStatus.failed.value],
        archived_forecasts=breakdown[ForecastStatus.archived.value],
        status_breakdown=breakdown,
        recent_activity=[_forecast_to_list_item(item) for item in forecasts[:5]],
    )


@router.get("/risks")
async def list_risks(
    risk_level: RiskLevel | None = Query(default=None),
    forecast_id: int | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    filters = [RiskAssessment.owner_id == current_user.id]
    if risk_level:
        filters.append(RiskAssessment.risk_level == risk_level)
    if forecast_id is not None:
        filters.append(RiskAssessment.forecast_id == forecast_id)
    if is_active is not None:
        filters.append(RiskAssessment.is_active == is_active)
    total = await db.scalar(select(func.count()).select_from(RiskAssessment).where(*filters)) or 0
    items = (
        await db.scalars(
            select(RiskAssessment)
            .where(*filters)
            .order_by(desc(RiskAssessment.updated_at), desc(RiskAssessment.id))
            .offset(skip)
            .limit(limit)
        )
    ).all()
    return {"items": [RiskAssessmentOut.model_validate(item) for item in items], "total": total, "skip": skip, "limit": limit}


@router.post("/risks", response_model=RiskAssessmentOut, status_code=status.HTTP_201_CREATED)
async def create_risk_assessment(
    payload: RiskAssessmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if payload.forecast_id is not None:
        await _get_forecast_or_404(db, payload.forecast_id, current_user.id, load_related=False)
    item = RiskAssessment(
        name=payload.name,
        risk_type=payload.risk_type,
        forecast_id=payload.forecast_id,
        owner_id=current_user.id,
        risk_level=payload.risk_level,
        probability=payload.probability,
        business_impact=payload.business_impact,
        recommended_actions=payload.recommended_actions,
        is_active=payload.is_active,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return RiskAssessmentOut.model_validate(item)


@router.get("/opportunities")
async def list_opportunities(
    is_active: bool | None = Query(default=None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    filters = [OpportunityInsight.owner_id == current_user.id]
    if is_active is not None:
        filters.append(OpportunityInsight.is_active == is_active)
    total = await db.scalar(select(func.count()).select_from(OpportunityInsight).where(*filters)) or 0
    items = (
        await db.scalars(
            select(OpportunityInsight)
            .where(*filters)
            .order_by(asc(OpportunityInsight.priority_rank), desc(OpportunityInsight.updated_at))
            .offset(skip)
            .limit(limit)
        )
    ).all()
    return {"items": [OpportunityInsightOut.model_validate(item) for item in items], "total": total, "skip": skip, "limit": limit}


@router.post("/opportunities/generate")
async def generate_opportunities(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = (
        await db.scalars(
            select(OpportunityInsight)
            .where(OpportunityInsight.owner_id == current_user.id, OpportunityInsight.is_active.is_(True))
            .order_by(asc(OpportunityInsight.priority_rank), desc(OpportunityInsight.updated_at))
        )
    ).all()
    if len(existing) >= 3:
        return [OpportunityInsightOut.model_validate(item) for item in existing[:5]]

    forecasts = (
        await db.scalars(
            select(ForecastDefinition)
            .where(ForecastDefinition.owner_id == current_user.id, ForecastDefinition.status == ForecastStatus.ready)
            .options(selectinload(ForecastDefinition.results))
            .order_by(desc(ForecastDefinition.last_generated_at), desc(ForecastDefinition.updated_at))
        )
    ).all()
    baseline = forecasts[0] if forecasts else None
    latest_result = max(baseline.results, key=lambda item: item.version_number) if baseline and baseline.results else None
    projected_value = _latest_value(latest_result) or 100000
    opportunities = [
        OpportunityInsight(
            name="Expand high-performing segments",
            opportunity_type="growth",
            owner_id=current_user.id,
            expected_value=round(projected_value * 0.08, 2),
            confidence_score=0.82,
            description="Forecast signals indicate headroom to scale the strongest-performing customer or product segments.",
            recommended_actions=["Increase budget behind the top segment", "Align sales coverage to growth territories"],
            priority_rank=1,
        ),
        OpportunityInsight(
            name="Optimize pricing and discount mix",
            opportunity_type="margin",
            owner_id=current_user.id,
            expected_value=round(projected_value * 0.05, 2),
            confidence_score=0.77,
            description="Scenario sensitivity suggests price realization can unlock incremental value without materially changing volume assumptions.",
            recommended_actions=["Audit current discount leakage", "Test a targeted pricing uplift"],
            priority_rank=2,
        ),
        OpportunityInsight(
            name="Improve operational throughput",
            opportunity_type="efficiency",
            owner_id=current_user.id,
            expected_value=round(projected_value * 0.03, 2),
            confidence_score=0.74,
            description="Driver analysis highlights execution efficiency as a controllable lever for improving the forecast range.",
            recommended_actions=["Prioritize workflow bottlenecks", "Track weekly throughput KPIs"],
            priority_rank=3,
        ),
    ]
    db.add_all(opportunities)
    await db.commit()
    return [OpportunityInsightOut.model_validate(item) for item in opportunities]


@router.post("/compare", response_model=ForecastCompareOut)
async def compare_forecasts(
    payload: ForecastCompareRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    primary = await _get_forecast_or_404(db, payload.primary_forecast_id, current_user.id)
    comparison = await _get_forecast_or_404(db, payload.comparison_forecast_id, current_user.id)
    primary_result = await _get_latest_result_or_404(primary)
    comparison_result = await _get_latest_result_or_404(comparison)
    primary_value = _latest_value(primary_result) or 0
    comparison_value = _latest_value(comparison_result) or 0
    _MIN_DIVISOR = 0.01
    delta = 0.0 if abs(comparison_value) < _MIN_DIVISOR else round(((primary_value - comparison_value) / abs(comparison_value)) * 100, 2)
    accuracy_difference = None
    if primary_result.accuracy_score is not None and comparison_result.accuracy_score is not None:
        accuracy_difference = round(primary_result.accuracy_score - comparison_result.accuracy_score, 3)
    return ForecastCompareOut(
        primary_forecast_id=primary.id,
        comparison_forecast_id=comparison.id,
        primary_metric=primary.target_metric,
        comparison_metric=comparison.target_metric,
        primary_latest_value=primary_value,
        comparison_latest_value=comparison_value,
        delta_percentage=delta,
        accuracy_difference=accuracy_difference,
        summary=(
            f"{primary.name} is {abs(delta):.2f}% {'above' if delta >= 0 else 'below'} {comparison.name} based on the latest projected values."
        ),
    )


@router.get("/{forecast_id}", response_model=ForecastDetail)
async def get_forecast_detail(
    forecast_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    forecast = await _get_forecast_or_404(db, forecast_id, current_user.id)
    recommendation_history = (
        await db.scalars(
            select(RecommendationHistory)
            .where(RecommendationHistory.owner_id == current_user.id, RecommendationHistory.forecast_id == forecast_id)
            .order_by(desc(RecommendationHistory.created_at))
        )
    ).all()
    return _forecast_to_detail(forecast, recommendations=recommendation_history)


@router.put("/{forecast_id}", response_model=ForecastDetail)
async def update_forecast(
    forecast_id: int,
    payload: ForecastUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    forecast = await _get_forecast_or_404(db, forecast_id, current_user.id)
    data = payload.model_dump(exclude_unset=True)
    if data.get("semantic_model_id") is not None:
        model_exists = await db.scalar(
            select(SemanticModel.id).where(SemanticModel.id == data["semantic_model_id"], SemanticModel.owner_id == current_user.id)
        )
        if not model_exists:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Semantic model not found")
    for key, value in data.items():
        setattr(forecast, key, value)
    forecast.updated_at = utcnow()
    await db.commit()
    forecast = await _get_forecast_or_404(db, forecast_id, current_user.id)
    recommendation_history = (
        await db.scalars(
            select(RecommendationHistory)
            .where(RecommendationHistory.owner_id == current_user.id, RecommendationHistory.forecast_id == forecast_id)
            .order_by(desc(RecommendationHistory.created_at))
        )
    ).all()
    return _forecast_to_detail(forecast, recommendations=recommendation_history)


@router.delete("/{forecast_id}")
async def delete_forecast(
    forecast_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    forecast = await _get_forecast_or_404(db, forecast_id, current_user.id, load_related=False)
    forecast.status = ForecastStatus.archived
    forecast.updated_at = utcnow()
    await db.commit()
    return {"message": "Forecast archived", "forecast_id": forecast_id, "status": forecast.status.value}


@router.post("/{forecast_id}/duplicate", response_model=ForecastDetail, status_code=status.HTTP_201_CREATED)
async def duplicate_forecast(
    forecast_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    source = await _get_forecast_or_404(db, forecast_id, current_user.id, load_related=False)
    duplicate = ForecastDefinition(
        name=f"{source.name} Copy",
        description=source.description,
        business_domain=source.business_domain,
        semantic_model_id=source.semantic_model_id,
        target_metric=source.target_metric,
        horizon=source.horizon,
        confidence_level=source.confidence_level,
        variables=list(source.variables or []),
        status=ForecastStatus.draft,
        owner_id=current_user.id,
        model_metadata={**(source.model_metadata or {}), "duplicated_from": source.id},
    )
    db.add(duplicate)
    await db.commit()
    duplicate = await _get_forecast_or_404(db, duplicate.id, current_user.id)
    return _forecast_to_detail(duplicate, recommendations=[])


@router.post("/{forecast_id}/generate", response_model=ForecastResultOut)
async def generate_forecast(
    forecast_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    forecast = await _get_forecast_or_404(db, forecast_id, current_user.id)
    if forecast.status == ForecastStatus.archived:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Archived forecasts cannot be generated")
    forecast.status = ForecastStatus.generating
    forecast.updated_at = utcnow()
    await db.flush()
    next_version = (max((item.version_number for item in forecast.versions), default=0) + 1) if forecast.versions else 1
    generated = _build_forecast_series(forecast, next_version)
    result = ForecastResult(
        forecast_id=forecast.id,
        version_number=next_version,
        historical_data=generated["historical"],
        forecast_data=generated["forecast"],
        confidence_upper=generated["upper"],
        confidence_lower=generated["lower"],
        accuracy_score=generated["accuracy_score"],
        trend_direction=generated["trend_direction"],
        executive_summary=generated["executive_summary"],
        key_factors=generated["key_factors"],
        assumptions=generated["assumptions"],
        recommendations=generated["recommendations"],
        model_used=generated["model_used"],
        generated_by=current_user.id,
    )
    db.add(result)
    await db.flush()
    forecast.status = ForecastStatus.ready
    forecast.last_generated_at = utcnow()
    forecast.updated_at = utcnow()
    forecast.model_metadata = {**(forecast.model_metadata or {}), **generated["metadata"], "latest_version": next_version}
    db.add(
        ForecastVersion(
            forecast_id=forecast.id,
            version_number=next_version,
            result_id=result.id,
            notes=f"Synthetic forecast generated for {forecast.target_metric} ({forecast.horizon.value}).",
            created_by=current_user.id,
        )
    )
    if result.trend_direction == TrendDirection.up:
        severity = RiskLevel.low
    elif result.trend_direction == TrendDirection.neutral:
        severity = RiskLevel.medium
    else:
        severity = RiskLevel.high
    db.add(
        PredictionAlert(
            forecast_id=forecast.id,
            alert_type="generation",
            severity=severity,
            title="Forecast generation complete",
            message=f"Version {next_version} is ready with an accuracy score of {result.accuracy_score:.1%}.",
            owner_id=current_user.id,
        )
    )
    await db.commit()
    await db.refresh(result)
    return ForecastResultOut.model_validate(result)


@router.get("/{forecast_id}/results", response_model=list[ForecastResultOut])
async def list_forecast_results(
    forecast_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    forecast = await _get_forecast_or_404(db, forecast_id, current_user.id)
    return [ForecastResultOut.model_validate(item) for item in sorted(forecast.results, key=lambda value: value.version_number, reverse=True)]


@router.get("/{forecast_id}/results/latest", response_model=ForecastResultOut)
async def get_latest_result(
    forecast_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    forecast = await _get_forecast_or_404(db, forecast_id, current_user.id)
    return ForecastResultOut.model_validate(await _get_latest_result_or_404(forecast))


@router.get("/{forecast_id}/scenarios", response_model=list[ScenarioOut])
async def list_scenarios(
    forecast_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_forecast_or_404(db, forecast_id, current_user.id, load_related=False)
    scenarios = (
        await db.scalars(
            select(ScenarioPlan)
            .where(ScenarioPlan.forecast_id == forecast_id, ScenarioPlan.owner_id == current_user.id)
            .options(selectinload(ScenarioPlan.what_if_variables))
            .order_by(desc(ScenarioPlan.updated_at))
        )
    ).all()
    return [_scenario_to_out(item) for item in scenarios]


@router.post("/{forecast_id}/scenarios", response_model=ScenarioOut, status_code=status.HTTP_201_CREATED)
async def create_scenario(
    forecast_id: int,
    payload: ScenarioCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_forecast_or_404(db, forecast_id, current_user.id, load_related=False)
    scenario = ScenarioPlan(
        name=payload.name,
        description=payload.description,
        forecast_id=forecast_id,
        variables=_serialize_variable_map(payload.variables),
        status=ScenarioStatus.draft,
        owner_id=current_user.id,
    )
    db.add(scenario)
    await db.flush()
    for item in payload.variables:
        db.add(
            WhatIfVariable(
                scenario_id=scenario.id,
                name=item.name,
                variable_type=item.variable_type,
                base_value=item.base_value,
                adjusted_value=item.adjusted_value,
                unit=item.unit,
                impact_direction=item.impact_direction,
            )
        )
    await db.commit()
    scenario = await _get_scenario_or_404(db, forecast_id, scenario.id, current_user.id)
    return _scenario_to_out(scenario)


@router.get("/{forecast_id}/scenarios/{scenario_id}", response_model=ScenarioOut)
async def get_scenario_detail(
    forecast_id: int,
    scenario_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_forecast_or_404(db, forecast_id, current_user.id, load_related=False)
    return _scenario_to_out(await _get_scenario_or_404(db, forecast_id, scenario_id, current_user.id))


@router.put("/{forecast_id}/scenarios/{scenario_id}", response_model=ScenarioOut)
async def update_scenario(
    forecast_id: int,
    scenario_id: int,
    payload: ScenarioUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    scenario = await _get_scenario_or_404(db, forecast_id, scenario_id, current_user.id)
    data = payload.model_dump(exclude_unset=True)
    variable_payload = data.pop("variables", None)
    for key, value in data.items():
        setattr(scenario, key, value)
    if variable_payload is not None:
        scenario.variables = _serialize_variable_map([WhatIfVariableInput(**item) if isinstance(item, dict) else item for item in variable_payload])
        for variable in list(scenario.what_if_variables):
            await db.delete(variable)
        await db.flush()
        for item in variable_payload:
            variable = WhatIfVariableInput(**item) if isinstance(item, dict) else item
            db.add(
                WhatIfVariable(
                    scenario_id=scenario.id,
                    name=variable.name,
                    variable_type=variable.variable_type,
                    base_value=variable.base_value,
                    adjusted_value=variable.adjusted_value,
                    unit=variable.unit,
                    impact_direction=variable.impact_direction,
                )
            )
    scenario.updated_at = utcnow()
    await db.commit()
    scenario = await _get_scenario_or_404(db, forecast_id, scenario_id, current_user.id)
    return _scenario_to_out(scenario)


@router.delete("/{forecast_id}/scenarios/{scenario_id}")
async def delete_scenario(
    forecast_id: int,
    scenario_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    scenario = await _get_scenario_or_404(db, forecast_id, scenario_id, current_user.id)
    await db.delete(scenario)
    await db.commit()
    return {"message": "Scenario deleted", "scenario_id": scenario_id}


@router.post("/{forecast_id}/scenarios/{scenario_id}/run", response_model=ScenarioOut)
async def run_scenario(
    forecast_id: int,
    scenario_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    forecast = await _get_forecast_or_404(db, forecast_id, current_user.id)
    scenario = await _get_scenario_or_404(db, forecast_id, scenario_id, current_user.id)
    latest_result = await _get_latest_result_or_404(forecast)
    baseline = _latest_value(latest_result) or 0
    scenario.status = ScenarioStatus.running
    await db.flush()
    contributions = []
    total_change = 0.0
    for item in scenario.what_if_variables:
        base = item.base_value or 0
        delta_pct = 0.0 if base == 0 else ((item.adjusted_value - base) / abs(base))
        BASE_WEIGHT = 0.06
        WEIGHT_VARIATION_DIVISOR = 100
        WEIGHT_VARIATION_RANGE = 12
        weight = BASE_WEIGHT + (_seed_for(item.name, scenario.id) % WEIGHT_VARIATION_RANGE) / WEIGHT_VARIATION_DIVISOR
        contribution = delta_pct * weight
        total_change += contribution
        contributions.append({"name": item.name, "change_percent": round(delta_pct * 100, 2), "weight": round(weight, 3)})
    projected = round(baseline * (1 + total_change), 2)
    scenario.status = ScenarioStatus.complete
    scenario.estimated_impact = {
        "baseline_value": round(baseline, 2),
        "projected_value": projected,
        "percentage_change": round(total_change * 100, 2),
        "variables": contributions,
    }
    scenario.result_summary = (
        f"Scenario '{scenario.name}' changes the projected {forecast.target_metric.lower()} by {total_change * 100:.2f}% "
        f"relative to the current baseline."
    )
    scenario.updated_at = utcnow()
    await db.commit()
    scenario = await _get_scenario_or_404(db, forecast_id, scenario_id, current_user.id)
    return _scenario_to_out(scenario)


@router.post("/{forecast_id}/what-if", response_model=WhatIfResult)
async def run_what_if(
    forecast_id: int,
    payload: WhatIfRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    forecast = await _get_forecast_or_404(db, forecast_id, current_user.id)
    latest_result = await _get_latest_result_or_404(forecast)
    baseline = _latest_value(latest_result) or 0
    total_change = 0.0
    breakdown: list[dict[str, Any]] = []
    for item in payload.variables:
        weight = item.weight if item.weight is not None else 0.05 + (_seed_for(item.name, forecast.id) % 12) / 100
        contribution = (item.adjustment_percent / 100) * weight
        total_change += contribution
        breakdown.append(
            {
                "name": item.name,
                "adjustment_percent": item.adjustment_percent,
                "weight": round(weight, 3),
                "contribution_percent": round(contribution * 100, 2),
            }
        )
    projected = round(baseline * (1 + total_change), 2)
    return WhatIfResult(
        baseline_value=round(baseline, 2),
        projected_value=projected,
        percentage_change=round(total_change * 100, 2),
        impact_breakdown=breakdown,
        summary=f"Projected {forecast.target_metric.lower()} shifts by {total_change * 100:.2f}% under the current what-if adjustments.",
    )


@router.get("/{forecast_id}/drivers", response_model=DriverAnalysisOut)
async def get_driver_analysis(
    forecast_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    forecast = await _get_forecast_or_404(db, forecast_id, current_user.id)
    if not forecast.driver_analyses:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver analysis not found")
    latest = max(forecast.driver_analyses, key=lambda item: item.created_at)
    return DriverAnalysisOut.model_validate(latest)


@router.post("/{forecast_id}/drivers/generate", response_model=DriverAnalysisOut)
async def generate_driver_analysis(
    forecast_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    forecast = await _get_forecast_or_404(db, forecast_id, current_user.id)
    analysis = await _generate_driver_analysis_record(forecast, current_user.id)
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)
    return DriverAnalysisOut.model_validate(analysis)


@router.get("/{forecast_id}/versions", response_model=list[ForecastVersionOut])
async def list_versions(
    forecast_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    forecast = await _get_forecast_or_404(db, forecast_id, current_user.id)
    return [ForecastVersionOut.model_validate(item) for item in sorted(forecast.versions, key=lambda value: value.version_number, reverse=True)]


@router.get("/{forecast_id}/alerts", response_model=list[PredictionAlertOut])
async def list_alerts(
    forecast_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    forecast = await _get_forecast_or_404(db, forecast_id, current_user.id)
    return [PredictionAlertOut.model_validate(item) for item in sorted(forecast.alerts, key=lambda value: value.created_at, reverse=True)]


@router.post("/{forecast_id}/alerts/{alert_id}/read", response_model=PredictionAlertOut)
async def mark_alert_read(
    forecast_id: int,
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_forecast_or_404(db, forecast_id, current_user.id, load_related=False)
    alert = await db.scalar(
        select(PredictionAlert).where(
            PredictionAlert.id == alert_id,
            PredictionAlert.forecast_id == forecast_id,
            PredictionAlert.owner_id == current_user.id,
        )
    )
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    alert.is_read = True
    await db.commit()
    await db.refresh(alert)
    return PredictionAlertOut.model_validate(alert)


@router.get("/{forecast_id}/recommendations", response_model=list[RecommendationOut])
async def get_recommendations(
    forecast_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_forecast_or_404(db, forecast_id, current_user.id, load_related=False)
    items = (
        await db.scalars(
            select(RecommendationHistory)
            .where(RecommendationHistory.forecast_id == forecast_id, RecommendationHistory.owner_id == current_user.id)
            .order_by(desc(RecommendationHistory.created_at))
        )
    ).all()
    return [RecommendationOut.model_validate(item) for item in items]


@router.post("/{forecast_id}/recommendations/generate", response_model=list[RecommendationOut])
async def generate_recommendations(
    forecast_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    forecast = await _get_forecast_or_404(db, forecast_id, current_user.id)
    latest_result = await _get_latest_result_or_404(forecast)
    existing = (
        await db.scalars(
            select(RecommendationHistory)
            .where(RecommendationHistory.forecast_id == forecast_id, RecommendationHistory.owner_id == current_user.id)
            .order_by(desc(RecommendationHistory.created_at))
        )
    ).all()
    if existing:
        return [RecommendationOut.model_validate(item) for item in existing[:5]]
    items = await _generate_recommendation_records(forecast, current_user.id, latest_result)
    db.add_all(items)
    await db.commit()
    return [RecommendationOut.model_validate(item) for item in items]


@router.post("/{forecast_id}/export")
async def export_forecast(
    forecast_id: int,
    payload: ForecastExportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    forecast = await _get_forecast_or_404(db, forecast_id, current_user.id)
    latest_result = await _get_latest_result_or_404(forecast)
    return {
        "export_format": payload.export_format,
        "note": "Export is returned as JSON payload because PDF/Excel libraries are not installed in this environment.",
        "generated_at": utcnow().isoformat(),
        "forecast": _forecast_to_detail(forecast, recommendations=[]).model_dump(),
        "latest_result": ForecastResultOut.model_validate(latest_result).model_dump(),
    }
