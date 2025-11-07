"""
Cargador de configuración personalizado.

Lee todas las variables de entorno necesarias y proporciona configuración mejorada
sin modificar el código core del servidor.
"""

import os
from typing import Optional
from dataclasses import dataclass

from ..types import ChromaClientConfig


@dataclass
class EnhancedClientConfig:
    """Configuración mejorada del cliente con todas las opciones de variables de entorno."""
    
    # Configuración base del cliente
    client_config: ChromaClientConfig
    
    # Configuración de embeddings
    embedding_function: str
    openai_model: Optional[str] = None
    openai_dimensions: Optional[int] = None
    
    # Configuración de distancia y metadata
    distance_metric: Optional[str] = None
    collection_metadata: Optional[str] = None
    
    # Configuración de aislamiento
    isolation_level: Optional[str] = None
    allow_reset: bool = True


def load_custom_config() -> EnhancedClientConfig:
    """
    Carga la configuración personalizada desde variables de entorno.
    
    Lee todas las variables de entorno definidas en .cursor/mcp.json y las
    convierte en una configuración estructurada.
    
    Returns:
        EnhancedClientConfig con toda la configuración cargada
    """
    # Cargar configuración base del cliente
    client_config = ChromaClientConfig(
        client_type=os.getenv("CHROMA_CLIENT_TYPE", "ephemeral"),
        data_dir=os.getenv("CHROMA_DATA_DIR"),
        host=os.getenv("CHROMA_HOST", "localhost"),
        port=os.getenv("CHROMA_PORT", "8000"),
        ssl=os.getenv("CHROMA_SSL", "false").lower() in ["true", "1", "yes"],
        tenant=os.getenv("CHROMA_TENANT", "default_tenant"),
        database=os.getenv("CHROMA_DATABASE", "default_database"),
        api_key=os.getenv("CHROMA_API_KEY"),
        embedding_function_name=os.getenv("CHROMA_EMBEDDING_FUNCTION", "default"),
        use_cpu_provider=None,  # Se maneja automáticamente
    )
    
    # Configuración de embeddings OpenAI
    openai_model = os.getenv("CHROMA_OPENAI_EMBEDDING_MODEL")
    openai_dimensions_str = os.getenv("CHROMA_OPENAI_EMBEDDING_DIMENSIONS")
    openai_dimensions = None
    if openai_dimensions_str:
        try:
            openai_dimensions = int(openai_dimensions_str)
        except ValueError:
            pass
    
    # Configuración de distancia y metadata
    distance_metric = os.getenv("CHROMA_DISTANCE_METRIC")
    collection_metadata = os.getenv("CHROMA_COLLECTION_METADATA")
    
    # Configuración de aislamiento
    isolation_level = os.getenv("CHROMA_ISOLATION_LEVEL")
    allow_reset = os.getenv("CHROMA_ALLOW_RESET", "true").lower() in ["true", "1", "yes"]
    
    return EnhancedClientConfig(
        client_config=client_config,
        embedding_function=client_config.embedding_function_name,
        openai_model=openai_model,
        openai_dimensions=openai_dimensions,
        distance_metric=distance_metric,
        collection_metadata=collection_metadata,
        isolation_level=isolation_level,
        allow_reset=allow_reset,
    )


def get_enhanced_client_config() -> ChromaClientConfig:
    """
    Obtiene la configuración del cliente mejorada desde variables de entorno.
    
    Esta función puede ser llamada desde el código core para obtener
    la configuración completa sin modificar el código base.
    
    Returns:
        ChromaClientConfig con toda la configuración cargada
    """
    enhanced_config = load_custom_config()
    return enhanced_config.client_config

