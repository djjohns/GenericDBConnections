from __future__ import annotations
from typing import Any, Dict
from ..core.BaseConnection import BaseConnection
from ..core.dict_to_query import dict_to_query


class MSSQLConnection(BaseConnection):
    TEST_QUERY = "SELECT 1"

    def build_url(self) -> str:
        x = self.config.extra or {}
        driver = x.get("odbc_driver", "ODBC Driver 18 for SQL Server")
        driver_q = driver.replace(" ", "+")
        user = self.config.user or ""
        password = self.config.password or ""
        host = self.config.host
        port = f":{self.config.port}" if self.config.port else ""
        dbname = self.config.schema or ""
        auth = f"{user}:{password}@" if (user or password) else ""
        base = f"mssql+pyodbc://{auth}{host}{port}/{dbname}?driver={driver_q}"
        q = x.get("query")
        if isinstance(q, dict) and q:
            return base + "&" + dict_to_query(q)
        return base

    def connect_args(self) -> Dict[str, Any]:
        ca: Dict[str, Any] = {}
        x = self.config.extra or {}
        if "connect_args" in x and isinstance(x["connect_args"], dict):
            ca.update(x["connect_args"])
        return ca
