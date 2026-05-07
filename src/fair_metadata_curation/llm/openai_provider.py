from __future__ import annotations

import json
import logging
from typing import Any

from fair_metadata_curation.llm.base import LLMOutputParseError, LLMProvider
from fair_metadata_curation.llm.prompts import build_curation_prompt, hash_prompt
from fair_metadata_curation.models import RawMetadataRecord

LOGGER = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    def __init__(self, client: Any, model_name: str = "gpt-4.1-mini") -> None:
        super().__init__()
        self.client = client
        self.model_name = model_name

    def generate_candidate(
        self,
        record: RawMetadataRecord,
        schema: dict,
        instructions: str,
    ) -> dict:
        prompt = build_curation_prompt(record, schema, instructions)
        prompt_hash = hash_prompt(prompt)
        self.last_response_metadata = {
            "model_name": self.model_name,
            "prompt_hash": prompt_hash,
        }
        response = self.client.chat.completions.create(
            model=self.model_name,
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.choices[0].message.content
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            LOGGER.error("Failed to parse OpenAI JSON response", exc_info=exc)
            raise LLMOutputParseError(str(exc)) from exc
