from pydantic import BaseModel
from typing import Dict, Any, List

class FieldEvidence(BaseModel):
    value: Any
    evidence: str = "NA"
    location: str = "NA"

def flatten_values(data: Dict[str, FieldEvidence], unknown_token: str = "NA") -> Dict[str, Any]:
    row = {}
    for k, fe in data.items():
        v = fe.value
        if isinstance(v, str) and v.strip().upper() == unknown_token:
            v = None
        row[k] = v
    return row

def expand_evidence(paper_id: str, data: Dict[str, FieldEvidence]) -> List[Dict[str, Any]]:
    rows = []
    for field, fe in data.items():
        rows.append({
            "paper_id": paper_id,
            "field": field,
            "value": fe.value,
            "quote": fe.evidence,
            "location": fe.location
        })
    return rows
