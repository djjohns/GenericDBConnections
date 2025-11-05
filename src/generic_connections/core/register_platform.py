from __future__ import annotations
from typing import Dict, Type
from .BaseConnection import BaseConnection

PLATFORM_REGISTRY: Dict[str, Type[BaseConnection]] = {}


def register_platform(name: str, klass: Type[BaseConnection]) -> None:
    PLATFORM_REGISTRY[name.strip().lower()] = klass
