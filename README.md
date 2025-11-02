# generic-connections (DLT‑ready)

Granular SQLAlchemy connection wrappers driven by YAML. Context‑manager friendly, platform‑extensible, and ready to plug into [dlt](https://dlthub.com/) pipelines.

This README walks you through **local development setup** end‑to‑end.

---

## 0) Prerequisites

- **Python**: 3.9+ (3.11 recommended)
- **Build tools**: `pip` and `venv`
- **Optional DB drivers** (install only what you need):
  - Postgres: `psycopg2-binary`
  - MS SQL Server: `pyodbc` + a system ODBC driver (e.g., *ODBC Driver 18 for SQL Server*)
  - Teradata: `teradatasql` + `teradatasqlalchemy`
- **(Optional) dlt**: `dlt>=1.5` if you want to run the example pipeline

> **Note for MSSQL on Linux/macOS**: You may need to install Microsoft’s ODBC driver (`msodbcsql18`) and `unixodbc` via your package manager. On Windows, install the ODBC Driver 18 MSI.

---

## 1) Generate the project (one‑shot scaffold)

If you used the one‑file scaffolder I provided:

```bash
# In an empty directory (or one you're OK to populate)
python scaffold_generic_connections_dlt.py
```

This will create the package under `src/`, tests, GitHub Actions, an example `connections.example.yml`, and an example DLT pipeline at `examples/DltPipeline.py`.

> Re‑run with `--force` to overwrite existing files:

```bash
python scaffold_generic_connections_dlt.py --force
```

---

## 2) Create and activate a virtual environment

**bash/zsh (macOS/Linux):**
```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

**PowerShell (Windows):**
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

---

## 3) Install the package for development

Install the core dev tools (ruff/black/mypy/pytest), then add optional extras you plan to use.

```bash
pip install -e .[dev]
# Add DB drivers and dlt only if needed:
pip install .[postgres] .[mssql] .[teradata] .[dlt]
```

> You can always install extras later, e.g. `pip install .[mssql]` when you need it.

---

## 4) Configure connections

Copy the example YAML and edit it to match your environment:

```bash
cp connections.example.yml connections.yml
```

The YAML supports `${ENV}` expansion, so you can keep secrets out of the file.

**connections.yml (example):**
```yaml
pg_reporting:
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
```

> The top‑level keys (e.g., `pg_reporting`, `mssql_dw`) are your `connection_id`s.

Export the referenced environment variables in your shell:
```bash
export PG_REPORT_PASS=your_local_password
export MSSQL_PASS=...
export TD_HOST=...
export TD_USER=...
export TD_PASS=...
```

**PowerShell:**
```powershell
$env:PG_REPORT_PASS="your_local_password"
```

---

## 5) Smoke test the YAML and URL building

Run the unit tests:
```bash
pytest -q
```

This validates YAML env expansion and URL construction for supported platforms.

---

## 6) Test live connections (optional)

Use the bundled CLI to test one or more `connection_id`s in your YAML:

```bash
# Test everything
conn-tester connections.yml

# Or a subset
conn-tester connections.yml --only pg_reporting mssql_dw
```

The tester will create an engine, connect, optionally run any `extra.connect_init_sql` statements, then run a lightweight `SELECT 1` probe.

---

## 7) Run the DLT example (optional)

The example reads from a source DB using your YAML and loads the rows into a DLT destination.

1) Ensure you installed the extra:
```bash
pip install .[dlt]
```

2) Run the demo pipeline (defaults to DuckDB as the destination):
```bash
python examples/DltPipeline.py
```

- Edit `examples/DltPipeline.py` to point at your `connection_id` and SQL.
- Configure DLT destination via environment or `.dlt/` config (see DLT docs).

---

## 8) Use in your own code

```python
from sqlalchemy import text
from generic_connections.core.BaseConnection import BaseConnection

with BaseConnection.from_yaml("pg_reporting", "connections.yml") as conn:
    rows = conn.execute(text("SELECT 42")).all()
    print(rows)
```

- `BaseConnection` is a context manager, so engine and connection are disposed cleanly.
- Platform‑specific child classes live in `src/generic_connections/platforms/`.

---

## 9) Add a new platform (extending the package)

1) Create `src/generic_connections/platforms/MyDbConnection.py`:
```python
from __future__ import annotations
from ..core.BaseConnection import BaseConnection
from ..core.DictToQuery import dict_to_query

class MyDbConnection(BaseConnection):
    TEST_QUERY = "SELECT 1"

    def build_url(self) -> str:
        x = self.config.extra or {}
        # build an SQLAlchemy URL string with f-strings and config fields
        return f"mydb+driver://{self.config.user}:{self.config.password}@{self.config.host}/..."
```

2) Register it in `src/generic_connections/platforms/__init__.py`:
```python
from ..core.PlatformRegistry import register_platform
from .MyDbConnection import MyDbConnection
register_platform("mydb", MyDbConnection)
```

3) Reference it in YAML with `platform: MyDb` (matching the key you registered).

---

## 10) Troubleshooting

- **MSSQL ODBC driver not found**  
  Ensure a system ODBC driver is installed (e.g., *ODBC Driver 18 for SQL Server*). On Linux, install `msodbcsql18` + `unixodbc`. On macOS, consider `brew install msodbcsql18 unixodbc`. On Windows, install the official ODBC 18 MSI.

- **Trust/SSL issues for MSSQL**  
  Add to YAML under `extra.query`: `TrustServerCertificate: "yes"` (as shown in the example) for dev boxes without proper certs.

- **Teradata drivers**  
  Install `teradatasql` and `teradatasqlalchemy`. Some environments require additional native dependencies—check your platform’s docs.

- **Cannot import platform**  
  Make sure you registered your platform in `platforms/__init__.py` using `register_platform("key", Class)` and that your YAML `platform` matches the registered key (case‑insensitive).

- **URL building looks off**  
  Run `pytest -q` to quickly sanity‑check the URL builders in tests. Review your `extra.query`, `engine_options`, and `connect_args` sections.

---

## 11) (Optional) Continuous Integration

The repo contains two GitHub Actions:

- **CI (lint & tests)**: runs ruff, black, mypy, and pytest on push/PR.
- **Connection Tests**: opt‑in live connection checks. Set the repo/org secret `RUN_CONN_TESTS=true` and provide necessary DB secrets (e.g., `PG_REPORT_PASS`).

---

## 12) Project structure (key files)

```
src/generic_connections/
  core/
    BaseConnection.py
    ConnectionConfig.py
    DictToQuery.py
    ExpandEnv.py
    PlatformRegistry.py
  io/
    LoadConnectionsYaml.py
  platforms/
    __init__.py
    PostgresConnection.py
    MSSQLConnection.py
    TeradataConnection.py
cli/
  Tester.py
examples/
  DltPipeline.py
connections.example.yml
connections.yml           # your local copy (not committed)
```

---

## 13) Uninstall / clean up

```bash
pip uninstall generic-connections -y
deactivate  # exit venv
rm -rf .venv .pytest_cache .mypy_cache .ruff_cache
```

---

Happy building! If you want a `.env` loader (`python-dotenv`), a `Makefile` (`make lint/test/demo`), or pre‑commit hooks, I can add them to the scaffold as well.
