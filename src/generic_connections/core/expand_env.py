from __future__ import annotations
import os
import re
from typing import Any

_ENV_PAT = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")

def expand_env(value: Any) -> Any:
    if isinstance(value, str):
        return _ENV_PAT.sub(lambda m: os.environ.get(m.group(1), ""), value)
    if isinstance(value, dict):
        return {k: expand_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [expand_env(v) for v in value]
    return value
