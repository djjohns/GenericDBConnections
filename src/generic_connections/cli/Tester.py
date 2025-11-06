from __future__ import annotations
import argparse
import logging
import sys
from typing import Iterable, Optional
from urllib.parse import urlsplit, urlunsplit

from ..core.BaseConnection import BaseConnection
from ..io.load_connections_yaml import load_connections_yaml

LOG = logging.getLogger("generic_connections.cli")
if not LOG.handlers:
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
    LOG.addHandler(h)
LOG.setLevel(logging.INFO)


def _mask_url_password(url: str) -> str:
    try:
        parts = urlsplit(url)
        if "@" in parts.netloc and ":" in parts.netloc:
            userpass, host = parts.netloc.split("@", 1)
            if ":" in userpass:
                user, _ = userpass.split(":", 1)
                netloc = f"{user}:***@{host}"
                return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))
        return url
    except Exception:
        return url


def test_all(yaml_path: str, only: Optional[Iterable[str]] = None, debug: bool = False) -> int:
    data = load_connections_yaml(yaml_path)
    failures = []
    selected = list(only) if only else list(data.keys())

    LOG.info("Discovered %d connections; testing %d", len(data), len(selected))
    for cid in selected:
        try:
            conn = BaseConnection.from_yaml(cid, yaml_path)
            if debug:
                # print resolved class + URL (masked)
                url = conn.build_url()
                LOG.info(
                    "CID=%s Class=%s URL=%s", cid, conn.__class__.__name__, _mask_url_password(url)
                )
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
    parser.add_argument(
        "--debug", action="store_true", help="Print resolved URL (password masked) & class"
    )
    args = parser.parse_args()
    sys.exit(test_all(args.yaml_path, args.only, args.debug))
