from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.models import RelationshipType, SemanticModelStatus, TrendDirection, ValidationSeverity


class ValidationIssueOut(BaseModel):
    severity: ValidationSeverity
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class SemanticModelBase(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: str = Field(default="", max_length=2000)
    data_source_ids: list[int] = Field(default_factory=list, min_length=1)
    selected_tables: list[str] = Field(default_factory=list)

    @field_validator("selected_tables")
    @classmethod
    def clean_tables(cls, value: list[str]) -> list[str]:
        seen = set()
        cleaned: list[str] = []
        for table in value:
            normalized = table.strip()
            if not normalized:
                continue
            key = normalized.lower()
            if key not in seen:
                seen.add(key)
                cleaned.append(normalized)
        return cleaned


class SemanticModelCreate(SemanticModelBase):
    pass


class SemanticModelUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    data_source_ids: list[int] | None = None
    selected_tables: list[str] | None = None


class SemanticModelListItem(BaseModel):
    id: int
    name: str
    description: str
    data_sources_used: list[str]
    owner: str
    status: SemanticModelStatus
    version: int
    last_updated: datetime
    created_date: datetime


class SemanticModelListResponse(BaseModel):
    items: list[SemanticModelListItem]
    total: int
    page: int
    page_size: int


class SemanticModelDetails(SemanticModelListItem):
    selected_tables: list[str] = Field(default_factory=list)
    validation_errors: list[ValidationIssueOut] = Field(default_factory=list)
    validation_warnings: list[ValidationIssueOut] = Field(default_factory=list)
    entities_count: int
    relationships_count: int
    dimensions_count: int
    measures_count: int
    calculated_fields_count: int
    kpis_count: int


class EntityBase(BaseModel):
    display_name: str = Field(min_length=2, max_length=255)
    description: str = Field(default="", max_length=2000)
    source_table: str = Field(min_length=1, max_length=255)
    primary_key: str = Field(min_length=1, max_length=255)
    business_owner: str = Field(default="", max_length=255)
    tags: list[str] = Field(default_factory=list)


class EntityCreate(EntityBase):
    pass


class EntityUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    source_table: str | None = Field(default=None, min_length=1, max_length=255)
    primary_key: str | None = Field(default=None, min_length=1, max_length=255)
    business_owner: str | None = Field(default=None, max_length=255)
    tags: list[str] | None = None


class EntityOut(EntityBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RelationshipBase(BaseModel):
    name: str = Field(default="", max_length=255)
    from_entity_id: int
    to_entity_id: int
    from_field: str = Field(min_length=1, max_length=255)
    to_field: str = Field(min_length=1, max_length=255)
    relationship_type: RelationshipType
    is_active: bool = True


class RelationshipCreate(RelationshipBase):
    pass


class RelationshipUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    from_entity_id: int | None = None
    to_entity_id: int | None = None
    from_field: str | None = Field(default=None, min_length=1, max_length=255)
    to_field: str | None = Field(default=None, min_length=1, max_length=255)
    relationship_type: RelationshipType | None = None
    is_active: bool | None = None


class RelationshipOut(RelationshipBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DimensionBase(BaseModel):
    entity_id: int | None = None
    display_name: str = Field(min_length=2, max_length=255)
    description: str = Field(default="", max_length=2000)
    data_type: str = Field(default="string", max_length=100)
    default_formatting: str = Field(default="", max_length=100)
    visibility: bool = True
    grouping: str = Field(default="", max_length=100)


class DimensionCreate(DimensionBase):
    pass


class DimensionUpdate(BaseModel):
    entity_id: int | None = None
    display_name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    data_type: str | None = Field(default=None, max_length=100)
    default_formatting: str | None = Field(default=None, max_length=100)
    visibility: bool | None = None
    grouping: str | None = Field(default=None, max_length=100)


class DimensionOut(DimensionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MeasureBase(BaseModel):
    entity_id: int | None = None
    display_name: str = Field(min_length=2, max_length=255)
    aggregation_type: str = Field(default="sum", max_length=50)
    formatting: str = Field(default="", max_length=100)
    description: str = Field(default="", max_length=2000)
    category: str = Field(default="", max_length=100)
    business_definition: str = Field(default="", max_length=2000)
    expression: str | None = None


class MeasureCreate(MeasureBase):
    pass


class MeasureUpdate(BaseModel):
    entity_id: int | None = None
    display_name: str | None = Field(default=None, min_length=2, max_length=255)
    aggregation_type: str | None = Field(default=None, max_length=50)
    formatting: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=2000)
    category: str | None = Field(default=None, max_length=100)
    business_definition: str | None = Field(default=None, max_length=2000)
    expression: str | None = None


class MeasureOut(MeasureBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CalculatedFieldBase(BaseModel):
    entity_id: int | None = None
    display_name: str = Field(min_length=2, max_length=255)
    description: str = Field(default="", max_length=2000)
    data_type: str = Field(default="string", max_length=100)
    expression: str = Field(min_length=1)


class CalculatedFieldCreate(CalculatedFieldBase):
    pass


class CalculatedFieldUpdate(BaseModel):
    entity_id: int | None = None
    display_name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    data_type: str | None = Field(default=None, max_length=100)
    expression: str | None = None


class CalculatedFieldOut(CalculatedFieldBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class KPIBase(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    business_description: str = Field(default="", max_length=2000)
    formula: str = Field(min_length=1)
    target_value: float | None = None
    warning_threshold: float | None = None
    critical_threshold: float | None = None
    unit: str = Field(default="", max_length=50)
    trend_direction: TrendDirection = TrendDirection.up
    display_format: str = Field(default="", max_length=100)


class KPICreate(KPIBase):
    pass


class KPIUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    business_description: str | None = Field(default=None, max_length=2000)
    formula: str | None = None
    target_value: float | None = None
    warning_threshold: float | None = None
    critical_threshold: float | None = None
    unit: str | None = Field(default=None, max_length=50)
    trend_direction: TrendDirection | None = None
    display_format: str | None = Field(default=None, max_length=100)


class KPIOut(KPIBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TimeIntelligenceBase(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: str = Field(default="", max_length=2000)
    expression: str = Field(min_length=1)


class TimeIntelligenceCreate(TimeIntelligenceBase):
    pass


class TimeIntelligenceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    expression: str | None = None


class TimeIntelligenceOut(TimeIntelligenceBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class HierarchyLevelInput(BaseModel):
    level_order: int = Field(ge=1)
    level_name: str = Field(min_length=1, max_length=255)
    dimension_name: str = Field(min_length=1, max_length=255)


class HierarchyBase(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: str = Field(default="", max_length=2000)
    levels: list[HierarchyLevelInput] = Field(default_factory=list, min_length=1)


class HierarchyCreate(HierarchyBase):
    pass


class HierarchyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    levels: list[HierarchyLevelInput] | None = None


class HierarchyOut(HierarchyBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class GlossaryTermBase(BaseModel):
    business_name: str = Field(min_length=2, max_length=255)
    technical_name: str = Field(default="", max_length=255)
    description: str = Field(default="", max_length=2000)
    business_owner: str = Field(default="", max_length=255)
    synonyms: list[str] = Field(default_factory=list)
    related_metrics: list[str] = Field(default_factory=list)


class GlossaryTermCreate(GlossaryTermBase):
    pass


class GlossaryTermUpdate(BaseModel):
    business_name: str | None = Field(default=None, min_length=2, max_length=255)
    technical_name: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    business_owner: str | None = Field(default=None, max_length=255)
    synonyms: list[str] | None = None
    related_metrics: list[str] | None = None


class GlossaryTermOut(GlossaryTermBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VersionOut(BaseModel):
    id: int
    version_number: int
    status: SemanticModelStatus
    created_by: int
    notes: str
    is_rollback: bool
    created_at: datetime

    class Config:
        from_attributes = True


class VersionComparisonOut(BaseModel):
    from_version: int
    to_version: int
    changed_sections: list[str]
    summary: dict[str, dict[str, int]]


class RelationshipCandidate(BaseModel):
    left_table: str
    right_table: str
    left_column: str
    right_column: str
    relationship_type: RelationshipType


class RelationshipCandidatesResponse(BaseModel):
    candidates: list[RelationshipCandidate]


class DocumentationOut(BaseModel):
    generated_at: datetime
    generated_by: int
    content: dict[str, Any]


class ImpactAnalysisOut(BaseModel):
    dashboards_affected: list[str]
    reports_affected: list[str]
    kpis_affected: list[str]
    ai_features_affected: list[str]
    scheduled_jobs_affected: list[str]
    generated_at: datetime

