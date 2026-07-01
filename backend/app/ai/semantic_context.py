"""Resolve business terminology using the semantic model."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    BusinessGlossaryTerm,
    Dimension,
    KPI,
    Measure,
    SemanticModel,
    SemanticModelStatus,
)

logger = logging.getLogger(__name__)


async def build_semantic_context(
    db: AsyncSession,
    user_id: int,
    semantic_model_id: int | None = None,
    question: str = "",
) -> dict:
    """Return a context dict describing available semantic entities relevant to the question."""
    context: dict = {
        "semantic_model": None,
        "relevant_measures": [],
        "relevant_kpis": [],
        "relevant_dimensions": [],
        "glossary_terms": [],
    }

    model: SemanticModel | None = None
    if semantic_model_id:
        result = await db.execute(
            select(SemanticModel).where(
                SemanticModel.id == semantic_model_id,
                SemanticModel.status == SemanticModelStatus.published,
            )
        )
        model = result.scalar_one_or_none()

    if model is None:
        result = await db.execute(
            select(SemanticModel)
            .where(SemanticModel.status == SemanticModelStatus.published)
            .order_by(SemanticModel.updated_at.desc())
            .limit(1)
        )
        model = result.scalar_one_or_none()

    if model is None:
        return context

    context["semantic_model"] = {
        "id": model.id,
        "name": model.name,
        "description": model.description,
    }

    q_lower = question.lower()

    measures_result = await db.execute(
        select(Measure).where(Measure.semantic_model_id == model.id)
    )
    measures = measures_result.scalars().all()
    for measure in measures:
        # Build a deduplicated list of non-empty search terms for this measure
        terms = [t for t in [measure.display_name.lower(), measure.category.lower()] if t]
        if not q_lower or any(term in q_lower for term in terms):
            context["relevant_measures"].append(
                {
                    "name": measure.display_name,
                    "aggregation": measure.aggregation_type,
                    "description": measure.description,
                }
            )

    kpis_result = await db.execute(select(KPI).where(KPI.semantic_model_id == model.id))
    kpis = kpis_result.scalars().all()
    for kpi in kpis:
        if not q_lower or kpi.name.lower() in q_lower or any(
            term in q_lower for term in kpi.name.lower().split()
        ):
            context["relevant_kpis"].append(
                {
                    "name": kpi.name,
                    "description": kpi.business_description,
                    "formula": kpi.formula,
                    "unit": kpi.unit,
                }
            )

    dims_result = await db.execute(
        select(Dimension).where(Dimension.semantic_model_id == model.id)
    )
    dims = dims_result.scalars().all()
    for dimension in dims:
        if not q_lower or dimension.display_name.lower() in q_lower:
            context["relevant_dimensions"].append(
                {
                    "name": dimension.display_name,
                    "data_type": dimension.data_type,
                    "description": dimension.description,
                }
            )

    terms_result = await db.execute(
        select(BusinessGlossaryTerm).where(
            BusinessGlossaryTerm.semantic_model_id == model.id
        )
    )
    terms = terms_result.scalars().all()
    for term in terms:
        synonyms = term.synonyms or []
        all_names = [term.business_name.lower(), *[synonym.lower() for synonym in synonyms]]
        if not q_lower or any(name in q_lower for name in all_names):
            context["glossary_terms"].append(
                {
                    "term": term.business_name,
                    "definition": term.description,
                    "synonyms": synonyms,
                }
            )

    return context
