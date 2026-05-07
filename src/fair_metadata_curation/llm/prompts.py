from __future__ import annotations

import hashlib
import json

from fair_metadata_curation.models import RawMetadataRecord


def build_curation_prompt(record: RawMetadataRecord, schema: dict, instructions: str) -> str:
    return (
        "You are a FAIR metadata curation assistant. Return only valid JSON matching the schema. "
        "Do not include markdown, prose, or comments.\n\n"
        f"Instructions:\n{instructions}\n\n"
        f"JSON Schema:\n{json.dumps(schema, indent=2, sort_keys=True)}\n\n"
        f"Input record:\n{json.dumps(record.model_dump(), indent=2, sort_keys=True)}"
    )


def hash_prompt(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()
