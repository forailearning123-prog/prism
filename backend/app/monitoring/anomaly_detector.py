import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Monitor, AnomalyEvent, AnomalyCategory, MonitorSeverity,
)

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """AI-powered anomaly detection for business metrics."""

    async def detect(self, monitor: Monitor, db: AsyncSession) -> Optional[AnomalyEvent]:
        """Detect anomalies for a given monitor. Returns AnomalyEvent if found."""
        try:
            # In production, this would use statistical models and ML
            # For now, detect based on historical deviation
            current_value = await self._get_current_metric_value(monitor, db)
            if current_value is None:
                return None

            historical_values = await self._get_historical_metric_values(monitor, db)
            if len(historical_values) < 10:
                return None

            mean = sum(historical_values) / len(historical_values)
            variance = sum((v - mean) ** 2 for v in historical_values) / len(historical_values)
            std_dev = variance ** 0.5

            if std_dev == 0:
                return None

            z_score = (current_value - mean) / std_dev
            anomaly_score = abs(z_score)

            if anomaly_score < 2.0:
                return None

            category = self._categorize_anomaly(monitor)
            confidence = min(anomaly_score / 5.0, 0.99)

            if anomaly_score >= 3.0:
                severity = MonitorSeverity.critical
            elif anomaly_score >= 2.5:
                severity = MonitorSeverity.high
            else:
                severity = MonitorSeverity.medium

            anomaly = AnomalyEvent(
                monitor_id=monitor.id,
                semantic_model_id=monitor.semantic_model_id,
                category=category,
                severity=severity,
                metric_name=monitor.measure_name or monitor.name,
                metric_value=current_value,
                expected_value=round(mean, 4),
                deviation=round(current_value - mean, 4),
                confidence=round(confidence, 4),
                anomaly_score=round(anomaly_score, 4),
                possible_causes=self._generate_possible_causes(category, monitor),
                suggested_actions=self._generate_suggested_actions(category, monitor),
                affected_kpis=[monitor.measure_name] if monitor.measure_name else [],
                ai_explanation=self._generate_explanation(monitor, current_value, mean, anomaly_score),
            )
            db.add(anomaly)
            await db.commit()
            await db.refresh(anomaly)
            return anomaly

        except Exception as e:
            logger.error(f"Error detecting anomaly for monitor {monitor.id}: {e}")
            return None

    def _categorize_anomaly(self, monitor: Monitor) -> AnomalyCategory:
        """Categorize the anomaly based on monitor context."""
        name_lower = monitor.name.lower()
        measure_lower = monitor.measure_name.lower()
        combined = name_lower + " " + measure_lower

        if any(w in combined for w in ["revenue", "sales", "income"]):
            return AnomalyCategory.revenue
        elif any(w in combined for w in ["cost", "expense", "spend"]):
            return AnomalyCategory.cost
        elif any(w in combined for w in ["inventory", "stock", "supply"]):
            return AnomalyCategory.inventory
        elif any(w in combined for w in ["employee", "headcount", "attrition", "workforce"]):
            return AnomalyCategory.workforce
        elif any(w in combined for w in ["operational", "efficiency", "throughput"]):
            return AnomalyCategory.operational
        elif any(w in combined for w in ["financial", "profit", "margin", "cash"]):
            return AnomalyCategory.financial
        return AnomalyCategory.sales

    def _generate_possible_causes(self, category: AnomalyCategory, monitor: Monitor) -> list[str]:
        """Generate possible causes for the anomaly."""
        causes = {
            AnomalyCategory.revenue: [
                "Unexpected change in sales volume",
                "Pricing strategy changes",
                "Customer acquisition fluctuations",
                "Seasonal demand shifts",
            ],
            AnomalyCategory.cost: [
                "Supplier price changes",
                "Operational inefficiencies",
                "One-time expenses",
                "Resource utilization changes",
            ],
            AnomalyCategory.sales: [
                "Market demand fluctuations",
                "Competitive pressure",
                "Marketing campaign impact",
                "Customer churn changes",
            ],
            AnomalyCategory.inventory: [
                "Supply chain disruption",
                "Demand forecasting errors",
                "Warehouse management issues",
                "Supplier delivery delays",
            ],
            AnomalyCategory.workforce: [
                "Employee turnover",
                "Hiring cycle changes",
                "Productivity shifts",
                "Department restructuring",
            ],
            AnomalyCategory.operational: [
                "Process bottlenecks",
                "Technology performance issues",
                "Resource allocation changes",
                "External factor impact",
            ],
            AnomalyCategory.financial: [
                "Market condition changes",
                "Currency fluctuations",
                "Regulatory impacts",
                "Investment performance",
            ],
        }
        return causes.get(category, ["Unexpected data pattern detected"])

    def _generate_suggested_actions(self, category: AnomalyCategory, monitor: Monitor) -> list[str]:
        """Generate suggested actions for the anomaly."""
        return [
            f"Review {monitor.measure_name or monitor.name} data for accuracy",
            f"Compare against historical trends for {monitor.measure_name or monitor.name}",
            "Investigate external factors that may have influenced the metric",
            "Alert relevant business owners for further analysis",
        ]

    def _generate_explanation(self, monitor: Monitor, current_value: float, expected_value: float, anomaly_score: float) -> str:
        """Generate an AI explanation for the anomaly."""
        deviation_pct = ((current_value - expected_value) / expected_value * 100) if expected_value != 0 else 0
        direction = "above" if deviation_pct > 0 else "below"
        return (
            f"Anomaly detected for {monitor.measure_name or monitor.name}: "
            f"current value {current_value:.2f} is {abs(deviation_pct):.1f}% {direction} "
            f"the expected value of {expected_value:.2f}. "
            f"Anomaly confidence score: {anomaly_score:.2f} (threshold: 2.0)."
        )

    async def _get_current_metric_value(self, monitor: Monitor, db: AsyncSession) -> Optional[float]:
        """Get the current value for the monitor's metric."""
        # In production, query the semantic model / data source
        return None

    async def _get_historical_metric_values(self, monitor: Monitor, db: AsyncSession) -> list[float]:
        """Get historical metric values for anomaly detection."""
        # In production, query time-series data from the semantic layer
        return []