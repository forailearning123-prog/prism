import re
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_user
from app.database import get_db
from app.models import (
    AppUserRole,
    BusinessEntity,
    BusinessGlossaryTerm,
    CalculatedField,
    DataSource,
    Dimension,
    EntityRelationship,
    Hierarchy,
    HierarchyLevel,
    ImpactAnalysisSnapshot,
    KPI,
    Measure,
    MetadataEntry,
    RelationshipType,
    SemanticModel,
    SemanticModelDataSource,
    SemanticModelStatus,
    SemanticModelVersion,
    TimeIntelligenceDefinition,
    TrendDirection,
    User,
    ValidationResult,
    ValidationSeverity,
    DocumentationMetadata,
)
from app.semantic_schemas import (
    CalculatedFieldCreate,
    CalculatedFieldOut,
    CalculatedFieldUpdate,
    DimensionCreate,
    DimensionOut,
    DimensionUpdate,
    DocumentationOut,
    EntityCreate,
    EntityOut,
    EntityUpdate,
    GlossaryTermCreate,
    GlossaryTermOut,
    GlossaryTermUpdate,
    HierarchyCreate,
    HierarchyOut,
    HierarchyUpdate,
    ImpactAnalysisOut,
    KPICreate,
    KPIOut,
    KPIUpdate,
    MeasureCreate,
    MeasureOut,
    MeasureUpdate,
    RelationshipCandidatesResponse,
    RelationshipCandidate,
    RelationshipCreate,
    RelationshipOut,
    RelationshipUpdate,
    SemanticModelCreate,
    SemanticModelDetails,
    SemanticModelListItem,
    SemanticModelListResponse,
    SemanticModelUpdate,
    TimeIntelligenceCreate,
    TimeIntelligenceOut,
    TimeIntelligenceUpdate,
    ValidationIssueOut,
    VersionComparisonOut,
    VersionOut,
)

router = APIRouter(prefix="/semantic-models", tags=["semantic-models"])

EXPRESSION_PATTERN = re.compile(r"^[A-Za-z0-9_\s+\-*/().,<>=!&|%:'\"]+$")
PUBLISH_ROLES = {AppUserRole.admin, AppUserRole.data_architect}
EDIT_ROLES = {AppUserRole.admin, AppUserRole.data_architect, AppUserRole.business_analyst}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _assert_role(user: User, *, publish: bool = False) -> None:
    if user.is_superuser:
        return
    if publish and user.role not in PUBLISH_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Admin or Data Architect can publish")
    if not publish and user.role not in EDIT_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to modify semantic models")


def _validate_expression(expression: str, context: str) -> str | None:
    if not expression.strip():
        return f"{context} expression is empty."
    if not EXPRESSION_PATTERN.match(expression):
        return (
            f"{context} contains unsupported characters. Use letters, numbers, operators, comparison symbols, "
            "and standard function syntax only."
        )
    balance = 0
    for char in expression:
        if char == "(":
            balance += 1
        elif char == ")":
            balance -= 1
        if balance < 0:
            return f"{context} has an unmatched closing parenthesis."
    if balance != 0:
        return f"{context} has unmatched parentheses."
    return None


async def _get_model_or_404(db: AsyncSession, model_id: int) -> SemanticModel:
    model = await db.scalar(
        select(SemanticModel)
        .where(SemanticModel.id == model_id)
        .options(
            selectinload(SemanticModel.owner),
            selectinload(SemanticModel.data_sources).selectinload(SemanticModelDataSource.data_source),
            selectinload(SemanticModel.entities),
            selectinload(SemanticModel.relationships),
            selectinload(SemanticModel.dimensions),
            selectinload(SemanticModel.measures),
            selectinload(SemanticModel.calculated_fields),
            selectinload(SemanticModel.kpis),
            selectinload(SemanticModel.time_intelligence_definitions),
            selectinload(SemanticModel.hierarchies).selectinload(Hierarchy.levels),
            selectinload(SemanticModel.glossary_terms),
            selectinload(SemanticModel.validation_results),
            selectinload(SemanticModel.documentation),
        )
    )
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Semantic model not found")
    return model


def _serialize_model(model: SemanticModel) -> dict[str, Any]:
    return {
        "name": model.name,
        "description": model.description,
        "status": model.status.value,
        "selected_tables": model.selected_tables,
        "data_source_ids": [entry.data_source_id for entry in model.data_sources],
        "entities": [
            {
                "id": item.id,
                "display_name": item.display_name,
                "description": item.description,
                "source_table": item.source_table,
                "primary_key": item.primary_key,
                "business_owner": item.business_owner,
                "tags": item.tags,
            }
            for item in model.entities
        ],
        "relationships": [
            {
                "name": item.name,
                "from_entity_id": item.from_entity_id,
                "to_entity_id": item.to_entity_id,
                "from_field": item.from_field,
                "to_field": item.to_field,
                "relationship_type": item.relationship_type.value,
                "is_active": item.is_active,
            }
            for item in model.relationships
        ],
        "dimensions": [
            {
                "entity_id": item.entity_id,
                "display_name": item.display_name,
                "description": item.description,
                "data_type": item.data_type,
                "default_formatting": item.default_formatting,
                "visibility": item.visibility,
                "grouping": item.grouping,
            }
            for item in model.dimensions
        ],
        "measures": [
            {
                "entity_id": item.entity_id,
                "display_name": item.display_name,
                "aggregation_type": item.aggregation_type,
                "formatting": item.formatting,
                "description": item.description,
                "category": item.category,
                "business_definition": item.business_definition,
                "expression": item.expression,
            }
            for item in model.measures
        ],
        "calculated_fields": [
            {
                "entity_id": item.entity_id,
                "display_name": item.display_name,
                "description": item.description,
                "data_type": item.data_type,
                "expression": item.expression,
            }
            for item in model.calculated_fields
        ],
        "kpis": [
            {
                "name": item.name,
                "business_description": item.business_description,
                "formula": item.formula,
                "target_value": item.target_value,
                "warning_threshold": item.warning_threshold,
                "critical_threshold": item.critical_threshold,
                "unit": item.unit,
                "trend_direction": item.trend_direction.value,
                "display_format": item.display_format,
            }
            for item in model.kpis
        ],
        "time_intelligence_definitions": [
            {"name": item.name, "description": item.description, "expression": item.expression}
            for item in model.time_intelligence_definitions
        ],
        "hierarchies": [
            {
                "name": item.name,
                "description": item.description,
                "levels": [
                    {"level_order": level.level_order, "level_name": level.level_name, "dimension_name": level.dimension_name}
                    for level in sorted(item.levels, key=lambda value: value.level_order)
                ],
            }
            for item in model.hierarchies
        ],
        "glossary_terms": [
            {
                "business_name": item.business_name,
                "technical_name": item.technical_name,
                "description": item.description,
                "business_owner": item.business_owner,
                "synonyms": item.synonyms,
                "related_metrics": item.related_metrics,
            }
            for item in model.glossary_terms
        ],
    }


async def _record_version(
    db: AsyncSession,
    model: SemanticModel,
    user_id: int,
    notes: str,
    *,
    bump_version: bool = True,
    is_rollback: bool = False,
) -> SemanticModelVersion:
    if bump_version:
        model.current_version += 1
    version = SemanticModelVersion(
        semantic_model_id=model.id,
        version_number=model.current_version,
        status=model.status,
        created_by=user_id,
        notes=notes[:500],
        snapshot=_serialize_model(model),
        is_rollback=is_rollback,
    )
    db.add(version)
    return version


def _build_model_summary(model: SemanticModel) -> SemanticModelListItem:
    return SemanticModelListItem(
        id=model.id,
        name=model.name,
        description=model.description,
        data_sources_used=[entry.data_source.name for entry in model.data_sources],
        owner=model.owner.full_name,
        status=model.status,
        version=model.current_version,
        last_updated=model.updated_at,
        created_date=model.created_at,
    )


async def _run_validation(model: SemanticModel) -> list[ValidationIssueOut]:
    issues: list[ValidationIssueOut] = []
    entity_by_id = {entity.id: entity for entity in model.entities}
    active_relationships = [item for item in model.relationships if item.is_active]

    if len(model.entities) > 1 and not active_relationships:
        issues.append(
            ValidationIssueOut(
                severity=ValidationSeverity.error,
                code="MISSING_RELATIONSHIPS",
                message="Model has multiple entities but no active relationships.",
                details={"suggestion": "Define joins between related entities before publishing."},
            )
        )

    names = {}
    for entity in model.entities:
        key = entity.display_name.strip().lower()
        names[key] = names.get(key, 0) + 1
    duplicates = [name for name, count in names.items() if count > 1]
    for duplicate in duplicates:
        issues.append(
            ValidationIssueOut(
                severity=ValidationSeverity.error,
                code="DUPLICATE_ENTITIES",
                message=f'Duplicate entity name "{duplicate}" detected.',
                details={"suggestion": "Rename duplicate entities to unique business names."},
            )
        )

    for measure in model.measures:
        if measure.expression:
            error = _validate_expression(measure.expression, f'Measure "{measure.display_name}"')
            if error:
                issues.append(
                    ValidationIssueOut(
                        severity=ValidationSeverity.error,
                        code="INVALID_MEASURE",
                        message=error,
                        details={"measure_id": measure.id},
                    )
                )

    for field in model.calculated_fields:
        error = _validate_expression(field.expression, f'Calculated field "{field.display_name}"')
        if error:
            issues.append(
                ValidationIssueOut(
                    severity=ValidationSeverity.error,
                    code="BROKEN_CALCULATED_FIELD",
                    message=error,
                    details={"calculated_field_id": field.id},
                )
            )

    for kpi in model.kpis:
        error = _validate_expression(kpi.formula, f'KPI "{kpi.name}"')
        if error:
            issues.append(
                ValidationIssueOut(
                    severity=ValidationSeverity.error,
                    code="INVALID_KPI_FORMULA",
                    message=error,
                    details={"kpi_id": kpi.id},
                )
            )

    adjacency: dict[int, set[int]] = {}
    for rel in active_relationships:
        adjacency.setdefault(rel.from_entity_id, set()).add(rel.to_entity_id)
        adjacency.setdefault(rel.to_entity_id, set())

    visited: set[int] = set()
    stack: set[int] = set()

    def has_cycle(node: int) -> bool:
        visited.add(node)
        stack.add(node)
        for neighbor in adjacency.get(node, set()):
            if neighbor not in visited:
                if has_cycle(neighbor):
                    return True
            elif neighbor in stack:
                return True
        stack.remove(node)
        return False

    for node in adjacency:
        if node not in visited and has_cycle(node):
            issues.append(
                ValidationIssueOut(
                    severity=ValidationSeverity.error,
                    code="CIRCULAR_DEPENDENCY",
                    message="Circular relationship dependency detected across entities.",
                    details={"suggestion": "Remove or redirect cyclic relationships."},
                )
            )
            break

    connected_entities = {rel.from_entity_id for rel in active_relationships} | {rel.to_entity_id for rel in active_relationships}
    for entity in model.entities:
        if len(model.entities) > 1 and entity.id not in connected_entities:
            issues.append(
                ValidationIssueOut(
                    severity=ValidationSeverity.warning,
                    code="ORPHAN_ENTITY",
                    message=f'Entity "{entity.display_name}" is not connected to other entities.',
                    details={"entity_id": entity.id},
                )
            )

    used_tables = {entity.source_table.strip().lower() for entity in model.entities}
    unused_tables = [table for table in model.selected_tables if table.strip().lower() not in used_tables]
    for table in unused_tables:
        issues.append(
            ValidationIssueOut(
                severity=ValidationSeverity.warning,
                code="UNUSED_TABLE",
                message=f'Table "{table}" is selected but not mapped to any business entity.',
                details={"table": table},
            )
        )

    catalog: dict[str, list[str]] = {}
    for source_name, values in [
        ("entity", [item.display_name for item in model.entities]),
        ("dimension", [item.display_name for item in model.dimensions]),
        ("measure", [item.display_name for item in model.measures]),
        ("kpi", [item.name for item in model.kpis]),
        ("glossary", [item.business_name for item in model.glossary_terms]),
    ]:
        for value in values:
            key = value.strip().lower()
            catalog.setdefault(key, []).append(source_name)
    for term, source_types in catalog.items():
        if len(source_types) > 1:
            issues.append(
                ValidationIssueOut(
                    severity=ValidationSeverity.warning,
                    code="DUPLICATE_BUSINESS_NAME",
                    message=f'Business term "{term}" is reused across multiple semantic assets.',
                    details={"asset_types": source_types},
                )
            )

    for rel in active_relationships:
        if rel.from_entity_id not in entity_by_id or rel.to_entity_id not in entity_by_id:
            issues.append(
                ValidationIssueOut(
                    severity=ValidationSeverity.error,
                    code="INVALID_RELATIONSHIP",
                    message="Relationship references an entity that does not exist.",
                    details={"relationship_id": rel.id},
                )
            )

    return issues


async def _persist_validation_results(db: AsyncSession, model: SemanticModel, issues: list[ValidationIssueOut]) -> None:
    await db.execute(
        ValidationResult.__table__.delete().where(ValidationResult.semantic_model_id == model.id)  # type: ignore[arg-type]
    )
    for issue in issues:
        db.add(
            ValidationResult(
                semantic_model_id=model.id,
                severity=issue.severity,
                code=issue.code,
                message=issue.message[:500],
                details=issue.details,
            )
        )


def _model_details(model: SemanticModel) -> SemanticModelDetails:
    errors = []
    warnings = []
    for item in model.validation_results:
        issue = ValidationIssueOut(severity=item.severity, code=item.code, message=item.message, details=item.details)
        if item.severity == ValidationSeverity.error:
            errors.append(issue)
        else:
            warnings.append(issue)
    summary = _build_model_summary(model)
    return SemanticModelDetails(
        **summary.model_dump(),
        selected_tables=model.selected_tables,
        validation_errors=errors,
        validation_warnings=warnings,
        entities_count=len(model.entities),
        relationships_count=len(model.relationships),
        dimensions_count=len(model.dimensions),
        measures_count=len(model.measures),
        calculated_fields_count=len(model.calculated_fields),
        kpis_count=len(model.kpis),
    )


def _assert_component_model(component_model_id: int, requested_model_id: int) -> None:
    if component_model_id != requested_model_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Resource does not belong to the requested semantic model")


@router.get("/", response_model=SemanticModelListResponse)
async def list_semantic_models(
    search: str | None = Query(default=None),
    status_filter: SemanticModelStatus | None = Query(default=None, alias="status"),
    sort_by: str = Query(default="updated_at"),
    sort_order: str = Query(default="desc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = select(SemanticModel).options(
        selectinload(SemanticModel.owner), selectinload(SemanticModel.data_sources).selectinload(SemanticModelDataSource.data_source)
    )
    count_query = select(func.count(SemanticModel.id))

    filters = []
    if search:
        like = f"%{search.strip()}%"
        filters.append(func.lower(SemanticModel.name).like(func.lower(like)))
    if status_filter:
        filters.append(SemanticModel.status == status_filter)
    if filters:
        query = query.where(*filters)
        count_query = count_query.where(*filters)

    sort_map = {
        "name": SemanticModel.name,
        "created_at": SemanticModel.created_at,
        "updated_at": SemanticModel.updated_at,
        "status": SemanticModel.status,
        "version": SemanticModel.current_version,
    }
    sort_column = sort_map.get(sort_by, SemanticModel.updated_at)
    order = asc(sort_column) if sort_order.lower() == "asc" else desc(sort_column)
    query = query.order_by(order).offset((page - 1) * page_size).limit(page_size)

    total = (await db.execute(count_query)).scalar_one()
    items = (await db.execute(query)).scalars().all()
    return SemanticModelListResponse(items=[_build_model_summary(item) for item in items], total=total, page=page, page_size=page_size)


@router.post("/", response_model=SemanticModelDetails, status_code=status.HTTP_201_CREATED)
async def create_semantic_model(
    payload: SemanticModelCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_role(current_user)
    existing_sources = (
        await db.execute(select(DataSource).where(DataSource.id.in_(payload.data_source_ids), DataSource.is_deleted.is_(False)))
    ).scalars().all()
    if len(existing_sources) != len(set(payload.data_source_ids)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more selected data sources do not exist")

    semantic_model = SemanticModel(
        name=payload.name.strip(),
        description=payload.description.strip(),
        owner_id=current_user.id,
        status=SemanticModelStatus.draft,
        current_version=1,
        selected_tables=payload.selected_tables,
    )
    db.add(semantic_model)
    await db.flush()
    for source_id in sorted(set(payload.data_source_ids)):
        db.add(SemanticModelDataSource(semantic_model_id=semantic_model.id, data_source_id=source_id))

    await db.flush()
    model_with_relations = await _get_model_or_404(db, semantic_model.id)
    await _record_version(db, model_with_relations, current_user.id, "Initial draft created", bump_version=False)
    issues = await _run_validation(model_with_relations)
    await _persist_validation_results(db, model_with_relations, issues)
    await db.commit()
    refreshed = await _get_model_or_404(db, semantic_model.id)
    return _model_details(refreshed)


@router.get("/{model_id}", response_model=SemanticModelDetails)
async def get_semantic_model(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    model = await _get_model_or_404(db, model_id)
    return _model_details(model)


@router.patch("/{model_id}", response_model=SemanticModelDetails)
async def update_semantic_model(
    model_id: int,
    payload: SemanticModelUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_role(current_user)
    model = await _get_model_or_404(db, model_id)

    updates = payload.model_dump(exclude_unset=True)
    if "name" in updates and updates["name"]:
        model.name = updates["name"].strip()
    if "description" in updates and updates["description"] is not None:
        model.description = updates["description"].strip()
    if "selected_tables" in updates and updates["selected_tables"] is not None:
        model.selected_tables = updates["selected_tables"]
    if "data_source_ids" in updates and updates["data_source_ids"] is not None:
        source_ids = sorted(set(updates["data_source_ids"]))
        existing_sources = (
            await db.execute(select(DataSource).where(DataSource.id.in_(source_ids), DataSource.is_deleted.is_(False)))
        ).scalars().all()
        if len(existing_sources) != len(source_ids):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more selected data sources do not exist")
        await db.execute(
            SemanticModelDataSource.__table__.delete().where(SemanticModelDataSource.semantic_model_id == model.id)  # type: ignore[arg-type]
        )
        for source_id in source_ids:
            db.add(SemanticModelDataSource(semantic_model_id=model.id, data_source_id=source_id))

    model.updated_at = utcnow()
    await db.flush()
    model = await _get_model_or_404(db, model.id)
    await _record_version(db, model, current_user.id, "Semantic model updated")
    issues = await _run_validation(model)
    await _persist_validation_results(db, model, issues)
    await db.commit()
    refreshed = await _get_model_or_404(db, model.id)
    return _model_details(refreshed)


@router.post("/{model_id}/duplicate", response_model=SemanticModelDetails, status_code=status.HTTP_201_CREATED)
async def duplicate_semantic_model(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_role(current_user)
    source = await _get_model_or_404(db, model_id)
    duplicate = SemanticModel(
        name=f"{source.name} (Copy)",
        description=source.description,
        owner_id=current_user.id,
        status=SemanticModelStatus.draft,
        current_version=1,
        selected_tables=source.selected_tables,
    )
    db.add(duplicate)
    await db.flush()
    for entry in source.data_sources:
        db.add(SemanticModelDataSource(semantic_model_id=duplicate.id, data_source_id=entry.data_source_id))
    for item in source.entities:
        db.add(
            BusinessEntity(
                semantic_model_id=duplicate.id,
                display_name=item.display_name,
                description=item.description,
                source_table=item.source_table,
                primary_key=item.primary_key,
                business_owner=item.business_owner,
                tags=item.tags,
            )
        )
    await db.flush()
    duplicate = await _get_model_or_404(db, duplicate.id)
    await _record_version(db, duplicate, current_user.id, "Duplicated from existing model", bump_version=False)
    issues = await _run_validation(duplicate)
    await _persist_validation_results(db, duplicate, issues)
    await db.commit()
    refreshed = await _get_model_or_404(db, duplicate.id)
    return _model_details(refreshed)


@router.post("/{model_id}/archive", response_model=SemanticModelDetails)
async def archive_semantic_model(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_role(current_user)
    model = await _get_model_or_404(db, model_id)
    model.status = SemanticModelStatus.archived
    model.archived_at = utcnow()
    model.updated_at = utcnow()
    await _record_version(db, model, current_user.id, "Model archived")
    await db.commit()
    refreshed = await _get_model_or_404(db, model_id)
    return _model_details(refreshed)


@router.post("/{model_id}/validate", response_model=list[ValidationIssueOut])
async def validate_semantic_model(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_role(current_user)
    model = await _get_model_or_404(db, model_id)
    issues = await _run_validation(model)
    await _persist_validation_results(db, model, issues)
    await db.commit()
    return issues


@router.post("/{model_id}/publish", response_model=SemanticModelDetails)
async def publish_semantic_model(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_role(current_user, publish=True)
    model = await _get_model_or_404(db, model_id)
    issues = await _run_validation(model)
    blocking = [issue for issue in issues if issue.severity == ValidationSeverity.error]
    if blocking:
        await _persist_validation_results(db, model, issues)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Model has validation errors and cannot be published. Resolve errors and retry.",
        )
    model.status = SemanticModelStatus.published
    model.updated_at = utcnow()
    await _persist_validation_results(db, model, issues)
    await _record_version(db, model, current_user.id, "Model published")
    await db.commit()
    refreshed = await _get_model_or_404(db, model_id)
    return _model_details(refreshed)


@router.get("/{model_id}/versions", response_model=list[VersionOut])
async def get_model_versions(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    await _get_model_or_404(db, model_id)
    versions = (
        await db.execute(
            select(SemanticModelVersion)
            .where(SemanticModelVersion.semantic_model_id == model_id)
            .order_by(desc(SemanticModelVersion.version_number))
        )
    ).scalars().all()
    return versions


@router.get("/{model_id}/versions/compare", response_model=VersionComparisonOut)
async def compare_versions(
    model_id: int,
    from_version_id: int = Query(...),
    to_version_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    await _get_model_or_404(db, model_id)
    from_version = await db.scalar(
        select(SemanticModelVersion).where(
            SemanticModelVersion.id == from_version_id, SemanticModelVersion.semantic_model_id == model_id
        )
    )
    to_version = await db.scalar(
        select(SemanticModelVersion).where(
            SemanticModelVersion.id == to_version_id, SemanticModelVersion.semantic_model_id == model_id
        )
    )
    if not from_version or not to_version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")

    sections = [
        "entities",
        "relationships",
        "dimensions",
        "measures",
        "calculated_fields",
        "kpis",
        "time_intelligence_definitions",
        "hierarchies",
        "glossary_terms",
    ]
    changed_sections: list[str] = []
    summary: dict[str, dict[str, int]] = {}
    for section in sections:
        before = from_version.snapshot.get(section, [])
        after = to_version.snapshot.get(section, [])
        if before != after:
            changed_sections.append(section)
        summary[section] = {"from_count": len(before), "to_count": len(after)}
    return VersionComparisonOut(
        from_version=from_version.version_number,
        to_version=to_version.version_number,
        changed_sections=changed_sections,
        summary=summary,
    )


@router.post("/{model_id}/rollback/{version_id}", response_model=SemanticModelDetails)
async def rollback_version(
    model_id: int,
    version_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_role(current_user, publish=True)
    model = await _get_model_or_404(db, model_id)
    target = await db.scalar(
        select(SemanticModelVersion).where(SemanticModelVersion.id == version_id, SemanticModelVersion.semantic_model_id == model_id)
    )
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")

    snapshot = target.snapshot
    model.name = snapshot.get("name", model.name)
    model.description = snapshot.get("description", model.description)
    model.status = SemanticModelStatus(snapshot.get("status", model.status.value))
    model.selected_tables = snapshot.get("selected_tables", model.selected_tables)
    model.updated_at = utcnow()

    hierarchy_ids = (
        await db.execute(select(Hierarchy.id).where(Hierarchy.semantic_model_id == model_id))
    ).scalars().all()
    if hierarchy_ids:
        await db.execute(HierarchyLevel.__table__.delete().where(HierarchyLevel.hierarchy_id.in_(hierarchy_ids)))  # type: ignore[arg-type]
    await db.execute(SemanticModelDataSource.__table__.delete().where(SemanticModelDataSource.semantic_model_id == model_id))  # type: ignore[arg-type]
    await db.execute(EntityRelationship.__table__.delete().where(EntityRelationship.semantic_model_id == model_id))  # type: ignore[arg-type]
    await db.execute(BusinessEntity.__table__.delete().where(BusinessEntity.semantic_model_id == model_id))  # type: ignore[arg-type]
    await db.execute(Dimension.__table__.delete().where(Dimension.semantic_model_id == model_id))  # type: ignore[arg-type]
    await db.execute(Measure.__table__.delete().where(Measure.semantic_model_id == model_id))  # type: ignore[arg-type]
    await db.execute(CalculatedField.__table__.delete().where(CalculatedField.semantic_model_id == model_id))  # type: ignore[arg-type]
    await db.execute(KPI.__table__.delete().where(KPI.semantic_model_id == model_id))  # type: ignore[arg-type]
    await db.execute(
        TimeIntelligenceDefinition.__table__.delete().where(TimeIntelligenceDefinition.semantic_model_id == model_id)  # type: ignore[arg-type]
    )
    await db.execute(Hierarchy.__table__.delete().where(Hierarchy.semantic_model_id == model_id))  # type: ignore[arg-type]
    await db.execute(BusinessGlossaryTerm.__table__.delete().where(BusinessGlossaryTerm.semantic_model_id == model_id))  # type: ignore[arg-type]

    for source_id in snapshot.get("data_source_ids", []):
        db.add(SemanticModelDataSource(semantic_model_id=model.id, data_source_id=source_id))
    await db.flush()

    old_entity_ids: list[int] = []
    for item in snapshot.get("entities", []):
        old_entity_ids.append(item.get("id", 0))
        payload = {key: value for key, value in item.items() if key != "id"}
        db.add(BusinessEntity(semantic_model_id=model.id, **payload))
    await db.flush()

    current_entities = (
        await db.execute(select(BusinessEntity).where(BusinessEntity.semantic_model_id == model.id).order_by(BusinessEntity.id))
    ).scalars().all()
    entity_id_map: dict[int, int] = {}
    for index, entity in enumerate(current_entities):
        old_id = old_entity_ids[index] if index < len(old_entity_ids) else 0
        if old_id:
            entity_id_map[old_id] = entity.id

    for item in snapshot.get("relationships", []):
        db.add(
            EntityRelationship(
                semantic_model_id=model.id,
                name=item.get("name", ""),
                from_entity_id=entity_id_map.get(item.get("from_entity_id", 0), item.get("from_entity_id", 0)),
                to_entity_id=entity_id_map.get(item.get("to_entity_id", 0), item.get("to_entity_id", 0)),
                from_field=item.get("from_field", ""),
                to_field=item.get("to_field", ""),
                relationship_type=RelationshipType(item.get("relationship_type", RelationshipType.one_to_many.value)),
                is_active=item.get("is_active", True),
            )
        )

    for item in snapshot.get("dimensions", []):
        db.add(Dimension(semantic_model_id=model.id, **item))
    for item in snapshot.get("measures", []):
        db.add(Measure(semantic_model_id=model.id, **item))
    for item in snapshot.get("calculated_fields", []):
        db.add(CalculatedField(semantic_model_id=model.id, **item))
    for item in snapshot.get("kpis", []):
        db.add(
            KPI(
                semantic_model_id=model.id,
                name=item.get("name", ""),
                business_description=item.get("business_description", ""),
                formula=item.get("formula", ""),
                target_value=item.get("target_value"),
                warning_threshold=item.get("warning_threshold"),
                critical_threshold=item.get("critical_threshold"),
                unit=item.get("unit", ""),
                trend_direction=TrendDirection(item.get("trend_direction", TrendDirection.up.value)),
                display_format=item.get("display_format", ""),
            )
        )
    for item in snapshot.get("time_intelligence_definitions", []):
        db.add(TimeIntelligenceDefinition(semantic_model_id=model.id, **item))

    for hierarchy in snapshot.get("hierarchies", []):
        hierarchy_row = Hierarchy(semantic_model_id=model.id, name=hierarchy.get("name", ""), description=hierarchy.get("description", ""))
        db.add(hierarchy_row)
        await db.flush()
        for level in hierarchy.get("levels", []):
            db.add(HierarchyLevel(hierarchy_id=hierarchy_row.id, **level))

    for item in snapshot.get("glossary_terms", []):
        db.add(BusinessGlossaryTerm(semantic_model_id=model.id, **item))

    await db.flush()
    restored_model = await _get_model_or_404(db, model.id)
    await _record_version(db, restored_model, current_user.id, f"Rollback to version {target.version_number}", is_rollback=True)
    issues = await _run_validation(restored_model)
    await _persist_validation_results(db, restored_model, issues)
    await db.commit()
    refreshed = await _get_model_or_404(db, model.id)
    return _model_details(refreshed)


@router.get("/relationship-candidates", response_model=RelationshipCandidatesResponse)
async def detect_relationship_candidates(
    data_source_ids: list[int] = Query(default_factory=list),
    selected_tables: list[str] = Query(default_factory=list),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    normalized_tables = {table.strip().lower() for table in selected_tables if table.strip()}
    query = select(MetadataEntry)
    if data_source_ids:
        query = query.where(MetadataEntry.data_source_id.in_(data_source_ids))
    metadata_rows = (await db.execute(query)).scalars().all()
    table_columns: dict[str, set[str]] = {}
    for row in metadata_rows:
        table_name = row.object_name.strip().lower()
        if normalized_tables and table_name not in normalized_tables:
            continue
        table_columns.setdefault(table_name, set()).add(row.column_name.strip().lower())

    candidates: list[RelationshipCandidate] = []
    for left_table, left_columns in table_columns.items():
        for column in left_columns:
            if not column.endswith("_id"):
                continue
            right_table = f"{column[:-3]}s"
            if right_table in table_columns and "id" in table_columns[right_table]:
                candidates.append(
                    RelationshipCandidate(
                        left_table=left_table,
                        right_table=right_table,
                        left_column=column,
                        right_column="id",
                        relationship_type=RelationshipType.many_to_one,
                    )
                )
    return RelationshipCandidatesResponse(candidates=candidates)


@router.get("/{model_id}/impact-analysis", response_model=ImpactAnalysisOut)
async def get_impact_analysis(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    model = await _get_model_or_404(db, model_id)
    latest = await db.scalar(
        select(ImpactAnalysisSnapshot)
        .where(ImpactAnalysisSnapshot.semantic_model_id == model.id)
        .order_by(desc(ImpactAnalysisSnapshot.created_at))
    )
    if latest:
        return ImpactAnalysisOut(
            dashboards_affected=latest.dashboards_affected,
            reports_affected=latest.reports_affected,
            kpis_affected=latest.kpis_affected,
            ai_features_affected=latest.ai_features_affected,
            scheduled_jobs_affected=latest.scheduled_jobs_affected,
            generated_at=latest.created_at,
        )

    generated = ImpactAnalysisSnapshot(
        semantic_model_id=model.id,
        dashboards_affected=[],
        reports_affected=[],
        kpis_affected=[kpi.name for kpi in model.kpis],
        ai_features_affected=["insight-generation", "conversational-analytics"] if model.status == SemanticModelStatus.published else [],
        scheduled_jobs_affected=["daily-briefing-refresh"] if model.status == SemanticModelStatus.published else [],
    )
    db.add(generated)
    await db.commit()
    return ImpactAnalysisOut(
        dashboards_affected=generated.dashboards_affected,
        reports_affected=generated.reports_affected,
        kpis_affected=generated.kpis_affected,
        ai_features_affected=generated.ai_features_affected,
        scheduled_jobs_affected=generated.scheduled_jobs_affected,
        generated_at=generated.created_at,
    )


@router.post("/{model_id}/documentation/generate", response_model=DocumentationOut)
async def generate_documentation(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_role(current_user)
    model = await _get_model_or_404(db, model_id)
    content = {
        "model": {"name": model.name, "description": model.description, "status": model.status.value, "version": model.current_version},
        "entities": [EntityOut.model_validate(entity).model_dump() for entity in model.entities],
        "relationships": [RelationshipOut.model_validate(item).model_dump() for item in model.relationships],
        "dimensions": [DimensionOut.model_validate(item).model_dump() for item in model.dimensions],
        "measures": [MeasureOut.model_validate(item).model_dump() for item in model.measures],
        "calculated_fields": [CalculatedFieldOut.model_validate(item).model_dump() for item in model.calculated_fields],
        "kpis": [KPIOut.model_validate(item).model_dump() for item in model.kpis],
        "time_intelligence": [TimeIntelligenceOut.model_validate(item).model_dump() for item in model.time_intelligence_definitions],
        "hierarchies": [
            {
                "name": hierarchy.name,
                "description": hierarchy.description,
                "levels": [
                    {"order": level.level_order, "name": level.level_name, "dimension": level.dimension_name}
                    for level in sorted(hierarchy.levels, key=lambda value: value.level_order)
                ],
            }
            for hierarchy in model.hierarchies
        ],
        "glossary": [GlossaryTermOut.model_validate(item).model_dump() for item in model.glossary_terms],
        "business_definitions": {
            "measures": {item.display_name: item.business_definition for item in model.measures},
            "kpis": {item.name: item.business_description for item in model.kpis},
        },
    }
    if model.documentation:
        model.documentation.generated_by = current_user.id
        model.documentation.generated_at = utcnow()
        model.documentation.content = content
    else:
        db.add(
            DocumentationMetadata(
                semantic_model_id=model.id,
                generated_by=current_user.id,
                generated_at=utcnow(),
                content=content,
            )
        )
    await db.commit()
    refreshed = await _get_model_or_404(db, model.id)
    documentation = refreshed.documentation
    if not documentation:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate documentation")
    return DocumentationOut(generated_at=documentation.generated_at, generated_by=documentation.generated_by, content=documentation.content)


@router.get("/{model_id}/documentation", response_model=DocumentationOut)
async def get_documentation(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    model = await _get_model_or_404(db, model_id)
    if not model.documentation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documentation has not been generated for this model")
    return DocumentationOut(
        generated_at=model.documentation.generated_at,
        generated_by=model.documentation.generated_by,
        content=model.documentation.content,
    )


@router.get("/{model_id}/entities", response_model=list[EntityOut])
async def list_entities(model_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    await _get_model_or_404(db, model_id)
    rows = (await db.execute(select(BusinessEntity).where(BusinessEntity.semantic_model_id == model_id).order_by(BusinessEntity.id))).scalars().all()
    return rows


@router.post("/{model_id}/entities", response_model=EntityOut, status_code=status.HTTP_201_CREATED)
async def create_entity(
    model_id: int,
    payload: EntityCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_role(current_user)
    await _get_model_or_404(db, model_id)
    row = BusinessEntity(semantic_model_id=model_id, **payload.model_dump())
    db.add(row)
    await db.flush()
    model = await _get_model_or_404(db, model_id)
    await _record_version(db, model, current_user.id, f'Entity "{row.display_name}" created')
    await db.commit()
    await db.refresh(row)
    return row


@router.patch("/{model_id}/entities/{entity_id}", response_model=EntityOut)
async def update_entity(
    model_id: int,
    entity_id: int,
    payload: EntityUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_role(current_user)
    row = await db.scalar(select(BusinessEntity).where(BusinessEntity.id == entity_id))
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found")
    _assert_component_model(row.semantic_model_id, model_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    row.updated_at = utcnow()
    model = await _get_model_or_404(db, model_id)
    await _record_version(db, model, current_user.id, f'Entity "{row.display_name}" updated')
    await db.commit()
    await db.refresh(row)
    return row


@router.delete("/{model_id}/entities/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entity(
    model_id: int,
    entity_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_role(current_user)
    row = await db.scalar(select(BusinessEntity).where(BusinessEntity.id == entity_id))
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found")
    _assert_component_model(row.semantic_model_id, model_id)
    await db.delete(row)
    model = await _get_model_or_404(db, model_id)
    await _record_version(db, model, current_user.id, "Entity deleted")
    await db.commit()


@router.get("/{model_id}/relationships", response_model=list[RelationshipOut])
async def list_relationships(model_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    await _get_model_or_404(db, model_id)
    rows = (await db.execute(select(EntityRelationship).where(EntityRelationship.semantic_model_id == model_id).order_by(EntityRelationship.id))).scalars().all()
    return rows


@router.post("/{model_id}/relationships", response_model=RelationshipOut, status_code=status.HTTP_201_CREATED)
async def create_relationship(
    model_id: int,
    payload: RelationshipCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_role(current_user)
    await _get_model_or_404(db, model_id)
    row = EntityRelationship(semantic_model_id=model_id, **payload.model_dump())
    db.add(row)
    await db.flush()
    model = await _get_model_or_404(db, model_id)
    await _record_version(db, model, current_user.id, "Relationship created")
    await db.commit()
    await db.refresh(row)
    return row


@router.patch("/{model_id}/relationships/{relationship_id}", response_model=RelationshipOut)
async def update_relationship(
    model_id: int,
    relationship_id: int,
    payload: RelationshipUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_role(current_user)
    row = await db.scalar(select(EntityRelationship).where(EntityRelationship.id == relationship_id))
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relationship not found")
    _assert_component_model(row.semantic_model_id, model_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    row.updated_at = utcnow()
    model = await _get_model_or_404(db, model_id)
    await _record_version(db, model, current_user.id, "Relationship updated")
    await db.commit()
    await db.refresh(row)
    return row


@router.delete("/{model_id}/relationships/{relationship_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_relationship(
    model_id: int,
    relationship_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_role(current_user)
    row = await db.scalar(select(EntityRelationship).where(EntityRelationship.id == relationship_id))
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relationship not found")
    _assert_component_model(row.semantic_model_id, model_id)
    await db.delete(row)
    model = await _get_model_or_404(db, model_id)
    await _record_version(db, model, current_user.id, "Relationship deleted")
    await db.commit()


for route_name, orm_model, create_schema, update_schema, output_schema in [
    ("dimensions", Dimension, DimensionCreate, DimensionUpdate, DimensionOut),
    ("measures", Measure, MeasureCreate, MeasureUpdate, MeasureOut),
    ("calculated-fields", CalculatedField, CalculatedFieldCreate, CalculatedFieldUpdate, CalculatedFieldOut),
    ("kpis", KPI, KPICreate, KPIUpdate, KPIOut),
    ("time-intelligence", TimeIntelligenceDefinition, TimeIntelligenceCreate, TimeIntelligenceUpdate, TimeIntelligenceOut),
    ("glossary", BusinessGlossaryTerm, GlossaryTermCreate, GlossaryTermUpdate, GlossaryTermOut),
]:

    @router.get(f"/{{model_id}}/{route_name}", response_model=list[output_schema])  # type: ignore[misc,valid-type]
    async def _list_items(
        model_id: int,
        db: AsyncSession = Depends(get_db),
        _: User = Depends(get_current_user),
        orm_model=orm_model,
    ):
        await _get_model_or_404(db, model_id)
        return (await db.execute(select(orm_model).where(orm_model.semantic_model_id == model_id).order_by(orm_model.id))).scalars().all()

    @router.post(f"/{{model_id}}/{route_name}", response_model=output_schema, status_code=status.HTTP_201_CREATED)  # type: ignore[misc,valid-type]
    async def _create_item(
        model_id: int,
        payload: create_schema,  # type: ignore[valid-type]
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
        orm_model=orm_model,
    ):
        _assert_role(current_user)
        await _get_model_or_404(db, model_id)
        row = orm_model(semantic_model_id=model_id, **payload.model_dump())
        db.add(row)
        await db.flush()
        model = await _get_model_or_404(db, model_id)
        await _record_version(db, model, current_user.id, f"{route_name} item created")
        await db.commit()
        await db.refresh(row)
        return row

    @router.patch(f"/{{model_id}}/{route_name}/{{item_id}}", response_model=output_schema)  # type: ignore[misc,valid-type]
    async def _update_item(
        model_id: int,
        item_id: int,
        payload: update_schema,  # type: ignore[valid-type]
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
        orm_model=orm_model,
    ):
        _assert_role(current_user)
        row = await db.scalar(select(orm_model).where(orm_model.id == item_id))
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
        _assert_component_model(row.semantic_model_id, model_id)
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(row, key, value)
        if hasattr(row, "updated_at"):
            row.updated_at = utcnow()
        model = await _get_model_or_404(db, model_id)
        await _record_version(db, model, current_user.id, f"{route_name} item updated")
        await db.commit()
        await db.refresh(row)
        return row

    @router.delete(f"/{{model_id}}/{route_name}/{{item_id}}", status_code=status.HTTP_204_NO_CONTENT)
    async def _delete_item(
        model_id: int,
        item_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
        orm_model=orm_model,
    ):
        _assert_role(current_user)
        row = await db.scalar(select(orm_model).where(orm_model.id == item_id))
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
        _assert_component_model(row.semantic_model_id, model_id)
        await db.delete(row)
        model = await _get_model_or_404(db, model_id)
        await _record_version(db, model, current_user.id, f"{route_name} item deleted")
        await db.commit()


@router.get("/{model_id}/hierarchies", response_model=list[HierarchyOut])
async def list_hierarchies(model_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    await _get_model_or_404(db, model_id)
    rows = (
        await db.execute(select(Hierarchy).where(Hierarchy.semantic_model_id == model_id).options(selectinload(Hierarchy.levels)))
    ).scalars().all()
    return [
        HierarchyOut(name=row.name, description=row.description, levels=row.levels, id=row.id, created_at=row.created_at)
        for row in rows
    ]


@router.post("/{model_id}/hierarchies", response_model=HierarchyOut, status_code=status.HTTP_201_CREATED)
async def create_hierarchy(
    model_id: int,
    payload: HierarchyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_role(current_user)
    await _get_model_or_404(db, model_id)
    row = Hierarchy(semantic_model_id=model_id, name=payload.name, description=payload.description)
    db.add(row)
    await db.flush()
    for level in payload.levels:
        db.add(HierarchyLevel(hierarchy_id=row.id, **level.model_dump()))
    await db.flush()
    model = await _get_model_or_404(db, model_id)
    await _record_version(db, model, current_user.id, "Hierarchy created")
    await db.commit()
    refreshed = await db.scalar(select(Hierarchy).where(Hierarchy.id == row.id).options(selectinload(Hierarchy.levels)))
    if not refreshed:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to load hierarchy")
    return HierarchyOut(
        id=refreshed.id,
        name=refreshed.name,
        description=refreshed.description,
        levels=refreshed.levels,
        created_at=refreshed.created_at,
    )


@router.patch("/{model_id}/hierarchies/{hierarchy_id}", response_model=HierarchyOut)
async def update_hierarchy(
    model_id: int,
    hierarchy_id: int,
    payload: HierarchyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_role(current_user)
    row = await db.scalar(select(Hierarchy).where(Hierarchy.id == hierarchy_id).options(selectinload(Hierarchy.levels)))
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hierarchy not found")
    _assert_component_model(row.semantic_model_id, model_id)
    updates = payload.model_dump(exclude_unset=True)
    if "name" in updates:
        row.name = updates["name"]
    if "description" in updates:
        row.description = updates["description"]
    if "levels" in updates and updates["levels"] is not None:
        await db.execute(HierarchyLevel.__table__.delete().where(HierarchyLevel.hierarchy_id == row.id))  # type: ignore[arg-type]
        for level in updates["levels"]:
            if hasattr(level, "model_dump"):
                level = level.model_dump()
            db.add(HierarchyLevel(hierarchy_id=row.id, **level))
    model = await _get_model_or_404(db, model_id)
    await _record_version(db, model, current_user.id, "Hierarchy updated")
    await db.commit()
    refreshed = await db.scalar(select(Hierarchy).where(Hierarchy.id == row.id).options(selectinload(Hierarchy.levels)))
    if not refreshed:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to load hierarchy")
    return HierarchyOut(
        id=refreshed.id,
        name=refreshed.name,
        description=refreshed.description,
        levels=refreshed.levels,
        created_at=refreshed.created_at,
    )


@router.delete("/{model_id}/hierarchies/{hierarchy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_hierarchy(
    model_id: int,
    hierarchy_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_role(current_user)
    row = await db.scalar(select(Hierarchy).where(Hierarchy.id == hierarchy_id))
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hierarchy not found")
    _assert_component_model(row.semantic_model_id, model_id)
    await db.delete(row)
    model = await _get_model_or_404(db, model_id)
    await _record_version(db, model, current_user.id, "Hierarchy deleted")
    await db.commit()
