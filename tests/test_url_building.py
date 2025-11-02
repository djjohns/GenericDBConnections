from generic_connections.core.ConnectionConfig import ConnectionConfig
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
