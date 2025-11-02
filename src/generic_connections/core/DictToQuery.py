from __future__ import annotations
from typing import Any, Dict
from urllib.parse import urlencode
import json

def dict_to_query(d: Dict[str, Any]) -> str:
    cleaned: Dict[str, Any] = {}
    for k, v in d.items():
        if isinstance(v, (str, int, float, bool)) or v is None:
            cleaned[k] = v
        else:
            cleaned[k] = json.dumps(v, separators=(",", ":"))
    return urlencode(cleaned, doseq=True)
