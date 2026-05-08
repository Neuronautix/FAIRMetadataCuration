from __future__ import annotations

from pathlib import Path

import jsonschema
from pydantic import ValidationError as PydanticValidationError

from fair_metadata_curation.io import load_json
from fair_metadata_curation.models import NORMALIZED_RECORD_FIELDS, NormalizedMetadataRecord
from fair_metadata_curation.validation.errors import ValidationError


class SchemaValidator:
    def __init__(self, schema_path: str | Path) -> None:
        self.schema = load_json(schema_path)

    @staticmethod
    def error(layer: str, field: str | None, message: str) -> ValidationError:
        return ValidationError(layer=layer, field=field, message=message, severity="error")

    def validate(self, candidate: dict | NormalizedMetadataRecord) -> list[ValidationError]:
        errors: list[ValidationError] = []
        if isinstance(candidate, NormalizedMetadataRecord):
            payload = candidate.model_dump()
            return errors
        if not isinstance(candidate, dict):
            return [
                ValidationError(
                    layer="json_parse",
                    field=None,
                    message="Candidate must be a JSON object.",
                    severity="error",
                )
            ]
        unknown_fields = sorted(set(candidate.keys()) - set(NORMALIZED_RECORD_FIELDS))
        errors.extend(
            ValidationError(
                layer="field_allowlist",
                field=field,
                message=f"Unknown field '{field}' is not allowed.",
                severity="error",
            )
            for field in unknown_fields
        )
        try:
            jsonschema.validate(candidate, self.schema)
        except jsonschema.ValidationError as exc:
            errors.append(
                ValidationError(
                    layer="schema",
                    field=".".join(str(item) for item in exc.path) or None,
                    message=exc.message,
                    severity="error",
                )
            )
        try:
            NormalizedMetadataRecord.model_validate(candidate)
        except PydanticValidationError as exc:
            for issue in exc.errors():
                loc = issue.get("loc", [])
                errors.append(
                    ValidationError(
                        layer="schema",
                        field=loc[0] if loc else None,
                        message=issue.get("msg", "Validation failed"),
                        severity="error",
                    )
                )
        return errors

    def normalize(self, candidate: dict) -> NormalizedMetadataRecord:
        return NormalizedMetadataRecord.model_validate(candidate)
