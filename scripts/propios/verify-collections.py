#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar que las colecciones de ChromaDB están correctamente configuradas.
Lee el mcp.json del proyecto y verifica que las colecciones usen el embedding function correcto.
"""
import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# Configurar codificación UTF-8 para stdin/stdout/stderr
os.environ['PYTHONIOENCODING'] = 'utf-8'

if sys.version_info >= (3, 7):
    try:
        if sys.stdin.isatty():
            sys.stdin.reconfigure(encoding='utf-8', errors='replace')
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except (AttributeError, ValueError, OSError):
        pass

def get_chroma_mcp_server_root() -> Path:
    """Obtiene la raíz del proyecto chroma_mcp_server."""
    script_dir = Path(__file__).parent.resolve()
    current = script_dir
    markers = ["pyproject.toml", "Makefile", ".git"]
    
    for _ in range(5):
        for marker in markers:
            if (current / marker).exists():
                return current.resolve()
        parent = current.parent
        if parent == current:
            break
        current = parent
    
    fallback_root = script_dir.parent.parent
    return fallback_root.resolve()

CHROMA_MCP_SERVER_ROOT = get_chroma_mcp_server_root()

# Agregar el directorio src al path para importar módulos
sys.path.insert(0, str(CHROMA_MCP_SERVER_ROOT / "src"))

def safe_input(prompt: str) -> str:
    """Lee entrada del usuario con manejo robusto de codificación UTF-8."""
    try:
        return input(prompt).strip()
    except (UnicodeError, UnicodeDecodeError):
        try:
            sys.stdout.write(prompt)
            sys.stdout.flush()
            line = sys.stdin.readline()
            if not line:
                raise EOFError("Entrada cancelada")
            if isinstance(line, bytes):
                return line.decode('utf-8', errors='replace').strip()
            return line.strip()
        except (UnicodeError, UnicodeDecodeError, EOFError) as e:
            raise

def get_project_path(project_path_arg: Optional[str] = None) -> Path:
    """Obtiene la ruta del proyecto destino."""
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
            project_path = safe_input("📁 Ingresa la ruta del proyecto a verificar: ")
        except (UnicodeError, UnicodeDecodeError) as e:
            print(f"\n⚠️  Error de codificación al leer la entrada: {e}", file=sys.stderr)
            print("💡 Asegúrate de que tu terminal esté configurado con UTF-8", file=sys.stderr)
            sys.exit(1)
        except (EOFError, KeyboardInterrupt):
            print("\n⚠️  Operación cancelada.", file=sys.stderr)
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
        "CHROMA_OPENAI_EMBEDDING_MODEL": env_vars.get("CHROMA_OPENAI_EMBEDDING_MODEL"),
        "CHROMA_OPENAI_EMBEDDING_DIMENSIONS": env_vars.get("CHROMA_OPENAI_EMBEDDING_DIMENSIONS"),
    }
    
    return {k: v for k, v in relevant_vars.items() if v is not None}

def verify_embedding_function(ef, expected_dimensions: Optional[int] = None) -> tuple[bool, int, Optional[str]]:
    """Verifica el embedding function y retorna (is_valid, dimensions, error_message)."""
    try:
        # Probar con un texto de prueba
        test_text = "test"
        test_embedding = ef([test_text])
        
        if not test_embedding or len(test_embedding) == 0:
            return False, 0, "El embedding function no generó embeddings"
        
        dimensions = len(test_embedding[0])
        
        if expected_dimensions and dimensions != expected_dimensions:
            return False, dimensions, f"Dimensiones incorrectas: esperado {expected_dimensions}, actual {dimensions}"
        
        return True, dimensions, None
    except Exception as e:
        return False, 0, f"Error al verificar embedding function: {e}"

def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Verifica que las colecciones de ChromaDB estén correctamente configuradas.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--project-path",
        type=str,
        help="Ruta del proyecto a verificar (si no se proporciona, se pregunta interactivamente)"
    )
    
    args = parser.parse_args()
    
    print("🔍 Verificador de Colecciones de ChromaDB\n")
    
    # Obtener la ruta del proyecto
    project_path = get_project_path(args.project_path)
    print(f"✅ Proyecto: {project_path}\n")
    
    # Leer mcp.json
    mcp_json_path = project_path / ".cursor" / "mcp.json"
    print(f"📖 Leyendo configuración desde {mcp_json_path}...")
    mcp_config = read_mcp_json(mcp_json_path)
    
    # Extraer variables de entorno del mcp.json
    env_vars = get_chroma_env_vars_from_mcp_json(mcp_config)
    
    # Mostrar configuración esperada
    print("\n📋 Configuración esperada del mcp.json:")
    print(f"  CHROMA_EMBEDDING_FUNCTION: {env_vars.get('CHROMA_EMBEDDING_FUNCTION', 'N/A')}")
    print(f"  CHROMA_OPENAI_EMBEDDING_MODEL: {env_vars.get('CHROMA_OPENAI_EMBEDDING_MODEL', 'N/A')}")
    print(f"  CHROMA_OPENAI_EMBEDDING_DIMENSIONS: {env_vars.get('CHROMA_OPENAI_EMBEDDING_DIMENSIONS', 'N/A')}")
    print(f"  CHROMA_TENANT: {env_vars.get('CHROMA_TENANT', 'N/A')}")
    print(f"  CHROMA_DATABASE: {env_vars.get('CHROMA_DATABASE', 'N/A')}")
    print()
    
    # Configurar variables de entorno temporalmente
    for key, value in env_vars.items():
        os.environ[key] = value
    
    # Cambiar al directorio del proyecto para que find_project_root() funcione correctamente
    original_cwd = os.getcwd()
    result = 1
    try:
        os.chdir(str(project_path))
        
        # Importar después de configurar el path
        from chroma_mcp_client.connection import get_client_and_ef
        
        # Conectar a ChromaDB
        print("🔌 Conectando a ChromaDB...")
        client, ef = get_client_and_ef(
            tenant=env_vars.get("CHROMA_TENANT"),
            database=env_vars.get("CHROMA_DATABASE"),
            host=env_vars.get("CHROMA_HOST"),
            port=env_vars.get("CHROMA_PORT"),
            client_type=env_vars.get("CHROMA_CLIENT_TYPE"),
            ssl=env_vars.get("CHROMA_SSL", "false").lower() in ["true", "1", "yes"],
            api_key=env_vars.get("CHROMA_API_KEY"),
            data_dir=env_vars.get("CHROMA_DATA_DIR"),
            embedding_function=env_vars.get("CHROMA_EMBEDDING_FUNCTION"),
            openai_api_key=env_vars.get("OPENAI_API_KEY"),
        )
        print("✅ Conexión establecida\n")
        
        # Verificar embedding function
        expected_dimensions = None
        if env_vars.get("CHROMA_OPENAI_EMBEDDING_DIMENSIONS"):
            try:
                expected_dimensions = int(env_vars.get("CHROMA_OPENAI_EMBEDDING_DIMENSIONS"))
            except ValueError:
                pass
        
        print("🔍 Verificando embedding function...")
        is_valid, dimensions, error_msg = verify_embedding_function(ef, expected_dimensions)
        
        if is_valid:
            print(f"✅ Embedding function: {dimensions} dimensiones")
            if expected_dimensions:
                print(f"   ✅ Coincide con la configuración esperada ({expected_dimensions})")
        else:
            print(f"❌ Error en embedding function: {error_msg}")
            if dimensions > 0:
                print(f"   Dimensiones actuales: {dimensions}")
        
        print()
        
        # Verificar colecciones
        print("📊 Verificando colecciones existentes:")
        collections_to_check = [
            "codebase_v1",
            "chat_history_v1",
            "derived_learnings_v1",
            "thinking_sessions_v1",
            "validation_evidence_v1",
            "test_results_v1"
        ]
        
        all_ok = True
        documents_to_delete = {}  # {collection_name: [list of ids]}
        
        for coll_name in collections_to_check:
            try:
                # Intentar obtener la colección con el embedding function correcto
                collection = client.get_collection(name=coll_name, embedding_function=ef)
                count = collection.count()
                
                # Verificar dimensiones si hay documentos
                if count > 0:
                    try:
                        # Obtener todos los documentos para verificar dimensiones
                        all_data = collection.get(include=["embeddings"])
                        
                        if all_data and "embeddings" in all_data and len(all_data["embeddings"]) > 0:
                            incorrect_ids = []
                            correct_count = 0
                            
                            # Verificar cada documento
                            for i, embedding in enumerate(all_data["embeddings"]):
                                if embedding is None:
                                    continue
                                    
                                doc_dimensions = len(embedding)
                                
                                if expected_dimensions and doc_dimensions != expected_dimensions:
                                    # Documento con dimensiones incorrectas
                                    doc_id = all_data["ids"][i]
                                    incorrect_ids.append(doc_id)
                                else:
                                    correct_count += 1
                            
                            if incorrect_ids:
                                print(f"  ⚠️  {coll_name}: {count} documentos - {len(incorrect_ids)} con dimensiones incorrectas, {correct_count} correctos")
                                documents_to_delete[coll_name] = incorrect_ids
                                all_ok = False
                            else:
                                # Verificar dimensiones de muestra para mostrar
                                sample_dimensions = len(all_data["embeddings"][0])
                                print(f"  ✅ {coll_name}: {count} documentos - Dimensiones correctas ({sample_dimensions})")
                        else:
                            print(f"  ✅ {coll_name}: {count} documentos")
                    except Exception as e:
                        print(f"  ⚠️  {coll_name}: {count} documentos - No se pudieron verificar dimensiones: {e}")
                        all_ok = False
                else:
                    print(f"  ℹ️  {coll_name}: {count} documentos (vacía)")
                    
            except Exception as e:
                error_str = str(e).lower()
                if "dimension" in error_str or "mismatch" in error_str:
                    print(f"  ❌ {coll_name}: Error de dimensiones - {e}")
                    # Si hay error de dimensiones, intentar obtener sin embedding function para eliminar todos los documentos
                    try:
                        collection_no_ef = client.get_collection(name=coll_name)
                        count = collection_no_ef.count()
                        if count > 0:
                            print(f"     La colección tiene {count} documentos que necesitan ser eliminados")
                            # Obtener todos los IDs para eliminarlos
                            all_data = collection_no_ef.get()
                            if all_data and "ids" in all_data:
                                documents_to_delete[coll_name] = all_data["ids"]
                    except Exception as inner_e:
                        print(f"     ⚠️  No se pudieron obtener los documentos para eliminar: {inner_e}")
                    all_ok = False
                elif "not found" in error_str or "does not exist" in error_str or "404" in error_str:
                    print(f"  ℹ️  {coll_name}: No existe")
                else:
                    print(f"  ⚠️  {coll_name}: Error - {e}")
                    all_ok = False
        
        # Eliminar documentos con dimensiones incorrectas
        if documents_to_delete:
            print()
            print("🗑️  Eliminando documentos con dimensiones incorrectas...")
            total_deleted = 0
            
            for coll_name, ids_to_delete in documents_to_delete.items():
                try:
                    # Intentar obtener la colección con el embedding function correcto
                    # Si falla, intentar sin embedding function
                    try:
                        collection = client.get_collection(name=coll_name, embedding_function=ef)
                    except Exception:
                        # Si falla por dimensiones, obtener sin embedding function
                        collection = client.get_collection(name=coll_name)
                    
                    delete_count = len(ids_to_delete)
                    
                    # Eliminar por lotes para evitar problemas con grandes cantidades
                    batch_size = 100
                    deleted_in_collection = 0
                    
                    for i in range(0, len(ids_to_delete), batch_size):
                        batch_ids = ids_to_delete[i:i+batch_size]
                        try:
                            collection.delete(ids=batch_ids)
                            deleted_in_collection += len(batch_ids)
                        except Exception as e:
                            print(f"  ⚠️  Error al eliminar lote de {coll_name}: {e}")
                    
                    if deleted_in_collection > 0:
                        print(f"  ✅ {coll_name}: {deleted_in_collection} documentos eliminados")
                        total_deleted += deleted_in_collection
                    else:
                        print(f"  ⚠️  {coll_name}: No se pudieron eliminar los documentos")
                        
                except Exception as e:
                    print(f"  ❌ Error al eliminar documentos de {coll_name}: {e}")
            
            if total_deleted > 0:
                print(f"\n✅ Total: {total_deleted} documentos eliminados")
                all_ok = True  # Después de eliminar, las colecciones deberían estar bien
        
        print()
        
        # Resumen
        if all_ok:
            print("✅ Todas las colecciones están correctamente configuradas")
            result = 0
        else:
            print("⚠️  Algunas colecciones tienen problemas de configuración")
            print("💡 Puedes usar 'make reset-collections' para recrear las colecciones con la configuración correcta")
            result = 1
            
    except Exception as e:
        print(f"❌ Error durante la verificación: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        result = 1
    finally:
        # Restaurar el directorio original
        os.chdir(original_cwd)
        return result

if __name__ == "__main__":
    sys.exit(main())

