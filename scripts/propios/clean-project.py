#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para limpiar completamente un proyecto configurado con ChromaDB MCP Server.
Elimina colecciones, configuración MCP, reglas de Cursor y hooks de Git.
"""
import os
import sys
import json
import argparse
import shutil
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
            project_path = input("📁 Ingresa la ruta del proyecto a limpiar: ").strip()
        except UnicodeError as e:
            print(f"⚠️  Error de codificación al leer la entrada: {e}", file=sys.stderr)
            print("💡 Intenta ejecutar el script con: PYTHONIOENCODING=utf-8 python3 clean-project.py", file=sys.stderr)
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
        print(f"⚠️  No se encontró el archivo {mcp_json_path}", file=sys.stderr)
        return {}
    
    try:
        with open(mcp_json_path, 'r', encoding='utf-8') as f:
            mcp_config = json.load(f)
        return mcp_config
    except json.JSONDecodeError as e:
        print(f"❌ Error al leer {mcp_json_path}: {e}", file=sys.stderr)
        return {}
    except Exception as e:
        print(f"❌ Error al leer {mcp_json_path}: {e}", file=sys.stderr)
        return {}

def get_chroma_tenant_from_mcp_json(mcp_config: Dict[str, Any]) -> Optional[str]:
    """Extrae el valor de CHROMA_TENANT del archivo mcp.json."""
    chroma_config = mcp_config.get("mcpServers", {}).get("chroma", {})
    env_vars = chroma_config.get("env", {})
    tenant = env_vars.get("CHROMA_TENANT")
    return tenant

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

def delete_collections(tenant: str, env_vars: Dict[str, str], chroma_mcp_server_root: Path, project_path: Path) -> bool:
    """Borra las colecciones de ChromaDB para el tenant especificado."""
    try:
        # Agregar el directorio src al path para importar módulos
        sys.path.insert(0, str(chroma_mcp_server_root / "src"))
        
        # Usar el cliente desde chroma_mcp_client (el que está en scripts/propios)
        from chroma_mcp_client.connection import get_client_and_ef
        
        # Cambiar al directorio del proyecto del usuario para que find_project_root()
        # encuentre el .env del proyecto del usuario si existe
        original_cwd = os.getcwd()
        try:
            os.chdir(str(project_path))
            
            # Convertir SSL de string a bool si está presente
            ssl_val = None
            if "CHROMA_SSL" in env_vars:
                ssl_str = env_vars["CHROMA_SSL"]
                ssl_val = ssl_str.lower() in ["true", "1", "yes"]
            
            # Conectar a ChromaDB pasando TODOS los parámetros directamente
            # Esto permite que cada ejecución tenga sus propias variables sin interferir
            print("🔌 Conectando a ChromaDB...")
            client, _ = get_client_and_ef(
                tenant=tenant,
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
        
        print(f"\n✅ {deleted_count} colecciones borradas.")
        return True
        
    except Exception as e:
        print(f"❌ Error al borrar colecciones: {e}", file=sys.stderr)
        import traceback
        print(traceback.format_exc(), file=sys.stderr)
        return False

def remove_chroma_from_mcp_json(mcp_json_path: Path) -> bool:
    """Elimina solo la entrada 'chroma' del mcp.json, preservando todas las demás entradas.
    
    Usa deserialización y serialización explícita de JSON para garantizar la integridad del archivo.
    """
    print(f"🔍 Verificando archivo: {mcp_json_path}")
    print(f"   ¿Existe?: {mcp_json_path.exists()}")
    print(f"   ¿Es absoluto?: {mcp_json_path.is_absolute()}")
    
    if not mcp_json_path.exists():
        print(f"ℹ️  El archivo {mcp_json_path} no existe, omitiendo...")
        return True
    
    try:
        # 1. DESERIALIZACIÓN: Leer el archivo JSON completo
        print(f"📖 Leyendo archivo JSON: {mcp_json_path}")
        with open(mcp_json_path, 'r', encoding='utf-8') as f:
            mcp_config = json.load(f)
        
        # Validar estructura básica
        if not isinstance(mcp_config, dict):
            print(f"⚠️  El archivo {mcp_json_path} no tiene una estructura válida, omitiendo...")
            return True
        
        # Si no hay mcpServers, no hay nada que hacer
        if "mcpServers" not in mcp_config:
            print(f"ℹ️  No hay mcpServers en {mcp_json_path}, omitiendo...")
            return True
        
        if not isinstance(mcp_config["mcpServers"], dict):
            print(f"⚠️  mcpServers no es un objeto válido en {mcp_json_path}, omitiendo...")
            return True
        
        # Guardar todas las entradas antes de modificar para logging
        all_entries_before = list(mcp_config["mcpServers"].keys())
        print(f"📋 Entradas encontradas en mcpServers: {', '.join(all_entries_before)}")
        
        # Si no hay entrada 'chroma', no hay nada que hacer
        if "chroma" not in mcp_config["mcpServers"]:
            print(f"ℹ️  No hay entrada 'chroma' en mcpServers, omitiendo...")
            return True
        
        print(f"✅ Encontrada entrada 'chroma' en mcpServers, procediendo a eliminarla...")
        
        # 2. CREAR NUEVA ESTRUCTURA: Construir un nuevo diccionario sin la entrada 'chroma'
        # Preservar todas las demás entradas y propiedades del archivo
        new_mcp_config = {}
        
        # Copiar todas las propiedades del archivo original (excepto mcpServers que lo manejamos aparte)
        for key, value in mcp_config.items():
            if key != "mcpServers":
                new_mcp_config[key] = value
        
        # Crear nuevo mcpServers sin la entrada 'chroma'
        new_mcp_servers = {}
        for key, value in mcp_config["mcpServers"].items():
            if key != "chroma":
                new_mcp_servers[key] = value
        
        # Solo agregar mcpServers si tiene entradas
        if new_mcp_servers:
            new_mcp_config["mcpServers"] = new_mcp_servers
            print(f"📋 Entradas restantes después de eliminar chroma: {', '.join(new_mcp_servers.keys())}")
        else:
            print(f"ℹ️  mcpServers quedó vacío después de eliminar chroma, no se incluirá en el archivo")
        
        # 3. SERIALIZACIÓN: Guardar el nuevo JSON completo
        with open(mcp_json_path, 'w', encoding='utf-8') as f:
            json.dump(new_mcp_config, f, indent=2, ensure_ascii=False)
        
        # Verificar el resultado
        remaining_entries = list(new_mcp_config.get("mcpServers", {}).keys())
        if remaining_entries:
            print(f"✅ Entrada 'chroma' eliminada de {mcp_json_path}")
            print(f"   Entradas restantes en mcpServers: {', '.join(remaining_entries)}")
        else:
            print(f"✅ Entrada 'chroma' eliminada de {mcp_json_path}")
            print(f"   mcpServers quedó vacío y fue eliminado del archivo")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Error al leer JSON de {mcp_json_path}: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"❌ Error al eliminar entrada 'chroma' de {mcp_json_path}: {e}", file=sys.stderr)
        import traceback
        print(traceback.format_exc(), file=sys.stderr)
        return False

def remove_cursor_rules(project_path: Path) -> bool:
    """Elimina las reglas de Cursor creadas por generate_cursor_rules."""
    rules_dir = project_path / ".cursor" / "rules"
    
    if not rules_dir.exists():
        print(f"ℹ️  El directorio {rules_dir} no existe, omitiendo...")
        return True
    
    # Reglas que se crean con generate_cursor_rules (sin _optimized)
    rules_to_delete = [
        "main_memory_rule.mdc",      # De main_memory_rule_optimized.mdc
        "auto_log_chat.mdc",         # De auto_log_chat_optimized.mdc
        "workflow.mdc",              # De workflow_optimized.mdc
        "thinking_sessions.mdc",
        "derived_learnings.mdc",
        "validation_evidence.mdc",
        "debug_assist.mdc",
        "daily_workflow.mdc",
    ]
    
    deleted_count = 0
    for rule_name in rules_to_delete:
        rule_file = rules_dir / rule_name
        if rule_file.exists():
            try:
                rule_file.unlink()
                print(f"✅ Regla eliminada: {rule_name}")
                deleted_count += 1
            except Exception as e:
                print(f"⚠️  Error al eliminar {rule_name}: {e}")
    
    # Si el directorio queda vacío (excepto reglas específicas del proyecto), eliminarlo
    if rules_dir.exists():
        remaining_files = [f for f in rules_dir.iterdir() if f.is_file()]
        if not remaining_files:
            try:
                rules_dir.rmdir()
                print(f"✅ Directorio {rules_dir} eliminado (estaba vacío)")
            except Exception as e:
                print(f"⚠️  No se pudo eliminar el directorio {rules_dir}: {e}")
    
    print(f"✅ {deleted_count} reglas eliminadas.")
    return True

def remove_git_hook(project_path: Path) -> bool:
    """Elimina el hook post-commit de Git."""
    hook_path = project_path / ".git" / "hooks" / "post-commit"
    
    if not hook_path.exists():
        print(f"ℹ️  El hook {hook_path} no existe, omitiendo...")
        return True
    
    try:
        # Verificar que es el hook que creamos (contiene "chroma-mcp-client" o "Indexing changed files")
        hook_content = hook_path.read_text(encoding='utf-8')
        if "Indexing changed files" in hook_content or "chroma-mcp-client" in hook_content or "chroma_mcp_client" in hook_content:
            hook_path.unlink()
            print(f"✅ Hook eliminado: {hook_path}")
            return True
        else:
            print(f"⚠️  El hook {hook_path} no parece ser el creado por setup-git-hook, omitiendo...")
            return False
    except Exception as e:
        print(f"❌ Error al eliminar hook {hook_path}: {e}", file=sys.stderr)
        return False

def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Limpia completamente un proyecto configurado con ChromaDB MCP Server.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--project-path",
        type=str,
        help="Ruta del proyecto a limpiar (si no se proporciona, se pregunta interactivamente)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="No pedir confirmación antes de eliminar"
    )
    
    args = parser.parse_args()
    
    print("🧹 Limpiador de Proyecto para ChromaDB MCP Server\n")
    
    # Obtener rutas
    chroma_mcp_server_root = get_chroma_mcp_server_root()
    
    # Obtener path del proyecto
    project_path = get_project_path(args.project_path)
    print(f"✅ Proyecto: {project_path}\n")
    
    # Leer mcp.json
    mcp_json_path = project_path / ".cursor" / "mcp.json"
    print(f"📖 Leyendo configuración desde {mcp_json_path}...")
    mcp_config = read_mcp_json(mcp_json_path)
    
    if not mcp_config:
        print("⚠️  No se encontró configuración válida en mcp.json.")
        print("💡 El proyecto puede no estar configurado con ChromaDB MCP Server.")
        response = input("¿Deseas continuar limpiando otros elementos (reglas, hooks)? (s/N): ").strip().lower()
        if response not in ['s', 'sí', 'si', 'y', 'yes']:
            print("❌ Operación cancelada.")
            return 1
        
        # Continuar solo con reglas y hooks
        tenant = None
        env_vars = {}
    else:
        # Extraer tenant y variables de entorno
        tenant = get_chroma_tenant_from_mcp_json(mcp_config)
        env_vars = get_chroma_env_vars_from_mcp_json(mcp_config)
        
        if not tenant:
            print("⚠️  No se encontró CHROMA_TENANT en la configuración.")
            print("💡 No se podrán borrar las colecciones de ChromaDB.")
            tenant = None
    
    # Mostrar resumen de lo que se va a eliminar
    print("\n" + "=" * 60)
    print("📋 Resumen de elementos a eliminar:")
    print("=" * 60)
    
    items_to_delete = []
    
    if tenant:
        items_to_delete.append(f"  - Colecciones de ChromaDB (tenant: {tenant})")
        items_to_delete.append("    * codebase_v1")
        items_to_delete.append("    * chat_history_v1")
        items_to_delete.append("    * derived_learnings_v1")
        items_to_delete.append("    * thinking_sessions_v1")
        items_to_delete.append("    * validation_evidence_v1")
        items_to_delete.append("    * test_results_v1")
    
    if mcp_config and "mcpServers" in mcp_config and "chroma" in mcp_config["mcpServers"]:
        items_to_delete.append(f"  - Entrada 'chroma' en {mcp_json_path}")
    
    rules_dir = project_path / ".cursor" / "rules"
    if rules_dir.exists():
        items_to_delete.append(f"  - Reglas de Cursor en {rules_dir}")
    
    hook_path = project_path / ".git" / "hooks" / "post-commit"
    if hook_path.exists():
        items_to_delete.append(f"  - Hook de Git en {hook_path}")
    
    if not items_to_delete:
        print("ℹ️  No se encontraron elementos para eliminar.")
        print("💡 El proyecto puede no estar configurado con ChromaDB MCP Server.")
        return 0
    
    for item in items_to_delete:
        print(item)
    
    print("\n" + "=" * 60)
    
    # Pedir confirmación
    if not args.force:
        try:
            response = input("\n⚠️  ¿Estás seguro de que deseas eliminar todos estos elementos? (s/N): ").strip().lower()
        except UnicodeError as e:
            print(f"⚠️  Error de codificación: {e}", file=sys.stderr)
            response = 'n'
        
        if response not in ['s', 'sí', 'si', 'y', 'yes']:
            print("❌ Operación cancelada.")
            return 1
    
    print("\n🧹 Iniciando limpieza...\n")
    
    success = True
    
    # 1. Borrar colecciones de ChromaDB
    if tenant:
        print("=" * 60)
        print("1️⃣  Borrando colecciones de ChromaDB...")
        print("=" * 60)
        if not delete_collections(tenant, env_vars, chroma_mcp_server_root, project_path):
            success = False
    else:
        print("⏭️  Omitiendo borrado de colecciones (no hay tenant configurado)")
    
    # 2. Eliminar entrada chroma del mcp.json
    print("\n" + "=" * 60)
    print("2️⃣  Eliminando entrada 'chroma' del mcp.json...")
    print("=" * 60)
    if not remove_chroma_from_mcp_json(mcp_json_path):
        success = False
    
    # 3. Eliminar reglas de Cursor
    print("\n" + "=" * 60)
    print("3️⃣  Eliminando reglas de Cursor...")
    print("=" * 60)
    if not remove_cursor_rules(project_path):
        success = False
    
    # 4. Eliminar hook de Git
    print("\n" + "=" * 60)
    print("4️⃣  Eliminando hook de Git...")
    print("=" * 60)
    if not remove_git_hook(project_path):
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("✅ ¡Limpieza completada exitosamente!")
    else:
        print("⚠️  Limpieza completada con algunos errores.")
    print("=" * 60)
    
    print(f"\n📋 Resumen:")
    print(f"   - Proyecto: {project_path}")
    if tenant:
        print(f"   - Tenant: {tenant}")
    print(f"   - Configuración MCP: {'Eliminada' if not (mcp_json_path.exists() and read_mcp_json(mcp_json_path).get('mcpServers', {}).get('chroma')) else 'Parcial'}")
    print(f"   - Reglas de Cursor: {'Eliminadas' if not (project_path / '.cursor' / 'rules').exists() or not any((project_path / '.cursor' / 'rules').glob('*.mdc')) else 'Parcial'}")
    print(f"   - Hook de Git: {'Eliminado' if not (project_path / '.git' / 'hooks' / 'post-commit').exists() else 'Parcial'}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

