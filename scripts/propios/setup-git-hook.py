#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para crear un hook post-commit de Git que indexa automáticamente
los archivos modificados usando la configuración del .cursor/mcp.json del proyecto.
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
        
        # Verificar que es un repositorio git
        git_dir = project_path / ".git"
        if not git_dir.exists() or not git_dir.is_dir():
            print(f"❌ Error: {project_path} no es un repositorio Git.", file=sys.stderr)
            sys.exit(1)
        
        return project_path
    
    # Si no se pasó argumento, preguntar interactivamente
    while True:
        try:
            project_path = input("📁 Ingresa la ruta del proyecto donde quieres crear el hook de Git: ").strip()
        except UnicodeError as e:
            print(f"⚠️  Error de codificación al leer la entrada: {e}", file=sys.stderr)
            print("💡 Intenta ejecutar el script con: PYTHONIOENCODING=utf-8 python3 setup-git-hook.py", file=sys.stderr)
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
        
        # Verificar que es un repositorio git
        git_dir = project_path / ".git"
        if not git_dir.exists() or not git_dir.is_dir():
            print(f"⚠️  {project_path} no es un repositorio Git. Intenta de nuevo.")
            continue
        
        return project_path

def read_mcp_json(mcp_json_path: Path) -> Dict[str, Any]:
    """Lee el archivo mcp.json y retorna su contenido."""
    if not mcp_json_path.exists():
        print(f"❌ Error: No se encontró el archivo {mcp_json_path}", file=sys.stderr)
        print(f"💡 Asegúrate de haber configurado el proyecto con: make setup-mcp-config", file=sys.stderr)
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

def get_chroma_env_vars(mcp_config: Dict[str, Any]) -> Dict[str, str]:
    """Extrae las variables de entorno de la configuración de chroma en mcp.json."""
    chroma_config = mcp_config.get("mcpServers", {}).get("chroma", {})
    
    if not chroma_config:
        print("❌ Error: No se encontró la configuración 'chroma' en mcpServers", file=sys.stderr)
        sys.exit(1)
    
    env_vars = chroma_config.get("env", {})
    
    if not env_vars:
        print("❌ Error: No se encontraron variables de entorno en la configuración de chroma", file=sys.stderr)
        sys.exit(1)
    
    # Retornar TODAS las variables de entorno del mcp.json
    # Esto asegura que todas las variables necesarias estén disponibles en el hook
    # Las variables del mcp.json tienen prioridad sobre las del .env
    return {k: v for k, v in env_vars.items() if v is not None}

def get_chroma_mcp_server_root() -> Path:
    """
    Obtiene la raíz del proyecto chroma_mcp_server buscando marcadores como
    pyproject.toml o Makefile, empezando desde el directorio del script.
    """
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

def generate_post_commit_hook(project_path: Path, env_vars: Dict[str, str], chroma_mcp_server_path: Path) -> str:
    """Genera el contenido del hook post-commit."""
    
    # Construir las exportaciones de variables de entorno
    env_exports = []
    for key, value in sorted(env_vars.items()):
        # Escapar comillas y caracteres especiales en el valor
        escaped_value = value.replace('"', '\\"').replace('$', '\\$').replace('`', '\\`')
        env_exports.append(f'export {key}="{escaped_value}"')
    
    env_exports_str = '\n'.join(env_exports)
    
    hook_content = f"""#!/bin/sh
# .git/hooks/post-commit
# Hook generado automáticamente para indexar archivos modificados en ChromaDB
# Proyecto: {project_path}

echo "Running post-commit hook: Indexing changed files..."

# Ensure we are in the project root
PROJECT_ROOT=$(git rev-parse --show-toplevel)
cd "$PROJECT_ROOT" || exit 1

# Configurar variables de entorno desde mcp.json
{env_exports_str}

# Get list of changed/added files in the last commit
# Use --diff-filter=AM to only get Added or Modified files
FILES=$(git diff-tree --no-commit-id --name-only -r HEAD --diff-filter=AM -- "*.py" "*.js" "*.ts" "*.md" "*.txt" "*.json" "*.yaml" "*.yml")

if [ -z "$FILES" ]; then
  echo "No relevant files changed in this commit."
  exit 0
fi

echo "Files to index:"
echo "$FILES"

# Convert relative file paths to absolute paths
ABSOLUTE_FILES=""
for file in $FILES; do
  ABSOLUTE_FILE="$PROJECT_ROOT/$file"
  if [ -f "$ABSOLUTE_FILE" ]; then
    ABSOLUTE_FILES="$ABSOLUTE_FILES $ABSOLUTE_FILE"
  fi
done

if [ -z "$ABSOLUTE_FILES" ]; then
  echo "No valid files to index."
  exit 0
fi

# Run the indexer using chroma-client.sh from scripts/propios
# Usar el script chroma-client.sh que carga automáticamente las variables de entorno
CHROMA_CLIENT_SCRIPT="{chroma_mcp_server_path}/scripts/propios/chroma-client.sh"

if [ ! -f "$CHROMA_CLIENT_SCRIPT" ]; then
  echo "Error: No se encontró el script $CHROMA_CLIENT_SCRIPT"
  exit 1
fi

# Ejecutar el cliente con las variables de entorno ya configuradas
# Las variables de entorno del mcp.json tienen prioridad sobre las del .env
# El script chroma-client.sh usará las variables ya exportadas
"$CHROMA_CLIENT_SCRIPT" -vv index --repo-root "$PROJECT_ROOT" $ABSOLUTE_FILES

if [ $? -ne 0 ]; then
  echo "Error running chroma-mcp-client indexer!"
  exit 1
fi

echo "Post-commit indexing complete."
exit 0
"""
    return hook_content

def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Crea un hook post-commit de Git para indexación automática.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--project-path",
        type=str,
        help="Ruta del proyecto donde crear el hook (si no se proporciona, se pregunta interactivamente)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Sobrescribir el hook si ya existe sin preguntar"
    )
    
    args = parser.parse_args()
    
    print("🔧 Configurador de Git Hook para Indexación Automática\n")
    
    # Obtener la ruta del proyecto
    project_path = get_project_path(args.project_path)
    print(f"✅ Proyecto destino: {project_path}\n")
    
    # Leer mcp.json
    mcp_json_path = project_path / ".cursor" / "mcp.json"
    print(f"📖 Leyendo configuración desde {mcp_json_path}...")
    mcp_config = read_mcp_json(mcp_json_path)
    
    # Extraer variables de entorno relevantes
    print("🔍 Extrayendo variables de entorno de la configuración...")
    env_vars = get_chroma_env_vars(mcp_config)
    print(f"✅ {len(env_vars)} variables de entorno encontradas\n")
    
    # Mostrar valores importantes
    print("📋 Configuración detectada:")
    if "CHROMA_TENANT" in env_vars:
        print(f"   - CHROMA_TENANT: {env_vars['CHROMA_TENANT']}")
    if "CHROMA_DATABASE" in env_vars:
        print(f"   - CHROMA_DATABASE: {env_vars['CHROMA_DATABASE']}")
    if "CHROMA_OPENAI_EMBEDDING_MODEL" in env_vars:
        print(f"   - CHROMA_OPENAI_EMBEDDING_MODEL: {env_vars['CHROMA_OPENAI_EMBEDDING_MODEL']}")
    if "CHROMA_OPENAI_EMBEDDING_DIMENSIONS" in env_vars:
        print(f"   - CHROMA_OPENAI_EMBEDDING_DIMENSIONS: {env_vars['CHROMA_OPENAI_EMBEDDING_DIMENSIONS']}")
    print()
    
    # Obtener la ruta de chroma_mcp_server
    chroma_mcp_server_path = get_chroma_mcp_server_root()
    print(f"📦 Ruta de chroma_mcp_server: {chroma_mcp_server_path}\n")
    
    # Generar el hook
    print("🔧 Generando hook post-commit...")
    hook_content = generate_post_commit_hook(project_path, env_vars, chroma_mcp_server_path)
    
    # Crear el directorio de hooks si no existe
    hooks_dir = project_path / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    
    # Escribir el hook
    hook_path = hooks_dir / "post-commit"
    
    # Verificar si ya existe un hook
    if hook_path.exists() and not args.force:
        print(f"⚠️  El archivo {hook_path} ya existe.")
        response = input("¿Deseas sobrescribirlo? (s/N): ").strip().lower()
        if response not in ['s', 'sí', 'si', 'y', 'yes']:
            print("❌ Operación cancelada.")
            return 1
    
    try:
        with open(hook_path, 'w', encoding='utf-8') as f:
            f.write(hook_content)
        
        # Hacer el hook ejecutable
        os.chmod(hook_path, 0o755)
        
        print(f"✅ Hook creado exitosamente en {hook_path}")
        print("\n📋 Resumen:")
        print(f"   - Proyecto: {project_path}")
        print(f"   - Hook: {hook_path}")
        print(f"   - Tenant: {env_vars.get('CHROMA_TENANT', 'N/A')}")
        print(f"   - Database: {env_vars.get('CHROMA_DATABASE', 'N/A')}")
        print(f"   - Model: {env_vars.get('CHROMA_OPENAI_EMBEDDING_MODEL', 'N/A')}")
        print(f"   - Dimensions: {env_vars.get('CHROMA_OPENAI_EMBEDDING_DIMENSIONS', 'N/A')}")
        print("\n💡 El hook se ejecutará automáticamente después de cada commit.")
        
        return 0
    except Exception as e:
        print(f"❌ Error al crear el hook: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())

