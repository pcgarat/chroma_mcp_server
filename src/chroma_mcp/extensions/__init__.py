"""
Extensiones personalizadas para chroma_mcp_server.

Este módulo contiene funcionalidad personalizada que se integra con el código base
sin modificar el código core, facilitando la actualización del fork con el repositorio original.
"""

from .database_manager import (
    ensure_database_exists,
    ensure_tenant_exists,
    verify_database_access,
)
from .config_loader import load_custom_config, get_enhanced_client_config

__all__ = [
    "ensure_database_exists",
    "ensure_tenant_exists",
    "verify_database_access",
    "load_custom_config",
    "get_enhanced_client_config",
]

