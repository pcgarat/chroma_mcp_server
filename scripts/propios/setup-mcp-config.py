#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para configurar el servidor MCP de ChromaDB en un proyecto.
Lee el .env de la raíz de chroma_mcp_server y crea/actualiza el .cursor/mcp.json
del proyecto destino con la configuración del servidor ChromaDB.
"""
import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# Configurar codificación UTF-8 para stdin/stdout/stderr
if sys.version_info >= (3, 7):
    # Python 3.7+ soporta reconfigure
    try:
        sys.stdin.reconfigure(encoding='utf-8')
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except (AttributeError, ValueError):
        # Si reconfigure no está disponible o falla, usar variables de entorno
        os.environ['PYTHONIOENCODING'] = 'utf-8'
else:
    # Python < 3.7: usar variables de entorno
    os.environ['PYTHONIOENCODING'] = 'utf-8'

def get_chroma_mcp_server_root() -> Path:
    """
    Obtiene la raíz del proyecto chroma_mcp_server buscando marcadores como
    pyproject.toml o Makefile, empezando desde el directorio del script.
    """
    # Obtener el directorio donde está este script
    script_dir = Path(__file__).parent.resolve()
    
    # Buscar hacia arriba desde el script hasta encontrar la raíz del proyecto
    # El script está en scripts/propios/, así que la raíz está dos niveles arriba
    # Pero también buscamos marcadores para asegurarnos
    current = script_dir
    markers = ["pyproject.toml", "Makefile", ".git"]
    
    # Buscar hasta 5 niveles arriba (por si acaso)
    for _ in range(5):
        # Verificar si encontramos algún marcador
        for marker in markers:
            if (current / marker).exists():
                return current.resolve()
        # Si no encontramos, subir un nivel
        parent = current.parent
        if parent == current:  # Llegamos a la raíz del sistema
            break
        current = parent
    
    # Fallback: usar el cálculo relativo (dos niveles arriba desde scripts/propios)
    fallback_root = script_dir.parent.parent
    return fallback_root.resolve()

# Obtener la raíz del proyecto chroma_mcp_server dinámicamente
CHROMA_MCP_SERVER_ROOT = get_chroma_mcp_server_root()
ENV_FILE = CHROMA_MCP_SERVER_ROOT / ".env"

# Ruta del Makefile para detectar la raíz de chroma_mcp_server
MAKEFILE_PATH = CHROMA_MCP_SERVER_ROOT / "Makefile"
CHROMA_MCP_SERVER_ABS_PATH = str(CHROMA_MCP_SERVER_ROOT)

def load_env_file(env_file: Path) -> Dict[str, str]:
    """Carga variables de entorno desde un archivo .env."""
    env_vars = {}
    if not env_file.exists():
        print(f"❌ Error: No se encontró el archivo .env en {env_file}", file=sys.stderr)
        sys.exit(1)
    
    try:
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                # Ignorar comentarios y líneas vacías
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Eliminar comillas si existen
                    value = value.strip('"\'')
                    env_vars[key.strip()] = value
    except Exception as e:
        print(f"❌ Error al cargar .env: {e}", file=sys.stderr)
        sys.exit(1)
    
    return env_vars

def get_project_path(project_path_arg: Optional[str] = None) -> Path:
    """Obtiene la ruta del proyecto destino, ya sea desde argumento o preguntando al usuario."""
    if project_path_arg:
        project_path = os.path.expanduser(project_path_arg)
        project_path = os.path.expandvars(project_path)
        project_path = Path(project_path).resolve()
        
        if not project_path.exists():
            print(f"❌ Error: La ruta {project_path} no existe.", file=sys.stderr)
            sys.exit(1)
        
        if not project_path.is_dir():
            print(f"❌ Error: {project_path} no es un directorio.", file=sys.stderr)
            sys.exit(1)
        
        return project_path
    
    # Si no se pasó argumento, preguntar interactivamente
    while True:
        try:
            project_path = input("📁 Ingresa la ruta del proyecto donde quieres añadir el MCP server de ChromaDB: ").strip()
        except UnicodeError as e:
            print(f"⚠️  Error de codificación al leer la entrada: {e}", file=sys.stderr)
            print("💡 Intenta ejecutar el script con: PYTHONIOENCODING=utf-8 python3 setup-mcp-config.py", file=sys.stderr)
            sys.exit(1)
        
        if not project_path:
            print("⚠️  La ruta no puede estar vacía. Intenta de nuevo.")
            continue
        
        # Expandir ~ y variables de entorno
        project_path = os.path.expanduser(project_path)
        project_path = os.path.expandvars(project_path)
        
        # Convertir a Path y resolver
        project_path = Path(project_path).resolve()
        
        if not project_path.exists():
            print(f"⚠️  La ruta {project_path} no existe. Intenta de nuevo.")
            continue
        
        if not project_path.is_dir():
            print(f"⚠️  {project_path} no es un directorio. Intenta de nuevo.")
            continue
        
        return project_path

def get_tenant(tenant_arg: Optional[str] = None) -> str:
    """Obtiene el tenant, ya sea desde argumento o preguntando al usuario."""
    if tenant_arg:
        return tenant_arg if tenant_arg else "default_tenant"
    
    # Si no se pasó argumento, preguntar interactivamente
    try:
        tenant = input("🏢 Ingresa el CHROMA_TENANT (o presiona Enter para usar 'default_tenant'): ").strip()
    except UnicodeError as e:
        print(f"⚠️  Error de codificación al leer la entrada: {e}", file=sys.stderr)
        print("💡 Intenta ejecutar el script con: PYTHONIOENCODING=utf-8 python3 setup-mcp-config.py", file=sys.stderr)
        sys.exit(1)
    
    if not tenant:
        tenant = "default_tenant"
    
    return tenant

def create_or_load_mcp_json(mcp_json_path: Path) -> Dict[str, Any]:
    """Crea o carga el archivo mcp.json."""
    if mcp_json_path.exists():
        try:
            with open(mcp_json_path, 'r') as f:
                mcp_config = json.load(f)
        except json.JSONDecodeError as e:
            print(f"⚠️  Error al leer {mcp_json_path}: {e}", file=sys.stderr)
            print("🔄 Creando un nuevo archivo mcp.json...", file=sys.stderr)
            mcp_config = {"mcpServers": {}}
    else:
        mcp_config = {"mcpServers": {}}
    
    return mcp_config

def replace_paths(text: str, old_path: str, new_path: str) -> str:
    """Reemplaza paths absolutos por la nueva ruta."""
    return text.replace(old_path, new_path)

def build_chroma_config(env_vars: Dict[str, str], tenant: str, chroma_mcp_server_path: str) -> Dict[str, Any]:
    """Construye la configuración del servidor ChromaDB para mcp.json."""
    # Ruta del script run-mcp-server-simple.sh
    script_path = Path(chroma_mcp_server_path) / "scripts" / "propios" / "run-mcp-server-simple.sh"
    script_path_str = str(script_path.resolve())
    
    # Ruta del src para PYTHONPATH
    src_path = Path(chroma_mcp_server_path) / "src"
    src_path_str = str(src_path.resolve())
    
    # Construir el objeto de configuración
    chroma_config = {
        "command": script_path_str,
        "args": [
            "--log-level",
            "DEBUG"
        ],
        "env": {}
    }
    
    # Mapear variables del .env al objeto env
    env_mapping = {
        "CHROMA_CLIENT_TYPE": env_vars.get("CHROMA_CLIENT_TYPE", "http"),
        "CHROMA_HOST": env_vars.get("CHROMA_HOST", "localhost"),
        "CHROMA_PORT": env_vars.get("CHROMA_PORT", "8000"),
        "CHROMA_SSL": env_vars.get("CHROMA_SSL", "false"),
        "CHROMA_API_KEY": env_vars.get("CHROMA_API_KEY", ""),
        "CHROMA_TENANT": tenant,  # Preguntado al usuario
        "CHROMA_DATABASE": env_vars.get("CHROMA_DATABASE", "default_database"),  # Del .env
        "CHROMA_LOG_DIR": env_vars.get("CHROMA_LOG_DIR", ""),
        "LOG_LEVEL": env_vars.get("LOG_LEVEL", "INFO"),
        "MCP_LOG_LEVEL": env_vars.get("MCP_LOG_LEVEL", "INFO"),
        "MCP_SERVER_LOG_LEVEL": env_vars.get("MCP_SERVER_LOG_LEVEL", "INFO"),
        "CHROMA_EMBEDDING_FUNCTION": env_vars.get("CHROMA_EMBEDDING_FUNCTION", "openai"),
        "OPENAI_API_KEY": env_vars.get("OPENAI_API_KEY", ""),
        "CHROMA_OPENAI_EMBEDDING_MODEL": env_vars.get("CHROMA_OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        "CHROMA_OPENAI_EMBEDDING_DIMENSIONS": env_vars.get("CHROMA_OPENAI_EMBEDDING_DIMENSIONS", "1536"),
        "CHROMA_DISTANCE_METRIC": env_vars.get("CHROMA_DISTANCE_METRIC", "cosine"),
        "CHROMA_COLLECTION_METADATA": env_vars.get("CHROMA_COLLECTION_METADATA", '{"hnsw:space": "cosine"}'),
        "CHROMA_ISOLATION_LEVEL": env_vars.get("CHROMA_ISOLATION_LEVEL", "read_committed"),
        "CHROMA_ALLOW_RESET": env_vars.get("CHROMA_ALLOW_RESET", "true"),
    }
    
    # Añadir PYTHONPATH
    chroma_config["env"]["PYTHONPATH"] = src_path_str
    
    # Añadir todas las variables mapeadas
    for key, value in env_mapping.items():
        if value or key in ["CHROMA_TENANT"]:  # Añadir siempre tenant
            chroma_config["env"][key] = value
    
    return chroma_config

def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Configura el servidor MCP de ChromaDB en un proyecto.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--project-path",
        type=str,
        help="Ruta del proyecto donde configurar el MCP server (si no se proporciona, se pregunta interactivamente)"
    )
    parser.add_argument(
        "--tenant",
        type=str,
        help="CHROMA_TENANT a usar (si no se proporciona, se pregunta interactivamente o se usa 'default_tenant')"
    )
    
    args = parser.parse_args()
    
    print("🔧 Configurador de MCP Server para ChromaDB\n")
    
    # Verificar que existe el Makefile (para detectar la raíz de chroma_mcp_server)
    if not MAKEFILE_PATH.exists():
        print(f"⚠️  Advertencia: No se encontró el Makefile en {CHROMA_MCP_SERVER_ROOT}", file=sys.stderr)
        print(f"   Usando la ruta detectada: {CHROMA_MCP_SERVER_ABS_PATH}", file=sys.stderr)
    
    # Cargar variables de entorno desde .env
    print(f"📖 Cargando variables de entorno desde {ENV_FILE}...")
    env_vars = load_env_file(ENV_FILE)
    print(f"✅ {len(env_vars)} variables cargadas\n")
    
    # Obtener la ruta del proyecto destino
    project_path = get_project_path(args.project_path)
    print(f"✅ Proyecto destino: {project_path}\n")
    
    # Obtener tenant
    tenant = get_tenant(args.tenant)
    database = env_vars.get("CHROMA_DATABASE", "default_database")
    print(f"✅ CHROMA_TENANT: {tenant}")
    print(f"✅ CHROMA_DATABASE: {database} (del .env)\n")
    
    # Ruta del archivo mcp.json
    cursor_dir = project_path / ".cursor"
    mcp_json_path = cursor_dir / "mcp.json"
    
    # Crear directorio .cursor si no existe
    if not cursor_dir.exists():
        print(f"📁 Creando directorio {cursor_dir}...")
        cursor_dir.mkdir(parents=True, exist_ok=True)
    
    # Crear o cargar mcp.json
    mcp_config = create_or_load_mcp_json(mcp_json_path)
    
    # Construir la configuración de ChromaDB
    print("🔧 Construyendo configuración de ChromaDB...")
    chroma_config = build_chroma_config(env_vars, tenant, CHROMA_MCP_SERVER_ABS_PATH)
    
    # Añadir o actualizar la entrada "chroma"
    mcp_config["mcpServers"]["chroma"] = chroma_config
    
    # Guardar el archivo mcp.json
    print(f"💾 Guardando configuración en {mcp_json_path}...")
    try:
        with open(mcp_json_path, 'w') as f:
            json.dump(mcp_config, f, indent=2)
        print(f"✅ Configuración guardada exitosamente en {mcp_json_path}")
    except Exception as e:
        print(f"❌ Error al guardar {mcp_json_path}: {e}", file=sys.stderr)
        sys.exit(1)
    
    print("\n✅ Proceso completado exitosamente!")
    print(f"📋 El servidor MCP de ChromaDB ha sido configurado en {mcp_json_path}")
    print(f"   - Tenant: {tenant}")
    print(f"   - Database: {database}")
    print(f"   - Ruta del servidor: {CHROMA_MCP_SERVER_ABS_PATH}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

