"""Generate structured business reports."""

import json
import logging

from app.ai.llm_client import chat_completion

logger = logging.getLogger(__name__)

_REPORT_SYSTEM = """You are a senior business analyst generating a formal business report.
Respond with valid JSON:
{
  "title": "string",
  "report_type": "string",
  "executive_summary": "string",
  "sections": [
    {
      "heading": "string",
      "content": "string",
      "key_points": ["string", ...]
    }
  ],
  "kpis": [{"name": "string", "value": "string", "status": "good|warning|critical"}],
  "visualizations": [...],
  "conclusions": ["string", ...],
  "recommendations": [{"action": "string", "priority": "high|medium|low", "rationale": "string"}]
}"""


async def generate_report(
    report_type: str,
    context: dict,
    conversation_summary: str = "",
) -> dict:
    prompt = f"""Generate a {report_type.replace('_', ' ').title()} report.

Context: {json.dumps(context, indent=2)[:2000]}
Conversation insights: {conversation_summary[:500] if conversation_summary else 'None'}

Produce a comprehensive report with narrative, KPIs, and actionable recommendations."""

    messages = [
        {"role": "system", "content": _REPORT_SYSTEM},
        {"role": "user", "content": prompt},
    ]

    try:
        raw = await chat_completion(messages, max_tokens=3000)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1]
            if raw.endswith("```"):
                raw = raw[: raw.rfind("```")]
        return json.loads(raw)
    except Exception as exc:
        logger.warning("Report generation error: %s", exc)
        return _demo_report(report_type)


def _demo_report(report_type: str) -> dict:
    return {
        "title": f"{report_type.replace('_', ' ').title()} — Demo Report",
        "report_type": report_type,
        "executive_summary": "This report summarises current business performance across key operational and financial metrics. Overall health is solid with targeted improvement areas identified.",
        "sections": [
            {
                "heading": "Financial Performance",
                "content": "Revenue for the period reached $4.2M, representing 11% year-on-year growth. While below the 15% target, the trajectory remains positive with Q3 acceleration expected.",
                "key_points": ["Revenue $4.2M (+11% YoY)", "Gross margin at 42%", "Operating costs up 7% due to supply chain"],
            },
            {
                "heading": "Operational Highlights",
                "content": "Customer satisfaction remained strong at 87%. Employee attrition increased to 14.3%, requiring focused HR intervention particularly in Sales and Engineering.",
                "key_points": ["Customer satisfaction 87%", "Attrition at 14.3% (above 11% benchmark)", "On-time delivery at 94%"],
            },
            {
                "heading": "Risk Assessment",
                "content": "Three primary risks identified: revenue growth shortfall, rising attrition in key departments, and supply chain cost pressure. All are being actively monitored.",
                "key_points": ["Revenue growth below target", "Talent retention risk", "Input cost inflation"],
            },
        ],
        "kpis": [
            {"name": "Revenue", "value": "$4.2M", "status": "warning"},
            {"name": "Gross Margin", "value": "42%", "status": "good"},
            {"name": "Customer Satisfaction", "value": "87%", "status": "good"},
            {"name": "Employee Attrition", "value": "14.3%", "status": "warning"},
        ],
        "visualizations": [],
        "conclusions": [
            "The business is performing adequately but below growth targets.",
            "People and cost pressures represent the highest near-term risk.",
            "Customer-facing metrics remain strong, providing a solid foundation.",
        ],
        "recommendations": [
            {"action": "Review and revise revenue growth strategy", "priority": "high", "rationale": "4-point gap to target requires strategic review before Q3."},
            {"action": "Launch retention programme for Sales and Engineering", "priority": "high", "rationale": "Attrition above benchmark in revenue-critical functions."},
            {"action": "Renegotiate supply chain contracts", "priority": "medium", "rationale": "7% cost increase reducing margin; structured review needed."},
        ],
    }
