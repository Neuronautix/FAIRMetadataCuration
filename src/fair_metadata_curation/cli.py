from __future__ import annotations

from pathlib import Path

import click

from fair_metadata_curation.curation.pipeline import CurationPipeline
from fair_metadata_curation.export.json_export import export_proposals
from fair_metadata_curation.export.jsonld_export import export_jsonld
from fair_metadata_curation.export.report import generate_markdown_report
from fair_metadata_curation.io import load_jsonl
from fair_metadata_curation.llm.mock_provider import MockProvider
from fair_metadata_curation.ontology.local_cache import LocalCacheResolver


@click.command()
@click.argument("input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--schema", "schema_name", default="biosample_cedar")
@click.option("--out", "out_path", required=True, type=click.Path(dir_okay=False, path_type=Path))
@click.option("--report", "report_path", type=click.Path(dir_okay=False, path_type=Path))
@click.option("--jsonld", "jsonld_path", type=click.Path(dir_okay=False, path_type=Path))
@click.option("--max-remediation-attempts", default=3, type=int)
@click.option("--require-ontology-grounding", is_flag=True, default=False)
@click.option("--mock", "use_mock", is_flag=True, default=False)
def main(
    input_path: Path,
    schema_name: str,
    out_path: Path,
    report_path: Path | None,
    jsonld_path: Path | None,
    max_remediation_attempts: int,
    require_ontology_grounding: bool,
    use_mock: bool,
) -> None:
    if not use_mock:
        raise click.ClickException("Only --mock mode is supported in the testable CLI baseline.")
    repo_root = Path.cwd()
    llm = MockProvider(repo_root / "tests" / "fixtures" / "mock_llm_response.json")
    resolver = LocalCacheResolver(repo_root / "tests" / "fixtures" / "ontology_cache.json")
    pipeline = CurationPipeline(
        llm=llm,
        resolver=resolver,
        config={
            "schema_path": repo_root / "src" / "fair_metadata_curation" / "schemas" / f"{schema_name}.schema.json",
            "max_remediation_attempts": max_remediation_attempts,
            "require_ontology_grounding": require_ontology_grounding,
        },
    )
    proposals = pipeline.run_batch(load_jsonl(input_path))
    export_proposals(proposals, str(out_path))
    if jsonld_path:
        export_jsonld(proposals, str(jsonld_path))
    if report_path:
        report_path.write_text(generate_markdown_report(proposals), encoding="utf-8")


if __name__ == "__main__":
    main()
