from __future__ import annotations

from fair_metadata_curation.llm.base import LLMOutputParseError, LLMProvider
from fair_metadata_curation.models import RawMetadataRecord


class RemediationLoop:
    def __init__(self, max_attempts: int = 3) -> None:
        self.max_attempts = max_attempts

    def run(
        self,
        record: RawMetadataRecord,
        schema: dict,
        instructions: str,
        llm: LLMProvider,
        validate_candidate,
        initial_candidate: dict | None = None,
    ) -> tuple[object, object, int, list[dict]]:
        attempts: list[dict] = []
        remediation_attempts = 0
        candidate = initial_candidate
        if candidate is None:
            try:
                candidate = llm.generate_candidate(record, schema, instructions)
            except LLMOutputParseError as exc:
                candidate = {"_parse_error": str(exc)}
        while True:
            normalized_record, report = validate_candidate(candidate)
            attempts.append(
                {
                    "record": normalized_record,
                    "report": report,
                    "metadata": dict(llm.last_response_metadata),
                }
            )
            if report.passed or remediation_attempts >= self.max_attempts:
                return normalized_record, report, remediation_attempts, attempts
            remediation_attempts += 1
            error_messages = [f"- {error.field or 'record'}: {error.message}" for error in report.errors]
            remediation_instructions = (
                instructions
                + "\n\nPrevious candidate failed validation. Fix these issues and return only valid JSON:\n"
                + "\n".join(error_messages)
            )
            try:
                candidate = llm.generate_candidate(record, schema, remediation_instructions)
            except LLMOutputParseError as exc:
                candidate = {"_parse_error": str(exc)}
