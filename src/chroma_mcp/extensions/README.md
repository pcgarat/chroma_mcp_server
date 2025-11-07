# Extensiones Personalizadas

Este directorio contiene funcionalidad personalizada que se integra con el código base sin modificar el código core, facilitando la actualización del fork con el repositorio original.

## Estructura

```
extensions/
├── __init__.py              # Exporta las funciones principales
├── database_manager.py       # Gestión automática de bases de datos
├── config_loader.py          # Cargador de configuración mejorado
└── README.md                 # Este archivo
```

## Funcionalidad

### `database_manager.py`

Proporciona funciones para verificar y crear automáticamente bases de datos cuando se usa el cliente HTTP:

- `ensure_database_exists()`: Verifica si la base de datos existe y la crea si no existe
- `verify_database_access()`: Verifica que se puede acceder a la base de datos

### `config_loader.py`

Carga todas las configuraciones desde variables de entorno:

- `load_custom_config()`: Carga configuración completa desde variables de entorno
- `get_enhanced_client_config()`: Obtiene configuración del cliente mejorada

## Integración con el Código Core

Las extensiones se integran en el código core mediante llamadas opcionales en puntos estratégicos:

1. **Inicialización del cliente HTTP** (`server.py`):
   - Se llama a `ensure_database_exists()` antes de crear el cliente HTTP
   - Si las extensiones no están disponibles, el código continúa normalmente

2. **Configuración de embeddings** (`chroma_client.py`):
   - Las configuraciones se leen directamente de variables de entorno
   - No requiere modificación del código core

## Variables de Entorno Soportadas

Todas las variables de entorno definidas en `.cursor/mcp.json` son soportadas:

### Cliente
- `CHROMA_CLIENT_TYPE`: Tipo de cliente (http, cloud, persistent, ephemeral)
- `CHROMA_HOST`: Host del servidor ChromaDB
- `CHROMA_PORT`: Puerto del servidor ChromaDB
- `CHROMA_SSL`: Si se usa SSL (true/false)
- `CHROMA_TENANT`: Tenant de ChromaDB
- `CHROMA_DATABASE`: Base de datos de ChromaDB
- `CHROMA_API_KEY`: API key para autenticación

### Embeddings
- `CHROMA_EMBEDDING_FUNCTION`: Función de embeddings a usar
- `CHROMA_OPENAI_EMBEDDING_MODEL`: Modelo de OpenAI para embeddings
- `CHROMA_OPENAI_EMBEDDING_DIMENSIONS`: Dimensiones del modelo de embeddings

### Configuración Adicional
- `CHROMA_DISTANCE_METRIC`: Métrica de distancia
- `CHROMA_COLLECTION_METADATA`: Metadata de colecciones
- `CHROMA_ISOLATION_LEVEL`: Nivel de aislamiento
- `CHROMA_ALLOW_RESET`: Permitir reset (true/false)

## Mantenimiento del Fork

### Actualizar desde el Repositorio Original

1. **Agregar el upstream remoto** (si no existe):
   ```bash
   git remote add upstream <url-del-repo-original>
   ```

2. **Obtener cambios del upstream**:
   ```bash
   git fetch upstream
   ```

3. **Mergear cambios**:
   ```bash
   git merge upstream/main  # o la rama principal correspondiente
   ```

### Resolución de Conflictos

Los conflictos deberían ser mínimos porque:

1. **Código core no modificado**: Solo se agregan llamadas opcionales a extensiones
2. **Extensiones en directorio separado**: Todo el código personalizado está en `extensions/`
3. **Manejo de errores robusto**: Si las extensiones fallan, el código continúa normalmente

### Si hay conflictos en `server.py`

El único punto de integración es en `_initialize_chroma_client()`:

```python
# EXTENSION: Verificar/crear base de datos automáticamente para cliente HTTP
# Esta extensión personalizada no modifica el código core, solo agrega funcionalidad
try:
    from chroma_mcp.extensions.database_manager import ensure_database_exists
    # ... código de extensión ...
except ImportError:
    # Si las extensiones no están disponibles, continuar sin verificación
    logger.debug("Extensiones personalizadas no disponibles, omitiendo verificación de base de datos")
except Exception as ext_error:
    # No fallar si la extensión tiene problemas, solo loguear
    logger.warning(f"Error en extensión de verificación de base de datos: {ext_error}")
```

Si hay conflictos, busca el bloque marcado con `# EXTENSION:` y resuélvelos manualmente.

## Agregar Nuevas Extensiones

Para agregar nueva funcionalidad personalizada:

1. **Crear un nuevo módulo** en `extensions/`:
   ```python
   # extensions/mi_extension.py
   def mi_funcion_personalizada():
       # Tu código aquí
       pass
   ```

2. **Exportar en `__init__.py`**:
   ```python
   from .mi_extension import mi_funcion_personalizada
   __all__ = [..., "mi_funcion_personalizada"]
   ```

3. **Integrar en punto estratégico**:
   - Usar `try/except ImportError` para que sea opcional
   - No fallar si la extensión no está disponible
   - Documentar claramente con comentarios `# EXTENSION:`

## Ventajas de esta Estructura

1. **Mínimos conflictos**: El código core apenas se modifica
2. **Fácil mantenimiento**: Las extensiones están claramente separadas
3. **Robusto**: Si las extensiones fallan, el código continúa
4. **Documentado**: Cada punto de integración está claramente marcado
5. **Escalable**: Fácil agregar nuevas extensiones sin tocar el core

