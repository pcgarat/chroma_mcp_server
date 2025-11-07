# Configuración de Variables de Entorno para chroma-mcp-client

Si no quieres mezclar las variables de entorno de ChromaDB con el `.env` del proyecto, tienes varias opciones:

## Opción 1: Pasar Variables Directamente en la Línea de Comandos (Recomendada)

Puedes pasar las variables de entorno directamente antes del comando:

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

O exportarlas en tu sesión de terminal:

```bash
export CHROMA_CLIENT_TYPE=http
export CHROMA_HOST=localhost
export CHROMA_PORT=8000
export CHROMA_SSL=false
export CHROMA_API_KEY=your-chroma-api-key-here
export CHROMA_EMBEDDING_FUNCTION=openai
export OPENAI_API_KEY=your-openai-api-key-here

# Ahora puedes ejecutar los comandos normalmente
chroma-mcp-client setup-collections
chroma-mcp-client index --all
```

## Opción 2: Usar un Archivo .env Separado con Script Wrapper

### Paso 1: Crear un archivo `.env` separado para ChromaDB

Crea un archivo en una ubicación separada, por ejemplo:

```bash
mkdir -p ~/.config/chroma-mcp
cat > ~/.config/chroma-mcp/.env << 'EOF'
CHROMA_CLIENT_TYPE=http
CHROMA_HOST=localhost
CHROMA_PORT=8000
CHROMA_SSL=false
CHROMA_API_KEY=your-chroma-api-key-here
CHROMA_EMBEDDING_FUNCTION=openai
OPENAI_API_KEY=your-openai-api-key-here
CHROMA_LOG_DIR=/home/pacogarat/projects/symfony/memory/logs
LOG_LEVEL=INFO
MCP_LOG_LEVEL=INFO
MCP_SERVER_LOG_LEVEL=INFO
PROJECT_NAME=symfony
CHROMA_DISTANCE_METRIC=cosine
CHROMA_COLLECTION_METADATA={"hnsw:space": "cosine"}
CHROMA_ISOLATION_LEVEL=read_committed
CHROMA_ALLOW_RESET=true
EOF
```

### Paso 2: Crear un script wrapper

Crea un script `chroma-client` en tu `PATH` o en un directorio local:

```bash
#!/bin/bash
# Wrapper para chroma-mcp-client que carga variables desde archivo separado

CHROMA_ENV_FILE="${CHROMA_ENV_FILE:-$HOME/.config/chroma-mcp/.env}"

if [ -f "$CHROMA_ENV_FILE" ]; then
    set -a
    source "$CHROMA_ENV_FILE"
    set +a
fi

exec chroma-mcp-client "$@"
```

### Paso 3: Hacer el script ejecutable y usarlo

```bash
chmod +x chroma-client
./chroma-client setup-collections
./chroma-client index --all
```

## Opción 3: Usar un Alias con source

Puedes crear un alias en tu `.bashrc` o `.zshrc`:

```bash
alias chroma-client='source ~/.config/chroma-mcp/.env && chroma-mcp-client'
```

Luego úsalo normalmente:

```bash
chroma-client setup-collections
chroma-client index --all
```

## Opción 4: Crear un Archivo .env.chroma en el Proyecto

Si prefieres tener el archivo en el proyecto pero con otro nombre:

```bash
# Crear .env.chroma en la raíz del proyecto
cat > .env.chroma << 'EOF'
CHROMA_CLIENT_TYPE=http
# ... resto de variables
EOF
```

Y usar un script wrapper local:

```bash
#!/bin/bash
set -a
source .env.chroma
set +a
exec chroma-mcp-client "$@"
```

## Variables de Entorno Necesarias

Basándote en tu configuración de `mcp.json`, necesitas estas variables:

```bash
CHROMA_CLIENT_TYPE=http
CHROMA_HOST=localhost
CHROMA_PORT=8000
CHROMA_SSL=false
CHROMA_API_KEY=your-chroma-api-key-here
CHROMA_EMBEDDING_FUNCTION=openai
OPENAI_API_KEY=your-openai-api-key-here
CHROMA_LOG_DIR=/home/pacogarat/projects/symfony/memory/logs
LOG_LEVEL=INFO
MCP_LOG_LEVEL=INFO
MCP_SERVER_LOG_LEVEL=INFO
PROJECT_NAME=symfony
CHROMA_DISTANCE_METRIC=cosine
CHROMA_COLLECTION_METADATA={"hnsw:space": "cosine"}
CHROMA_ISOLATION_LEVEL=read_committed
CHROMA_ALLOW_RESET=true
```

## Recomendación

**Opción 1 (variables directas)** es la más simple y no requiere archivos adicionales. Si usas ChromaDB frecuentemente, **Opción 2 (archivo separado + wrapper)** es más conveniente a largo plazo.

