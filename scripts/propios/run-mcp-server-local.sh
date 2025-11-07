#!/bin/bash
# Script para ejecutar el servidor MCP desde el código fuente local
# Uso: Este script se ejecuta desde .cursor/mcp.json para usar el código fuente local
# Crea/activa un entorno virtual y asegura que todas las dependencias [full] estén instaladas
# Opciones: -v o --verbose para modo verbose (muestra más información)

# Detectar modo verbose
VERBOSE=false
for arg in "$@"; do
    case "$arg" in
        -v|--verbose)
            VERBOSE=true
            ;;
    esac
done

# Función para mostrar mensajes verbose
verbose_echo() {
    if [ "$VERBOSE" = true ]; then
        echo "$@" >&2
    fi
}

# Obtener el directorio del script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Ir al directorio raíz del proyecto chroma_mcp_server (dos niveles arriba)
CHROMA_MCP_SERVER_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

verbose_echo "📁 Directorio del script: $SCRIPT_DIR"
verbose_echo "📁 Directorio raíz del proyecto: $CHROMA_MCP_SERVER_DIR"

# Cambiar al directorio del servidor MCP
cd "$CHROMA_MCP_SERVER_DIR" || exit 1

# Definir la ruta del entorno virtual
VENV_DIR="$CHROMA_MCP_SERVER_DIR/.venv"
verbose_echo "🐍 Entorno virtual: $VENV_DIR"

# Función para crear el entorno virtual si no existe
create_venv_if_needed() {
    if [ ! -d "$VENV_DIR" ]; then
        echo "🔧 Creando entorno virtual en $VENV_DIR..." >&2
        if [ "$VERBOSE" = true ]; then
            python3 -m venv "$VENV_DIR" || {
                echo "❌ Error al crear el entorno virtual" >&2
                exit 1
            }
        else
            python3 -m venv "$VENV_DIR" >/dev/null 2>&1 || {
                echo "❌ Error al crear el entorno virtual" >&2
                exit 1
            }
        fi
        echo "✅ Entorno virtual creado exitosamente" >&2
    else
        verbose_echo "ℹ️  Entorno virtual ya existe en $VENV_DIR"
    fi
}

# Función para activar el entorno virtual
activate_venv() {
    if [ -f "$VENV_DIR/bin/activate" ]; then
        verbose_echo "🔄 Activando entorno virtual..."
        # Activar el entorno virtual
        source "$VENV_DIR/bin/activate" || {
            echo "❌ Error al activar el entorno virtual" >&2
            exit 1
        }
        if [ "$VERBOSE" = true ]; then
            verbose_echo "✅ Entorno virtual activado"
            verbose_echo "   Python: $(which python)"
            verbose_echo "   Versión: $(python --version 2>&1)"
        fi
    else
        echo "❌ No se encontró el script de activación del entorno virtual" >&2
        exit 1
    fi
}

# Función para instalar/actualizar dependencias [full]
install_dependencies() {
    echo "📦 Verificando/instalando dependencias [full]..." >&2
    if [ "$VERBOSE" = true ]; then
        verbose_echo "   Actualizando pip, setuptools, wheel..."
        pip install --upgrade pip setuptools wheel || {
            echo "⚠️  Advertencia: No se pudo actualizar pip" >&2
        }
        verbose_echo "   Instalando chroma-mcp-server[full] en modo editable..."
        pip install -e '.[full]' || {
            echo "❌ Error al instalar dependencias [full]" >&2
            exit 1
        }
    else
        pip install --quiet --upgrade pip setuptools wheel || {
            echo "⚠️  Advertencia: No se pudo actualizar pip" >&2
        }
        pip install --quiet -e '.[full]' || {
            echo "❌ Error al instalar dependencias [full]" >&2
            exit 1
        }
    fi
    echo "✅ Dependencias [full] instaladas/actualizadas" >&2
}

# Crear entorno virtual si no existe
create_venv_if_needed

# Activar el entorno virtual
activate_venv

# Instalar/actualizar dependencias [full] en el entorno virtual
install_dependencies

# Configurar PYTHONPATH para que Python encuentre el código fuente
export PYTHONPATH="$CHROMA_MCP_SERVER_DIR/src:$PYTHONPATH"
verbose_echo "🔧 PYTHONPATH: $PYTHONPATH"

# Verificar/crear la base de datos si se usa cliente HTTP
if [ "$CHROMA_CLIENT_TYPE" = "http" ] && [ -n "$CHROMA_TENANT" ] && [ "$CHROMA_TENANT" != "default_tenant" ]; then
    # Usar default_database si no está definido CHROMA_DATABASE
    DB_NAME="${CHROMA_DATABASE:-default_database}"
    verbose_echo "🔍 Verificando base de datos '${DB_NAME}' en tenant '${CHROMA_TENANT}'..."
    
    # Verificar si la base de datos existe
    if [ "$VERBOSE" = true ]; then
        DB_CHECK=$(curl -w "%{http_code}" -o /dev/null \
            -X GET "http://${CHROMA_HOST:-localhost}:${CHROMA_PORT:-8000}/api/v2/tenants/${CHROMA_TENANT}/databases/${DB_NAME}" \
            -H "Authorization: Bearer ${CHROMA_API_KEY:-}" 2>&1 | tail -n1 || echo "000")
    else
        DB_CHECK=$(curl -s -w "%{http_code}" -o /dev/null \
            -X GET "http://${CHROMA_HOST:-localhost}:${CHROMA_PORT:-8000}/api/v2/tenants/${CHROMA_TENANT}/databases/${DB_NAME}" \
            -H "Authorization: Bearer ${CHROMA_API_KEY:-}" 2>/dev/null || echo "000")
    fi
    
    verbose_echo "   Código de respuesta: $DB_CHECK"
    
    if [ "$DB_CHECK" = "404" ] || [ "$DB_CHECK" = "000" ]; then
        # La base de datos no existe, crearla
        echo "🔧 Creando base de datos '${DB_NAME}' en tenant '${CHROMA_TENANT}'..." >&2
        if [ "$VERBOSE" = true ]; then
            DB_CREATE=$(curl -w "%{http_code}" -o /dev/null \
                -X POST "http://${CHROMA_HOST:-localhost}:${CHROMA_PORT:-8000}/api/v2/tenants/${CHROMA_TENANT}/databases" \
                -H "Content-Type: application/json" \
                -H "Authorization: Bearer ${CHROMA_API_KEY:-}" \
                -d "{\"name\": \"${DB_NAME}\"}" 2>&1 | tail -n1 || echo "000")
        else
            DB_CREATE=$(curl -s -w "%{http_code}" -o /dev/null \
                -X POST "http://${CHROMA_HOST:-localhost}:${CHROMA_PORT:-8000}/api/v2/tenants/${CHROMA_TENANT}/databases" \
                -H "Content-Type: application/json" \
                -H "Authorization: Bearer ${CHROMA_API_KEY:-}" \
                -d "{\"name\": \"${DB_NAME}\"}" 2>/dev/null || echo "000")
        fi
        
        if [ "$DB_CREATE" = "200" ] || [ "$DB_CREATE" = "201" ]; then
            echo "✅ Base de datos '${DB_NAME}' creada exitosamente" >&2
        else
            echo "⚠️  No se pudo crear la base de datos '${DB_NAME}' (código: ${DB_CREATE}). Continuando..." >&2
        fi
    else
        verbose_echo "✅ Base de datos '${DB_NAME}' ya existe"
    fi
fi

# Preparar argumentos para el servidor
SERVER_ARGS=("--mode" "stdio")
if [ "$VERBOSE" = true ]; then
    SERVER_ARGS+=("--log-level" "DEBUG")
    verbose_echo "🚀 Iniciando servidor MCP en modo verbose (DEBUG)..."
    verbose_echo "   Comando: python -m chroma_mcp.cli ${SERVER_ARGS[*]}"
    verbose_echo "   Variables de entorno:"
    verbose_echo "     CHROMA_CLIENT_TYPE=${CHROMA_CLIENT_TYPE:-not set}"
    verbose_echo "     CHROMA_HOST=${CHROMA_HOST:-not set}"
    verbose_echo "     CHROMA_PORT=${CHROMA_PORT:-not set}"
    verbose_echo "     CHROMA_TENANT=${CHROMA_TENANT:-not set}"
    verbose_echo "     CHROMA_DATABASE=${CHROMA_DATABASE:-not set}"
    verbose_echo "     CHROMA_EMBEDDING_FUNCTION=${CHROMA_EMBEDDING_FUNCTION:-not set}"
    verbose_echo "     CHROMA_OPENAI_EMBEDDING_MODEL=${CHROMA_OPENAI_EMBEDDING_MODEL:-not set}"
    verbose_echo "     CHROMA_OPENAI_EMBEDDING_DIMENSIONS=${CHROMA_OPENAI_EMBEDDING_DIMENSIONS:-not set}"
else
    verbose_echo "🚀 Iniciando servidor MCP..."
fi

# Ejecutar el servidor usando Python del entorno virtual
# El modo stdio es el que usa MCP
# Las variables de entorno se pasan automáticamente desde .cursor/mcp.json
# Usar python del venv (que ya está activado) en lugar de python3 del sistema
exec python -m chroma_mcp.cli "${SERVER_ARGS[@]}"


