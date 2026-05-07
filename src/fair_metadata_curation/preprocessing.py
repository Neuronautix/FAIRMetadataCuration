from __future__ import annotations

from copy import deepcopy
from typing import Any

from .models import CANONICAL_FIELDS

_KEY_ALIASES = {
    "gse": "geo_accession",
    "geo accession": "geo_accession",
    "geo_accession": "geo_accession",
    "gsm": "gsm_accession",
    "gsm accession": "gsm_accession",
    "gsm_accession": "gsm_accession",
    "sample title": "title",
    "sample_title": "title",
    "organism name": "organism",
    "sex gender": "sex",
    "sex/gender": "sex",
    "gender": "sex",
    "tissue type": "tissue",
    "celltype": "cell_type",
    "cell line": "cell_line",
    "study design": "design",
    "diagnosis": "disease",
    "treatment compound": "treatment",
    "desc": "description",
}
_MISSING_VALUES = {"n/a", "na", "none", "unknown", "", "null"}


def _normalize_key(key: str) -> str:
    compact = " ".join(key.strip().lower().replace("/", " ").replace("-", " ").split())
    return _KEY_ALIASES.get(compact, compact.replace(" ", "_"))


def normalize_keys(record: dict) -> dict:
    normalized = {}
    for key, value in record.items():
        normalized[_normalize_key(str(key))] = value
    return normalized


def _normalize_value(value: Any) -> Any:
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.lower() in _MISSING_VALUES:
            return None
        return stripped
    if isinstance(value, list):
        return [_normalize_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _normalize_value(item) for key, item in value.items()}
    return value


def normalize_missing(record: dict) -> dict:
    return {key: _normalize_value(value) for key, value in deepcopy(record).items()}


def extract_canonical_fields(record: dict) -> tuple[dict, dict]:
    canonical = {}
    unmapped = {}
    allowed = set(CANONICAL_FIELDS)
    for key, value in record.items():
        if key in allowed:
            canonical[key] = value
        else:
            unmapped[key] = value
    return canonical, unmapped
