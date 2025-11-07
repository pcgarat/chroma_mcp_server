"""
Gestor de base de datos personalizado.

Verifica y crea automáticamente la base de datos cuando se usa cliente HTTP,
sin modificar el código core del servidor.
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Intentar importar requests para verificación de base de datos
# Nota: requests no es una dependencia obligatoria, la verificación es opcional
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    # No loguear warning aquí para evitar spam, solo cuando se intente usar


def ensure_database_exists(
    host: str,
    port: int,
    tenant: str,
    database: str,
    api_key: Optional[str] = None,
    ssl: bool = False,
    verbose: bool = False,
) -> bool:
    """
    Verifica si la base de datos existe y la crea si no existe.
    
    Args:
        host: Host del servidor ChromaDB
        port: Puerto del servidor ChromaDB
        tenant: Tenant de ChromaDB
        database: Nombre de la base de datos
        api_key: API key opcional para autenticación
        ssl: Si se usa SSL
        verbose: Si se debe mostrar información detallada
        
    Returns:
        True si la base de datos existe o se creó exitosamente, False en caso contrario
    """
    if not REQUESTS_AVAILABLE:
        # requests no está disponible, la verificación es opcional
        # El código continuará normalmente sin verificación
        logger.debug("requests no está disponible. Omitiendo verificación automática de base de datos.")
        return False
    
    # Solo verificar si no es el tenant/database por defecto
    if tenant == "default_tenant" and database == "default_database":
        if verbose:
            logger.debug("Usando tenant/database por defecto, omitiendo verificación")
        return True
    
    protocol = "https" if ssl else "http"
    base_url = f"{protocol}://{host}:{port}"
    
    # Preparar headers
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    headers["Content-Type"] = "application/json"
    
    # Verificar si la base de datos existe
    check_url = f"{base_url}/api/v2/tenants/{tenant}/databases/{database}"
    
    try:
        if verbose:
            logger.info(f"Verificando base de datos '{database}' en tenant '{tenant}'...")
        
        response = requests.get(check_url, headers=headers, timeout=5)
        status_code = response.status_code
        
        if verbose:
            logger.debug(f"Código de respuesta: {status_code}")
        
        if status_code == 200:
            if verbose:
                logger.info(f"Base de datos '{database}' ya existe")
            return True
        elif status_code == 404:
            # La base de datos no existe, crearla
            if verbose:
                logger.info(f"Base de datos '{database}' no existe, creándola...")
            
            create_url = f"{base_url}/api/v2/tenants/{tenant}/databases"
            create_data = {"name": database}
            
            create_response = requests.post(
                create_url,
                headers=headers,
                json=create_data,
                timeout=5
            )
            
            create_status = create_response.status_code
            
            if create_status in (200, 201):
                if verbose:
                    logger.info(f"Base de datos '{database}' creada exitosamente")
                return True
            else:
                logger.warning(
                    f"No se pudo crear la base de datos '{database}' "
                    f"(código: {create_status}). Continuando..."
                )
                return False
        else:
            logger.warning(
                f"Error al verificar base de datos '{database}' "
                f"(código: {status_code}). Continuando..."
            )
            return False
            
    except requests.exceptions.RequestException as e:
        logger.warning(
            f"Error al verificar/crear base de datos '{database}': {e}. "
            "Continuando sin verificación..."
        )
        return False
    except Exception as e:
        logger.error(f"Error inesperado al verificar/crear base de datos: {e}", exc_info=True)
        return False


def verify_database_access(
    host: str,
    port: int,
    tenant: str,
    database: str,
    api_key: Optional[str] = None,
    ssl: bool = False,
) -> bool:
    """
    Verifica que se puede acceder a la base de datos.
    
    Args:
        host: Host del servidor ChromaDB
        port: Puerto del servidor ChromaDB
        tenant: Tenant de ChromaDB
        database: Nombre de la base de datos
        api_key: API key opcional para autenticación
        ssl: Si se usa SSL
        
    Returns:
        True si se puede acceder, False en caso contrario
    """
    if not REQUESTS_AVAILABLE:
        return False
    
    protocol = "https" if ssl else "http"
    base_url = f"{protocol}://{host}:{port}"
    
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    check_url = f"{base_url}/api/v2/tenants/{tenant}/databases/{database}"
    
    try:
        response = requests.get(check_url, headers=headers, timeout=5)
        return response.status_code == 200
    except Exception:
        return False

