from __future__ import annotations

from fair_metadata_curation.models import NormalizedMetadataRecord
from fair_metadata_curation.validation.errors import ValidationError


class SemanticValidator:
    allowed_sex_values = {"male", "female", "unknown", None}

    def validate(self, record: NormalizedMetadataRecord) -> list[ValidationError]:
        errors: list[ValidationError] = []
        if record.sex not in self.allowed_sex_values:
            errors.append(
                ValidationError(
                    layer="semantic",
                    field="sex",
                    message="sex must be one of: male, female, unknown, or null.",
                    severity="error",
                )
            )
        if record.organism and (record.organism_term is None or record.organism_term.match_type == "unresolved"):
            errors.append(
                ValidationError(
                    layer="semantic",
                    field="organism",
                    message="organism should resolve to a recognized species term.",
                    severity="error",
                )
            )
        return errors
