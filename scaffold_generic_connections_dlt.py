#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Scaffold the 'generic_connections' package with granular modules, tests,
# CI workflows, an example connections.yml, and a DLT demo pipeline.
#
# Usage:
#     python scaffold_generic_connections_dlt.py [--force]
#
# By default, existing files are not overwritten. Use --force to overwrite.

from __future__ import annotations
import os
import sys
from typing import Dict

FORCE = "--force" in sys.argv

files: Dict[str, str] = {}

files["pyproject.toml"] = """[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "generic-connections"
version = "0.2.0"
description = "Granular SQLAlchemy connection wrappers driven by YAML (DLT-ready)"
readme = "README.md"
requires-python = ">=3.9"
license = { text = "MIT" }
authors = [{ name = "Your Team" }]
dependencies = [
  "SQLAlchemy>=2.0.0",
  "PyYAML>=6.0"
]

[project.optional-dependencies]
postgres = ["psycopg2-binary>=2.9; platform_system!='Windows'",
            "psycopg2-binary>=2.9; platform_system=='Windows'"]
mssql = ["pyodbc>=5.0.0"]
teradata = ["teradatasql", "teradatasqlalchemy"]
dlt = ["dlt>=1.5"]
dev = ["ruff>=0.6", "black>=24.3", "mypy>=1.10", "pytest>=8.0", "pytest-cov>=5.0"]

[project.scripts]
conn-tester = "generic_connections.cli.Tester:main"

[tool.ruff]
line-length = 100
target-version = "py39"

[tool.black]
line-length = 100
target-version = ["py39"]

[tool.mypy]
python_version = "3.9"
warn_unused_ignores = true
strict_optional = true
ignore_missing_imports = true

[tool.pytest.ini_options]
addopts = "-q"
pythonpath = ["src"]
"""
files["README.md"] = """# generic-connections

Granular SQLAlchemy connection wrappers driven by YAML. Context-manager friendly, platform-extensible, and DLT-ready.

## Install (dev)

```bash
python -m pip install --upgrade pip
pip install -e .[dev]
```

Optionally install DB drivers and DLT as needed:

```bash
pip install .[postgres] .[mssql] .[teradata] .[dlt]
```

## Configure

Create `connections.yml` (see `connections.example.yml`). You can reference env vars like `${PG_REPORT_PASS}`.

## Test all connections

```bash
export PG_REPORT_PASS=secret
conn-tester connections.example.yml
# or subset
conn-tester connections.example.yml --only pg_reporting
```

## Use in code

```python
from sqlalchemy import text
from generic_connections.core.BaseConnection import BaseConnection

with BaseConnection.from_yaml("pg_reporting", "connections.yml") as conn:
    rows = conn.execute(text("SELECT 1")).all()
```

## Use with dlt (data load tool)

```bash
pip install -e .[dev,dlt]
# Configure your dlt destination via env or .dlt/ per the dlt docs
python examples/DltPipeline.py
```

`examples/DltPipeline.py` shows how to:
1) open a source DB with `BaseConnection.from_yaml(...)`
2) stream rows as Python dicts
3) load to your dlt destination with `pipeline.run(...)`
"""

files["connections.example.yml"] = """pg_reporting:
  platform: Postgres
  host: localhost
  port: 5432
  user: report_user
  password: ${PG_REPORT_PASS}
  schema: reporting_db
  extra:
    driver: psycopg2
    query:
      application_name: conn_tester
    engine_options:
      pool_size: 5
      pool_recycle: 1800

mssql_dw:
  platform: MSSQL
  host: sqlhost.example.com
  port: 1433
  user: svc_reader
  password: ${MSSQL_PASS}
  schema: DataWarehouse
  extra:
    odbc_driver: "ODBC Driver 18 for SQL Server"
    query:
      TrustServerCertificate: "yes"
    connect_args:
      autocommit: true

td_analytics:
  platform: Teradata
  host: ${TD_HOST}
  user: ${TD_USER}
  password: ${TD_PASS}
  schema: DWH
  extra:
    query:
      LOGMECH: TD2
    engine_options:
      pool_size: 5
      max_overflow: 5
"""

files[".github/workflows/ci.yml"] = """name: CI (lint & tests)

on:
  push:
  pull_request:

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install deps
        run: |
          python -m pip install --upgrade pip
          pip install -e .[dev]
          pip install .[postgres] .[mssql] .[teradata] .[dlt] || true
      - name: Ruff
        run: ruff check .
      - name: Black
        run: black --check .
      - name: MyPy
        run: mypy src/generic_connections
      - name: PyTest
        run: pytest -q
"""

files[".github/workflows/connection-test.yml"] = """name: Connection Tests (optional)

on:
  push:
  workflow_dispatch:

env:
  RUN_CONN_TESTS: ${{ secrets.RUN_CONN_TESTS }}

jobs:
  conn-test:
    if: env.RUN_CONN_TESTS == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install package & drivers
        run: |
          python -m pip install --upgrade pip
          pip install -e .
          pip install .[postgres] .[mssql] .[teradata] .[dlt] || true
      - name: Export secrets -> env
        env:
          PG_REPORT_PASS: ${{ secrets.PG_REPORT_PASS }}
          MSSQL_PASS: ${{ secrets.MSSQL_PASS }}
          TD_HOST: ${{ secrets.TD_HOST }}
          TD_USER: ${{ secrets.TD_USER }}
          TD_PASS: ${{ secrets.TD_PASS }}
        run: |
          echo "Secrets exported (values hidden)."
      - name: Run conn-tester
        run: |
          conn-tester connections.example.yml || true
"""

files["src/generic_connections/__init__.py"] = """from .core.ConnectionConfig import ConnectionConfig
from .core.BaseConnection import BaseConnection
from .core.PlatformRegistry import PLATFORM_REGISTRY, register_platform
from .io.LoadConnectionsYaml import load_connections_yaml
from .platforms import PostgresConnection, MSSQLConnection, TeradataConnection

__all__ = [
    "ConnectionConfig",
    "BaseConnection",
    "PLATFORM_REGISTRY",
    "register_platform",
    "load_connections_yaml",
    "PostgresConnection",
    "MSSQLConnection",
    "TeradataConnection",
]
"""

files["src/generic_connections/core/ConnectionConfig.py"] = """from __future__ import annotations
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
"""

files["src/generic_connections/core/DictToQuery.py"] = """from __future__ import annotations
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
"""

files["src/generic_connections/core/ExpandEnv.py"] = """from __future__ import annotations
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
"""

files["src/generic_connections/core/PlatformRegistry.py"] = """from __future__ import annotations
from typing import Dict, Type
from .BaseConnection import BaseConnection

PLATFORM_REGISTRY: Dict[str, Type[BaseConnection]] = {}

def register_platform(name: str, klass: Type[BaseConnection]) -> None:
    PLATFORM_REGISTRY[name.strip().lower()] = klass
"""

files["src/generic_connections/core/BaseConnection.py"] = """from __future__ import annotations

import sys
import time
import logging
from typing import Any, Dict, Iterable, Optional, Type

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, Connection
from sqlalchemy.exc import SQLAlchemyError

from .ConnectionConfig import ConnectionConfig
from .PlatformRegistry import PLATFORM_REGISTRY

LOG = logging.getLogger("generic_connections")
if not LOG.handlers:
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
    LOG.addHandler(h)
LOG.setLevel(logging.INFO)

class BaseConnection:
    TEST_QUERY: str = "SELECT 1"

    def __init__(self, config: ConnectionConfig):
        self.config = config
        self._engine: Optional[Engine] = None
        self._conn: Optional[Connection] = None

    def build_url(self) -> str:  # pragma: no cover
        raise NotImplementedError

    def connect_args(self) -> Dict[str, Any]:
        return {}

    def engine_options(self) -> Dict[str, Any]:
        opts: Dict[str, Any] = {"pool_pre_ping": True}
        if isinstance(self.config.extra, dict):
            eo = self.config.extra.get("engine_options")
            if isinstance(eo, dict):
                opts.update(eo)
        return opts

    @property
    def engine(self) -> Engine:
        if self._engine is None:
            url = self.build_url()
            LOG.info("Creating engine for %s: %s", self.config.connection_id, url)
            self._engine = create_engine(url, connect_args=self.connect_args(), **self.engine_options())
        return self._engine

    def connect(self) -> Connection:
        if self._conn is None:
            self._conn = self.engine.connect()
        return self._conn

    def __enter__(self) -> Connection:
        return self.connect()

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            if self._conn is not None:
                self._conn.close()
        finally:
            self._conn = None
            if self._engine is not None:
                self._engine.dispose()
            self._engine = None

    def test_connection(self, timeout_seconds: int = 15) -> bool:
        start = time.time()
        LOG.info("Testing connection_id=%s", self.config.connection_id)
        try:
            with self as conn:
                init_sql: Optional[Iterable[str]] = None
                if isinstance(self.config.extra, dict):
                    cis = self.config.extra.get("connect_init_sql")
                    if isinstance(cis, (list, tuple)):
                        init_sql = cis
                if init_sql:
                    for sql in init_sql:
                        conn.execute(text(sql))
                res = conn.execute(text(self.TEST_QUERY)).scalar()
                ok = (res is not None)
                LOG.info("Test result for %s: %s in %.2fs", self.config.connection_id, res, time.time() - start)
                return bool(ok)
        except SQLAlchemyError as e:
            LOG.error("Connection test failed for %s: %s", self.config.connection_id, e)
            return False

    @classmethod
    def from_yaml(cls, connection_id: str, yaml_path: str) -> "BaseConnection":
        from ..io.LoadConnectionsYaml import load_connections_yaml
        from .ConnectionConfig import ConnectionConfig
        data = load_connections_yaml(yaml_path)
        if connection_id not in data:
            raise KeyError(f"connection_id '{connection_id}' not found in {yaml_path}")
        cfg = ConnectionConfig.from_dict(connection_id, data[connection_id])
        kls: Optional[Type[BaseConnection]] = PLATFORM_REGISTRY.get(cfg.platform.lower().strip())
        if not kls:
            raise ValueError(f"Unsupported platform '{cfg.platform}' for {connection_id}")
        return kls(cfg)
"""

files["src/generic_connections/io/LoadConnectionsYaml.py"] = """from __future__ import annotations
from typing import Any, Dict
import yaml
from ..core.ExpandEnv import expand_env

def load_connections_yaml(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    data = expand_env(data)
    if not isinstance(data, dict):
        raise ValueError("Top-level YAML must be mapping of connection_id -> config")
    return data
"""

files["src/generic_connections/platforms/__init__.py"] = """from __future__ import annotations
from ..core.PlatformRegistry import register_platform, PLATFORM_REGISTRY
from .PostgresConnection import PostgresConnection
from .MSSQLConnection import MSSQLConnection
from .TeradataConnection import TeradataConnection

register_platform("postgres", PostgresConnection)
register_platform("postgresql", PostgresConnection)
register_platform("pg", PostgresConnection)
register_platform("mssql", MSSQLConnection)
register_platform("sqlserver", MSSQLConnection)
register_platform("ms sql", MSSQLConnection)
register_platform("teradata", TeradataConnection)

__all__ = ["PostgresConnection", "MSSQLConnection", "TeradataConnection", "PLATFORM_REGISTRY"]
"""

files["src/generic_connections/platforms/PostgresConnection.py"] = """from __future__ import annotations
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
"""

files["src/generic_connections/platforms/MSSQLConnection.py"] = """from __future__ import annotations
from typing import Any, Dict
from ..core.BaseConnection import BaseConnection
from ..core.DictToQuery import dict_to_query

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
"""

files["src/generic_connections/platforms/TeradataConnection.py"] = """from __future__ import annotations
from ..core.BaseConnection import BaseConnection
from ..core.DictToQuery import dict_to_query

class TeradataConnection(BaseConnection):
    TEST_QUERY = "SELECT 1"

    def build_url(self) -> str:
        x = self.config.extra or {}
        user = self.config.user or ""
        password = self.config.password or ""
        host = self.config.host
        database = self.config.schema or ""
        auth = f"{user}:{password}@" if (user or password) else ""
        base = f"teradatasql://{auth}{host}/"
        q = {"database": database} if database else {}
        extra_q = x.get("query")
        if isinstance(extra_q, dict):
            q.update(extra_q)
        if q:
            return base + "?" + dict_to_query(q)
        return base
"""

files["src/generic_connections/cli/Tester.py"] = """from __future__ import annotations
import argparse
import logging
import sys
from typing import Iterable, Optional

from ..core.BaseConnection import BaseConnection
from ..io.LoadConnectionsYaml import load_connections_yaml

LOG = logging.getLogger("generic_connections.cli")
if not LOG.handlers:
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
    LOG.addHandler(h)
LOG.setLevel(logging.INFO)

def test_all(yaml_path: str, only: Optional[Iterable[str]] = None) -> int:
    data = load_connections_yaml(yaml_path)
    failures = []
    selected = list(only) if only else list(data.keys())

    LOG.info("Discovered %d connections; testing %d", len(data), len(selected))
    for cid in selected:
        try:
            conn = BaseConnection.from_yaml(cid, yaml_path)
            if not conn.test_connection():
                failures.append(cid)
        except Exception as e:
            LOG.error("Error for %s: %s", cid, e)
            failures.append(cid)
    if failures:
        LOG.error("Failed: %s", failures)
        return 1
    LOG.info("All tested connections OK")
    return 0

def main() -> None:
    parser = argparse.ArgumentParser(description="Test DB connections from YAML")
    parser.add_argument("yaml_path", help="Path to connections YAML")
    parser.add_argument("--only", nargs="*", help="Specific connection_ids to test")
    args = parser.parse_args()
    sys.exit(test_all(args.yaml_path, args.only))
"""

files["examples/DltPipeline.py"] = """from __future__ import annotations
import dlt
from sqlalchemy import text
from generic_connections.core.BaseConnection import BaseConnection

def fetch_rows(yaml_path: str, connection_id: str, sql: str, fetch_size: int = 5000):
    with BaseConnection.from_yaml(connection_id, yaml_path) as conn:
        result = conn.execution_options(stream_results=True).execute(text(sql))
        cols = list(result.keys())
        while True:
            chunk = result.fetchmany(fetch_size)
            if not chunk:
                break
            for row in chunk:
                yield dict(zip(cols, row))

def run_pipeline():
    pipeline = dlt.pipeline(
        pipeline_name="generic_connections_demo",
        destination="duckdb",
        dataset_name="demo",
    )
    rows = fetch_rows(
        yaml_path="connections.example.yml",
        connection_id="pg_reporting",
        sql="SELECT 1 AS id, 'hello'::text AS msg",
    )
    load_info = pipeline.run(rows, table_name="hello_world")
    print(load_info)

if __name__ == "__main__":
    run_pipeline()
"""

files["tests/__init__.py"] = """"""

files["tests/test_yaml_parsing.py"] = """from generic_connections.io.LoadConnectionsYaml import load_connections_yaml

def test_load_yaml_env_expansion(tmp_path, monkeypatch):
    y = tmp_path/"c.yml"
    y.write_text("a:\n  platform: Postgres\n  host: ${H}\n")
    monkeypatch.setenv("H", "db.local")
    data = load_connections_yaml(str(y))
    assert data["a"]["host"] == "db.local"
"""

files["tests/test_url_building.py"] = """from generic_connections.core.ConnectionConfig import ConnectionConfig
from generic_connections.platforms.PostgresConnection import PostgresConnection
from generic_connections.platforms.MSSQLConnection import MSSQLConnection
from generic_connections.platforms.TeradataConnection import TeradataConnection

def test_pg_url():
    cfg = ConnectionConfig(
        connection_id="pg",
        platform="Postgres",
        host="h",
        user="u", password="p",
        schema="db", port=5432,
        extra={"driver":"psycopg2","query":{"application_name":"t"}}
    )
    assert "postgresql+psycopg2://u:p@h:5432/db?application_name=t" == PostgresConnection(cfg).build_url()

def test_mssql_url():
    cfg = ConnectionConfig(
        connection_id="m",
        platform="MSSQL",
        host="h",
        user="u", password="p",
        schema="db", port=1433,
        extra={"odbc_driver":"ODBC Driver 18 for SQL Server",
               "query":{"TrustServerCertificate":"yes"}}
    )
    url = MSSQLConnection(cfg).build_url()
    assert url.startswith("mssql+pyodbc://u:p@h:1433/db?driver=ODBC+Driver+18+for+SQL+Server")
    assert "TrustServerCertificate=yes" in url

def test_td_url():
    cfg = ConnectionConfig(
        connection_id="t",
        platform="Teradata",
        host="h",
        user="u", password="p",
        schema="DWH",
        extra={"query":{"LOGMECH":"TD2"}}
    )
    url = TeradataConnection(cfg).build_url()
    assert url.startswith("teradatasql://u:p@h/?")
    assert "database=DWH" in url and "LOGMECH=TD2" in url
"""

def write_file(path: str, content: str) -> None:
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)
    if os.path.exists(path) and "--force" not in sys.argv:
        print(f"SKIP (exists): {path}")
        return
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"WROTE: {path}")

def main() -> None:
    for path, content in files.items():
        write_file(path, content)

    print("\nDone. Next steps:")
    print("  1) python -m pip install --upgrade pip")
    print("  2) pip install -e .[dev,dlt]")
    print("  3) pytest -q")
    print("  4) conn-tester connections.example.yml --only pg_reporting")
    print("  5) python examples/DltPipeline.py  # demo dlt load into DuckDB")
    print("\nOptional: push to GitHub; CI will run lint and tests on push/PR.")

if __name__ == "__main__":
    main()
