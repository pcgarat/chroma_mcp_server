# WARP.md

Este archivo proporciona orientación a WARP (warp.dev) al trabajar con código en este repositorio.

## Comandos Comunes de Desarrollo

### Configuración del Entorno

```bash
# Activar el entorno de desarrollo con Hatch
hatch shell

# Instalar con todas las dependencias (modelos de embedding completos)
pip install "chroma-mcp-server[full,dev]"

# Instalar versión ligera (solo embeddings por defecto)
pip install "chroma-mcp-server[client,dev]"
```

### Ejecución de Tests

```bash
# Ejecutar todos los tests (usa Python 3.10 por defecto)
hatch test

# Ejecutar tests con cobertura
hatch test --cover

# Ejecutar tests con verbose
hatch test --cover -v

# Ejecutar tests para una versión específica de Python
hatch test --python 3.10
hatch test --python 3.11
hatch test --python 3.12

# Ejecutar tests para un archivo o directorio específico
hatch test tests/tools/test_auto_log_chat_bridge.py
hatch test --cover tests/tools/

# Usando el script de tests (alternativa)
./scripts/test.sh -c -v
./scripts/test.sh -c -v --python 3.11 tests/tools/
./scripts/test.sh -c -v --auto-capture-workflow
```

**Importante:** Siempre usar `hatch test` o `./scripts/test.sh`, NUNCA ejecutar `pytest` directamente. Esto asegura que se use la matriz de Python correcta y las variables de entorno apropiadas.

### Build e Instalación

```bash
# Build del paquete
hatch run build-mcp

# Build + Reinstalar en el entorno de Hatch (requerido después de cambios)
# Reemplazar <version> con la versión actual (ej: 0.2.28)
hatch build && hatch run pip uninstall chroma-mcp-server -y && hatch run pip install 'dist/chroma_mcp_server-<version>-py3-none-any.whl[full,dev]'

# Para instalación ligera (más rápida)
hatch build && hatch run pip uninstall chroma-mcp-server -y && hatch run pip install 'dist/chroma_mcp_server-<version>-py3-none-any.whl[client,dev]'
```

**Nota crítica:** Después de cambios en el servidor MCP o componentes del cliente, DEBES rebuild y reinstalar antes de que los cambios surtan efecto. Además, el usuario debe recargar manualmente el servidor MCP en su IDE.

### Linting y Formateo

```bash
# Formatear código con black
black src/ tests/

# Ordenar imports con isort
isort src/ tests/

# Ejecutar verificación de tipos con mypy
mypy src/

# Ejecutar pylint
pylint src/
```

### Ejecutar el Servidor Localmente

```bash
# Modo efímero (en memoria)
chroma-mcp-server --client-type ephemeral

# Modo persistente
chroma-mcp-server --client-type persistent --data-dir ./my_data

# Modo de desarrollo (usando Hatch)
./scripts/run_chroma_mcp_server_dev.sh --client-type persistent --data-dir ./dev_data --log-dir ./dev_logs
```

## Arquitectura de Alto Nivel

### Estructura de Tres Paquetes

El proyecto está organizado en tres paquetes principales en `src/`:

1. **`chroma_mcp/`** - Servidor MCP principal
   - `server.py`: Implementación central del servidor MCP
   - `cli.py`: CLI para ejecutar el servidor
   - `app.py`: Instancia compartida del servidor MCP
   - `tools/`: Herramientas MCP (collection, document, thinking, auto_log_chat)
   - `utils/`: Utilidades de configuración y logging

2. **`chroma_mcp_client/`** - Cliente CLI para automatización
   - `cli.py`: CLI principal para operaciones automatizadas
   - `indexing.py`: Indexación automática del codebase
   - `analysis.py`: Análisis del historial de chat
   - `interactive_promoter.py`: Promoción interactiva de learnings
   - `scripts/`: Scripts CLI (log-chat, analyze-chat, promote-learning, etc.)
   - `validation/`: Sistema de validación basado en evidencia
   - `pytest_plugin.py`: Plugin de pytest para workflow automatizado

3. **`chroma_mcp_thinking/`** - Herramientas de pensamiento estructurado
   - Captura y recuperación de sesiones de pensamiento

### Flujo de Trabajo del "Segundo Cerebro"

Este proyecto implementa un concepto de "segundo cerebro" para desarrollo asistido por IA:

- **Indexación Automática del Código**: Los cambios de código se indexan automáticamente en ChromaDB vía hooks post-commit
- **Logging Automatizado de Chat**: Las interacciones con IA se registran con contexto enriquecido (diffs, secuencias de herramientas, scores de confianza)
- **Enlace Bidireccional**: Conecta discusiones con cambios de código para rastrear la evolución de features
- **Chunking Semántico**: Preserva estructuras lógicas de código (funciones, clases) para recuperación más significativa
- **Sistema de Validación**: Validación basada en evidencia para cambios de código y promociones de learning

### Colecciones de ChromaDB

El sistema usa colecciones específicas:

- `codebase_v1`: Código indexado con chunking semántico
- `chat_history_v1`: Log de diálogos IA-desarrollador con contexto enriquecido
- `derived_learnings_v1`: Insights curados y soluciones validadas
- `thinking_sessions_v1`: Pensamientos y razonamientos estructurados del desarrollador
- `validation_evidence_v1`: Evidencia de validación para cambios de código
- `test_results_v1`: Resultados de ejecución de tests (planificado)

### Model Context Protocol (MCP)

El servidor implementa MCP para integración con IDEs:

- **Comunicación stdio**: JSON sobre stdin/stdout para integración con IDEs
- **Logging Separado**: Los logs se redirigen a archivos para evitar contaminar el stream JSON
- **Herramientas MCP**: Expone operaciones de collection, document y thinking como herramientas MCP

### Sistema de Embedding

- Soporta múltiples funciones de embedding (default, fast, accurate, openai, cohere, etc.)
- Usa ONNX Runtime para embeddings por defecto basados en CPU
- Configuración vía `CHROMA_EMBEDDING_FUNCTION` environment variable

## Workflow de Desarrollo

### Después de Cambios de Código

1. Aplicar linting y formateo
2. Si los cambios involucran servidor MCP o componentes del cliente, rebuild y reinstalar
3. Ejecutar tests con cobertura: `hatch test --cover -v`
4. Verificar que todos los tests pasen y la cobertura sea >= 80%
5. Corregir problemas y repetir hasta que todos los tests pasen
6. Para cambios en el servidor MCP, recordar al usuario recargar manualmente el servidor MCP en su IDE

### Workflow de Test-Driven Learning Automatizado

El flag `--auto-capture-workflow` habilita el sistema automatizado:

1. Captura automáticamente fallos de test con contexto
2. Monitorea transiciones de fallo a éxito después de cambios de código
3. Crea evidencia de validación enlazando fallos, fixes e historial de chat
4. Promueve fixes de alta calidad a derived learnings

```bash
# Configurar antes del primer uso
chroma-mcp-client setup-test-workflow --workspace-dir .

# Ejecutar tests (auto-capture está habilitado por defecto)
hatch test --cover -v

# Verificar workflows completados
chroma-mcp-client check-test-transitions --workspace-dir .
```

## Notas Importantes

### Gestión de Entorno

- **Usar Hatch**: Siempre trabajar dentro del entorno Hatch (`hatch shell`)
- **Rebuild Requerido**: Después de modificar código del servidor o cliente, DEBES rebuild e reinstalar el paquete
- **Recarga Manual del IDE**: Los cambios en el servidor MCP requieren recarga manual en el IDE (no hay forma automatizada)

### Cobertura de Tests

- Mantener cobertura >= 80% en total
- Cubrir todos los paths de código relevantes para evitar errores en runtime
- Los tests están configurados con timeout de 10 segundos
- Usar `--timeout` y `-p no:xdist` (ya configurado en scripts)

### Logging

- **Modo Stdio**: Los logs van a archivos timestamped en `CHROMA_LOG_DIR` (default: `./logs/`)
- **Retención de Logs**: Configurar con `LOG_RETENTION_DAYS` (default: 7 días)
- **Niveles de Log**: `LOG_LEVEL`, `MCP_LOG_LEVEL`, `MCP_SERVER_LOG_LEVEL`

### Configuración

- Copiar `.env.template` a `.env` y ajustar configuración
- Configurar `CHROMA_CLIENT_TYPE`: ephemeral, persistent, http, cloud
- Para modo persistent, configurar `CHROMA_DATA_DIR`
- Para modo http/cloud, configurar credenciales apropiadas

### Integración con Cursor

Editar `.cursor/mcp.json` para configurar el servidor MCP:

```json
{
  "mcpServers": {
    "chroma": {
      "command": "uvx",
      "args": ["chroma-mcp-server"],
      "env": {
        "CHROMA_CLIENT_TYPE": "persistent",
        "CHROMA_DATA_DIR": "/path/to/your/data",
        "CHROMA_LOG_DIR": "/path/to/your/logs",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

## Scripts CLI del Cliente

Scripts disponibles después de instalar `[client]`:

- `log-chat`: Registrar entrada de chat con contexto enriquecido
- `analyze-chat`: Analizar historial de chat
- `promote-learning`: Crear entradas en derived_learnings
- `review-promote`: Interfaz interactiva para revisar y promover learnings
- `log-error`: Registrar errores con contexto
- `log-test`: Registrar resultados de test
- `log-quality`: Registrar métricas de calidad
- `validate-evidence`: Validar evidencia de cambios de código
- `record-thought`: Registrar pensamiento estructurado

## Reglas Específicas del Proyecto

### Al Iniciar una Nueva Sesión de Chat

- Capturar el timestamp actual del sistema cliente usando `date "+%Y-%m-%d %H:%M:%S %z"`
- Familiarizarse con la guía de build y test (docs/rules/testing-and-build-guide.md)
- Verificar qué plan markdown se está siguiendo actualmente (ver docs/refactoring/README.md)

### Reglas de Cursor Disponibles

El directorio `.cursor/rules/` contiene reglas adicionales:

- `markdown-rules.mdc`: Reglas de linting para markdown
- `python-github-rules.mdc`: Reglas de desarrollo para Python y GitHub
- `auto_log_chat.mdc`: Habilita logging automático de resúmenes de chat IA
- `memory-integration-rule.mdc`: Uso de herramientas de pensamiento secuencial
- `testing-and-build-guide.mdc`: Instrucciones completas de testing y build

### Versionado y Releases

Al preparar un release:

1. Actualizar `CHANGELOG.md` con la nueva versión e información de cambios
2. Actualizar el número de versión en `pyproject.toml`
3. Build del paquete y verificar que la versión correcta aparece en los artifacts
4. Probar la nueva versión antes de publicar

## Documentación

Documentación completa disponible en el directorio `docs/`:

- `docs/README.md`: Guía completa
- `docs/getting_started.md`: Instrucciones detalladas de configuración
- `docs/developer_guide.md`: Para contribuidores y desarrolladores
- `docs/integration/`: Guías de integración con IDEs
- `docs/usage/`: Guías detalladas sobre features específicos
- `docs/api_reference.md`: Herramientas MCP disponibles y parámetros
