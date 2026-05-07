import jsonschema
from pathlib import Path

import pytest
from pydantic import ValidationError as PydanticValidationError

from fair_metadata_curation.io import load_json
from fair_metadata_curation.models import NormalizedMetadataRecord
from fair_metadata_curation.validation.schema_validator import SchemaValidator

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "src" / "fair_metadata_curation" / "schemas" / "biosample_cedar.schema.json"


def test_valid_normalized_record_passes_pydantic_validation():
    record = NormalizedMetadataRecord(
        geo_accession="GSE1000",
        tissue="liver",
        sex="female",
        unmapped_fields={"legacy": "value"},
    )
    assert record.tissue == "liver"


def test_unknown_fields_are_rejected_unless_in_unmapped_fields():
    with pytest.raises(PydanticValidationError):
        NormalizedMetadataRecord.model_validate({"geo_accession": "GSE1000", "extra": "nope"})
    record = NormalizedMetadataRecord.model_validate({"geo_accession": "GSE1000", "unmapped_fields": {"extra": "ok"}})
    assert record.unmapped_fields == {"extra": "ok"}


def test_null_values_are_handled_correctly():
    record = NormalizedMetadataRecord.model_validate({"geo_accession": "GSE1000", "title": None})
    assert record.title is None


def test_json_schema_validation_accepts_valid_record():
    schema = load_json(SCHEMA_PATH)
    payload = {"geo_accession": "GSE1000", "title": None, "unmapped_fields": {"legacy": "value"}}
    jsonschema.validate(payload, schema)


def test_schema_validator_reports_unknown_fields():
    validator = SchemaValidator(SCHEMA_PATH)
    errors = validator.validate({"geo_accession": "GSE1000", "mystery": "value"})
    assert any(error.layer == "field_allowlist" for error in errors)
