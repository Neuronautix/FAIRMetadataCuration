# Migration Guide

## What the original notebook workflow did

The original notebooks used prompt text to ask an LLM to rewrite GEO/BioSample metadata into BioSample/CEDAR-like fields and ontology-like values. The baseline then parsed model output with `eval(...)`, which made the workflow unsafe and non-auditable.

## Why `eval()` was removed

`eval()` could execute arbitrary code if the model returned malicious or malformed content. The new package uses `json.loads()` only and treats parse failures as explicit validation failures that can trigger remediation or human review.

## Where the original logic moved

- notebook JSON/CSV helpers → `src/fair_metadata_curation/io.py`
- key and missing-value normalization → `src/fair_metadata_curation/preprocessing.py`
- schema contracts → `src/fair_metadata_curation/models.py` and `src/fair_metadata_curation/schemas/`
- prompt construction and structured LLM handling → `src/fair_metadata_curation/llm/`
- ontology grounding → `src/fair_metadata_curation/ontology/`
- validation layers → `src/fair_metadata_curation/validation/`
- remediation, provenance, and proposal assembly → `src/fair_metadata_curation/curation/`
- JSON/JSON-LD/report export → `src/fair_metadata_curation/export/`
- command-line entry point → `src/fair_metadata_curation/cli.py`

## New entry points

- Python API: `fair_metadata_curation.curation.pipeline.CurationPipeline`
- CLI: `fair-curate`
- Demo notebooks: `notebooks/01_original_prompt_baseline.ipynb`, `notebooks/02_validated_curation_pipeline.ipynb`

## Framing change

The project goal is not to make the LLM “FAIR.” The LLM only proposes candidate corrections. Deterministic validators, ontology resolvers, provenance tracking, validation reports, and optional human review decide whether those suggestions are accepted.
