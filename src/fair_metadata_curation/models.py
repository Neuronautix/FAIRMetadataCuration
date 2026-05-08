from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

CANONICAL_FIELDS = [
    "geo_accession",
    "gsm_accession",
    "title",
    "summary",
    "organism",
    "age",
    "biomaterial_provider",
    "sex",
    "tissue",
    "cell_type",
    "cell_line",
    "design",
    "disease",
    "treatment",
    "description",
]

ONTOLOGY_TERM_FIELDS = [
    "organism_term",
    "tissue_term",
    "cell_type_term",
    "disease_term",
    "treatment_term",
]

NORMALIZED_RECORD_FIELDS = CANONICAL_FIELDS + ONTOLOGY_TERM_FIELDS + ["unmapped_fields"]


class OntologyTerm(BaseModel):
    id: str
    label: str
    ontology: str
    iri: Optional[str] = None
    match_type: Literal["exact_label", "synonym", "fuzzy", "unresolved", "ambiguous"]
    confidence: float = Field(ge=0.0, le=1.0)
    candidates: Optional[list[dict]] = None


class RawMetadataRecord(BaseModel):
    model_config = ConfigDict(extra="allow")

    geo_accession: Optional[str] = None


class NormalizedMetadataRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    geo_accession: Optional[str] = None
    gsm_accession: Optional[str] = None
    title: Optional[str] = None
    summary: Optional[str] = None
    organism: Optional[str] = None
    organism_term: Optional[OntologyTerm] = None
    age: Optional[str] = None
    biomaterial_provider: Optional[str] = None
    sex: Optional[str] = None
    tissue: Optional[str] = None
    tissue_term: Optional[OntologyTerm] = None
    cell_type: Optional[str] = None
    cell_type_term: Optional[OntologyTerm] = None
    cell_line: Optional[str] = None
    design: Optional[str] = None
    disease: Optional[str] = None
    disease_term: Optional[OntologyTerm] = None
    treatment: Optional[str] = None
    treatment_term: Optional[OntologyTerm] = None
    description: Optional[str] = None
    unmapped_fields: Optional[dict] = None

    @field_validator(*CANONICAL_FIELDS, mode="before")
    @classmethod
    def empty_strings_to_none(cls, value: Optional[str]) -> Optional[str]:
        if isinstance(value, str) and not value.strip():
            return None
        return value


class FieldCurationProposal(BaseModel):
    model_config = ConfigDict(frozen=True)

    attempt_number: int = 0
    original_key: Optional[str] = None
    original_value: Optional[str] = None
    proposed_key: str
    proposed_value: Optional[str] = None
    normalized_value: Optional[str] = None
    ontology_term: Optional[OntologyTerm] = None
    source_method: Literal["rule", "llm", "ontology_lookup", "human"]
    model_name: Optional[str] = None
    prompt_hash: Optional[str] = None
    validation_status: Literal["valid", "invalid", "needs_review", "unresolved"]
    reviewer_status: Literal["pending", "accepted", "rejected", "needs_review"] = "pending"
    timestamp: datetime


from .validation.errors import ValidationError  # noqa: E402


class ValidationReport(BaseModel):
    record_id: str
    passed: bool
    json_parse_valid: bool
    schema_valid: bool
    allowed_fields_valid: bool
    ontology_valid: bool
    semantic_valid: bool
    errors: list[ValidationError] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metrics: dict[str, float] = Field(default_factory=dict)


class CurationProposal(BaseModel):
    record_id: str
    raw_record: RawMetadataRecord
    proposed_record: NormalizedMetadataRecord
    field_proposals: list[FieldCurationProposal]
    validation_report: ValidationReport
    remediation_attempts: int = 0
    is_accepted: bool = False
    created_at: datetime
