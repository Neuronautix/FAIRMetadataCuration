import json
from pathlib import Path

from fair_metadata_curation.preprocessing import extract_canonical_fields, normalize_keys, normalize_missing


def test_json_loads_parses_valid_json_correctly():
    assert json.loads('{"title": "example"}') == {"title": "example"}


def test_json_loads_raises_on_malformed_json():
    try:
        json.loads('{"title":')
    except json.JSONDecodeError:
        pass
    else:
        raise AssertionError("Malformed JSON should raise JSONDecodeError")


def test_eval_is_not_called_anywhere_in_src():
    repo_root = Path(__file__).resolve().parents[1]
    for path in (repo_root / "src").rglob("*.py"):
        assert "eval(" not in path.read_text(encoding="utf-8")


def test_preprocessing_helpers_normalize_and_split_fields():
    raw = {
        "Tissue": " liver ",
        "Sex/gender": "N/A",
        "gsm": "GSM1",
        "custom field": "value",
    }
    normalized = normalize_missing(normalize_keys(raw))
    canonical, unmapped = extract_canonical_fields(normalized)
    assert canonical == {"tissue": "liver", "sex": None, "gsm_accession": "GSM1"}
    assert unmapped == {"custom_field": "value"}
