from __future__ import annotations

from datetime import datetime, timezone

from fair_metadata_curation.curation.provenance import ProvenanceTracker
from fair_metadata_curation.models import CurationProposal, NormalizedMetadataRecord, RawMetadataRecord, ValidationReport


class ProposalBuilder:
    def __init__(self, provenance_tracker: ProvenanceTracker | None = None) -> None:
        self.provenance_tracker = provenance_tracker or ProvenanceTracker()

    def build(
        self,
        record_id: str,
        raw_record: RawMetadataRecord,
        final_record: NormalizedMetadataRecord,
        validation_report: ValidationReport,
        attempts: list[dict],
        remediation_attempts: int,
    ) -> CurationProposal:
        return CurationProposal(
            record_id=record_id,
            raw_record=raw_record,
            proposed_record=final_record,
            field_proposals=self.provenance_tracker.build(raw_record, attempts, final_record, validation_report),
            validation_report=validation_report,
            remediation_attempts=remediation_attempts,
            is_accepted=validation_report.passed and not any(
                item.validation_status in {"invalid", "unresolved"} for item in self.provenance_tracker.build(raw_record, attempts, final_record, validation_report)
            ),
            created_at=datetime.now(timezone.utc),
        )
