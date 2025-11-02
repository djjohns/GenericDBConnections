from __future__ import annotations
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
