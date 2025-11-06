from __future__ import annotations
import importlib
import sys
import time
import logging
from typing import Any, Dict, Iterable, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, Connection
from sqlalchemy.exc import SQLAlchemyError
from urllib.parse import urlsplit, urlunsplit

from .ConnectionConfig import ConnectionConfig
from .register_platform import PLATFORM_REGISTRY


LOG = logging.getLogger("generic_connections")
if not LOG.handlers:
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
    LOG.addHandler(h)
LOG.setLevel(logging.INFO)


class BaseConnection:
    """Base class for all platform-specific SQLAlchemy connections."""

    TEST_QUERY: str = "SELECT 1"

    def __init__(self, config: ConnectionConfig):
        self.config = config
        self._engine: Optional[Engine] = None
        self._conn: Optional[Connection] = None

    # ------------------------------------------------------------------
    # Utility: safely mask password in URLs for logging
    # ------------------------------------------------------------------
    @staticmethod
    def _mask_url_password(url: str) -> str:
        """Return a copy of the URL with any password replaced by *** for safe logging."""
        try:
            parts = urlsplit(url)
            if "@" in parts.netloc and ":" in parts.netloc:
                userpass, host = parts.netloc.split("@", 1)
                if ":" in userpass:
                    user, _ = userpass.split(":", 1)
                    netloc = f"{user}:***@{host}"
                    return urlunsplit(
                        (parts.scheme, netloc, parts.path, parts.query, parts.fragment)
                    )
            return url
        except Exception:
            return url

    # ------------------------------------------------------------------
    # Abstracts to override
    # ------------------------------------------------------------------
    def build_url(self) -> str:  # pragma: no cover
        raise NotImplementedError

    def connect_args(self) -> Dict[str, Any]:
        """Platform-specific connect_args (defaults to none)."""
        return {}

    def engine_options(self) -> Dict[str, Any]:
        opts: Dict[str, Any] = {"pool_pre_ping": True}
        if isinstance(self.config.extra, dict):
            eo = self.config.extra.get("engine_options")
            if isinstance(eo, dict):
                opts.update(eo)
        return opts

    # ------------------------------------------------------------------
    # Engine + connection management
    # ------------------------------------------------------------------
    @property
    def engine(self) -> Engine:
        if self._engine is None:
            url = self.build_url()
            safe_url = self._mask_url_password(url)
            LOG.info("Creating engine for %s: %s", self.config.connection_id, safe_url)
            self._engine = create_engine(
                url,
                connect_args=self.connect_args(),
                **self.engine_options(),
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

    # ------------------------------------------------------------------
    # Connection testing
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------
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
            # Lazy-load platform registrations if not yet done
            try:
                importlib.import_module("generic_connections.platforms")
            except Exception:
                pass
            kls = PLATFORM_REGISTRY.get(key)

        if not kls:
            raise ValueError(f"Unsupported platform '{cfg.platform}' for {connection_id}")

        return kls(cfg)
