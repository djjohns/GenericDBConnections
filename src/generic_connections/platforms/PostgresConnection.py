from __future__ import annotations
from ..core.BaseConnection import BaseConnection
from ..core.DictToQuery import dict_to_query

class PostgresConnection(BaseConnection):
    TEST_QUERY = "SELECT 1"

    def build_url(self) -> str:
        x = self.config.extra or {}
        driver = x.get("driver", "psycopg2")
        user = self.config.user or ""
        password = self.config.password or ""
        host = self.config.host
        port = self.config.port or 5432
        dbname = self.config.schema or ""
        auth = f"{user}:{password}@" if (user or password) else ""
        base = f"postgresql+{driver}://{auth}{host}:{port}/{dbname}"
        q = x.get("query")
        if isinstance(q, dict) and q:
            return base + "?" + dict_to_query(q)
        return base
