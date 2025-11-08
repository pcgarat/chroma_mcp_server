#!/usr/bin/env python3
"""
Script para borrar todas las colecciones de ChromaDB y recrearlas desde cero.
Lee la configuración del .cursor/mcp.json del proyecto del usuario.
"""
import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# Configurar codificación UTF-8 para stdin/stdout/stderr
if sys.version_info >= (3, 7):
    try:
        sys.stdin.reconfigure(encoding='utf-8')
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except (AttributeError, ValueError):
        os.environ['PYTHONIOENCODING'] = 'utf-8'
else:
    os.environ['PYTHONIOENCODING'] = 'utf-8'

def get_chroma_mcp_server_root() -> Path:
    """
    Obtiene la raíz del proyecto chroma_mcp_server buscando marcadores como
    pyproject.toml o Makefile, empezando desde el directorio del script.
    """
    # Obtener el directorio donde está este script
    script_dir = Path(__file__).parent.resolve()
    
    # Buscar hacia arriba desde el script hasta encontrar la raíz del proyecto
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
            project_path = input("📁 Ingresa la ruta del proyecto: ").strip()
        except UnicodeError as e:
            print(f"⚠️  Error de codificación al leer la entrada: {e}", file=sys.stderr)
            print("💡 Intenta ejecutar el script con: PYTHONIOENCODING=utf-8 python3 reset_collections.py", file=sys.stderr)
            sys.exit(1)
        
        if not project_path:
            print("⚠️  La ruta no puede estar vacía. Intenta de nuevo.")
            continue
        
        project_path = os.path.expanduser(project_path)
        project_path = os.path.expandvars(project_path)
        project_path = Path(project_path).resolve()
        
        if not project_path.exists():
            print(f"⚠️  La ruta {project_path} no existe. Intenta de nuevo.")
            continue
        
        if not project_path.is_dir():
            print(f"⚠️  {project_path} no es un directorio. Intenta de nuevo.")
            continue
        
        return project_path

def read_mcp_json(mcp_json_path: Path) -> Dict[str, Any]:
    """Lee el archivo mcp.json y retorna su contenido."""
    if not mcp_json_path.exists():
        print(f"❌ Error: No se encontró el archivo {mcp_json_path}", file=sys.stderr)
        sys.exit(1)
    
    try:
        with open(mcp_json_path, 'r', encoding='utf-8') as f:
            mcp_config = json.load(f)
        return mcp_config
    except json.JSONDecodeError as e:
        print(f"❌ Error al leer {mcp_json_path}: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error al leer {mcp_json_path}: {e}", file=sys.stderr)
        sys.exit(1)

def get_chroma_env_vars_from_mcp_json(mcp_config: Dict[str, Any]) -> Dict[str, str]:
    """Extrae todas las variables de entorno relevantes del mcp.json."""
    chroma_config = mcp_config.get("mcpServers", {}).get("chroma", {})
    env_vars = chroma_config.get("env", {})
    
    # Variables relevantes para conectar a ChromaDB
    relevant_vars = {
        "CHROMA_CLIENT_TYPE": env_vars.get("CHROMA_CLIENT_TYPE"),
        "CHROMA_HOST": env_vars.get("CHROMA_HOST"),
        "CHROMA_PORT": env_vars.get("CHROMA_PORT"),
        "CHROMA_SSL": env_vars.get("CHROMA_SSL"),
        "CHROMA_API_KEY": env_vars.get("CHROMA_API_KEY"),
        "CHROMA_TENANT": env_vars.get("CHROMA_TENANT"),
        "CHROMA_DATABASE": env_vars.get("CHROMA_DATABASE"),
        "CHROMA_DATA_DIR": env_vars.get("CHROMA_DATA_DIR"),
        "CHROMA_EMBEDDING_FUNCTION": env_vars.get("CHROMA_EMBEDDING_FUNCTION"),
        "OPENAI_API_KEY": env_vars.get("OPENAI_API_KEY"),
    }
    
    return {k: v for k, v in relevant_vars.items() if v is not None}

# Agregar el directorio src al path para importar módulos
sys.path.insert(0, str(CHROMA_MCP_SERVER_ROOT / "src"))

from chroma_mcp_client.connection import get_client_and_ef

def main():
    """Borra todas las colecciones y las recrea."""
    parser = argparse.ArgumentParser(
        description="Borra todas las colecciones de ChromaDB y las recrea.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--project-path",
        type=str,
        help="Ruta del proyecto (si no se proporciona, se pregunta interactivamente)"
    )
    
    args = parser.parse_args()
    
    print("🔄 Reseteando colecciones de ChromaDB\n")
    
    # Obtener la ruta del proyecto
    project_path = get_project_path(args.project_path)
    print(f"✅ Proyecto: {project_path}\n")
    
    # Leer mcp.json
    mcp_json_path = project_path / ".cursor" / "mcp.json"
    print(f"📖 Leyendo configuración desde {mcp_json_path}...")
    mcp_config = read_mcp_json(mcp_json_path)
    
    # Extraer variables de entorno del mcp.json
    env_vars = get_chroma_env_vars_from_mcp_json(mcp_config)
    
    # Convertir SSL de string a bool si está presente
    ssl_val = None
    if "CHROMA_SSL" in env_vars:
        ssl_str = env_vars["CHROMA_SSL"]
        ssl_val = ssl_str.lower() in ["true", "1", "yes"]
    
    # Cambiar al directorio del proyecto del usuario para que find_project_root()
    # encuentre el .env del proyecto del usuario si existe
    original_cwd = os.getcwd()
    try:
        os.chdir(str(project_path))
        
        # Conectar a ChromaDB usando el cliente de chroma_mcp_client
        # Pasando TODOS los parámetros directamente desde el mcp.json
        print("🔌 Conectando a ChromaDB...")
        client, ef = get_client_and_ef(
            tenant=env_vars.get("CHROMA_TENANT"),
            database=env_vars.get("CHROMA_DATABASE"),
            host=env_vars.get("CHROMA_HOST"),
            port=env_vars.get("CHROMA_PORT"),
            client_type=env_vars.get("CHROMA_CLIENT_TYPE"),
            ssl=ssl_val,
            api_key=env_vars.get("CHROMA_API_KEY"),
            data_dir=env_vars.get("CHROMA_DATA_DIR"),
            embedding_function=env_vars.get("CHROMA_EMBEDDING_FUNCTION"),
            openai_api_key=env_vars.get("OPENAI_API_KEY"),
        )
    finally:
        # Restaurar el directorio original
        os.chdir(original_cwd)

    # Colecciones a borrar
    collections_to_delete = [
        "codebase_v1",
        "chat_history_v1",
        "derived_learnings_v1",
        "thinking_sessions_v1",
        "validation_evidence_v1",
        "test_results_v1"
    ]

    print("🗑️  Borrando colecciones de ChromaDB...")
    deleted_count = 0
    
    for collection_name in collections_to_delete:
        try:
            # Intentar obtener la colección
            collection = client.get_collection(name=collection_name)
            count = collection.count()
            
            # Primero borrar todos los documentos de la colección
            if count > 0:
                print(f"  🗑️  Borrando {count} documentos de '{collection_name}'...")
                # Obtener todos los IDs
                all_data = collection.get()
                if all_data and 'ids' in all_data and len(all_data['ids']) > 0:
                    # Borrar todos los documentos por lotes
                    batch_size = 100
                    ids = all_data['ids']
                    for i in range(0, len(ids), batch_size):
                        batch_ids = ids[i:i+batch_size]
                        collection.delete(ids=batch_ids)
                    print(f"    ✅ {count} documentos borrados")
            
            # Luego borrar la colección
            client.delete_collection(name=collection_name)
            print(f"✅ Colección '{collection_name}' borrada exitosamente")
            deleted_count += 1
        except Exception as e:
            # Si la colección no existe, simplemente continuar
            error_str = str(e).lower()
            if "does not exist" in error_str or "not found" in error_str or "404" in error_str:
                print(f"ℹ️  Colección '{collection_name}' no existe, omitiendo")
            else:
                print(f"⚠️  Error al borrar '{collection_name}': {e}")

    print(f"\n✅ Proceso completado. {deleted_count} colecciones borradas.")
    
    # Recrear las colecciones usando setup-collections
    print("\n🔄 Recreando colecciones...")
    try:
        import subprocess
        script_dir = Path(__file__).parent.resolve()
        chroma_client_script = script_dir / "chroma-client.sh"
        
        if chroma_client_script.exists():
            result = subprocess.run(
                [str(chroma_client_script), "setup-collections"],
                capture_output=True,
                text=True,
                cwd=str(script_dir)
            )
            if result.returncode == 0:
                print("✅ Colecciones recreadas exitosamente")
            else:
                print(f"⚠️  Error al recrear colecciones: {result.stderr}")
                print("💡 Puedes recrearlas manualmente con: ./chroma-client.sh setup-collections")
        else:
            print("⚠️  No se encontró chroma-client.sh, no se pueden recrear las colecciones automáticamente")
            print("💡 Recrea las colecciones manualmente con: ./chroma-client.sh setup-collections")
    except Exception as e:
        print(f"⚠️  Error al recrear colecciones: {e}")
        print("💡 Recrea las colecciones manualmente con: ./chroma-client.sh setup-collections")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

