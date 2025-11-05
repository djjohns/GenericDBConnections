# generic_connections/core/register_platform.py
from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Type

if TYPE_CHECKING:
    # Only imported when type-checking, never at runtime
    from .BaseConnection import BaseConnection

PLATFORM_REGISTRY: Dict[str, Type["BaseConnection"]] = {}


def register_platform(name: str, klass: Type["BaseConnection"]) -> None:
    PLATFORM_REGISTRY[name.strip().lower()] = klass
