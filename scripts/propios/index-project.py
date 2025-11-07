#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para indexar todos los documentos de un proyecto.
Lee el archivo .cursor/mcp.json del proyecto para obtener CHROMA_TENANT
y ejecuta la indexación excluyendo archivos según .gitignore y .git/info/exclude.
"""
import os
import sys
import json
import subprocess
import fnmatch
from pathlib import Path
from typing import Dict, Any, List, Set

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

# Obtener la raíz del proyecto chroma_mcp_server dinámicamente
CHROMA_MCP_SERVER_ROOT = get_chroma_mcp_server_root()

def get_project_path() -> Path:
    """Pregunta al usuario la ruta del proyecto destino."""
    while True:
        try:
            project_path = input("📁 Ingresa la ruta del proyecto que quieres indexar: ").strip()
        except (UnicodeDecodeError, UnicodeError) as e:
            print(f"⚠️  Error de codificación al leer la entrada: {e}", file=sys.stderr)
            print("💡 Intenta ejecutar el script con: PYTHONIOENCODING=utf-8 python3 index-project.py", file=sys.stderr)
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
        with open(mcp_json_path, 'r') as f:
            mcp_config = json.load(f)
        return mcp_config
    except json.JSONDecodeError as e:
        print(f"❌ Error al leer {mcp_json_path}: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error al leer {mcp_json_path}: {e}", file=sys.stderr)
        sys.exit(1)

def get_chroma_tenant_from_mcp_json(mcp_config: Dict[str, Any]) -> str:
    """Extrae el valor de CHROMA_TENANT del archivo mcp.json."""
    chroma_config = mcp_config.get("mcpServers", {}).get("chroma", {})
    env_vars = chroma_config.get("env", {})
    tenant = env_vars.get("CHROMA_TENANT")
    
    if not tenant:
        print("❌ Error: No se encontró CHROMA_TENANT en la configuración de chroma en mcp.json", file=sys.stderr)
        sys.exit(1)
    
    return tenant

def read_git_exclude_patterns(project_root: Path) -> List[str]:
    """Lee los patrones de exclusión de .git/info/exclude."""
    exclude_file = project_root / ".git" / "info" / "exclude"
    patterns = []
    
    if exclude_file.exists():
        try:
            with open(exclude_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Ignorar comentarios y líneas vacías
                    if line and not line.startswith('#'):
                        patterns.append(line)
        except Exception as e:
            print(f"⚠️  Advertencia: No se pudo leer {exclude_file}: {e}", file=sys.stderr)
    
    return patterns

def matches_pattern(file_path: Path, pattern: str, project_root: Path) -> bool:
    """
    Verifica si un archivo coincide con un patrón de gitignore/exclude.
    Soporta patrones básicos de gitignore.
    """
    # Obtener la ruta relativa desde la raíz del proyecto
    try:
        rel_path = file_path.relative_to(project_root)
        rel_path_str = str(rel_path)
    except ValueError:
        # Si el archivo no está dentro del proyecto, no coincide
        return False
    
    # Normalizar separadores de ruta
    rel_path_str = rel_path_str.replace('\\', '/')
    pattern = pattern.replace('\\', '/')
    
    # Si el patrón termina con /, solo coincide con directorios
    if pattern.endswith('/'):
        if not file_path.is_dir():
            return False
        pattern = pattern[:-1]
    
    # Si el patrón comienza con /, es relativo a la raíz
    if pattern.startswith('/'):
        pattern = pattern[1:]
        return fnmatch.fnmatch(rel_path_str, pattern) or fnmatch.fnmatch(rel_path_str, pattern + '/*')
    
    # Si el patrón contiene **, expandirlo
    if '**' in pattern:
        # Convertir ** a * para fnmatch (simplificado)
        pattern = pattern.replace('**', '*')
    
    # Verificar coincidencia directa o en cualquier subdirectorio
    if fnmatch.fnmatch(rel_path_str, pattern):
        return True
    
    # Verificar si coincide en algún nivel del path
    path_parts = rel_path_str.split('/')
    for i in range(len(path_parts)):
        sub_path = '/'.join(path_parts[i:])
        if fnmatch.fnmatch(sub_path, pattern):
            return True
    
    return False

def filter_files_by_exclude(files: List[Path], project_root: Path, exclude_patterns: List[str]) -> List[Path]:
    """Filtra archivos según los patrones de exclusión."""
    filtered = []
    for file_path in files:
        should_exclude = False
        for pattern in exclude_patterns:
            if matches_pattern(file_path, pattern, project_root):
                should_exclude = True
                break
        if not should_exclude:
            filtered.append(file_path)
    return filtered

def get_all_files_in_project(project_root: Path) -> List[Path]:
    """
    Obtiene todos los archivos del proyecto usando git ls-files,
    que automáticamente respeta .gitignore.
    """
    try:
        cmd = ["git", "-C", str(project_root), "ls-files", "-z"]
        result = subprocess.run(cmd, capture_output=True, check=True, encoding="utf-8")
        
        files = []
        for file_str in result.stdout.strip("\0").split("\0"):
            if file_str:
                file_path = project_root / file_str
                if file_path.exists() and file_path.is_file():
                    files.append(file_path)
        
        return files
    except FileNotFoundError:
        print("❌ Error: 'git' command not found. Ensure Git is installed and in PATH.", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error ejecutando 'git ls-files' en {project_root}: {e}", file=sys.stderr)
        print(f"   stderr: {e.stderr}", file=sys.stderr)
        sys.exit(1)

def run_indexing(project_root: Path, tenant: str) -> int:
    """
    Ejecuta el script de indexación usando chroma-mcp-client.
    Establece CHROMA_TENANT antes de ejecutar e ignora el valor del .env.
    """
    # Obtener todos los archivos del proyecto (git ls-files ya respeta .gitignore)
    print(f"📋 Obteniendo lista de archivos del proyecto...")
    all_files_before_exclude = get_all_files_in_project(project_root)
    print(f"   Encontrados {len(all_files_before_exclude)} archivos rastreados por git")
    
    # Leer patrones de .git/info/exclude
    exclude_patterns = read_git_exclude_patterns(project_root)
    all_files = all_files_before_exclude
    if exclude_patterns:
        print(f"📋 Aplicando {len(exclude_patterns)} patrones de exclusión de .git/info/exclude...")
        all_files = filter_files_by_exclude(all_files, project_root, exclude_patterns)
        print(f"   Quedan {len(all_files)} archivos después de aplicar exclusiones")
    
    # Preparar el comando de indexación
    # Usar chroma-mcp-client desde el proyecto chroma_mcp_server
    client_script = CHROMA_MCP_SERVER_ROOT / "scripts" / "propios" / "chroma-client.sh"
    
    if not client_script.exists():
        print(f"❌ Error: No se encontró el script {client_script}", file=sys.stderr)
        sys.exit(1)
    
    # Establecer CHROMA_TENANT en el entorno (sobrescribe cualquier valor del .env)
    env = os.environ.copy()
    env['CHROMA_TENANT'] = tenant
    
    # Si hay archivos excluidos por .git/info/exclude, necesitamos indexar archivo por archivo
    # en lugar de usar --all, ya que --all no respeta .git/info/exclude
    has_exclusions = exclude_patterns and len(all_files) < len(all_files_before_exclude)
    if has_exclusions:
        print(f"\n🚀 Iniciando indexación con CHROMA_TENANT={tenant}...")
        print(f"   Proyecto: {project_root}")
        print(f"   Archivos a indexar: {len(all_files)}")
        print(f"   (Usando indexación archivo por archivo debido a exclusiones de .git/info/exclude)")
        
        # Indexar archivo por archivo
        indexed_count = 0
        for file_path in all_files:
            try:
                # Obtener ruta relativa desde la raíz del proyecto
                rel_path = file_path.relative_to(project_root)
                cmd = [str(client_script), "index", str(rel_path), "--repo-root", str(project_root)]
                result = subprocess.run(
                    cmd,
                    cwd=str(project_root),
                    env=env,
                    check=False,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    indexed_count += 1
                    if indexed_count % 10 == 0:
                        print(f"   Indexados {indexed_count}/{len(all_files)} archivos...")
                else:
                    print(f"   ⚠️  Error indexando {rel_path}: {result.stderr}", file=sys.stderr)
            except Exception as e:
                print(f"   ⚠️  Error indexando {file_path}: {e}", file=sys.stderr)
        
        print(f"\n✅ Indexación completada: {indexed_count}/{len(all_files)} archivos indexados")
        return 0 if indexed_count > 0 else 1
    else:
        # Si no hay exclusiones adicionales, usar --all que es más eficiente
        print(f"\n🚀 Iniciando indexación con CHROMA_TENANT={tenant}...")
        print(f"   Proyecto: {project_root}")
        print(f"   Archivos a indexar: {len(all_files)}")
        
        try:
            cmd = [str(client_script), "index", "--all", "--repo-root", str(project_root)]
            result = subprocess.run(
                cmd,
                cwd=str(project_root),
                env=env,
                check=False,
                capture_output=False  # Mostrar output en tiempo real
            )
            
            if result.returncode == 0:
                print(f"\n✅ Indexación completada exitosamente")
                return 0
            else:
                print(f"\n❌ Error durante la indexación (código de salida: {result.returncode})", file=sys.stderr)
                return result.returncode
                
        except Exception as e:
            print(f"❌ Error ejecutando el comando de indexación: {e}", file=sys.stderr)
            sys.exit(1)

def main():
    """Función principal."""
    print("🔍 Indexador de Proyecto para ChromaDB\n")
    
    # Preguntar la ruta del proyecto
    project_path = get_project_path()
    print(f"✅ Proyecto: {project_path}\n")
    
    # Leer mcp.json
    mcp_json_path = project_path / ".cursor" / "mcp.json"
    print(f"📖 Leyendo configuración desde {mcp_json_path}...")
    mcp_config = read_mcp_json(mcp_json_path)
    
    # Extraer CHROMA_TENANT
    tenant = get_chroma_tenant_from_mcp_json(mcp_config)
    print(f"✅ CHROMA_TENANT: {tenant}\n")
    
    # Ejecutar indexación
    exit_code = run_indexing(project_path, tenant)
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())

