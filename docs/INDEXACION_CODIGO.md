# Guía de Indexación de Código con chroma-mcp-client

Esta guía explica cómo indexar el código del proyecto Symfony excluyendo carpetas innecesarias.

## Pasos para Indexar el Código

### 1. Configurar Variables de Entorno

**IMPORTANTE:** Si ya tienes un `.env` del proyecto y no quieres mezclarlo con la configuración de ChromaDB, tienes varias opciones:

#### Opción A: Usar Script de Configuración (Recomendada)

Usa el script `setup-chroma-env.sh` que exporta todas las variables necesarias:

```bash
# Exportar variables en tu sesión actual
source ./chroma_mcp_server/scripts/setup-chroma-env.sh

# Ahora puedes ejecutar comandos normalmente
chroma-mcp-client setup-collections
chroma-mcp-client index --all
```

O ejecutar comandos directamente con el script:

```bash
./chroma_mcp_server/scripts/setup-chroma-env.sh setup-collections
./chroma_mcp_server/scripts/setup-chroma-env.sh index --all
```

**Alternativa:** Si prefieres pasar las variables manualmente en la línea de comandos:

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

#### Opción B: Usar un Archivo .env Separado

Crea un archivo `.env.chroma` o en otra ubicación (por ejemplo `~/.config/chroma-mcp/.env`) y usa un script wrapper. Ver [CONFIGURACION_ENV.md](CONFIGURACION_ENV.md) para más detalles.

#### Opción C: Crear archivo `.env` en la raíz del proyecto

Si prefieres usar el `.env` estándar, crea un archivo `.env` en la raíz del proyecto con la configuración de ChromaDB. Basándote en tu configuración de `mcp.json`, el archivo `.env` debería contener:

```bash
# Configuración de ChromaDB para chroma-mcp-client
CHROMA_CLIENT_TYPE=http
CHROMA_HOST=localhost
CHROMA_PORT=8000
CHROMA_SSL=false
CHROMA_API_KEY=your-chroma-api-key-here

# Función de embedding
CHROMA_EMBEDDING_FUNCTION=openai
OPENAI_API_KEY=your-openai-api-key-here

# Directorio de logs
CHROMA_LOG_DIR=/home/pacogarat/projects/symfony/memory/logs

# Niveles de logging
LOG_LEVEL=INFO
MCP_LOG_LEVEL=INFO
MCP_SERVER_LOG_LEVEL=INFO

# Configuración adicional
PROJECT_NAME=symfony
CHROMA_DISTANCE_METRIC=cosine
CHROMA_COLLECTION_METADATA={"hnsw:space": "cosine"}
CHROMA_ISOLATION_LEVEL=read_committed
CHROMA_ALLOW_RESET=true
```

### 2. Inicializar las Colecciones

Antes de indexar, es recomendable inicializar las colecciones necesarias:

```bash
chroma-mcp-client setup-collections
```

Este comando crea las siguientes colecciones si no existen:
- `codebase_v1` - Para el código indexado
- `chat_history_v1` - Para el historial de chats
- `derived_learnings_v1` - Para aprendizajes derivados
- `thinking_sessions_v1` - Para sesiones de pensamiento
- `validation_evidence_v1` - Para evidencia de validación
- `test_results_v1` - Para resultados de tests

### 3. Indexar el Código

El comando `index --all` automáticamente respeta el archivo `.gitignore`, por lo que las siguientes carpetas ya están excluidas:

- `/vendor/` - Dependencias de Composer
- `/node_modules/` - Dependencias de Node.js
- `/var/` - Archivos temporales de Symfony
- `/public/bundles/` - Bundles compilados
- `/public/ao-assets/` - Assets compilados
- `/logs/` - Archivos de log
- `/.cursor/` - Configuración de Cursor
- `/.idea/` - Configuración de JetBrains
- Y todas las demás carpetas especificadas en `.gitignore`

Para indexar todo el código rastreado por Git:

```bash
chroma-mcp-client index --all
```

**Nota importante:** El comando `index --all` solo indexa archivos que están rastreados por Git y que NO están en `.gitignore`. Esto significa que:

- ✅ Se indexan: `src/`, `config/`, `tests/`, `templates/`, etc.
- ❌ NO se indexan: `vendor/`, `node_modules/`, `var/`, `logs/`, etc.

### 4. Verificar el Indexado

Para ver cuántos documentos se han indexado:

```bash
chroma-mcp-client count --collection-name codebase_v1
```

### 5. Probar una Consulta

Para verificar que el indexado funciona correctamente:

```bash
chroma-mcp-client query "autenticación de usuarios" --collection-name codebase_v1 -n 5
```

## Exclusión Automática de Carpetas

El sistema respeta automáticamente `.gitignore`, por lo que las siguientes carpetas están excluidas:

### Carpetas Excluidas por `.gitignore`:

- `vendor/` - Dependencias de Composer
- `node_modules/` - Dependencias de Node.js
- `var/` - Archivos temporales y caché de Symfony
- `public/bundles/` - Bundles compilados
- `public/ao-assets/` - Assets compilados
- `public/js/`, `public/css/` - Assets compilados
- `logs/` - Archivos de log
- `.cursor/` - Configuración de Cursor
- `.idea/` - Configuración de JetBrains
- `.vscode/` - Configuración de VS Code
- `coverage/` - Cobertura de tests
- Y cualquier otra carpeta especificada en `.gitignore`

### Tipos de Archivos Soportados

El indexado solo procesa archivos con las siguientes extensiones:

- Código: `.py`, `.js`, `.ts`, `.php`, `.java`, `.go`, `.rb`, `.c`, `.cpp`, `.cs`
- Configuración: `.yaml`, `.json`, `.toml`, `.ini`, `.cfg`
- Documentación: `.md`, `.txt`
- Scripts: `.sh`
- Docker: `Dockerfile`, `.dockerfile`
- SQL: `.sql`

## Comandos Útiles

### Indexar un archivo específico

```bash
chroma-mcp-client index ./src/MiClase.php
```

### Indexar una carpeta específica

```bash
chroma-mcp-client index ./src/
```

### Consultar el código indexado

```bash
chroma-mcp-client query "cómo funciona la autenticación" -n 10
```

### Ver estadísticas

```bash
chroma-mcp-client count --collection-name codebase_v1
```

## Solución de Problemas

### Error: "Collection does not exist"

Ejecuta primero:
```bash
chroma-mcp-client setup-collections
```

### Error: "Could not connect to Chroma server"

Verifica que:
1. El servidor Chroma está corriendo en `localhost:8000`
2. El archivo `.env` tiene la configuración correcta
3. El `CHROMA_API_KEY` es correcto

### Error: "Embedding function name mismatch"

Si cambias la función de embedding, actualiza la colección:

```bash
chroma-mcp-client update-collection-ef --collection-name codebase_v1 --ef-name sentence_transformer
```

## Resumen

1. ✅ Crear `.env` con la configuración de ChromaDB
2. ✅ Ejecutar `setup-collections` para inicializar colecciones
3. ✅ Ejecutar `index --all` para indexar todo el código (respeta `.gitignore` automáticamente)
4. ✅ Verificar con `count` y `query`

**No necesitas configurar exclusiones manualmente** - el sistema respeta `.gitignore` automáticamente.

