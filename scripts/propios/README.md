# Scripts de Utilidad para chroma-mcp-client

## Comportamiento de los Scripts

**Todos los scripts propios cargan automáticamente `setup-chroma-env.sh` antes de ejecutarse**, por lo que no necesitas hacerlo explícitamente. Los scripts que cargan automáticamente las variables son:

- `reset-collections.sh` - Carga automáticamente `setup-chroma-env.sh`
- `chroma-client-uvx.sh` - Carga automáticamente `setup-chroma-env.sh`
- `chroma-client.sh` - Carga automáticamente `setup-chroma-env.sh` (y opcionalmente un `.env` adicional)

## setup-chroma-env.sh

Script para configurar las variables de entorno de ChromaDB cargándolas desde un archivo `.env` en la raíz de `chroma_mcp_server`.

### Configuración Inicial

**Primera vez:** Copia el archivo `env-template` a `.env` en la raíz de `chroma_mcp_server`:

```bash
cd chroma_mcp_server
cp scripts/propios/env-template .env
```

Luego edita el archivo `.env` con tus valores específicos (API keys, rutas, etc.).

### Uso

#### Opción 1: Exportar variables en tu sesión actual

```bash
source ./chroma_mcp_server/scripts/propios/setup-chroma-env.sh
```

Después de esto, puedes ejecutar comandos normalmente:

```bash
chroma-mcp-client setup-collections
chroma-mcp-client index --all
chroma-mcp-client count --collection-name codebase_v1
```

#### Opción 2: Ejecutar comandos directamente

```bash
./chroma_mcp_server/scripts/propios/setup-chroma-env.sh setup-collections
./chroma_mcp_server/scripts/propios/setup-chroma-env.sh index --all
./chroma_mcp_server/scripts/propios/setup-chroma-env.sh count --collection-name codebase_v1
```

#### Opción 3: Pasar variables directamente en la línea de comandos

```bash
CHROMA_CLIENT_TYPE=http \
CHROMA_HOST=localhost \
CHROMA_PORT=8000 \
CHROMA_SSL=false \
CHROMA_API_KEY=your-chroma-api-key-here \
CHROMA_EMBEDDING_FUNCTION=openai \
OPENAI_API_KEY=your-openai-api-key-here \
chroma-mcp-client setup-collections
```

### Configuración

El script carga las variables de entorno desde el archivo `.env` en la raíz de `chroma_mcp_server`. Si necesitas cambiar los valores, edita el archivo `.env` (no el script).

**Nota:** El archivo `.env` no debe ser versionado en Git (debe estar en `.gitignore`). El archivo `env-template` es el template que puedes versionar.

## reset-collections.sh

Script para borrar todas las colecciones de ChromaDB y recrearlas desde cero.

### Uso

```bash
./chroma_mcp_server/scripts/propios/reset-collections.sh
```

Este script:
1. Borra todas las colecciones existentes (codebase_v1, chat_history_v1, derived_learnings_v1, thinking_sessions_v1, validation_evidence_v1, test_results_v1)
2. Recrea todas las colecciones vacías usando `setup-collections`

**⚠️ Advertencia:** Este script borra **todos los datos** de las colecciones. Úsalo solo si estás seguro de que quieres empezar desde cero.

### Ejemplos Completos

```bash
# Opción A: Usar los scripts propios (cargarán automáticamente setup-chroma-env.sh)
# 1. Inicializar colecciones usando el wrapper
./chroma_mcp_server/scripts/propios/chroma-client-uvx.sh setup-collections

# 2. Indexar código
./chroma_mcp_server/scripts/propios/chroma-client-uvx.sh index --all

# 3. Verificar cuántos documentos se indexaron
./chroma_mcp_server/scripts/propios/chroma-client-uvx.sh count --collection-name codebase_v1

# 4. Hacer una consulta
./chroma_mcp_server/scripts/propios/chroma-client-uvx.sh query "autenticación de usuarios" -n 5

# 5. Resetear todas las colecciones (borrar y recrear)
./chroma_mcp_server/scripts/propios/reset-collections.sh

# Opción B: Cargar variables manualmente y usar chroma-mcp-client directamente
# 1. Exportar variables en tu sesión actual
source ./chroma_mcp_server/scripts/propios/setup-chroma-env.sh

# 2. Ahora puedes usar chroma-mcp-client directamente
chroma-mcp-client setup-collections
chroma-mcp-client index --all
chroma-mcp-client count --collection-name codebase_v1
```

