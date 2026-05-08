import json
from pathlib import Path

from click.testing import CliRunner

from fair_metadata_curation.cli import main
from fair_metadata_curation.curation.pipeline import CurationPipeline
from fair_metadata_curation.llm.base import LLMOutputParseError
from fair_metadata_curation.llm.mock_provider import MockProvider
from fair_metadata_curation.ontology.local_cache import LocalCacheResolver

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "mock_llm_response.json"
CACHE_PATH = REPO_ROOT / "tests" / "fixtures" / "ontology_cache.json"


def _pipeline(overrides=None, max_attempts=3):
    return CurationPipeline(
        llm=MockProvider(FIXTURE_PATH, overrides=overrides),
        resolver=LocalCacheResolver(CACHE_PATH),
        config={
            "schema_path": REPO_ROOT / "src" / "fair_metadata_curation" / "schemas" / "biosample_cedar.schema.json",
            "max_remediation_attempts": max_attempts,
        },
    )


def test_full_pipeline_with_mock_provider_and_local_cache_passes():
    proposal = _pipeline().run({
        "geo_accession": "GSE1000",
        "gsm": "GSM1000",
        "Tissue": "liver",
        "organism": "Homo sapiens",
        "sex/gender": "female",
        "disease": "Alzheimer disease",
        "cell_type": "hepatocyte",
    })
    assert proposal.validation_report.passed is True
    assert proposal.proposed_record.tissue_term.id == "UBERON:0002107"


def test_malformed_llm_response_triggers_remediation():
    pipeline = _pipeline(overrides={"GSE1000": ['{"geo_accession": ', {
        "geo_accession": "GSE1000",
        "gsm_accession": "GSM1000",
        "organism": "Homo sapiens",
        "sex": "female",
        "tissue": "liver",
        "disease": "Alzheimer disease",
        "cell_type": "hepatocyte",
    }]})
    proposal = pipeline.run({"geo_accession": "GSE1000", "Tissue": "liver", "organism": "Homo sapiens", "sex": "female", "disease": "Alzheimer disease", "cell_type": "hepatocyte"})
    assert proposal.remediation_attempts == 1
    assert proposal.validation_report.passed is True


def test_unresolvable_ontology_term_marks_record_for_review():
    proposal = _pipeline().run({
        "geo_accession": "GSE2000",
        "gsm": "GSM2000",
        "Tissue": "cortex",
        "organism": "Homo sapiens",
        "sex": "unknown",
        "disease": "Alzheimer disease",
    })
    assert proposal.validation_report.passed is True
    assert proposal.validation_report.warnings
    assert any(field.validation_status == "unresolved" for field in proposal.field_proposals if field.proposed_key == "tissue")


def test_max_attempts_is_respected():
    pipeline = _pipeline(overrides={"GSE1000": [LLMOutputParseError("bad json"), LLMOutputParseError("bad json"), LLMOutputParseError("bad json")]}, max_attempts=2)
    proposal = pipeline.run({"geo_accession": "GSE1000"})
    assert proposal.remediation_attempts == 2
    assert proposal.validation_report.passed is False


def test_cli_runs_end_to_end(tmp_path, monkeypatch):
    input_path = tmp_path / "input.jsonl"
    input_path.write_text(json.dumps({
        "geo_accession": "GSE1000",
        "gsm": "GSM1000",
        "Tissue": "liver",
        "organism": "Homo sapiens",
        "sex/gender": "female",
        "disease": "Alzheimer disease",
        "cell_type": "hepatocyte",
    }) + "\n", encoding="utf-8")
    runner = CliRunner()
    monkeypatch.chdir(REPO_ROOT)
    result = runner.invoke(main, [str(input_path), "--out", str(tmp_path / "curated.jsonl"), "--report", str(tmp_path / "report.md"), "--jsonld", str(tmp_path / "curated.jsonld"), "--mock"])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "curated.jsonl").exists()
    assert (tmp_path / "report.md").exists()
    assert (tmp_path / "curated.jsonld").exists()
