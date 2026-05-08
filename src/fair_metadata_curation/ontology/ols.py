from __future__ import annotations

from typing import Any

import requests

from fair_metadata_curation.models import OntologyTerm
from fair_metadata_curation.ontology.base import OntologyResolver


class OLSResolver(OntologyResolver):
    search_url = "https://www.ebi.ac.uk/ols4/api/search"

    def __init__(self, session: requests.Session | None = None, timeout: int = 10) -> None:
        self.session = session or requests.Session()
        self.timeout = timeout

    def resolve(self, term: str, ontology: str) -> OntologyTerm:
        if not term:
            return self._unresolved(term, ontology)
        try:
            response = self.session.get(
                self.search_url,
                params={"q": term, "ontology": ontology.lower(), "rows": 5},
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException:
            return self._unresolved(term, ontology)

        docs = payload.get("response", {}).get("docs", [])
        if not docs:
            return self._unresolved(term, ontology)

        best = docs[0]
        top_score = float(best.get("score", 1.0) or 1.0)
        candidates = [self._candidate(doc) for doc in docs[:5]]
        if len(docs) > 1:
            second_score = float(docs[1].get("score", 0.0) or 0.0)
            if top_score and abs(top_score - second_score) / top_score < 0.05:
                return OntologyTerm(
                    id=best.get("obo_id") or best.get("short_form") or term,
                    label=best.get("label") or term,
                    ontology=ontology,
                    iri=best.get("iri"),
                    match_type="ambiguous",
                    confidence=0.5,
                    candidates=candidates,
                )

        label = best.get("label") or term
        synonyms = [syn.lower() for syn in best.get("synonym", [])]
        match_type = "fuzzy"
        confidence = 0.8
        if label.lower() == term.lower():
            match_type = "exact_label"
            confidence = 1.0
        elif term.lower() in synonyms:
            match_type = "synonym"
            confidence = 0.9
        return OntologyTerm(
            id=best.get("obo_id") or best.get("short_form") or term,
            label=label,
            ontology=ontology,
            iri=best.get("iri"),
            match_type=match_type,
            confidence=confidence,
            candidates=candidates if match_type == "fuzzy" else None,
        )

    @staticmethod
    def _candidate(doc: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": doc.get("obo_id") or doc.get("short_form"),
            "label": doc.get("label"),
            "iri": doc.get("iri"),
            "score": doc.get("score"),
        }

    @staticmethod
    def _unresolved(term: str, ontology: str) -> OntologyTerm:
        return OntologyTerm(
            id=term or "UNRESOLVED",
            label=term or "",
            ontology=ontology,
            iri=None,
            match_type="unresolved",
            confidence=0.0,
            candidates=None,
        )
