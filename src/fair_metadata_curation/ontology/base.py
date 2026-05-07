from __future__ import annotations

from abc import ABC, abstractmethod

from fair_metadata_curation.models import OntologyTerm

FIELD_ONTOLOGY_MAP = {
    "tissue": "UBERON",
    "disease": "MONDO",
    "cell_type": "CL",
    "organism": "NCBITAXON",
    "treatment": "CHEBI",
}


class OntologyResolver(ABC):
    @abstractmethod
    def resolve(self, term: str, ontology: str) -> OntologyTerm:
        raise NotImplementedError
