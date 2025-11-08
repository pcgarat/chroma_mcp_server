#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para configurar completamente un proyecto con ChromaDB MCP Server.
Ejecuta todas las configuraciones necesarias en secuencia.
"""
import os
import sys
import subprocess
from pathlib import Path
from typing import Optional

# Configurar codificación UTF-8 para stdin/stdout/stderr
# Asegurar que PYTHONIOENCODING esté configurado antes de cualquier operación
os.environ['PYTHONIOENCODING'] = 'utf-8'

if sys.version_info >= (3, 7):
    try:
        # Intentar reconfigurar los streams con manejo de errores
        if sys.stdin.isatty():
            sys.stdin.reconfigure(encoding='utf-8', errors='replace')
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except (AttributeError, ValueError, OSError):
        # Si falla, al menos tenemos PYTHONIOENCODING configurado
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

def safe_input(prompt: str) -> str:
    """Lee entrada del usuario con manejo robusto de codificación UTF-8."""
    try:
        # Intentar usar input() normal primero (más compatible)
        return input(prompt).strip()
    except (UnicodeError, UnicodeDecodeError):
        # Si falla, usar readline() directamente
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

def get_project_path() -> Path:
    """Pregunta al usuario la ruta del proyecto destino."""
    while True:
        try:
            project_path = safe_input("📁 Ingresa la ruta del proyecto a configurar: ")
                
        except (UnicodeError, UnicodeDecodeError) as e:
            print(f"\n⚠️  Error de codificación al leer la entrada: {e}", file=sys.stderr)
            print("💡 Asegúrate de que tu terminal esté configurado con UTF-8", file=sys.stderr)
            print("💡 O ejecuta: export PYTHONIOENCODING=utf-8", file=sys.stderr)
            sys.exit(1)
        except (EOFError, KeyboardInterrupt):
            print("\n⚠️  Operación cancelada.", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"\n⚠️  Error inesperado al leer entrada: {e}", file=sys.stderr)
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

def check_env_exists(chroma_mcp_server_root: Path) -> bool:
    """Verifica si existe el archivo .env en chroma_mcp_server."""
    env_file = chroma_mcp_server_root / ".env"
    return env_file.exists()

def create_env_from_template(chroma_mcp_server_root: Path) -> bool:
    """Crea el archivo .env desde el template si existe."""
    env_file = chroma_mcp_server_root / ".env"
    template_file = chroma_mcp_server_root / "scripts" / "propios" / "env-template"
    
    if template_file.exists():
        try:
            import shutil
            shutil.copy(template_file, env_file)
            print(f"✅ Archivo .env creado desde template en {env_file}")
            print("⚠️  IMPORTANTE: Edita el archivo .env con tus valores antes de continuar.")
            try:
                response = safe_input("¿Has editado el archivo .env con tus valores? (s/N): ").lower()
            except (UnicodeError, UnicodeDecodeError, EOFError, KeyboardInterrupt):
                response = 'n'
            
            if response not in ['s', 'sí', 'si', 'y', 'yes']:
                print("❌ Por favor, edita el archivo .env y vuelve a ejecutar setup-all.")
                return False
            return True
        except Exception as e:
            print(f"❌ Error al crear .env desde template: {e}", file=sys.stderr)
            return False
    else:
        print(f"❌ No se encontró el template en {template_file}", file=sys.stderr)
        print(f"💡 Crea manualmente el archivo .env en {chroma_mcp_server_root}")
        return False

def run_script_interactive(script_path: Path, args: Optional[list[str]] = None, cwd: Optional[Path] = None) -> bool:
    """Ejecuta un script Python de forma interactiva (el usuario interactúa directamente)."""
    try:
        cmd = [sys.executable, str(script_path)]
        if args:
            cmd.extend(args)
        
        # Ejecutar el script directamente, permitiendo interacción del usuario
        result = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            timeout=600  # 10 minutos para scripts interactivos
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"❌ Timeout ejecutando {script_path.name}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"❌ Error ejecutando {script_path.name}: {e}", file=sys.stderr)
        return False

def run_make_command(command: str, chroma_mcp_server_root: Path) -> bool:
    """Ejecuta una orden del Makefile."""
    try:
        result = subprocess.run(
            ['make', command],
            cwd=str(chroma_mcp_server_root),
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=300
        )
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"❌ Timeout ejecutando make {command}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"❌ Error ejecutando make {command}: {e}", file=sys.stderr)
        return False

def main():
    """Función principal."""
    print("🚀 Configurador Completo de Proyecto para ChromaDB MCP Server\n")
    
    # Obtener rutas
    chroma_mcp_server_root = get_chroma_mcp_server_root()
    scripts_dir = chroma_mcp_server_root / "scripts" / "propios"
    
    print(f"📦 Chroma MCP Server: {chroma_mcp_server_root}\n")
    
    # 1. Preguntar path del proyecto una vez
    project_path = get_project_path()
    print(f"✅ Proyecto destino: {project_path}\n")
    
    # 2. check-env (solo para crear el mcp.json, no para los demás comandos)
    print("=" * 60)
    print("1️⃣  Verificando archivo .env...")
    print("=" * 60)
    env_exists = check_env_exists(chroma_mcp_server_root)
    
    if not env_exists:
        print("⚠️  Archivo .env no encontrado.")
        # 3. setup-env (crear desde template)
        print("\n" + "=" * 60)
        print("2️⃣  Creando archivo .env desde template...")
        print("=" * 60)
        if not create_env_from_template(chroma_mcp_server_root):
            print("❌ No se pudo crear el archivo .env. Abortando.")
            return 1
    else:
        print(f"✅ Archivo .env encontrado en {chroma_mcp_server_root / '.env'}")
    
    # 4. setup-mcp-config (PRIMERO - crea el mcp.json del proyecto)
    print("\n" + "=" * 60)
    print("3️⃣  Configurando servidor MCP de ChromaDB...")
    print("=" * 60)
    print("💡 Se ejecutará setup-mcp-config.")
    print(f"   Proyecto: {project_path}")
    print("   Se te pedirá el tenant.")
    print("   ⚠️  IMPORTANTE: Este paso crea el .cursor/mcp.json del proyecto.")
    print("   Todos los demás comandos leerán la configuración de ese archivo.\n")
    setup_mcp_config_script = scripts_dir / "setup-mcp-config.py"
    # Pasar el project-path como argumento, pero dejar que pregunte el tenant
    if not run_script_interactive(setup_mcp_config_script, ["--project-path", str(project_path)]):
        print("❌ Error en setup-mcp-config. Abortando.")
        return 1
    
    # Verificar que el mcp.json se creó correctamente
    mcp_json_path = project_path / '.cursor' / 'mcp.json'
    if not mcp_json_path.exists():
        print(f"❌ El archivo {mcp_json_path} no se creó correctamente. Abortando.")
        return 1
    print(f"✅ Archivo {mcp_json_path} creado correctamente.\n")
    
    # 5. reset-collections
    print("\n" + "=" * 60)
    print("4️⃣  Reseteando colecciones de ChromaDB...")
    print("=" * 60)
    print(f"💡 Proyecto: {project_path}\n")
    reset_collections_script = scripts_dir / "reset_collections.py"
    if not run_script_interactive(reset_collections_script, ["--project-path", str(project_path)]):
        print("❌ Error en reset-collections. Continuando de todas formas...")
    
    # 6. generate-cursor-rules
    print("\n" + "=" * 60)
    print("5️⃣  Generando reglas de Cursor...")
    print("=" * 60)
    print(f"💡 Proyecto: {project_path}\n")
    generate_rules_script = scripts_dir / "generate_cursor_rules.py"
    if not run_script_interactive(generate_rules_script, ["--project-path", str(project_path)]):
        print("❌ Error en generate-cursor-rules. Continuando de todas formas...")
    
    # 7. setup-git-hook
    print("\n" + "=" * 60)
    print("6️⃣  Configurando hook de Git...")
    print("=" * 60)
    print(f"💡 Proyecto: {project_path}\n")
    setup_git_hook_script = scripts_dir / "setup-git-hook.py"
    # Pasar --force para sobrescribir si ya existe
    if not run_script_interactive(setup_git_hook_script, ["--project-path", str(project_path), "--force"]):
        print("❌ Error en setup-git-hook. Continuando de todas formas...")
    
    # 8. Preguntar si indexar
    print("\n" + "=" * 60)
    print("7️⃣  Indexación del código del proyecto")
    print("=" * 60)
    try:
        response = safe_input("¿Deseas indexar el código del proyecto ahora? (s/N): ").lower()
    except (UnicodeError, UnicodeDecodeError, EOFError) as e:
        print(f"\n⚠️  Error de codificación: {e}", file=sys.stderr)
        response = 'n'
    except KeyboardInterrupt:
        print("\n⚠️  Operación cancelada. Omitiendo indexación.", file=sys.stderr)
        response = 'n'
    
    if response in ['s', 'sí', 'si', 'y', 'yes']:
        print("\n📚 Indexando proyecto...")
        print(f"💡 Proyecto: {project_path}\n")
        index_project_script = scripts_dir / "index-project.py"
        if not run_script_interactive(index_project_script, ["--project-path", str(project_path)]):
            print("❌ Error en index-project.")
            return 1
    else:
        print("⏭️  Indexación omitida. Puedes ejecutarla más tarde con: make index-project")
    
    print("\n" + "=" * 60)
    print("✅ ¡Configuración completada!")
    print("=" * 60)
    print("\n📋 Resumen:")
    print(f"   - Proyecto: {project_path}")
    mcp_json_path = project_path / '.cursor' / 'mcp.json'
    hook_path = project_path / '.git' / 'hooks' / 'post-commit'
    print(f"   - Configuración MCP: {mcp_json_path}")
    print(f"   - Hook de Git: {hook_path}")
    print("\n💡 Próximos pasos:")
    print(f"   - Verifica la configuración en {mcp_json_path}")
    print("   - Si no indexaste, ejecuta: make index-project")
    print("   - El hook de Git indexará automáticamente los cambios en cada commit")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

