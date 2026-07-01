import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import MonitorRule, Monitor, RuleType, RuleOperator

logger = logging.getLogger(__name__)


class RuleEvaluator:
    """Evaluates monitor rules against current data."""

    async def evaluate(self, rule: MonitorRule, monitor: Monitor, db: AsyncSession) -> bool:
        """Evaluate a single rule. Returns True if the rule is triggered."""
        try:
            current_value = await self._get_current_value(monitor, db)
            if current_value is None:
                return False

            rule_type = rule.rule_type

            if rule_type == RuleType.threshold:
                return self._evaluate_threshold(rule, current_value)
            elif rule_type == RuleType.trend:
                return await self._evaluate_trend(rule, monitor, current_value, db)
            elif rule_type == RuleType.percentage_change:
                return await self._evaluate_percentage_change(rule, monitor, current_value, db)
            elif rule_type == RuleType.comparison:
                return await self._evaluate_comparison(rule, monitor, current_value, db)
            elif rule_type == RuleType.multi_condition:
                return self._evaluate_multi_condition(rule, current_value)
            elif rule_type == RuleType.time_based:
                return self._evaluate_time_based(rule, current_value)
            elif rule_type == RuleType.composite:
                return await self._evaluate_composite(rule, monitor, current_value, db)
            else:
                logger.warning(f"Unknown rule type: {rule_type}")
                return False

        except Exception as e:
            logger.error(f"Error evaluating rule {rule.id}: {e}")
            return False

    def _evaluate_threshold(self, rule: MonitorRule, current_value: float) -> bool:
        """Evaluate a simple threshold rule."""
        threshold = rule.threshold_value
        if threshold is None:
            return False

        op = rule.operator
        if op == RuleOperator.gt:
            return current_value > threshold
        elif op == RuleOperator.gte:
            return current_value >= threshold
        elif op == RuleOperator.lt:
            return current_value < threshold
        elif op == RuleOperator.lte:
            return current_value <= threshold
        elif op == RuleOperator.eq:
            return current_value == threshold
        elif op == RuleOperator.neq:
            return current_value != threshold
        elif op == RuleOperator.between:
            if rule.threshold_low is not None and rule.threshold_high is not None:
                return rule.threshold_low <= current_value <= rule.threshold_high
            return False
        elif op == RuleOperator.outside:
            if rule.threshold_low is not None and rule.threshold_high is not None:
                return current_value < rule.threshold_low or current_value > rule.threshold_high
            return False
        return False

    async def _evaluate_trend(self, rule: MonitorRule, monitor: Monitor, current_value: float, db: AsyncSession) -> bool:
        """Evaluate a trend rule over a time window."""
        window = rule.trend_window or 3
        direction = rule.trend_direction
        if not direction:
            return False

        historical = await self._get_historical_values(monitor, window, db)
        if len(historical) < window:
            return False

        if direction == "up":
            return all(historical[i] < historical[i + 1] for i in range(len(historical) - 1))
        elif direction == "down":
            return all(historical[i] > historical[i + 1] for i in range(len(historical) - 1))
        return False

    async def _evaluate_percentage_change(self, rule: MonitorRule, monitor: Monitor, current_value: float, db: AsyncSession) -> bool:
        """Evaluate a percentage change rule."""
        percentage = rule.percentage or 10.0
        historical = await self._get_historical_values(monitor, 1, db)
        if not historical:
            return False

        previous = historical[-1]
        if previous == 0:
            return False

        change_pct = ((current_value - previous) / previous) * 100

        op = rule.operator
        if op == RuleOperator.gt:
            return change_pct > percentage
        elif op == RuleOperator.lt:
            return change_pct < -percentage
        elif op == RuleOperator.gte:
            return abs(change_pct) >= percentage
        return abs(change_pct) >= percentage

    async def _evaluate_comparison(self, rule: MonitorRule, monitor: Monitor, current_value: float, db: AsyncSession) -> bool:
        """Evaluate a comparison against another monitor's value."""
        if not rule.comparison_monitor_id:
            return False

        other_monitor = await db.get(Monitor, rule.comparison_monitor_id)
        if not other_monitor:
            return False

        other_value = await self._get_current_value(other_monitor, db)
        if other_value is None:
            return False

        op = rule.operator
        threshold = rule.threshold_value or 0

        if op == RuleOperator.gt:
            return (current_value - other_value) > threshold
        elif op == RuleOperator.lt:
            return (current_value - other_value) < threshold
        elif op == RuleOperator.eq:
            return abs(current_value - other_value) <= threshold
        return False

    def _evaluate_multi_condition(self, rule: MonitorRule, current_value: float) -> bool:
        """Evaluate a multi-condition rule with nested logic."""
        logic = rule.condition_logic
        if not logic:
            return False
        return self._evaluate_condition_tree(logic, current_value)

    def _evaluate_time_based(self, rule: MonitorRule, current_value: float) -> bool:
        """Evaluate a time-based rule."""
        if rule.time_field and rule.time_value:
            # Simple threshold evaluation; time context is applied at monitor level
            return self._evaluate_threshold(rule, current_value or 0)
        return self._evaluate_threshold(rule, current_value or 0)

    async def _evaluate_composite(self, rule: MonitorRule, monitor: Monitor, current_value: float, db: AsyncSession) -> bool:
        """Evaluate a composite rule combining multiple conditions."""
        logic = rule.condition_logic
        if not logic or "rules" not in logic:
            return False
        return await self._evaluate_composite_tree(logic, monitor, current_value, db)

    def _evaluate_condition_tree(self, node: dict, current_value: float) -> bool:
        """Recursively evaluate a condition tree."""
        if "operator" in node and "conditions" in node:
            op = node["operator"].lower()
            conditions = node["conditions"]
            if op == "and":
                return all(self._evaluate_condition_tree(c, current_value) for c in conditions)
            elif op == "or":
                return any(self._evaluate_condition_tree(c, current_value) for c in conditions)
            elif op == "not":
                return not self._evaluate_condition_tree(conditions[0], current_value) if conditions else False

        if "field" in node and "value" in node:
            field_op = node.get("operator", "eq")
            threshold = node["value"]
            if field_op == "gt":
                return current_value > threshold
            elif field_op == "gte":
                return current_value >= threshold
            elif field_op == "lt":
                return current_value < threshold
            elif field_op == "lte":
                return current_value <= threshold
            elif field_op == "eq":
                return current_value == threshold
        return False

    async def _evaluate_composite_tree(self, node: dict, monitor: Monitor, current_value: float, db: AsyncSession) -> bool:
        """Recursively evaluate a composite rule tree."""
        if "operator" in node and "rules" in node:
            op = node["operator"].lower()
            rules_data = node["rules"]
            results = []
            for r in rules_data:
                if "rule_id" in r:
                    rule = await db.get(MonitorRule, r["rule_id"])
                    if rule:
                        results.append(await self.evaluate(rule, monitor, db))
                elif "threshold" in r:
                    op_type = r.get("operator", "gt")
                    val = r["threshold"]
                    if op_type == "gt":
                        results.append(current_value > val)
                    else:
                        results.append(current_value < val)

            if op == "and":
                return all(results)
            elif op == "or":
                return any(results)
        return False

    async def _get_current_value(self, monitor: Monitor, db: AsyncSession) -> Optional[float]:
        """Get the current KPI/measure value for a monitor."""
        # In production, this would query the semantic model or data source
        # For now, return None to be overridden by actual data
        return None

    async def _get_historical_values(self, monitor: Monitor, count: int, db: AsyncSession) -> list[float]:
        """Get historical values for trend analysis."""
        # In production, this would query historical data from the semantic layer
        return []