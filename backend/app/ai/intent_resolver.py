"""Classify user intent from natural language query."""

from enum import Enum


class AnalystIntent(str, Enum):
    trend_analysis = "trend_analysis"
    comparison = "comparison"
    root_cause = "root_cause"
    forecast = "forecast"
    ranking = "ranking"
    breakdown = "breakdown"
    explain_dashboard = "explain_dashboard"
    explain_kpi = "explain_kpi"
    summarise = "summarise"
    anomaly_detection = "anomaly_detection"
    recommendation = "recommendation"
    general = "general"


_INTENT_PATTERNS: list[tuple[AnalystIntent, list[str]]] = [
    (AnalystIntent.root_cause, ["why", "cause", "reason", "explain why", "what caused", "root cause", "contributing factor"]),
    (AnalystIntent.forecast, ["forecast", "predict", "next month", "next quarter", "projection", "future", "estimate"]),
    (AnalystIntent.comparison, ["compare", "versus", "vs", "difference between", "against", "benchmark", "contrast"]),
    (AnalystIntent.ranking, ["top", "bottom", "best", "worst", "highest", "lowest", "rank", "leading", "trailing", "most", "least"]),
    (AnalystIntent.trend_analysis, ["trend", "over time", "growth", "decline", "change", "trajectory", "progress", "momentum"]),
    (AnalystIntent.anomaly_detection, ["anomaly", "outlier", "unusual", "unexpected", "spike", "drop", "abnormal", "deviation"]),
    (AnalystIntent.explain_dashboard, ["explain this dashboard", "what does this dashboard", "describe the dashboard"]),
    (AnalystIntent.explain_kpi, ["what does", "what is", "explain", "define", "meaning of", "kpi", "metric", "measure"]),
    (AnalystIntent.summarise, ["summarise", "summarize", "summary", "overview", "how is", "how are", "overall", "today", "this week", "this month"]),
    (AnalystIntent.breakdown, ["break down", "breakdown", "by department", "by region", "by category", "segment", "split by", "show by"]),
    (AnalystIntent.recommendation, ["recommend", "suggest", "what should", "action", "improve", "optimise", "optimize", "what can we"]),
]


def resolve_intent(question: str) -> AnalystIntent:
    """Return the most likely intent for a natural language question."""
    q = question.lower()
    for intent, patterns in _INTENT_PATTERNS:
        if any(pattern in q for pattern in patterns):
            return intent
    return AnalystIntent.general
