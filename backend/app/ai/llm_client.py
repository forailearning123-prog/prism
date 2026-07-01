"""LLM client — provider-agnostic wrapper.

Uses OpenAI (or any OpenAI-compatible endpoint) when OPENAI_API_KEY is set.
Falls back to deterministic demo responses so the module works without a key.
"""

import json
import logging
from typing import AsyncIterator

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"

_DEMO_SYSTEM_PROMPT = """You are an expert AI Business Analyst.
Respond with structured JSON exactly matching the schema provided."""


async def chat_completion(
    messages: list[dict],
    temperature: float = 0.3,
    max_tokens: int = 2000,
) -> str:
    """Return a complete response string."""
    if settings.openai_api_key:
        return await _openai_chat(messages, temperature, max_tokens)
    return _demo_response(messages)


async def chat_completion_stream(
    messages: list[dict],
    temperature: float = 0.3,
    max_tokens: int = 2000,
) -> AsyncIterator[str]:
    """Yield response chunks."""
    if settings.openai_api_key:
        async for chunk in _openai_stream(messages, temperature, max_tokens):
            yield chunk
    else:
        for chunk in _demo_response_stream(messages):
            yield chunk


async def _openai_chat(messages: list[dict], temperature: float, max_tokens: int) -> str:
    base_url = settings.openai_base_url or _DEFAULT_OPENAI_BASE_URL
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": "Bearer " + settings.openai_api_key,
                "Content-Type": "application/json",
            },
            json={
                "model": settings.openai_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


async def _openai_stream(
    messages: list[dict], temperature: float, max_tokens: int
) -> AsyncIterator[str]:
    base_url = settings.openai_base_url or _DEFAULT_OPENAI_BASE_URL
    async with httpx.AsyncClient(timeout=60) as client:
        async with client.stream(
            "POST",
            f"{base_url}/chat/completions",
            headers={
                "Authorization": "Bearer " + settings.openai_api_key,
                "Content-Type": "application/json",
            },
            json={
                "model": settings.openai_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": True,
            },
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: ") and line != "data: [DONE]":
                    try:
                        chunk = json.loads(line[6:])
                        delta = chunk["choices"][0]["delta"].get("content", "")
                        if delta:
                            yield delta
                    except (KeyError, json.JSONDecodeError):
                        continue


def _demo_response(messages: list[dict]) -> str:
    """Return a deterministic demo response based on the last user message."""
    question = _extract_question(messages)
    return json.dumps(_build_demo_payload(question))


def _demo_response_stream(messages: list[dict]):
    """Yield the demo response in small chunks to simulate streaming."""
    full = _demo_response(messages)
    chunk_size = 20
    for i in range(0, len(full), chunk_size):
        yield full[i : i + chunk_size]


def _extract_question(messages: list[dict]) -> str:
    for message in reversed(messages):
        if message.get("role") == "user":
            return message.get("content", "")
    return ""


def _build_demo_payload(question: str) -> dict:
    q_lower = question.lower()
    if any(word in q_lower for word in ["revenue", "sales", "income"]):
        topic = "revenue"
        kpi_label = "Total Revenue"
        kpi_value = "$4.2M"
        trend_data = [
            {"period": "Jan", "value": 620000},
            {"period": "Feb", "value": 580000},
            {"period": "Mar", "value": 710000},
            {"period": "Apr", "value": 690000},
            {"period": "May", "value": 840000},
            {"period": "Jun", "value": 760000},
        ]
        summary = "Revenue totalled $4.2M over the analysed period, with May recording the strongest month at $840K — a 21% increase versus the prior month."
        interpretation = "The upward revenue trajectory reflects successful Q2 marketing initiatives and improved customer retention. The May peak correlates with the spring product launch."
        findings = [
            "May was the highest-revenue month at $840K (+21% MoM)",
            "February showed a 6% dip before a strong recovery in March",
            "Overall 6-month revenue grew 23% compared to H2 of the prior year",
        ]
        recommendations = [
            {"action": "Replicate May's marketing playbook in Q3", "rationale": "May's campaign drove the strongest single-month result; adapting it for summer audiences could sustain growth."},
            {"action": "Investigate February decline root cause", "rationale": "A recurring seasonal dip in February may be mitigated with targeted promotions."},
        ]
        viz_type = "line_chart"
    elif any(word in q_lower for word in ["region", "geography", "location", "area"]):
        topic = "regional performance"
        kpi_label = "Top Region"
        kpi_value = "North — $1.8M"
        trend_data = [
            {"period": "North", "value": 1800000},
            {"period": "South", "value": 1200000},
            {"period": "East", "value": 950000},
            {"period": "West", "value": 700000},
        ]
        summary = "The North region leads with $1.8M in revenue, contributing 37% of total. The West region underperforms, showing an 18% decline year-on-year."
        interpretation = "North's dominance is driven by a concentration of enterprise accounts and a high-performing field sales team. West's decline warrants investigation into market saturation and competitive pressure."
        findings = [
            "North region contributes 37% of total revenue",
            "West declined 18% YoY — the only region in negative territory",
            "South shows emerging growth potential, up 12% QoQ",
        ]
        recommendations = [
            {"action": "Launch targeted recovery initiative in West region", "rationale": "West is the only declining region; early intervention can limit further market share loss."},
            {"action": "Replicate North's account management model in South", "rationale": "South's trajectory is positive and could accelerate with proven enterprise playbooks."},
        ]
        viz_type = "bar_chart"
    elif any(word in q_lower for word in ["attrition", "employee", "hr", "staff", "turnover"]):
        topic = "employee attrition"
        kpi_label = "Attrition Rate"
        kpi_value = "14.3%"
        trend_data = [
            {"period": "Engineering", "value": 18},
            {"period": "Sales", "value": 22},
            {"period": "Operations", "value": 10},
            {"period": "Finance", "value": 6},
            {"period": "Marketing", "value": 14},
        ]
        summary = "Overall attrition stands at 14.3%, above the industry benchmark of 11%. Sales has the highest attrition at 22%, followed by Engineering at 18%."
        interpretation = "Elevated attrition in Sales and Engineering suggests compensation competitiveness and workload concerns. Exit survey data indicates career development opportunities as the primary driver."
        findings = [
            "Sales attrition at 22% — 11 points above benchmark",
            "Engineering attrition at 18% — affecting delivery capacity",
            "Finance and Operations remain within healthy ranges",
        ]
        recommendations = [
            {"action": "Conduct compensation benchmarking in Sales and Engineering", "rationale": "Both high-attrition departments may be losing talent to better-compensated competitors."},
            {"action": "Introduce structured career development programmes", "rationale": "Exit surveys identify growth opportunities as the top driver of voluntary departures."},
        ]
        viz_type = "bar_chart"
    elif any(word in q_lower for word in ["churn", "customer", "retention"]):
        topic = "customer churn"
        kpi_label = "Churn Rate"
        kpi_value = "8.7%"
        trend_data = [
            {"period": "Q1", "value": 6.2},
            {"period": "Q2", "value": 7.4},
            {"period": "Q3", "value": 9.1},
            {"period": "Q4", "value": 8.7},
        ]
        summary = "Customer churn has increased from 6.2% in Q1 to 8.7% in Q4, representing an additional 340 customers lost compared to the same period last year."
        interpretation = "The churn acceleration through Q3 coincided with a pricing restructure. The Q4 stabilisation suggests the revised retention programme is beginning to show impact."
        findings = [
            "Churn increased 40% from Q1 to Q3",
            "Enterprise segment churn is lower at 4.2% vs 11.3% for SMB",
            "Customers with 3+ product modules show 65% lower churn probability",
        ]
        recommendations = [
            {"action": "Target at-risk SMB customers with success check-ins", "rationale": "SMB churn is 2.7x higher than enterprise; proactive engagement can reduce involuntary churn."},
            {"action": "Accelerate multi-module adoption programmes", "rationale": "Higher module engagement strongly correlates with retention."},
        ]
        viz_type = "line_chart"
    else:
        topic = "business performance"
        kpi_label = "Business Health Score"
        kpi_value = "74 / 100"
        trend_data = [
            {"period": "Jan", "value": 68},
            {"period": "Feb", "value": 65},
            {"period": "Mar", "value": 72},
            {"period": "Apr", "value": 71},
            {"period": "May", "value": 78},
            {"period": "Jun", "value": 74},
        ]
        summary = "Overall business health scores 74/100 this period, reflecting solid operational performance offset by moderate financial headwinds in two business units."
        interpretation = "The business is performing in the upper-mid tier. Strengths in customer satisfaction and operational efficiency are partially countered by revenue growth below target and rising input costs."
        findings = [
            "Customer satisfaction score at 87% — above target",
            "Revenue growth at 11% vs 15% target",
            "Operating costs increased 7% due to supply chain pressures",
        ]
        recommendations = [
            {"action": "Review pricing strategy to restore revenue growth trajectory", "rationale": "Revenue is 4 points below target while costs are rising — margin compression risk is increasing."},
            {"action": "Accelerate supply chain renegotiations", "rationale": "Input cost increases are the primary drag on operating profit."},
        ]
        viz_type = "line_chart"

    return {
        "executive_summary": summary,
        "key_findings": findings,
        "supporting_evidence": [
            {"source": "Semantic Model", "metric": kpi_label, "value": kpi_value},
            {"source": "Historical Data", "period": "Last 6 months", "data_points": len(trend_data)},
        ],
        "business_interpretation": interpretation,
        "confidence_level": 82,
        "data_sources_used": ["Semantic Model", "Historical Trends", "Benchmark Database"],
        "visualizations": [
            {
                "type": viz_type,
                "title": f"{topic.title()} Overview",
                "data": trend_data,
                "x_key": "period",
                "y_key": "value",
            },
            {
                "type": "kpi_card",
                "title": kpi_label,
                "value": kpi_value,
                "trend": "up",
            },
        ],
        "recommendations": recommendations,
        "suggested_questions": [
            f"Compare {topic} with last quarter",
            f"Which factors most influence {topic}?",
            f"Forecast {topic} for next quarter",
            f"Show {topic} by department",
            f"What actions should we take to improve {topic}?",
        ],
    }
