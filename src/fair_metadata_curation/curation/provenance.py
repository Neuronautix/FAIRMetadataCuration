from __future__ import annotations

from datetime import datetime, timezone

from fair_metadata_curation.models import CANONICAL_FIELDS, FieldCurationProposal, NormalizedMetadataRecord, RawMetadataRecord, ValidationReport


class ProvenanceTracker:
    def build(
        self,
        raw_record: RawMetadataRecord,
        attempts: list[dict],
        final_record: NormalizedMetadataRecord,
        validation_report: ValidationReport,
    ) -> list[FieldCurationProposal]:
        raw_payload = raw_record.model_dump()
        field_proposals: list[FieldCurationProposal] = []
        for attempt in attempts:
            candidate = attempt["record"]
            metadata = attempt.get("metadata", {})
            report = attempt.get("report", validation_report)
            for field_name in CANONICAL_FIELDS:
                proposed_value = getattr(candidate, field_name, None)
                normalized_value = getattr(final_record, field_name, None)
                if field_name not in raw_payload and proposed_value is None and normalized_value is None:
                    continue
                status = self._status_for_field(field_name, report)
                field_proposals.append(
                    FieldCurationProposal(
                        original_key=field_name if field_name in raw_payload else None,
                        original_value=raw_payload.get(field_name),
                        proposed_key=field_name,
                        proposed_value=proposed_value,
                        normalized_value=normalized_value,
                        ontology_term=getattr(candidate, f"{field_name}_term", None) if hasattr(candidate, f"{field_name}_term") else None,
                        source_method="llm",
                        model_name=metadata.get("model_name"),
                        prompt_hash=metadata.get("prompt_hash"),
                        validation_status=status,
                        reviewer_status="needs_review" if status in {"invalid", "needs_review", "unresolved"} else "pending",
                        timestamp=datetime.now(timezone.utc),
                    )
                )
        return field_proposals

    @staticmethod
    def _status_for_field(field_name: str, report: ValidationReport) -> str:
        statuses = [error for error in report.errors if error.field == field_name]
        if any(error.layer == "ontology" for error in statuses):
            return "unresolved"
        if statuses:
            return "invalid"
        if any(field_name in warning for warning in report.warnings):
            return "unresolved"
        return "valid"
