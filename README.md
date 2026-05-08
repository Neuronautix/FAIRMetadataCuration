# FAIRMetadataCuration

Validation-first FAIR metadata curation toolkit for transforming raw GEO/BioSample-style metadata into auditable curation proposals.

> **Epistemic caution**
> LLM output is **proposal-only**. The model does not ensure FAIRness, enforce standards, or guarantee ontology compliance. It only proposes candidate corrections. Deterministic parsing, schema validation, ontology grounding, semantic validation, provenance capture, validation reports, and optional human review decide whether a proposal is accepted.

## Why the repository changed

The original notebooks used prompt-guided normalization and parsed model output with `eval(...)`. That is unsafe and scientifically weak for FAIR reuse because mentioning BioSample, CEDAR, or ontology terms in a prompt does **not** make output compliant. Compliance requires explicit machine-checkable contracts.

This repository now centers on a Python package that places LLM-generated candidates inside a reproducible validation pipeline.

## Architecture

```text
raw metadata
→ deterministic preprocessing
→ LLM candidate proposal
→ safe JSON parsing
→ JSON Schema / Pydantic validation
→ ontology grounding
→ semantic validation
→ remediation loop if needed
→ curation proposal with provenance
→ human-review-ready output
→ validated JSON / JSON-LD export
```

## Validation layers

1. **Safe parsing** — `json.loads()` only; no `eval()`, `exec()`, or unsafe deserialization.
2. **Schema validation** — JSON Schema and Pydantic models constrain accepted fields and value shapes.
3. **Field allowlist checks** — unknown keys are rejected unless preserved in `unmapped_fields`.
4. **Ontology grounding** — accepted grounded fields carry ontology IDs, labels, confidence, and match evidence.
5. **Semantic validation** — deterministic checks catch inconsistent values such as invalid `sex` labels.
6. **Provenance and review** — every accepted proposal is auditable, and ambiguous/unresolved cases remain visible.

## Package layout

```text
src/fair_metadata_curation/
├── models.py
├── preprocessing.py
├── io.py
├── llm/
├── ontology/
├── validation/
├── curation/
├── export/
└── cli.py
```

Schemas live in `src/fair_metadata_curation/schemas/` as JSON Schema, LinkML, and SHACL resources.

## Quickstart

```bash
python -m pip install -e '.[dev]'
python -m pytest
```

Run the mock-backed end-to-end pipeline:

```bash
fair-curate examples/input_records.jsonl \
  --schema biosample_cedar \
  --out examples/curated_output.jsonl \
  --report examples/validation_report.md \
  --jsonld examples/curated_output.jsonld \
  --max-remediation-attempts 3 \
  --mock
```

## CLI behavior

The CLI writes:

- normalized JSONL output
- JSON-LD output
- a markdown validation report
- an audit JSON next to the JSONL output

`--mock` uses deterministic fixtures so tests and examples do not require network calls.

## Notebook demos

- `notebooks/01_original_prompt_baseline.ipynb` preserves the original prompt-only baseline and starts with an explicit safety warning.
- `notebooks/02_validated_curation_pipeline.ipynb` demonstrates loading JSONL, running the package pipeline, inspecting proposals, and exporting outputs.

## Scientific rationale

FAIR metadata reuse depends on more than plausible text. A free-text label that resembles an ontology term is not enough. Accepted ontology-grounded fields should carry resolvable identifiers, preferred labels, match evidence, confidence, and provenance. Ambiguous or unresolved matches must remain flagged for review rather than being silently treated as valid.

Likewise, prompt-guided standardization is not schema validation. BioSample or CEDAR wording in a prompt can guide a proposal, but it cannot replace JSON Schema, Pydantic, LinkML, SHACL, controlled vocabularies, or machine-readable validation reports.

## Example report excerpt

See `examples/validation_report.md` for a generated example. The report summarizes valid %, schema-valid %, ontology-resolved %, and records that still require review.

## Migration notes

See [MIGRATION.md](MIGRATION.md) for how the original notebook logic maps into the package.

## Original project context

The original notebooks remain in the repository for reference and demo purposes, but core curation logic now lives in importable Python modules and tests.
