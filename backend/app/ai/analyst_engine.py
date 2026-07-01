"""AI Analyst Engine — orchestrates the full analysis workflow."""

import json
import logging
import time
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.intent_resolver import AnalystIntent, resolve_intent
from app.ai.llm_client import chat_completion, chat_completion_stream
from app.ai.semantic_context import build_semantic_context

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are an expert AI Business Analyst embedded in an enterprise BI platform.

Your role is to answer business questions with the depth and precision of an experienced analyst.
You have access to a semantic model that defines business entities, KPIs, measures, and glossary terms.

ALWAYS respond with valid JSON matching this exact schema:
{
  "executive_summary": "string — 2-3 sentence summary suitable for an executive",
  "key_findings": ["string", ...],
  "supporting_evidence": [{"source": "string", "metric": "string", "value": "string"}, ...],
  "business_interpretation": "string — explain WHY, not just WHAT",
  "confidence_level": integer 0-100,
  "data_sources_used": ["string", ...],
  "visualizations": [
    {
      "type": "line_chart|bar_chart|kpi_card|table|pie_chart",
      "title": "string",
      "data": [{"period": "string", "value": number}, ...],
      "x_key": "period",
      "y_key": "value"
    }
  ],
  "recommendations": [
    {"action": "string", "rationale": "string"}
  ],
  "suggested_questions": ["string", ...]
}

Rules:
- Always explain WHY results occurred, not just WHAT happened.
- Recommendations must be specific, data-driven, and actionable.
- Confidence level reflects data completeness and analytical certainty.
- Use business language. Never expose technical table names or SQL.
- Generate at least one visualization when data allows.
- Always provide 3-5 suggested follow-up questions.
"""


def _build_user_prompt(
    question: str,
    intent: AnalystIntent,
    semantic_context: dict,
    conversation_history: list[dict],
) -> str:
    parts = [f"Question: {question}", f"Intent: {intent.value}"]

    if semantic_context.get("semantic_model"):
        model = semantic_context["semantic_model"]
        parts.append(f"\nSemantic Model: {model['name']} — {model['description']}")

    if semantic_context.get("relevant_kpis"):
        kpi_names = [kpi["name"] for kpi in semantic_context["relevant_kpis"]]
        parts.append(f"Relevant KPIs: {', '.join(kpi_names)}")

    if semantic_context.get("relevant_measures"):
        measure_names = [measure["name"] for measure in semantic_context["relevant_measures"]]
        parts.append(f"Relevant Measures: {', '.join(measure_names)}")

    if semantic_context.get("glossary_terms"):
        terms = [
            f"{term['term']}: {term['definition']}"
            for term in semantic_context["glossary_terms"][:5]
        ]
        parts.append("Business Glossary:\n" + "\n".join(terms))

    if conversation_history:
        parts.append("\nRecent conversation context:")
        for message in conversation_history[-4:]:
            role = message.get("role", "user")
            content = message.get("content", "")[:300]
            parts.append(f"  [{role}]: {content}")

    return "\n".join(parts)


async def run_analysis(
    question: str,
    db: AsyncSession,
    user_id: int,
    conversation_history: list[dict] | None = None,
    semantic_model_id: int | None = None,
) -> dict:
    """Run the full analysis pipeline and return a structured result."""
    start_ms = int(time.time() * 1000)
    intent = resolve_intent(question)
    semantic_context = await build_semantic_context(db, user_id, semantic_model_id, question)
    user_prompt = _build_user_prompt(
        question, intent, semantic_context, conversation_history or []
    )
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    try:
        raw = await chat_completion(messages)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1]
            if raw.endswith("```"):
                raw = raw[: raw.rfind("```")]
        payload = json.loads(raw)
    except Exception as exc:
        logger.warning("LLM parse error: %s", exc)
        from app.ai.llm_client import _build_demo_payload

        payload = _build_demo_payload(question)

    payload["intent"] = intent.value
    payload["duration_ms"] = int(time.time() * 1000) - start_ms
    return payload


async def stream_analysis(
    question: str,
    db: AsyncSession,
    user_id: int,
    conversation_history: list[dict] | None = None,
    semantic_model_id: int | None = None,
) -> AsyncIterator[str]:
    """Stream analysis chunks as SSE data lines."""
    intent = resolve_intent(question)
    semantic_context = await build_semantic_context(db, user_id, semantic_model_id, question)
    user_prompt = _build_user_prompt(
        question, intent, semantic_context, conversation_history or []
    )
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    yield f"data: {json.dumps({'type': 'intent', 'value': intent.value})}\n\n"

    buffer = ""
    try:
        async for chunk in chat_completion_stream(messages):
            buffer += chunk
            yield f"data: {json.dumps({'type': 'chunk', 'value': chunk})}\n\n"
    except Exception as exc:
        logger.warning("Streaming error: %s", exc)
        from app.ai.llm_client import _build_demo_payload

        payload = _build_demo_payload(question)
        payload["intent"] = intent.value
        yield f"data: {json.dumps({'type': 'result', 'value': payload})}\n\n"
        yield "data: [DONE]\n\n"
        return

    try:
        raw = buffer.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1]
            if raw.endswith("```"):
                raw = raw[: raw.rfind("```")]
        payload = json.loads(raw)
        payload["intent"] = intent.value
    except Exception:
        from app.ai.llm_client import _build_demo_payload

        payload = _build_demo_payload(question)
        payload["intent"] = intent.value

    yield f"data: {json.dumps({'type': 'result', 'value': payload})}\n\n"
    yield "data: [DONE]\n\n"
