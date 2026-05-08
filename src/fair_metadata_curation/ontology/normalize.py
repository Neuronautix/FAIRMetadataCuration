from __future__ import annotations

from fair_metadata_curation.models import NormalizedMetadataRecord
from fair_metadata_curation.ontology.base import FIELD_ONTOLOGY_MAP, OntologyResolver


def ground_record(record: NormalizedMetadataRecord, resolver: OntologyResolver) -> NormalizedMetadataRecord:
    updates = {}
    for field_name, ontology in FIELD_ONTOLOGY_MAP.items():
        value = getattr(record, field_name)
        if value:
            updates[f"{field_name}_term"] = resolver.resolve(value, ontology)
    return record.model_copy(update=updates)
