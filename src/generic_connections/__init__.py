# generic_connections/__init__.py
from .core.ConnectionConfig import ConnectionConfig
from .core.BaseConnection import BaseConnection
from .core.register_platform import PLATFORM_REGISTRY, register_platform
from .io.load_connections_yaml import load_connections_yaml

__all__ = [
    "ConnectionConfig",
    "BaseConnection",
    "PLATFORM_REGISTRY",
    "register_platform",
    "load_connections_yaml",
]
