#!/usr/bin/env python3
"""
Script para borrar todas las colecciones de ChromaDB y recrearlas desde cero.
"""
import os
import sys
from pathlib import Path

# Obtener el directorio donde está este script
SCRIPT_DIR = Path(__file__).parent.resolve()
ENV_FILE = SCRIPT_DIR / ".env"

# Cargar variables de entorno desde el archivo .env si existe
if ENV_FILE.exists():
    try:
        # Intentar usar python-dotenv si está disponible
        try:
            from dotenv import load_dotenv
            load_dotenv(dotenv_path=ENV_FILE, override=True)
        except ImportError:
            # Si python-dotenv no está disponible, cargar manualmente
            print("⚠️  python-dotenv no está instalado. Cargando .env manualmente...", file=sys.stderr)
            with open(ENV_FILE, 'r') as f:
                for line in f:
                    line = line.strip()
                    # Ignorar comentarios y líneas vacías
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        # Eliminar comillas si existen
                        value = value.strip('"\'')
                        os.environ[key.strip()] = value
    except Exception as e:
        print(f"⚠️  Error al cargar .env: {e}", file=sys.stderr)
        print(f"💡 Asegúrate de que el archivo .env existe en {SCRIPT_DIR}", file=sys.stderr)
else:
    print(f"⚠️  No se encontró el archivo .env en {SCRIPT_DIR}", file=sys.stderr)
    print(f"💡 Copia env-template a .env: cp {SCRIPT_DIR}/env-template {ENV_FILE}", file=sys.stderr)

# Agregar el directorio src al path para importar módulos
# __file__ está en chroma_mcp_server/scripts/propios/reset_collections.py
# Necesitamos llegar a chroma_mcp_server/src
project_root = Path(__file__).parent.parent.parent  # chroma_mcp_server
sys.path.insert(0, str(project_root / "src"))  # chroma_mcp_server/src

import chromadb
from chroma_mcp.utils.chroma_client import get_chroma_client, get_embedding_function
from chroma_mcp.types import ChromaClientConfig

def main():
    """Borra todas las colecciones y las recrea."""
    # Obtener configuración del cliente desde variables de entorno
    client_config = ChromaClientConfig(
        client_type=os.getenv("CHROMA_CLIENT_TYPE", "persistent"),
        data_dir=os.getenv("CHROMA_DATA_DIR", "./chroma_data"),
        host=os.getenv("CHROMA_HOST", "localhost"),
        port=os.getenv("CHROMA_PORT", "8000"),
        ssl=os.getenv("CHROMA_SSL", "false").lower() in ["true", "1", "yes"],
        tenant=os.getenv("CHROMA_TENANT", chromadb.DEFAULT_TENANT),
        database=os.getenv("CHROMA_DATABASE", chromadb.DEFAULT_DATABASE),
        api_key=os.getenv("CHROMA_API_KEY"),
    )

    # Conectar a ChromaDB
    print("🔌 Conectando a ChromaDB...")
    client = get_chroma_client(config=client_config)
    ef = get_embedding_function(os.getenv("CHROMA_EMBEDDING_FUNCTION", "default"))

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

