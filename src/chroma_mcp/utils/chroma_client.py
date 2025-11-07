"""
ChromaDB client utility module for managing client instances and configuration.
"""

import os
import platform
from typing import Optional, Union, Any, Dict, Callable
from dataclasses import dataclass

# Migrate deprecated PYTORCH_CUDA_ALLOC_CONF to PYTORCH_ALLOC_CONF
# This prevents warnings from PyTorch dependencies (e.g., sentence-transformers)
# Do this early, before any imports that might use PyTorch
if "PYTORCH_CUDA_ALLOC_CONF" in os.environ and "PYTORCH_ALLOC_CONF" not in os.environ:
    os.environ["PYTORCH_ALLOC_CONF"] = os.environ["PYTORCH_CUDA_ALLOC_CONF"]
    # Optionally remove the deprecated variable to avoid confusion
    # os.environ.pop("PYTORCH_CUDA_ALLOC_CONF", None)

import chromadb
from chromadb.config import Settings
from chromadb import EmbeddingFunction, Documents, Embeddings
from chromadb.utils import embedding_functions as ef

# For database verification/creation
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# --- Dependency Availability Checks ---

# SentenceTransformers
try:
    from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

    SENTENCE_TRANSFORMER_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMER_AVAILABLE = False

# Google Generative AI (Still needed for Chroma's Google EF)
try:
    import google.generativeai as genai

    # Chroma uses GoogleGenerativeAiEmbeddingFunction, check its existence
    assert hasattr(ef, "GoogleGenerativeAiEmbeddingFunction")
    GENAI_AVAILABLE = True
except (ImportError, AssertionError):
    GENAI_AVAILABLE = False

# OpenAI
try:
    import openai  # type: ignore

    assert hasattr(ef, "OpenAIEmbeddingFunction")
    OPENAI_AVAILABLE = True
except (ImportError, AssertionError):
    OPENAI_AVAILABLE = False

# Cohere
try:
    import cohere  # type: ignore

    assert hasattr(ef, "CohereEmbeddingFunction")
    COHERE_AVAILABLE = True
except (ImportError, AssertionError):
    COHERE_AVAILABLE = False

# HuggingFace Hub API
try:
    import huggingface_hub  # type: ignore

    assert hasattr(ef, "HuggingFaceEmbeddingFunction")
    HF_API_AVAILABLE = True
except (ImportError, AssertionError):  # Corrected: check both import and assert
    HF_API_AVAILABLE = False

# VoyageAI
try:
    import voyageai  # type: ignore

    assert hasattr(ef, "VoyageAIEmbeddingFunction")
    VOYAGEAI_AVAILABLE = True
except (ImportError, AssertionError):
    VOYAGEAI_AVAILABLE = False

# ONNX Runtime
try:
    import onnxruntime  # type: ignore

    ONNXRUNTIME_AVAILABLE = True
except ImportError:
    ONNXRUNTIME_AVAILABLE = False

# Amazon Bedrock (boto3)
try:
    import boto3  # type: ignore

    assert hasattr(ef, "AmazonBedrockEmbeddingFunction")
    BEDROCK_AVAILABLE = True
except (ImportError, AssertionError):
    BEDROCK_AVAILABLE = False

# Ollama (ollama client library)
try:
    import ollama  # type: ignore

    assert hasattr(ef, "OllamaEmbeddingFunction")
    OLLAMA_AVAILABLE = True
except (ImportError, AssertionError):
    OLLAMA_AVAILABLE = False


from mcp.shared.exceptions import McpError
from mcp.types import ErrorData, INTERNAL_ERROR, INVALID_PARAMS

# Local application imports
from ..types import ChromaClientConfig
from .errors import EmbeddingError, ConfigurationError
from . import get_logger, get_server_config

# --- Constants ---

# Module-level cache for the client ONLY
_chroma_client: Optional[Union[chromadb.PersistentClient, chromadb.HttpClient, chromadb.EphemeralClient]] = None


# --- Embedding Function Registry & Helpers ---


def get_api_key(service_name: str) -> Optional[str]:
    """Retrieve API key for a service from environment variables."""
    env_var_name = f"{service_name.upper()}_API_KEY"
    key = os.getenv(env_var_name)
    # Only log if logger is configured (avoid warnings during initialization)
    from . import _main_logger_instance
    if _main_logger_instance is not None:
        logger = get_logger("utils.chroma_client")
        if key:
            logger.debug(f"Found API key for {service_name} in env var {env_var_name}")
        else:
            logger.warning(f"API key for {service_name} not found in env var {env_var_name}")
    return key


# Helper for Ollama URL (can be extended for other non-key configs)
def get_ollama_base_url() -> str:
    """Retrieve Ollama base URL from environment or use default."""
    url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")  # Default to local
    # Only log if logger is configured (avoid warnings during initialization)
    from . import _main_logger_instance
    if _main_logger_instance is not None:
        logger = get_logger("utils.chroma_client")
        logger.debug(f"Using Ollama base URL: {url}")
    return url


# Helper for OpenAI embedding model name
def get_openai_embedding_model() -> str:
    """Retrieve OpenAI embedding model name from environment or use default."""
    model = os.getenv("CHROMA_OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")  # Default to text-embedding-3-small
    # Only log if logger is configured (avoid warnings during initialization)
    from . import _main_logger_instance
    if _main_logger_instance is not None:
        logger = get_logger("utils.chroma_client")
        logger.debug(f"Using OpenAI embedding model: {model}")
    return model


# Helper for OpenAI embedding dimensions
def get_openai_embedding_dimensions() -> Optional[int]:
    """Retrieve OpenAI embedding dimensions from environment or use model-specific defaults."""
    dimensions_env = os.getenv("CHROMA_OPENAI_EMBEDDING_DIMENSIONS")
    if dimensions_env:
        try:
            return int(dimensions_env)
        except ValueError:
            # Only log if logger is configured (avoid warnings during initialization)
            from . import _main_logger_instance
            if _main_logger_instance is not None:
                logger = get_logger("utils.chroma_client")
                logger.warning(f"Invalid CHROMA_OPENAI_EMBEDDING_DIMENSIONS value: {dimensions_env}, using model default")
    
    # Model-specific defaults for text-embedding-3-* models
    model = get_openai_embedding_model()
    if model == "text-embedding-3-small":
        return 1536  # Default dimension for text-embedding-3-small
    elif model == "text-embedding-3-large":
        return 1024  # Use smaller dimension for efficiency
    
    # For other models (e.g., text-embedding-ada-002), return None to use default
    return None


# Updated Registry
KNOWN_EMBEDDING_FUNCTIONS: Dict[str, Callable[[], EmbeddingFunction]] = {
    # --- Local CPU/ONNX Options ---
    "default": lambda: ef.ONNXMiniLM_L6_V2(
        preferred_providers=(
            onnxruntime.get_available_providers()
            if ONNXRUNTIME_AVAILABLE
            and os.getenv("CHROMA_CPU_EXECUTION_PROVIDER", "auto").lower() == "false"
            and onnxruntime.get_available_providers()  # Ensure it's not empty
            else ["CPUExecutionProvider"]
        )
    ),
    "fast": lambda: ef.ONNXMiniLM_L6_V2(  # Alias for default
        preferred_providers=(
            onnxruntime.get_available_providers()
            if ONNXRUNTIME_AVAILABLE
            and os.getenv("CHROMA_CPU_EXECUTION_PROVIDER", "auto").lower() == "false"
            and onnxruntime.get_available_providers()  # Ensure it's not empty
            else ["CPUExecutionProvider"]
        )
    ),
    # --- Local SentenceTransformer Option ---
    **(
        {"accurate": lambda: SentenceTransformerEmbeddingFunction(model_name="all-mpnet-base-v2")}
        if SENTENCE_TRANSFORMER_AVAILABLE
        else {}
    ),
    # --- API-based Options ---
    **(
        {
            "openai": lambda: ef.OpenAIEmbeddingFunction(
                api_key=get_api_key("openai"),
                model_name=get_openai_embedding_model(),
                dimensions=get_openai_embedding_dimensions(),
            )
        }
        if OPENAI_AVAILABLE
        else {}
    ),
    **({"cohere": lambda: ef.CohereEmbeddingFunction(api_key=get_api_key("cohere"))} if COHERE_AVAILABLE else {}),
    **(
        {
            "huggingface": lambda: ef.HuggingFaceEmbeddingFunction(  # Requires api_key and model_name
                api_key=get_api_key("huggingface"), model_name="sentence-transformers/all-MiniLM-L6-v2"  # Example model
            )
        }
        if HF_API_AVAILABLE
        else {}
    ),
    **(
        {"voyageai": lambda: ef.VoyageAIEmbeddingFunction(api_key=get_api_key("voyageai"))}
        if VOYAGEAI_AVAILABLE
        else {}
    ),
    # --- Use Chroma's Google EF ---
    **(
        {"google": lambda: ef.GoogleGenerativeAiEmbeddingFunction(api_key=get_api_key("google"))}
        if GENAI_AVAILABLE
        else {}
    ),
    # --- Add Bedrock (uses AWS credentials implicitly via boto3) ---
    **(
        {
            "bedrock": lambda: ef.AmazonBedrockEmbeddingFunction(
                # Assumes region/credentials configured via env vars/AWS config
                model_name="amazon.titan-embed-text-v1"  # Example model
            )
        }
        if BEDROCK_AVAILABLE
        else {}
    ),
    # --- Add Ollama (uses base URL) ---
    **(
        {
            "ollama": lambda: ef.OllamaEmbeddingFunction(
                url=get_ollama_base_url(), model_name="nomic-embed-text"  # Example model
            )
        }
        if OLLAMA_AVAILABLE
        else {}
    ),
}


def get_embedding_function(name: str) -> EmbeddingFunction:
    """
    Gets an instantiated embedding function by name from the registry.

    Args:
        name: The name of the embedding function (e.g., 'default', 'openai').

    Returns:
        An instance of the requested EmbeddingFunction.

    Raises:
        McpError: If the name is unknown or instantiation fails.
    """
    logger = get_logger("utils.chroma_client")
    normalized_name = name.lower()

    # Handle TOKENIZERS_PARALLELISM for 'accurate' model
    if normalized_name == "accurate":
        # If CHROMA_CPU_EXECUTION_PROVIDER is true, or if TOKENIZERS_PARALLELISM is not set,
        # default TOKENIZERS_PARALLELISM to "false" for the 'accurate' model to aid CPU execution.
        # Users can still override by setting TOKENIZERS_PARALLELISM explicitly in their environment.
        if (
            os.getenv("CHROMA_CPU_EXECUTION_PROVIDER", "auto").lower() == "true"
            or os.getenv("TOKENIZERS_PARALLELISM") is None
        ):
            logger.info(
                "For 'accurate' embedding function, setting TOKENIZERS_PARALLELISM=false "
                "to aid CPU execution. Set TOKENIZERS_PARALLELISM in your env to override."
            )
            os.environ["TOKENIZERS_PARALLELISM"] = "false"
        elif os.getenv("TOKENIZERS_PARALLELISM", "false").lower() != "false":
            logger.warning(
                "TOKENIZERS_PARALLELISM is set to something other than 'false' for the 'accurate' model. "
                "This might cause issues if you don't have appropriate GPU/parallel processing setup."
            )

    # Check availability flags first (more robust than just relying on dict presence)
    is_available = False
    if normalized_name == "default" or normalized_name == "fast":
        is_available = ONNXRUNTIME_AVAILABLE
    elif normalized_name == "accurate":
        is_available = SENTENCE_TRANSFORMER_AVAILABLE
    elif normalized_name == "openai":
        is_available = OPENAI_AVAILABLE
    elif normalized_name == "cohere":
        is_available = COHERE_AVAILABLE
    elif normalized_name == "huggingface":
        is_available = HF_API_AVAILABLE
    elif normalized_name == "voyageai":
        is_available = VOYAGEAI_AVAILABLE
    elif normalized_name == "google":
        is_available = GENAI_AVAILABLE
    elif normalized_name == "bedrock":
        is_available = BEDROCK_AVAILABLE
    elif normalized_name == "ollama":
        is_available = OLLAMA_AVAILABLE

    if not is_available:
        error_msg = f"Dependency potentially missing for embedding function '{normalized_name}'. Please ensure the required library is installed."
        logger.error(error_msg)
        # Raise McpError indicating dependency issue, even if key is in dict due to import trickery
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=error_msg))

    instantiator = KNOWN_EMBEDDING_FUNCTIONS.get(normalized_name)
    if not instantiator:
        logger.error(f"Unknown embedding function name requested: '{name}' (Not found in registry even if available)")
        raise McpError(ErrorData(code=INVALID_PARAMS, message=f"Unknown embedding function: {name}"))

    try:
        logger.info(f"Instantiating embedding function: '{normalized_name}'")
        # Ensure necessary keys/configs are present BEFORE calling instantiator
        # This prevents late errors within ChromaDB's code if possible
        if normalized_name in ["openai", "cohere", "google", "huggingface", "voyageai"]:
            if not get_api_key(normalized_name):  # get_api_key already logs warning
                raise ValueError(f"API key for '{normalized_name}' not found in environment variable.")
        elif normalized_name == "ollama":
            # Just ensure the helper runs, it has a default
            get_ollama_base_url()
        # Bedrock relies on implicit AWS credential chain (no specific check here)

        instance = instantiator()
        # Log configuration details for OpenAI
        if normalized_name == "openai":
            model_name = get_openai_embedding_model()
            dimensions = get_openai_embedding_dimensions()
            logger.info(f"Successfully instantiated OpenAI embedding function - Model: {model_name}, Dimensions: {dimensions}")
        else:
            logger.info(f"Successfully instantiated embedding function: '{normalized_name}'")
        return instance
    except ImportError as e:
        logger.error(f"ImportError instantiating '{normalized_name}': {e}. Dependency likely missing.", exc_info=True)
        raise McpError(
            ErrorData(
                code=INTERNAL_ERROR, message=f"Dependency missing for embedding function '{normalized_name}': {e}"
            )
        ) from e
    except ValueError as e:
        # Catch ValueErrors often raised for missing API keys or bad config
        logger.error(f"Configuration error instantiating '{normalized_name}': {e}", exc_info=True)
        raise McpError(
            ErrorData(
                code=INVALID_PARAMS, message=f"Configuration error for embedding function '{normalized_name}': {e}"
            )
        ) from e
    except Exception as e:
        logger.error(f"Failed to instantiate embedding function '{normalized_name}': {e}", exc_info=True)
        raise McpError(
            ErrorData(code=INTERNAL_ERROR, message=f"Failed to create embedding function '{normalized_name}': {e}")
        ) from e


def get_chroma_client(
    config: Optional[ChromaClientConfig] = None,
) -> Union[chromadb.PersistentClient, chromadb.HttpClient, chromadb.EphemeralClient]:
    """Get or initialize the ChromaDB client based on configuration."""
    global _chroma_client

    # ADD logger assignment inside the function
    logger = get_logger("utils.chroma_client")

    # If client already exists, return it
    if _chroma_client is not None:
        return _chroma_client

    # If client doesn't exist, initialize it (should only happen once)
    if config is None:
        # Import getter locally within the function
        config = get_server_config()  # Get the config set during server startup

    # Ensure config is actually set (should be by server startup)
    if config is None:
        logger.critical("Chroma client configuration not found during initialization.")
        raise McpError(
            ErrorData(code=INTERNAL_ERROR, message="Chroma client configuration not found during initialization.")
        )

    # Create ChromaDB settings with telemetry disabled
    # EXTENSION: Leer configuración adicional desde variables de entorno
    # Permite usar CHROMA_ISOLATION_LEVEL y CHROMA_ALLOW_RESET sin modificar la firma
    settings_kwargs = {
        "anonymized_telemetry": False,  # Opt out of telemetry
    }
    
    # EXTENSION: Configurar isolation level si está definido
    # NOTA: isolation_level no es un parámetro válido de Settings en ChromaDB
    # Se lee pero no se pasa a Settings
    isolation_level = os.getenv("CHROMA_ISOLATION_LEVEL")
    if isolation_level:
        logger.debug(f"CHROMA_ISOLATION_LEVEL={isolation_level} (not used in Settings, ChromaDB doesn't support this parameter)")
    
    # EXTENSION: Configurar allow_reset si está definido
    # NOTA: allow_reset tampoco es un parámetro válido de Settings en ChromaDB
    # Se lee pero no se pasa a Settings
    allow_reset_str = os.getenv("CHROMA_ALLOW_RESET", "true")
    allow_reset = allow_reset_str.lower() in ["true", "1", "yes"]
    logger.debug(f"CHROMA_ALLOW_RESET={allow_reset} (not used in Settings, ChromaDB doesn't support this parameter)")
    
    # Crear Settings con solo los parámetros básicos soportados por ChromaDB
    chroma_settings = Settings(anonymized_telemetry=False)

    # Validate configuration
    if config.client_type == "persistent" and not config.data_dir:
        raise ValueError("data_dir is required for persistent client")
    elif config.client_type == "http" and not config.host:
        raise ValueError("host is required for http client")

    try:
        logger.info(f"Initializing Chroma client (Type: {config.client_type})")
        if config.client_type == "persistent":
            _chroma_client = chromadb.PersistentClient(path=config.data_dir, settings=chroma_settings)
            logger.info(f"Persistent client initialized (Path: {config.data_dir})")
        elif config.client_type == "http":
            # Build headers if api_key is provided
            headers = None
            if config.api_key:
                headers = {"Authorization": f"Bearer {config.api_key}"}
            
            _chroma_client = chromadb.HttpClient(
                host=config.host,
                port=config.port,
                ssl=config.ssl,
                tenant=config.tenant,
                database=config.database,
                settings=chroma_settings,
                headers=headers,
            )
            logger.info(f"HTTP client initialized (Host: {config.host}, Port: {config.port}, SSL: {config.ssl}, Auth: {'Yes' if config.api_key else 'No'})")
        else:  # ephemeral
            _chroma_client = chromadb.EphemeralClient(settings=chroma_settings)
            logger.info("Ephemeral client initialized")

        return _chroma_client

    except Exception as e:
        error_msg = f"Failed to initialize ChromaDB client: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=error_msg))


def reset_client() -> None:
    """Reset the global client instance."""
    logger = get_logger("utils.chroma_client")
    logger.info("Resetting Chroma client instance.")
    global _chroma_client
    if _chroma_client is not None:
        try:
            _chroma_client.reset()
        except Exception as e:
            if "Resetting is not allowed" in str(e):
                logger.warning(f"Client reset failed gracefully (allow_reset=False): {e}")
            else:
                logger.error(f"Error resetting client: {e}")
        _chroma_client = None
        logger.info("Chroma client instance reset.")
    else:
        logger.info("No active Chroma client instance to reset.")
