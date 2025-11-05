from __future__ import annotations
import importlib
import sys
import time
import logging
from typing import Any, Dict, Iterable, Optional, Type
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, Connection
from sqlalchemy.exc import SQLAlchemyError
from .ConnectionConfig import ConnectionConfig
from .register_platform import PLATFORM_REGISTRY
from ..io import load_connections_yaml


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
            self._engine = create_engine(
                url, connect_args=self.connect_args(), **self.engine_options()
            )
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
                ok = res is not None
                LOG.info(
                    "Test result for %s: %s in %.2fs",
                    self.config.connection_id,
                    res,
                    time.time() - start,
                )
                return bool(ok)
        except SQLAlchemyError as e:
            LOG.error("Connection test failed for %s: %s", self.config.connection_id, e)
            return False

    @classmethod
    def from_yaml(cls, connection_id: str, yaml_path: str) -> "BaseConnection":
        from ..io.load_connections_yaml import load_connections_yaml
        from .ConnectionConfig import ConnectionConfig

        data = load_connections_yaml(yaml_path)
        if connection_id not in data:
            raise KeyError(f"connection_id '{connection_id}' not found in {yaml_path}")

        cfg = ConnectionConfig.from_dict(connection_id, data[connection_id])
        key = cfg.platform.lower().strip()

        kls = PLATFORM_REGISTRY.get(key)
        if not kls:
            # Lazy-load platform registrations
            try:
                importlib.import_module("generic_connections.platforms")
            except Exception:
                pass
            kls = PLATFORM_REGISTRY.get(key)

        if not kls:
            raise ValueError(f"Unsupported platform '{cfg.platform}' for {connection_id}")

        return kls(cfg)
