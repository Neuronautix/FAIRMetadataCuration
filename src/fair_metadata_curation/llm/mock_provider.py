from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fair_metadata_curation.llm.base import LLMOutputParseError, LLMProvider
from fair_metadata_curation.llm.prompts import build_curation_prompt, hash_prompt
from fair_metadata_curation.models import RawMetadataRecord


class MockProvider(LLMProvider):
    def __init__(
        self,
        fixture_path: str | Path | None = None,
        overrides: dict[str, list[Any]] | None = None,
        model_name: str = "mock-llm",
    ) -> None:
        super().__init__()
        if fixture_path is None:
            fixture_path = Path("tests/fixtures/mock_llm_response.json")
        self.fixture_path = Path(fixture_path)
        payload = json.loads(self.fixture_path.read_text(encoding="utf-8"))
        self.responses = {item["geo_accession"]: item["candidate"] for item in payload["records"]}
        self.overrides = {key: list(value) for key, value in (overrides or {}).items()}
        self.model_name = model_name

    def generate_candidate(
        self,
        record: RawMetadataRecord,
        schema: dict,
        instructions: str,
    ) -> dict:
        prompt = build_curation_prompt(record, schema, instructions)
        self.last_response_metadata = {
            "model_name": self.model_name,
            "prompt_hash": hash_prompt(prompt),
        }
        record_key = record.geo_accession or record.model_dump().get("geo_accession")
        if record_key in self.overrides and self.overrides[record_key]:
            candidate = self.overrides[record_key].pop(0)
        else:
            candidate = self.responses[record_key]
        if isinstance(candidate, Exception):
            raise candidate
        if isinstance(candidate, str):
            try:
                return json.loads(candidate)
            except json.JSONDecodeError as exc:
                raise LLMOutputParseError(str(exc)) from exc
        return candidate
