from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel


class ValidationError(BaseModel):
    layer: Literal["json_parse", "schema", "field_allowlist", "ontology", "semantic"]
    field: Optional[str] = None
    message: str
    severity: Literal["error", "warning"] = "error"
