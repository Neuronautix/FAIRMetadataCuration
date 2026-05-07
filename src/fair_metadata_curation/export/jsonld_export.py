from __future__ import annotations

import json
from pathlib import Path

from fair_metadata_curation.models import CurationProposal

FIELD_MAP = {
    "tissue": "schema:anatomicalLocation",
    "organism": "schema:taxonRank",
    "disease": "schema:MedicalCondition",
}


def export_jsonld(proposals: list[CurationProposal], path: str) -> None:
    graph = []
    for proposal in proposals:
        node = {
            "@id": f"urn:fair-metadata:{proposal.record_id}",
            "@type": "schema:CreativeWork",
            "schema:name": proposal.proposed_record.title,
            "schema:description": proposal.proposed_record.description or proposal.proposed_record.summary,
        }
        for field_name, predicate in FIELD_MAP.items():
            value = getattr(proposal.proposed_record, field_name)
            term = getattr(proposal.proposed_record, f"{field_name}_term")
            if value is None:
                continue
            if term and term.iri:
                node[predicate] = {"@id": term.iri, "name": term.label}
            else:
                node[predicate] = value
        graph.append(node)
    Path(path).write_text(json.dumps(graph, indent=2), encoding="utf-8")
