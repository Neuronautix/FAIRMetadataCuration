from __future__ import annotations

from pathlib import Path

from fair_metadata_curation.curation.proposal import ProposalBuilder
from fair_metadata_curation.curation.remediation import RemediationLoop
from fair_metadata_curation.llm.base import LLMOutputParseError, LLMProvider
from fair_metadata_curation.models import RawMetadataRecord, ValidationReport
from fair_metadata_curation.ontology.base import OntologyResolver
from fair_metadata_curation.ontology.normalize import ground_record
from fair_metadata_curation.preprocessing import extract_canonical_fields, normalize_keys, normalize_missing
from fair_metadata_curation.validation import OntologyValidator, SchemaValidator, SemanticValidator


class CurationPipeline:
    def __init__(self, llm: LLMProvider, resolver: OntologyResolver, config: dict | None = None) -> None:
        self.llm = llm
        self.resolver = resolver
        self.config = config or {}
        schema_path = self.config.get(
            "schema_path",
            Path(__file__).resolve().parents[1] / "schemas" / "biosample_cedar.schema.json",
        )
        self.schema_validator = SchemaValidator(schema_path)
        self.ontology_validator = OntologyValidator()
        self.semantic_validator = SemanticValidator()
        self.remediation = RemediationLoop(self.config.get("max_remediation_attempts", 3))
        self.proposal_builder = ProposalBuilder()
        self.instructions = self.config.get(
            "instructions",
            "Normalize the metadata into canonical FAIR fields and preserve unknown data under unmapped_fields.",
        )
        self.schema = self.schema_validator.schema

    def run(self, record: dict) -> object:
        normalized_keys = normalize_keys(record)
        cleaned = normalize_missing(normalized_keys)
        canonical, unmapped = extract_canonical_fields(cleaned)
        raw_record = RawMetadataRecord.model_validate(cleaned)
        record_id = canonical.get("geo_accession") or cleaned.get("geo_accession") or cleaned.get("gsm_accession") or "record"
        fallback_payload = {key: value for key, value in canonical.items() if key in self.schema["properties"]}
        fallback_payload["unmapped_fields"] = unmapped or None

        def validate_candidate(candidate: dict):
            if "_parse_error" in candidate:
                report = self._build_report(
                    record_id,
                    [
                        self.schema_validator.error(
                            layer="json_parse",
                            field=None,
                            message=candidate["_parse_error"],
                        )
                    ],
                    [],
                    [],
                )
                return self.schema_validator.normalize(fallback_payload), report
            payload = dict(candidate)
            payload.setdefault("unmapped_fields", unmapped or None)
            schema_errors = self.schema_validator.validate(payload)
            if schema_errors:
                report = self._build_report(record_id, schema_errors, [], [])
                fallback = self.schema_validator.normalize(
                    {
                        **fallback_payload,
                        **{key: value for key, value in payload.items() if key in self.schema["properties"]},
                    }
                )
                return fallback, report
            normalized_record = self.schema_validator.normalize(payload)
            grounded = ground_record(normalized_record, self.resolver)
            ontology_errors = self.ontology_validator.validate(grounded)
            semantic_errors = self.semantic_validator.validate(grounded)
            report = self._build_report(record_id, [], ontology_errors, semantic_errors)
            return grounded, report

        try:
            initial_candidate = self.llm.generate_candidate(raw_record, self.schema, self.instructions)
        except LLMOutputParseError as exc:
            initial_candidate = {"_parse_error": str(exc)}
        final_record, report, remediation_attempts, attempts = self.remediation.run(
            raw_record,
            self.schema,
            self.instructions,
            self.llm,
            validate_candidate,
            initial_candidate=initial_candidate,
        )
        if remediation_attempts >= self.remediation.max_attempts and not report.passed:
            report.warnings.append("Record requires human review after remediation limit was reached.")
        return self.proposal_builder.build(
            record_id=record_id,
            raw_record=raw_record,
            final_record=final_record,
            validation_report=report,
            attempts=attempts,
            remediation_attempts=remediation_attempts,
        )

    def run_batch(self, records: list[dict]) -> list[object]:
        return [self.run(record) for record in records]

    def _build_report(self, record_id: str, schema_errors: list, ontology_errors: list, semantic_errors: list) -> ValidationReport:
        all_errors = list(schema_errors) + [error for error in ontology_errors if error.severity == "error"] + list(semantic_errors)
        warnings = [error.message for error in ontology_errors if error.severity == "warning"]
        return ValidationReport(
            record_id=record_id,
            passed=not all_errors,
            json_parse_valid=not any(error.layer == "json_parse" for error in schema_errors),
            schema_valid=not any(error.layer == "schema" for error in schema_errors),
            allowed_fields_valid=not any(error.layer == "field_allowlist" for error in schema_errors),
            ontology_valid=not any(error.layer == "ontology" and error.severity == "error" for error in ontology_errors),
            semantic_valid=not semantic_errors,
            errors=all_errors,
            warnings=warnings,
            metrics={
                "error_count": float(len(all_errors)),
                "warning_count": float(len(warnings)),
            },
        )
