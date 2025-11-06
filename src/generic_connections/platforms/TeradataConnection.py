from __future__ import annotations
from ..core.BaseConnection import BaseConnection
from ..core.dict_to_query import dict_to_query


class TeradataConnection(BaseConnection):
    TEST_QUERY = "SELECT 1"

    # Teradata URL-safe params (driver understands these as query-string args)
    _ALLOWED_QUERY_KEYS = {
        "logmech",
        "logdata",
        "encryptdata",
        "cop",
        "coplast",
        "charset",
        "dbs_port",
        "symkey",
        "tdr_enable",
        "tdr_log",
        # add more as you actually need & confirm in teradatasql docs
    }

    def build_url(self) -> str:
        x = self.config.extra or {}
        user = self.config.user or ""
        password = self.config.password or ""
        host = self.config.host or ""

        auth = f"{user}:{password}@" if (user or password) else ""
        base = f"teradatasql://{auth}{host}/"

        # Build query params from YAML, but only allow known keys
        q = {}
        extra_q = x.get("query") or {}
        if isinstance(extra_q, dict):
            for k, v in extra_q.items():
                key = k.lower() if isinstance(k, str) else k
                if key in self._ALLOWED_QUERY_KEYS:
                    if isinstance(v, bool):
                        q[key] = "true" if v else "false"
                    else:
                        q[key] = v
                # silently drop unknown keys (e.g., 'database', 'engine_options', etc.)

        # Defaults:
        q.setdefault("logmech", "LDAP")
        q.setdefault("encryptdata", "true")

        return base + ("?" + dict_to_query(q) if q else "")

    def connect_args(self):
        # Important: do NOT pass extra kwargs to the DBAPI for Teradata
        return {}
