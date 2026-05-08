from __future__ import annotations

from fair_metadata_curation.models import NormalizedMetadataRecord
from fair_metadata_curation.ontology.base import FIELD_ONTOLOGY_MAP
from fair_metadata_curation.validation.errors import ValidationError


class OntologyValidator:
    def validate(self, record: NormalizedMetadataRecord) -> list[ValidationError]:
        errors: list[ValidationError] = []
        for field_name in FIELD_ONTOLOGY_MAP:
            value = getattr(record, field_name)
            term = getattr(record, f"{field_name}_term")
            if not value:
                continue
            if term is None or term.match_type == "unresolved":
                errors.append(
                    ValidationError(
                        layer="ontology",
                        field=field_name,
                        message=f"{field_name} could not be resolved to an ontology identifier.",
                        severity="error",
                    )
                )
            elif term.match_type == "ambiguous":
                errors.append(
                    ValidationError(
                        layer="ontology",
                        field=field_name,
                        message=f"{field_name} has multiple ontology candidates and needs review.",
                        severity="warning",
                    )
                )
        return errors
