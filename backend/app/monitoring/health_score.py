import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    BusinessHealthScore, Monitor, MonitorStatus, AlertEvent, AlertStatus,
    MonitorSeverity, AnomalyEvent, SLAMetric,
)

logger = logging.getLogger(__name__)


class HealthScoreCalculator:
    """Calculates the overall business health score from multiple dimensions."""

    async def calculate(self, db: AsyncSession) -> BusinessHealthScore:
        """Calculate the current business health score."""
        kpi_performance = await self._calculate_kpi_performance(db)
        forecast_confidence = await self._calculate_forecast_confidence(db)
        active_risks = await self._calculate_active_risks(db)
        open_alerts = await self._calculate_open_alerts_score(db)
        data_quality = await self._calculate_data_quality(db)
        operational_efficiency = await self._calculate_operational_efficiency(db)

        weights = {
            "kpi_performance": 0.30,
            "forecast_confidence": 0.15,
            "active_risks": 0.15,
            "open_alerts": 0.15,
            "data_quality": 0.10,
            "operational_efficiency": 0.15,
        }

        overall = (
            kpi_performance * weights["kpi_performance"]
            + forecast_confidence * weights["forecast_confidence"]
            + active_risks * weights["active_risks"]
            + open_alerts * weights["open_alerts"]
            + data_quality * weights["data_quality"]
            + operational_efficiency * weights["operational_efficiency"]
        )

        score = BusinessHealthScore(
            overall_score=round(overall, 2),
            kpi_performance=round(kpi_performance, 2),
            forecast_confidence=round(forecast_confidence, 2),
            active_risks=round(active_risks, 2),
            open_alerts=round(open_alerts, 2),
            data_quality=round(data_quality, 2),
            operational_efficiency=round(operational_efficiency, 2),
            details={
                "weights": weights,
                "total_monitors": await db.scalar(select(func.count(Monitor.id))) or 0,
                "active_monitors": await db.scalar(
                    select(func.count(Monitor.id)).where(Monitor.status == MonitorStatus.active)
                ) or 0,
            },
        )
        return score

    async def _calculate_kpi_performance(self, db: AsyncSession) -> float:
        """Score based on KPI performance (0-100)."""
        # In production, query actual KPI achievement rates
        return 75.0

    async def _calculate_forecast_confidence(self, db: AsyncSession) -> float:
        """Score based on forecast confidence levels."""
        # In production, query average forecast accuracy
        return 70.0

    async def _calculate_active_risks(self, db: AsyncSession) -> float:
        """Score based on active risks (higher risks = lower score)."""
        # In production, query risk assessments
        return 80.0

    async def _calculate_open_alerts_score(self, db: AsyncSession) -> float:
        """Score based on open alerts (more alerts = lower score)."""
        open_count = await db.scalar(
            select(func.count(AlertEvent.id)).where(AlertEvent.status == AlertStatus.open)
        ) or 0
        critical_count = await db.scalar(
            select(func.count(AlertEvent.id)).where(
                AlertEvent.status == AlertStatus.open,
                AlertEvent.severity == MonitorSeverity.critical,
            )
        ) or 0

        base_score = 100.0
        base_score -= open_count * 2
        base_score -= critical_count * 5
        return max(0, min(100, base_score))

    async def _calculate_data_quality(self, db: AsyncSession) -> float:
        """Score based on data quality metrics."""
        # In production, query data source health statuses
        return 85.0

    async def _calculate_operational_efficiency(self, db: AsyncSession) -> float:
        """Score based on operational efficiency."""
        # In production, query SLA compliance rates
        return 78.0