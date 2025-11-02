from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ConnectionConfig:
    connection_id: str
    platform: str
    host: str
    user: Optional[str] = None
    password: Optional[str] = None
    schema: Optional[str] = None
    port: Optional[int] = None
    extra: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, connection_id: str, d: Dict[str, Any]) -> "ConnectionConfig":

        if not isinstance(d, dict):
            raise ValueError(f"Invalid config for {connection_id}")

        for req in ("platform", "host"):

            if req not in d:

                raise ValueError(f"Missing required '{req}' for {connection_id}")

        return cls(
            connection_id=connection_id,
            platform=str(d["platform"]),
            host=str(d["host"]),
            user=d.get("user"),
            password=d.get("password"),
            schema=d.get("schema"),
            port=d.get("port"),
            extra=d.get("extra") or {},
        )
