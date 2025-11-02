from __future__ import annotations
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
