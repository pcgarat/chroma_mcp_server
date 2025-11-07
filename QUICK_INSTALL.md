# Instalación Rápida de Chroma MCP Server

Esta guía te ayudará a configurar rápidamente el servidor MCP de ChromaDB en Cursor.

## Requisitos Previos

### 1. ChromaDB en Local

**IMPORTANTE:** Debes tener un servidor ChromaDB corriendo localmente e independiente antes de configurar el MCP server.

#### Opción A: Usar Docker (Recomendado)

```bash
docker run -d \
  --name chroma \
  -p 8000:8000 \
  -v chroma-data:/chroma/chroma \
  chromadb/chroma:latest
```

#### Opción B: Instalación Local

```bash
pip install chromadb
chroma run --host localhost --port 8000
```

Verifica que ChromaDB esté corriendo:

```bash
curl http://localhost:8000/api/v1/heartbeat
```

### 2. Configurar MCP en Cursor

Añade la siguiente configuración a tu archivo `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "chroma": {
      "command": "uvx",
      "args": [
        "--python",
        "3.12",
        "chroma-mcp-server[full]"
      ],
      "env": {
        "CHROMA_CLIENT_TYPE": "http",
        "CHROMA_HOST": "localhost",
        "CHROMA_PORT": "8000",
        "CHROMA_SSL": "false",
        "CHROMA_API_KEY": "your-chroma-api-key-here",
        "CHROMA_LOG_DIR": "/home/pacogarat/projects/symfony/memory/logs",
        "LOG_LEVEL": "INFO",
        "MCP_LOG_LEVEL": "INFO",
        "MCP_SERVER_LOG_LEVEL": "INFO",
        "PROJECT_NAME": "symfony",
        "CHROMA_EMBEDDING_FUNCTION": "openai",
        "OPENAI_API_KEY": "your-openai-api-key-here",
        "CHROMA_OPENAI_EMBEDDING_MODEL": "text-embedding-3-small",
        "CHROMA_DISTANCE_METRIC": "cosine",
        "CHROMA_COLLECTION_METADATA": "{\"hnsw:space\": \"cosine\"}",
        "CHROMA_ISOLATION_LEVEL": "read_committed",
        "CHROMA_ALLOW_RESET": "true"
      }
    }
  }
}
```

### 3. Personalizar la Configuración

Ajusta los siguientes valores según tu entorno:

- **`CHROMA_HOST`**: Dirección del servidor ChromaDB (por defecto: `localhost`)
- **`CHROMA_PORT`**: Puerto del servidor ChromaDB (por defecto: `8000`)
- **`CHROMA_API_KEY`**: Token de autenticación de ChromaDB (ajusta según tu configuración)
- **`CHROMA_LOG_DIR`**: Directorio donde se guardarán los logs (ajusta la ruta)
- **`PROJECT_NAME`**: Nombre de tu proyecto
- **`OPENAI_API_KEY`**: Tu clave de API de OpenAI (necesaria si usas `openai` como embedding function)
- **`CHROMA_OPENAI_EMBEDDING_MODEL`**: Modelo de embedding de OpenAI a usar:
  - `text-embedding-ada-002` (por defecto, más económico)
  - `text-embedding-3-small` (recomendado, balanceado)
  - `text-embedding-3-large` (mayor precisión)

### 4. Reiniciar Cursor

Después de añadir la configuración, **reinicia Cursor** para que cargue el nuevo servidor MCP.

## Verificación

Una vez reiniciado Cursor, deberías poder:

1. Ver el servidor `chroma` en la lista de servidores MCP
2. Usar las herramientas de ChromaDB desde el chat de Cursor
3. Verificar la conexión consultando colecciones

## Solución de Problemas

### Error: "Could not connect to Chroma server"

- Verifica que ChromaDB esté corriendo: `curl http://localhost:8000/api/v1/heartbeat`
- Comprueba que `CHROMA_HOST` y `CHROMA_PORT` sean correctos
- Verifica que `CHROMA_API_KEY` sea válido

### Error: "Dependency potentially missing for embedding function 'openai'"

- Asegúrate de tener `chroma-mcp-server[full]` instalado
- Verifica que `OPENAI_API_KEY` esté configurado correctamente

### El servidor MCP no aparece en Cursor

- Verifica que el archivo `mcp.json` esté en `.cursor/mcp.json` (raíz del proyecto)
- Reinicia Cursor completamente
- Revisa los logs en `CHROMA_LOG_DIR` para ver errores

## Próximos Pasos

Una vez configurado, puedes:

1. **Inicializar colecciones:**
   ```bash
   ./chroma_mcp_server/scripts/chroma-client-uvx.sh setup-collections
   ```

2. **Indexar tu código:**
   ```bash
   ./chroma_mcp_server/scripts/chroma-client-uvx.sh index --all
   ```

3. **Consultar el código indexado:**
   ```bash
   ./chroma_mcp_server/scripts/chroma-client-uvx.sh query "tu consulta" -n 5
   ```

Para más información, consulta la [documentación completa](docs/README.md).

