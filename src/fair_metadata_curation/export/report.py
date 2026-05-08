from __future__ import annotations

from collections import defaultdict

from fair_metadata_curation.models import CurationProposal


def generate_markdown_report(proposals: list[CurationProposal]) -> str:
    total = len(proposals)
    if total == 0:
        return "\n".join(
            [
                "# Validation Report",
                "",
                "No proposals were generated, so no validation percentages are available.",
            ]
        )
    valid = sum(1 for proposal in proposals if proposal.validation_report.passed)
    schema_valid = sum(1 for proposal in proposals if proposal.validation_report.schema_valid)
    ontology_valid = sum(1 for proposal in proposals if proposal.validation_report.ontology_valid)
    review_required = sum(1 for proposal in proposals if proposal.validation_report.warnings or not proposal.validation_report.passed)
    lines = [
        "# Validation Report",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Total records | {len(proposals)} |",
        f"| Valid % | {valid / total:.0%} |",
        f"| Schema valid % | {schema_valid / total:.0%} |",
        f"| Ontology resolved % | {ontology_valid / total:.0%} |",
        f"| Human review required % | {review_required / total:.0%} |",
        "",
    ]
    for proposal in proposals:
        if proposal.validation_report.passed and not proposal.validation_report.warnings:
            continue
        lines.extend([
            f"## {proposal.record_id}",
            "",
            f"- Passed: {proposal.validation_report.passed}",
        ])
        for error in proposal.validation_report.errors:
            lines.append(f"- Error ({error.layer}/{error.field or 'record'}): {error.message}")
        for warning in proposal.validation_report.warnings:
            lines.append(f"- Warning: {warning}")
        grouped_fields = defaultdict(list)
        for field in proposal.field_proposals:
            grouped_fields[field.attempt_number].append(field)
        for attempt_number, fields in sorted(grouped_fields.items()):
            lines.extend(
                [
                    "",
                    f"### Attempt {attempt_number}",
                    "",
                    "| Field | Source | Status |",
                    "| --- | --- | --- |",
                ]
            )
            for field in fields:
                lines.append(f"| {field.proposed_key} | {field.source_method} | {field.validation_status} |")
        lines.append("")
    return "\n".join(lines)
