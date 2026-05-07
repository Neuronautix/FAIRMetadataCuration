from __future__ import annotations

import json
from pathlib import Path

from fair_metadata_curation.models import OntologyTerm
from fair_metadata_curation.ontology.base import OntologyResolver
from fair_metadata_curation.ontology.ols import OLSResolver


class LocalCacheResolver(OntologyResolver):
    def __init__(
        self,
        cache_path: str | Path,
        fallback_resolver: OntologyResolver | None = None,
    ) -> None:
        self.cache_path = Path(cache_path)
        if self.cache_path.exists():
            self.cache = json.loads(self.cache_path.read_text(encoding="utf-8"))
        else:
            self.cache = {}
        self.fallback_resolver = fallback_resolver or OLSResolver()

    def resolve(self, term: str, ontology: str) -> OntologyTerm:
        ontology_key = ontology.upper()
        term_key = term.strip().lower()
        cached = self.cache.get(ontology_key, {}).get(term_key)
        if cached is not None:
            return OntologyTerm.model_validate(cached)
        resolved = self.fallback_resolver.resolve(term, ontology_key)
        self.cache.setdefault(ontology_key, {})[term_key] = resolved.model_dump()
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(json.dumps(self.cache, indent=2), encoding="utf-8")
        return resolved
