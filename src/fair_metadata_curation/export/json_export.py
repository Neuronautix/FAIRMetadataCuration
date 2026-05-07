from __future__ import annotations

import json
from pathlib import Path

from fair_metadata_curation.models import CANONICAL_FIELDS, CurationProposal


def _substitute_none(payload: dict, null_value: str | None) -> dict:
    if null_value is None:
        return payload
    return {key: (null_value if value is None else value) for key, value in payload.items()}


def export_proposals(proposals: list[CurationProposal], path: str, null_value: str | None = "NA") -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for proposal in proposals:
            record = proposal.proposed_record.model_dump(include=set(CANONICAL_FIELDS) | {"unmapped_fields"})
            handle.write(json.dumps(_substitute_none(record, null_value), ensure_ascii=False) + "\n")
    audit_path = output_path.with_suffix(output_path.suffix + ".audit.json")
    audit_path.write_text(
        json.dumps([proposal.model_dump(mode="json") for proposal in proposals], indent=2),
        encoding="utf-8",
    )
