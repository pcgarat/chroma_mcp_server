#!/bin/bash
# Script wrapper para ejecutar chroma-mcp-client usando uvx
# Carga variables de entorno desde scripts/propios/.env vía setup-chroma-env.sh
# Evita problemas de instalación y usa Python 3.12 como en mcp.json

# Cargar variables de entorno desde setup-chroma-env.sh
# setup-chroma-env.sh carga las variables desde scripts/propios/.env
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    source "$SCRIPT_DIR/setup-chroma-env.sh"

# Verificar que las variables críticas estén cargadas
if [ -z "$CHROMA_TENANT" ]; then
    echo "⚠️  Advertencia: CHROMA_TENANT no está definido en scripts/propios/.env" >&2
fi

if [ -z "$CHROMA_EMBEDDING_FUNCTION" ]; then
    echo "⚠️  Advertencia: CHROMA_EMBEDDING_FUNCTION no está definido en scripts/propios/.env" >&2
fi

if [ "$CHROMA_EMBEDDING_FUNCTION" = "openai" ]; then
    if [ -z "$OPENAI_API_KEY" ]; then
        echo "⚠️  Advertencia: OPENAI_API_KEY no está definido en scripts/propios/.env" >&2
    fi
    if [ -z "$CHROMA_OPENAI_EMBEDDING_MODEL" ]; then
        echo "⚠️  Advertencia: CHROMA_OPENAI_EMBEDDING_MODEL no está definido en scripts/propios/.env" >&2
    fi
    if [ -z "$CHROMA_OPENAI_EMBEDDING_DIMENSIONS" ]; then
        echo "⚠️  Advertencia: CHROMA_OPENAI_EMBEDDING_DIMENSIONS no está definido en scripts/propios/.env" >&2
    fi
fi

# Ejecutar usando uvx con Python 3.12
# Nota: uvx instala el paquete con dependencias [full] que incluye aimodels
# Las variables de entorno se pasan automáticamente al proceso hijo
exec uvx --python 3.12 --from "chroma-mcp-server[full]" chroma-mcp-client "$@"

