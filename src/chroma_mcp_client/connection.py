"""
Handles direct connection to ChromaDB based on .env configuration.
Reuses configuration loading and client creation logic from the server's utils.
"""

import sys
import os
import chromadb
from pathlib import Path
from typing import Tuple, Optional, Dict
from chromadb import EmbeddingFunction
from functools import lru_cache

from chroma_mcp.utils.chroma_client import get_chroma_client, get_embedding_function
from chroma_mcp.types import ChromaClientConfig

# Default collection name used by the client
DEFAULT_COLLECTION_NAME = "codebase_v1"


def find_project_root(marker=".git"):
    """Find the project root by searching upwards for a marker file/directory."""
    path = Path(os.getcwd()).resolve()
    while path != path.parent:
        if (path / marker).exists():
            return path
        path = path.parent
    # If marker not found, fallback or raise error
    # Fallback to current dir might be risky, let's default to raising error
    # or returning None and handling it in the caller
    # For now, let's return current dir as a last resort but log a warning
    print(f"Warning: Could not find project root marker '{marker}'. Using CWD as fallback.", file=sys.stderr)
    return Path(os.getcwd()).resolve()


def _get_env_config() -> Dict[str, Optional[str]]:
    """
    Lee todas las variables de entorno relevantes para la configuración de ChromaDB.
    Esto asegura que el caché funcione correctamente para proyectos concurrentes.
    """
    return {
        "tenant": os.getenv("CHROMA_TENANT"),
        "database": os.getenv("CHROMA_DATABASE"),
        "host": os.getenv("CHROMA_HOST"),
        "port": os.getenv("CHROMA_PORT"),
        "client_type": os.getenv("CHROMA_CLIENT_TYPE"),
        "ssl": os.getenv("CHROMA_SSL"),
        "api_key": os.getenv("CHROMA_API_KEY"),
        "data_dir": os.getenv("CHROMA_DATA_DIR"),
        "embedding_function": os.getenv("CHROMA_EMBEDDING_FUNCTION"),
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
    }


def get_client_and_ef_from_env(
    env_path: Optional[str] = None,
    **overrides
) -> Tuple[chromadb.ClientAPI, Optional[chromadb.EmbeddingFunction]]:
    """
    Wrapper conveniente que lee todas las variables de entorno y las pasa a get_client_and_ef.
    Permite pasar overrides para parámetros específicos.
    
    Args:
        env_path: Optional explicit path to a .env file (overrides root search).
        **overrides: Parámetros que sobrescriben las variables de entorno.
    
    Returns:
        Tuple[chromadb.ClientAPI, Optional[chromadb.EmbeddingFunction]]
    """
    env_config = _get_env_config()
    
    # Aplicar overrides
    for key, value in overrides.items():
        if value is not None:
            env_config[key] = value
    
    # Convertir SSL de string a bool si es necesario
    ssl = env_config.get("ssl")
    if isinstance(ssl, str):
        ssl = ssl.lower() in ["true", "1", "yes"]
    elif ssl is None:
        ssl = None
    
    return get_client_and_ef(
        env_path=env_path,
        tenant=env_config.get("tenant"),
        database=env_config.get("database"),
        host=env_config.get("host"),
        port=env_config.get("port"),
        client_type=env_config.get("client_type"),
        ssl=ssl,
        api_key=env_config.get("api_key"),
        data_dir=env_config.get("data_dir"),
        embedding_function=env_config.get("embedding_function"),
        openai_api_key=env_config.get("openai_api_key"),
    )


# Use lru_cache to ensure client/EF are initialized only once per configuration
# Cache key includes env_path and critical env vars (tenant, database) to support multiple projects
@lru_cache(maxsize=20)  # Increased maxsize to support multiple concurrent projects with different configs
def get_client_and_ef(
    env_path: Optional[str] = None,
    tenant: Optional[str] = None,
    database: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[str] = None,
    client_type: Optional[str] = None,
    ssl: Optional[bool] = None,
    api_key: Optional[str] = None,
    data_dir: Optional[str] = None,
    embedding_function: Optional[str] = None,
    openai_api_key: Optional[str] = None,
) -> Tuple[chromadb.ClientAPI, Optional[chromadb.EmbeddingFunction]]:
    """Initializes and returns a cached tuple of ChromaDB client and embedding function.

    Reads configuration from environment variables or a .env file located at the project root.
    Ensures single initialization per configuration using lru_cache.
    
    The cache key includes tenant and database to support multiple concurrent projects
    with different configurations.

    Args:
        env_path: Optional explicit path to a .env file (overrides root search).
        tenant: Optional tenant override (if None, reads from CHROMA_TENANT env var).
        database: Optional database override (if None, reads from CHROMA_DATABASE env var).
        host: Optional host override (if None, reads from CHROMA_HOST env var).
        port: Optional port override (if None, reads from CHROMA_PORT env var).
        client_type: Optional client type override (if None, reads from CHROMA_CLIENT_TYPE env var).
        ssl: Optional SSL override (if None, reads from CHROMA_SSL env var).
        api_key: Optional API key override (if None, reads from CHROMA_API_KEY env var).
        data_dir: Optional data directory override (if None, reads from CHROMA_DATA_DIR env var).
        embedding_function: Optional embedding function name override (if None, reads from CHROMA_EMBEDDING_FUNCTION env var).
        openai_api_key: Optional OpenAI API key override (if None, reads from OPENAI_API_KEY env var).

    Returns:
        Tuple[chromadb.ClientAPI, Optional[chromadb.EmbeddingFunction]]

    Raises:
        Exception: If configuration loading or client/EF initialization fails.
    """
    print(f"Initializing ChromaDB connection and embedding function (env_path={env_path}, tenant={tenant}, database={database})...", file=sys.stderr)

    # Determine the base directory for resolving paths and loading .env
    if env_path:
        dotenv_path = Path(env_path).resolve()
        base_dir = dotenv_path.parent
        print(f"Using explicit env_path: {dotenv_path}", file=sys.stderr)
    else:
        base_dir = find_project_root()  # Find root based on .git marker
        dotenv_path = base_dir / ".env"
        print(f"Project root identified as: {base_dir}", file=sys.stderr)

    # Load .env from the determined path
    # from dotenv import load_dotenv # Import moved inside conditional
    if dotenv_path.exists():
        from dotenv import load_dotenv

        print(f"Loading .env file from: {dotenv_path}", file=sys.stderr)
        load_dotenv(dotenv_path=dotenv_path, override=True)
    else:
        print(f"Warning: .env file not found at {dotenv_path}. Using environment variables.", file=sys.stderr)

    # Resolve relative data path if persistent client is used
    # Use parameter override or fall back to environment variable
    client_type_val = client_type if client_type is not None else os.getenv("CHROMA_CLIENT_TYPE", "persistent")
    data_dir_env = data_dir if data_dir is not None else os.getenv("CHROMA_DATA_DIR", "./chroma_data")
    resolved_data_dir = data_dir_env
    if client_type_val == "persistent" and data_dir_env:
        data_path = Path(data_dir_env)
        if not data_path.is_absolute():
            # Resolve relative to the base_dir (either env_path parent or project root)
            resolved_data_dir = str(base_dir / data_path)
            print(f"Resolved relative CHROMA_DATA_DIR to: {resolved_data_dir}", file=sys.stderr)

    # 2. Construct ChromaClientConfig directly from parameters or environment variables
    #    Use provided overrides or fall back to environment variables
    #    Ensure all necessary fields expected by ChromaClientConfig are mapped.
    # Determine SSL value
    if ssl is not None:
        ssl_val = ssl
    else:
        ssl_env = os.getenv("CHROMA_SSL", "false")
        ssl_val = ssl_env.lower() in ["true", "1", "yes"]
    
    client_config = ChromaClientConfig(
        client_type=client_type_val,
        data_dir=resolved_data_dir,  # Use the resolved path
        host=host if host is not None else os.getenv("CHROMA_HOST", "localhost"),
        port=port if port is not None else os.getenv("CHROMA_PORT", "8000"),  # Keep as string (or None)
        ssl=ssl_val,
        tenant=tenant if tenant is not None else os.getenv("CHROMA_TENANT", chromadb.DEFAULT_TENANT),
        database=database if database is not None else os.getenv("CHROMA_DATABASE", chromadb.DEFAULT_DATABASE),
        api_key=api_key if api_key is not None else os.getenv("CHROMA_API_KEY"),  # Add API key for HTTP client authentication
        # embedding_function_name is NOT part of client connection config
        # Add any other required fields from ServerConfig here
    )
    print(
        f"Client Config from Env - Type: {client_config.client_type}, Host: {client_config.host}, Port: {client_config.port}, Path: {client_config.data_dir}",
        file=sys.stderr,
    )

    # 3. Ensure tenant and database exist before creating client (for HTTP clients)
    #    This prevents "Tenant not found" errors
    if client_config.client_type == "http":
        try:
            from chroma_mcp.extensions.database_manager import ensure_database_exists
            verbose = os.getenv("LOG_LEVEL", "INFO").upper() == "DEBUG"
            ensure_database_exists(
                host=client_config.host,
                port=int(client_config.port) if isinstance(client_config.port, str) else client_config.port,
                tenant=client_config.tenant,
                database=client_config.database,
                api_key=client_config.api_key,
                ssl=client_config.ssl,
                verbose=verbose,
            )
        except ImportError:
            # Si las extensiones no están disponibles, continuar sin verificación
            print("Extensiones personalizadas no disponibles, omitiendo verificación de tenant/database", file=sys.stderr)
        except Exception as ext_error:
            # No fallar si la extensión tiene problemas, solo loguear
            print(f"Error en extensión de verificación de tenant/database: {ext_error}", file=sys.stderr)
    
    # 4. Get the ChromaDB client using the constructed client_config
    #    get_chroma_client handles the actual client creation logic
    print(f"Getting ChromaDB client (Type: {client_config.client_type})...", file=sys.stderr)
    # Pass the explicitly constructed config
    try:
        client: chromadb.ClientAPI = get_chroma_client(config=client_config)
    except Exception as client_error:
        error_msg = f"Error al crear el cliente de ChromaDB: {client_error}"
        print(f"ERROR: {error_msg}", file=sys.stderr)
        import traceback
        print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
        # Re-raise with more context
        raise RuntimeError(error_msg) from client_error

    # 5. Get the embedding function name from parameter or environment
    #    (EF name is often part of the general config, not client-specific connection)
    ef_name = embedding_function if embedding_function is not None else os.getenv("CHROMA_EMBEDDING_FUNCTION", "default")
    print(f"Getting Embedding Function ('{ef_name}')...", file=sys.stderr)
    
    # Debug: Check if API key is available for OpenAI
    if ef_name.lower() == "openai":
        openai_key = openai_api_key if openai_api_key is not None else os.getenv("OPENAI_API_KEY")
        openai_model = os.getenv("CHROMA_OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        openai_dimensions = os.getenv("CHROMA_OPENAI_EMBEDDING_DIMENSIONS", "1536")
        
        print(f"DEBUG: OpenAI configuration BEFORE instantiation:", file=sys.stderr)
        print(f"  - Model: {openai_model}", file=sys.stderr)
        print(f"  - Dimensions: {openai_dimensions}", file=sys.stderr)
        print(f"  - API Key: {'SET' if openai_key else 'NOT SET'} (length: {len(openai_key) if openai_key else 0})", file=sys.stderr)
        print(f"  - CHROMA_OPENAI_EMBEDDING_MODEL env: {os.getenv('CHROMA_OPENAI_EMBEDDING_MODEL', 'NOT SET')}", file=sys.stderr)
        print(f"  - CHROMA_OPENAI_EMBEDDING_DIMENSIONS env: {os.getenv('CHROMA_OPENAI_EMBEDDING_DIMENSIONS', 'NOT SET')}", file=sys.stderr)
        
        if not openai_key:
            error_msg = "OPENAI_API_KEY not found in parameters or environment variables. Please set it in your .env file or pass it as parameter."
            print(f"ERROR: {error_msg}", file=sys.stderr)
            raise RuntimeError(error_msg)
        # Temporarily set OPENAI_API_KEY in environment for get_embedding_function
        if openai_api_key is not None:
            os.environ["OPENAI_API_KEY"] = openai_api_key
    
    try:
        embedding_function: Optional[chromadb.EmbeddingFunction] = get_embedding_function(ef_name)
        
        # For OpenAI, verify dimensions after instantiation
        if ef_name.lower() == "openai":
            try:
                # OpenAIEmbeddingFunction uses __call__ method, not embed_documents
                # Try different methods to get embeddings
                if hasattr(embedding_function, '__call__'):
                    test_embedding = embedding_function(["test"])
                    if isinstance(test_embedding, list) and len(test_embedding) > 0:
                        actual_dimensions = len(test_embedding[0])
                    else:
                        actual_dimensions = len(test_embedding) if isinstance(test_embedding, (list, tuple)) else 0
                elif hasattr(embedding_function, 'embed_documents'):
                    test_embedding = embedding_function.embed_documents(["test"])[0]
                    actual_dimensions = len(test_embedding)
                else:
                    # If we can't verify, just log the expected dimensions
                    actual_dimensions = None
                    print(f"DEBUG: OpenAI embedding dimensions AFTER instantiation:", file=sys.stderr)
                    print(f"  - Expected: {int(os.getenv('CHROMA_OPENAI_EMBEDDING_DIMENSIONS', '1536'))}", file=sys.stderr)
                    print(f"  - Actual: Could not verify (embedding function method not found)", file=sys.stderr)
                    print(f"SUCCESS: OpenAI embedding function instantiated (dimensions verification skipped)", file=sys.stderr)
                    return client, embedding_function
                
                expected_dimensions = int(os.getenv("CHROMA_OPENAI_EMBEDDING_DIMENSIONS", "1536"))
                print(f"DEBUG: OpenAI embedding dimensions AFTER instantiation:", file=sys.stderr)
                print(f"  - Expected: {expected_dimensions}", file=sys.stderr)
                print(f"  - Actual: {actual_dimensions}", file=sys.stderr)
                if actual_dimensions != expected_dimensions:
                    print(f"WARNING: OpenAI embedding dimensions mismatch! Expected: {expected_dimensions}, Got: {actual_dimensions}", file=sys.stderr)
                else:
                    print(f"SUCCESS: OpenAI embedding dimensions match ({actual_dimensions})", file=sys.stderr)
            except Exception as dim_check_error:
                print(f"WARNING: Could not verify embedding dimensions: {dim_check_error}", file=sys.stderr)
                print(f"INFO: OpenAI embedding function instantiated (dimension verification failed, but function is available)", file=sys.stderr)
    except Exception as e:
        error_msg = f"Error getting embedding function ('{ef_name}'): {e}"
        print(f"ERROR: {error_msg}", file=sys.stderr)
        import traceback
        print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
        # Re-raise with more context
        raise RuntimeError(error_msg) from e

    print("Client and EF initialization complete.", file=sys.stderr)
    return client, embedding_function


class ChromaMcpClient:
    """Encapsulates a ChromaDB client and its embedding function."""

    def __init__(self, env_path: Optional[str] = None):
        """Initialize the client, fetching or creating the connection."""
        # Read all config from environment to ensure correct cache key
        self.client, self.embedding_function = get_client_and_ef_from_env(
            env_path=env_path
        )

    def get_client(self) -> chromadb.ClientAPI:
        """Return the underlying ChromaDB client."""
        return self.client

    def get_embedding_function(self) -> Optional[chromadb.EmbeddingFunction]:
        """Return the configured embedding function."""
        return self.embedding_function

    # Add other convenience methods here as needed


# Example usage (optional, for testing connection module directly)
# if __name__ == "__main__":
