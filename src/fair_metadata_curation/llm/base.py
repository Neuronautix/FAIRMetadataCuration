from __future__ import annotations

from abc import ABC, abstractmethod

from fair_metadata_curation.models import RawMetadataRecord


class LLMOutputParseError(ValueError):
    """Raised when an LLM response cannot be parsed as JSON."""


class LLMProvider(ABC):
    def __init__(self) -> None:
        self.last_response_metadata: dict[str, str | None] = {
            "model_name": None,
            "prompt_hash": None,
        }

    @abstractmethod
    def generate_candidate(
        self,
        record: RawMetadataRecord,
        schema: dict,
        instructions: str,
    ) -> dict:
        """Return a parsed dict candidate using safe JSON parsing only."""
