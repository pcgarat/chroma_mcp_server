#!/usr/bin/env python3
"""
Script para generar reglas de Cursor en .cursor/rules basadas en las colecciones de ChromaDB.
"""
import os
import sys
from pathlib import Path
import shutil

# Obtener el directorio donde está este script
SCRIPT_DIR = Path(__file__).parent.resolve()
CURSOR_RULES_SOURCE = SCRIPT_DIR / "cursor-rules"
CURSOR_RULES_TARGET = Path(__file__).parent.parent.parent.parent / ".cursor" / "rules"
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent

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
    """Genera las reglas de Cursor en .cursor/rules."""
    print("🔄 Generando reglas de Cursor...\n")
    
    # Verificar que existe la carpeta de origen
    if not CURSOR_RULES_SOURCE.exists():
        print(f"❌ Error: No se encuentra la carpeta {CURSOR_RULES_SOURCE}")
        return 1
    
    # Crear carpeta de destino si no existe
    CURSOR_RULES_TARGET.mkdir(parents=True, exist_ok=True)
    
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
        target_file = CURSOR_RULES_TARGET / target_name
        shutil.copy2(rule_file, target_file)
        print(f"✅ Copiada: {rule_file.name} → {target_name}")
        copied_count += 1
    
    print(f"\n✅ Proceso completado. {copied_count} reglas copiadas a {CURSOR_RULES_TARGET}")
    print(f"\n📋 Colecciones disponibles para reglas específicas:")
    for collection in COLLECTIONS:
        print(f"   - {collection}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

