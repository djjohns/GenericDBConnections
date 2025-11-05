from __future__ import annotations
from ..core import BaseConnection, dict_to_query


class TeradataConnection(BaseConnection):
    TEST_QUERY = "SELECT 1"

    def build_url(self) -> str:
        x = self.config.extra or {}
        user = self.config.user or ""
        password = self.config.password or ""
        host = self.config.host
        database = self.config.schema or ""
        auth = f"{user}:{password}" if (user or password) else ""
        logmech = "LDAP"
        base = (
            f"teradatasql://{auth}@{host}/?logmech={logmech}&encryptdata=true&database={database}"
        )
        q = {"database": database} if database else {}
        extra_q = x.get("query")
        if isinstance(extra_q, dict):
            q.update(extra_q)
        if q:
            return base + "?" + dict_to_query(q)
        return base
