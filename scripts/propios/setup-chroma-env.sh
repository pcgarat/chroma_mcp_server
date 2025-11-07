#!/bin/bash
# Script para exportar variables de entorno de ChromaDB
# Uso: source ./chroma_mcp_server/scripts/propios/setup-chroma-env.sh
# O: ./chroma_mcp_server/scripts/propios/setup-chroma-env.sh && chroma-mcp-client <comando>
#
# Este script carga las variables de entorno desde un archivo .env en la raíz de chroma_mcp_server.
# Si no existe el archivo .env, muestra un mensaje de error indicando cómo crearlo.

# Obtener el directorio donde está este script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# El .env ahora está en la raíz de chroma_mcp_server (dos niveles arriba desde scripts/propios)
CHROMA_MCP_SERVER_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ENV_FILE="$CHROMA_MCP_SERVER_ROOT/.env"
ENV_TEMPLATE="$SCRIPT_DIR/env-template"

# Verificar si existe el archivo .env
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Error: No se encontró el archivo .env en $CHROMA_MCP_SERVER_ROOT" >&2
    echo "" >&2
    if [ -f "$ENV_TEMPLATE" ]; then
        echo "💡 Para crear el archivo .env, copia el template:" >&2
        echo "   cp $ENV_TEMPLATE $ENV_FILE" >&2
        echo "   # Luego edita $ENV_FILE con tus valores" >&2
    else
        echo "💡 Crea un archivo .env en $CHROMA_MCP_SERVER_ROOT con las variables de entorno necesarias." >&2
    fi
    echo "" >&2
    exit 1
fi

# Cargar variables de entorno desde el archivo .env
# Usar set -a para exportar automáticamente todas las variables
set -a
source "$ENV_FILE"
set +a

# Verificar que se cargaron las variables esenciales
if [ -z "$CHROMA_CLIENT_TYPE" ]; then
    echo "⚠️  Advertencia: CHROMA_CLIENT_TYPE no está definido en el archivo .env" >&2
fi

# Si se usa cliente HTTP y hay un tenant configurado, verificar/crear el tenant
if [ "$CHROMA_CLIENT_TYPE" = "http" ] && [ -n "$CHROMA_TENANT" ] && [ "$CHROMA_TENANT" != "default_tenant" ]; then
    # Verificar si el tenant existe
    TENANT_CHECK=$(curl -s -w "%{http_code}" -o /dev/null \
        -X GET "http://${CHROMA_HOST:-localhost}:${CHROMA_PORT:-8000}/api/v2/tenants/${CHROMA_TENANT}" \
        -H "Authorization: Bearer ${CHROMA_API_KEY:-}" 2>/dev/null || echo "000")
    
    if [ "$TENANT_CHECK" = "404" ] || [ "$TENANT_CHECK" = "000" ]; then
        # El tenant no existe, intentar crearlo
        echo "🔧 Creando tenant '${CHROMA_TENANT}' en ChromaDB..." >&2
        TENANT_CREATE=$(curl -s -w "%{http_code}" -o /dev/null \
            -X POST "http://${CHROMA_HOST:-localhost}:${CHROMA_PORT:-8000}/api/v2/tenants" \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer ${CHROMA_API_KEY:-}" \
            -d "{\"name\": \"${CHROMA_TENANT}\"}" 2>/dev/null || echo "000")
        
        if [ "$TENANT_CREATE" = "200" ] || [ "$TENANT_CREATE" = "201" ]; then
            echo "✅ Tenant '${CHROMA_TENANT}' creado exitosamente" >&2
        else
            echo "⚠️  No se pudo crear el tenant '${CHROMA_TENANT}' (código: ${TENANT_CREATE}). Continuando..." >&2
        fi
    fi
    
    # Verificar/crear la base de datos si está configurada
    if [ -n "$CHROMA_DATABASE" ] && [ "$CHROMA_DATABASE" != "default_database" ]; then
        DB_CHECK=$(curl -s -w "%{http_code}" -o /dev/null \
            -X GET "http://${CHROMA_HOST:-localhost}:${CHROMA_PORT:-8000}/api/v2/tenants/${CHROMA_TENANT}/databases/${CHROMA_DATABASE}" \
            -H "Authorization: Bearer ${CHROMA_API_KEY:-}" 2>/dev/null || echo "000")
        
        if [ "$DB_CHECK" = "404" ] || [ "$DB_CHECK" = "000" ]; then
            echo "🔧 Creando base de datos '${CHROMA_DATABASE}' en tenant '${CHROMA_TENANT}'..." >&2
            DB_CREATE=$(curl -s -w "%{http_code}" -o /dev/null \
                -X POST "http://${CHROMA_HOST:-localhost}:${CHROMA_PORT:-8000}/api/v2/tenants/${CHROMA_TENANT}/databases" \
                -H "Content-Type: application/json" \
                -H "Authorization: Bearer ${CHROMA_API_KEY:-}" \
                -d "{\"name\": \"${CHROMA_DATABASE}\"}" 2>/dev/null || echo "000")
            
            if [ "$DB_CREATE" = "200" ] || [ "$DB_CREATE" = "201" ]; then
                echo "✅ Base de datos '${CHROMA_DATABASE}' creada exitosamente" >&2
            else
                echo "⚠️  No se pudo crear la base de datos '${CHROMA_DATABASE}' (código: ${DB_CREATE}). Continuando..." >&2
            fi
        fi
    else
        # Si no hay CHROMA_DATABASE configurado, crear default_database
        DB_CHECK=$(curl -s -w "%{http_code}" -o /dev/null \
            -X GET "http://${CHROMA_HOST:-localhost}:${CHROMA_PORT:-8000}/api/v2/tenants/${CHROMA_TENANT}/databases/default_database" \
            -H "Authorization: Bearer ${CHROMA_API_KEY:-}" 2>/dev/null || echo "000")
        
        if [ "$DB_CHECK" = "404" ] || [ "$DB_CHECK" = "000" ]; then
            echo "🔧 Creando base de datos 'default_database' en tenant '${CHROMA_TENANT}'..." >&2
            DB_CREATE=$(curl -s -w "%{http_code}" -o /dev/null \
                -X POST "http://${CHROMA_HOST:-localhost}:${CHROMA_PORT:-8000}/api/v2/tenants/${CHROMA_TENANT}/databases" \
                -H "Content-Type: application/json" \
                -H "Authorization: Bearer ${CHROMA_API_KEY:-}" \
                -d '{"name": "default_database"}' 2>/dev/null || echo "000")
            
            if [ "$DB_CREATE" = "200" ] || [ "$DB_CREATE" = "201" ]; then
                echo "✅ Base de datos 'default_database' creada exitosamente" >&2
            fi
        fi
    fi
fi

# Si se ejecuta directamente (no con source), ejecutar el comando pasado como argumentos
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    if [ $# -eq 0 ]; then
        echo "Variables de entorno exportadas. Usa 'source $0' para exportarlas en tu sesión actual."
        echo ""
        echo "Ejemplos de uso:"
        echo "  source $0                    # Exportar variables en la sesión actual"
        echo "  $0 setup-collections         # Ejecutar comando directamente"
        echo "  $0 index --all               # Indexar código"
        exit 0
    else
        # Ejecutar el comando pasado como argumentos
        exec chroma-mcp-client "$@"
    fi
fi

