#!/bin/bash
# Script simple para ejecutar el servidor MCP desde el código fuente local
# Crea el venv con python3.12 si no existe e instala dependencias

# Obtener el directorio del script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Ir al directorio raíz del proyecto chroma_mcp_server (dos niveles arriba)
CHROMA_MCP_SERVER_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Definir la ruta del entorno virtual
VENV_DIR="$CHROMA_MCP_SERVER_DIR/.venv"
VENV_PYTHON="$VENV_DIR/bin/python"
VENV_ACTIVATE="$VENV_DIR/bin/activate"

# Función para crear el venv si no existe
create_venv_if_needed() {
    if [ ! -d "$VENV_DIR" ]; then
        echo "🔧 Creando entorno virtual con python3.12 en $VENV_DIR..." >&2
        
        # Verificar que python3.12 esté disponible
        if ! command -v python3.12 &> /dev/null; then
            echo "❌ Error: python3.12 no está disponible. Por favor, instálalo primero." >&2
            exit 1
        fi
        
        # Crear el venv con python3.12
        python3.12 -m venv "$VENV_DIR" || {
            echo "❌ Error al crear el entorno virtual" >&2
            exit 1
        }
        
        echo "✅ Entorno virtual creado exitosamente" >&2
        
        # Activar el venv
        source "$VENV_ACTIVATE" || {
            echo "❌ Error al activar el entorno virtual" >&2
            exit 1
        }
        
        # Actualizar pip, setuptools, wheel
        echo "📦 Actualizando pip, setuptools, wheel..." >&2
        pip install --quiet --upgrade pip setuptools wheel || {
            echo "⚠️  Advertencia: No se pudo actualizar pip" >&2
        }
        
        # Instalar dependencias base
        echo "📦 Instalando dependencias base..." >&2
        cd "$CHROMA_MCP_SERVER_DIR" || exit 1
        pip install --quiet -e '.' || {
            echo "❌ Error al instalar dependencias base" >&2
            exit 1
        }
        
        # Instalar todas las dependencias opcionales [full]
        # [full] incluye: [aimodels] + [server] + [client]
        echo "📦 Instalando todas las dependencias opcionales [full]..." >&2
        pip install --quiet -e '.[full]' || {
            echo "⚠️  Advertencia: No se pudieron instalar todas las dependencias opcionales" >&2
        }
        
        echo "✅ Dependencias instaladas exitosamente" >&2
    else
        # El venv ya existe, activarlo y verificar dependencias
        source "$VENV_ACTIVATE" || {
            echo "❌ Error al activar el entorno virtual" >&2
            exit 1
        }
        
        # Verificar si las dependencias están instaladas
        if ! "$VENV_PYTHON" -c "import pydantic" 2>/dev/null; then
            echo "📦 Dependencias no encontradas, instalando..." >&2
            cd "$CHROMA_MCP_SERVER_DIR" || exit 1
            
            # Actualizar pip, setuptools, wheel
            pip install --quiet --upgrade pip setuptools wheel || {
                echo "⚠️  Advertencia: No se pudo actualizar pip" >&2
            }
            
            # Instalar dependencias base
            echo "📦 Instalando dependencias base..." >&2
            pip install --quiet -e '.' || {
                echo "❌ Error al instalar dependencias base" >&2
                exit 1
            }
            
            # Instalar todas las dependencias opcionales [full]
            echo "📦 Instalando todas las dependencias opcionales [full]..." >&2
            pip install --quiet -e '.[full]' || {
                echo "⚠️  Advertencia: No se pudieron instalar todas las dependencias opcionales" >&2
            }
            
            echo "✅ Dependencias instaladas exitosamente" >&2
        fi
    fi
}

# Crear/activar el venv
create_venv_if_needed

# Configurar PYTHONPATH
export PYTHONPATH="$CHROMA_MCP_SERVER_DIR/src:$PYTHONPATH"

# Ejecutar el servidor
exec "$VENV_PYTHON" -m chroma_mcp.cli --mode stdio "$@"

