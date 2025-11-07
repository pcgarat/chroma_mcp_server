#!/bin/bash
# Script wrapper para resetear colecciones de ChromaDB
# Usa reset_collections.py internamente que borra documentos y colecciones, y luego las recrea

# Cargar variables de entorno
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/setup-chroma-env.sh"

# Ejecutar el script Python que hace todo el trabajo
# (borra documentos, borra colecciones y las recrea)
python3 "$SCRIPT_DIR/reset_collections.py"

