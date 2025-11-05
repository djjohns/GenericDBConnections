import yaml
from typing import Any, Dict
from __future__ import annotations
from ..core import expand_env


def load_connections_yaml(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    data = expand_env(data)
    if not isinstance(data, dict):
        raise ValueError("Top-level YAML must be mapping of connection_id -> config")
    return data
