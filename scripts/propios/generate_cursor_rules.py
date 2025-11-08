#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para generar reglas de Cursor en .cursor/rules basadas en las colecciones de ChromaDB.
"""
import os
import sys
import argparse
from pathlib import Path
from typing import Optional
import shutil

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
            project_path = input("📁 Ingresa la ruta del proyecto donde quieres generar las reglas de Cursor: ").strip()
        except UnicodeError as e:
            print(f"⚠️  Error de codificación al leer la entrada: {e}", file=sys.stderr)
            print("💡 Intenta ejecutar el script con: PYTHONIOENCODING=utf-8 python3 generate_cursor_rules.py", file=sys.stderr)
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

# Obtener el directorio donde está este script
SCRIPT_DIR = Path(__file__).parent.resolve()
# Obtener la raíz del proyecto chroma_mcp_server dinámicamente (para encontrar cursor-rules)
CHROMA_MCP_SERVER_ROOT = get_chroma_mcp_server_root()
CURSOR_RULES_SOURCE = SCRIPT_DIR / "cursor-rules"

# Colecciones de ChromaDB según reset_collections.py
COLLECTIONS = [
    "codebase_v1",
    "chat_history_v1",
    "derived_learnings_v1",
    "thinking_sessions_v1",
    "validation_evidence_v1",
    "test_results_v1"
]

def main():
    """Genera las reglas de Cursor en .cursor/rules del proyecto especificado."""
    parser = argparse.ArgumentParser(
        description="Genera reglas de Cursor en .cursor/rules basadas en las colecciones de ChromaDB.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--project-path",
        type=str,
        help="Ruta del proyecto donde generar las reglas (si no se proporciona, se pregunta interactivamente)"
    )
    
    args = parser.parse_args()
    
    print("🔄 Generador de Reglas de Cursor para ChromaDB\n")
    
    # Obtener la ruta del proyecto destino
    project_path = get_project_path(args.project_path)
    print(f"✅ Proyecto: {project_path}\n")
    
    # Definir la carpeta de destino en el proyecto especificado
    cursor_rules_target = project_path / ".cursor" / "rules"
    
    # Verificar que existe la carpeta de origen
    if not CURSOR_RULES_SOURCE.exists():
        print(f"❌ Error: No se encuentra la carpeta {CURSOR_RULES_SOURCE}", file=sys.stderr)
        return 1
    
    # Crear carpeta de destino si no existe
    cursor_rules_target.mkdir(parents=True, exist_ok=True)
    print(f"📁 Directorio de destino: {cursor_rules_target}\n")
    
    # Reglas específicas del proyecto que NO deben ser generadas por el script
    EXCLUDED_RULES = [
        "chroma-mcp.mdc",  # Regla específica del proyecto
        "autobiz.mdc",     # Regla específica del AutobizBundle
    ]
    
    # Solo generar reglas optimizadas (que usan los nombres correctos de colecciones)
    # Las reglas originales tienen nombres de colecciones incorrectos (symfony_codebase, etc.)
    OPTIMIZED_RULES = [
        "main_memory_rule_optimized.mdc",
        "auto_log_chat_optimized.mdc",
        "workflow_optimized.mdc",
        "thinking_sessions.mdc",        # Regla específica para Thinking Sessions
        "derived_learnings.mdc",        # Regla específica para Derived Learnings workflow
        "validation_evidence.mdc",       # Regla específica para Validation Evidence
        "debug_assist.mdc",             # Regla específica para Debug Assist (búsqueda proactiva de soluciones)
        "daily_workflow.mdc",           # Regla específica para Daily Workflow Integration
    ]
    
    # Copiar solo las reglas optimizadas a .cursor/rules (renombradas sin _optimized)
    copied_count = 0
    for rule_file in CURSOR_RULES_SOURCE.glob("*.mdc"):
        # Saltar reglas excluidas
        if rule_file.name in EXCLUDED_RULES:
            print(f"⏭️  Omitida (específica del proyecto): {rule_file.name}")
            continue
        
        # Solo procesar reglas optimizadas
        if rule_file.name not in OPTIMIZED_RULES:
            print(f"⏭️  Omitida (regla original con nombres incorrectos): {rule_file.name}")
            continue
        
        # Renombrar quitando _optimized del nombre
        target_name = rule_file.name.replace("_optimized", "")
        target_file = cursor_rules_target / target_name
        shutil.copy2(rule_file, target_file)
        print(f"✅ Copiada: {rule_file.name} → {target_name}")
        copied_count += 1
    
    print(f"\n✅ Proceso completado. {copied_count} reglas copiadas a {cursor_rules_target}")
    print(f"\n📋 Colecciones disponibles para reglas específicas:")
    for collection in COLLECTIONS:
        print(f"   - {collection}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

