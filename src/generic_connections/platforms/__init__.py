from __future__ import annotations
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
