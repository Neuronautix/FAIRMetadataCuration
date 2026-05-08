from pathlib import Path

from fair_metadata_curation.models import NormalizedMetadataRecord
from fair_metadata_curation.ontology.local_cache import LocalCacheResolver
from fair_metadata_curation.ontology.normalize import ground_record

CACHE_PATH = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "ontology_cache.json"


class FailingResolver:
    def resolve(self, term, ontology):
        raise AssertionError("Network resolver should not be called for cached terms")


def test_local_cache_resolves_known_terms_without_network_calls(tmp_path):
    cache_copy = tmp_path / "ontology_cache.json"
    cache_copy.write_text(CACHE_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    resolver = LocalCacheResolver(cache_copy, fallback_resolver=FailingResolver())
    term = resolver.resolve("liver", "UBERON")
    assert term.id == "UBERON:0002107"
    assert term.match_type == "exact_label"


def test_unresolved_terms_get_unresolved_match_type(tmp_path):
    cache_copy = tmp_path / "ontology_cache.json"
    cache_copy.write_text(CACHE_PATH.read_text(encoding="utf-8"), encoding="utf-8")

    class UnresolvedResolver:
        def resolve(self, term, ontology):
            from fair_metadata_curation.models import OntologyTerm
            return OntologyTerm(id=term, label=term, ontology=ontology, match_type="unresolved", confidence=0.0)

    resolver = LocalCacheResolver(cache_copy, fallback_resolver=UnresolvedResolver())
    term = resolver.resolve("mystery tissue", "UBERON")
    assert term.match_type == "unresolved"


def test_ambiguous_terms_include_candidates(tmp_path):
    cache_copy = tmp_path / "ontology_cache.json"
    cache_copy.write_text(CACHE_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    resolver = LocalCacheResolver(cache_copy, fallback_resolver=FailingResolver())
    term = resolver.resolve("cortex", "UBERON")
    assert term.match_type == "ambiguous"
    assert term.candidates


def test_ground_record_populates_term_fields(tmp_path):
    cache_copy = tmp_path / "ontology_cache.json"
    cache_copy.write_text(CACHE_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    resolver = LocalCacheResolver(cache_copy, fallback_resolver=FailingResolver())
    record = NormalizedMetadataRecord(
        geo_accession="GSE1000",
        tissue="liver",
        organism="Homo sapiens",
        disease="Alzheimer disease",
        cell_type="hepatocyte",
    )
    grounded = ground_record(record, resolver)
    assert grounded.tissue_term.id == "UBERON:0002107"
    assert grounded.organism_term.id == "NCBITaxon:9606"
    assert grounded.disease_term.id == "MONDO:0004975"
    assert grounded.cell_type_term.id == "CL:0000182"
