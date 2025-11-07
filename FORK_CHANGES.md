# Cambios en el Fork - Guía de Mantenimiento

Este documento lista todos los cambios realizados en el fork para facilitar las actualizaciones desde el repositorio original.

## Estrategia de Cambios

Todos los cambios están marcados con `# EXTENSION:` para facilitar su identificación. Los cambios son:
- **Mínimos**: Solo se agrega funcionalidad, no se modifica la lógica existente
- **Bien localizados**: Cada cambio está en un punto específico y documentado
- **Retrocompatibles**: Si las variables de entorno no están definidas, se usan valores por defecto

## Cambios Realizados

### 1. `chroma_mcp/utils/config.py` - Función `get_collection_settings()`

**Ubicación**: Líneas 98-132

**Cambios**:
- Agregado soporte para `CHROMA_DISTANCE_METRIC` (líneas 98-114)
- Agregado soporte para `CHROMA_COLLECTION_METADATA` (líneas 116-132)

**Cómo identificar durante actualización**:
```bash
# Buscar el bloque marcado con EXTENSION
grep -n "EXTENSION:" chroma_mcp/utils/config.py
```

**Resolución de conflictos**:
- Si hay conflictos en esta función, mantener el bloque `# EXTENSION:` completo
- El bloque debe ir después de la inicialización de `default_settings` (línea 96)
- Y antes de `# Override with provided parameters` (línea 134)

### 2. `chroma_mcp/utils/chroma_client.py` - Función `get_chroma_client()`

**Ubicación**: Líneas 388-415

**Cambios**:
- Agregado soporte para `CHROMA_ISOLATION_LEVEL` (líneas 395-399)
- Agregado soporte para `CHROMA_ALLOW_RESET` (líneas 401-405)
- Modificado la creación de `Settings` para usar kwargs dinámicos (líneas 391-415)

**Cómo identificar durante actualización**:
```bash
# Buscar el bloque marcado con EXTENSION
grep -n "EXTENSION:" chroma_mcp/utils/chroma_client.py
```

**Resolución de conflictos**:
- Si hay conflictos en esta función, mantener el bloque `# EXTENSION:` completo
- El bloque debe reemplazar la línea original:
  ```python
  chroma_settings = Settings(anonymized_telemetry=False)
  ```
- Con el nuevo bloque que incluye `settings_kwargs` y el try/except

### 3. `chroma_mcp/server.py` - Función `_initialize_chroma_client()`

**Ubicación**: Líneas 222-241

**Cambios**:
- Agregada llamada a `ensure_database_exists()` para verificar/crear base de datos automáticamente

**Cómo identificar durante actualización**:
```bash
# Buscar el bloque marcado con EXTENSION
grep -n "EXTENSION:" chroma_mcp/server.py
```

**Resolución de conflictos**:
- Si hay conflictos, mantener el bloque `# EXTENSION:` completo
- El bloque debe ir después de extraer las variables (host, port, tenant, database, etc.)
- Y antes de `# Build headers if api_key is provided` (línea 243)

## Archivos Nuevos (Sin Conflictos)

Estos archivos son completamente nuevos y no causarán conflictos:

- `chroma_mcp/extensions/__init__.py`
- `chroma_mcp/extensions/database_manager.py`
- `chroma_mcp/extensions/config_loader.py`
- `chroma_mcp/extensions/README.md`
- `EXTENSIONS.md`
- `FORK_CHANGES.md` (este archivo)

## Proceso de Actualización

### 1. Antes de Actualizar

```bash
# Crear una rama de respaldo
git checkout -b backup-before-update
git push origin backup-before-update

# Volver a la rama principal
git checkout main
```

### 2. Actualizar desde Upstream

```bash
# Obtener cambios del upstream
git fetch upstream

# Mergear cambios
git merge upstream/main
```

### 3. Resolver Conflictos

Si hay conflictos en los archivos modificados:

1. **Identificar los bloques EXTENSION**:
   ```bash
   grep -n "EXTENSION:" <archivo_conflictivo>
   ```

2. **Mantener los bloques EXTENSION** en tu versión

3. **Aplicar los cambios del upstream** en el resto del código

4. **Verificar que los bloques EXTENSION** estén en los lugares correctos (ver sección "Resolución de conflictos" arriba)

### 4. Verificar Funcionalidad

Después de resolver conflictos:

```bash
# Verificar que el código compila
python -m py_compile chroma_mcp/utils/config.py
python -m py_compile chroma_mcp/utils/chroma_client.py
python -m py_compile chroma_mcp/server.py

# Ejecutar tests si existen
# (agregar comandos de test aquí si es necesario)
```

## Variables de Entorno Soportadas

Todas estas variables de entorno del `mcp.json` están soportadas:

### Cliente
- `CHROMA_CLIENT_TYPE` ✅
- `CHROMA_HOST` ✅
- `CHROMA_PORT` ✅
- `CHROMA_SSL` ✅
- `CHROMA_TENANT` ✅
- `CHROMA_DATABASE` ✅
- `CHROMA_API_KEY` ✅

### Embeddings
- `CHROMA_EMBEDDING_FUNCTION` ✅
- `CHROMA_OPENAI_EMBEDDING_MODEL` ✅ (usado en `get_openai_embedding_model()`)
- `CHROMA_OPENAI_EMBEDDING_DIMENSIONS` ✅ (usado en `get_openai_embedding_dimensions()`)
- `OPENAI_API_KEY` ✅ (usado en `get_api_key("openai")`)

### Configuración de Colecciones
- `CHROMA_DISTANCE_METRIC` ✅ (EXTENSION: usado en `get_collection_settings()`)
- `CHROMA_COLLECTION_METADATA` ✅ (EXTENSION: usado en `get_collection_settings()`)

### Configuración de Settings
- `CHROMA_ISOLATION_LEVEL` ✅ (EXTENSION: usado en `get_chroma_client()`)
- `CHROMA_ALLOW_RESET` ✅ (EXTENSION: usado en `get_chroma_client()`)

## Notas Importantes

1. **No modificar código fuera de bloques EXTENSION**: Si necesitas hacer cambios adicionales, crear nuevos bloques EXTENSION o usar el módulo de extensiones

2. **Mantener compatibilidad**: Todos los cambios son retrocompatibles - si las variables no están definidas, se usan valores por defecto

3. **Documentar nuevos cambios**: Si agregas nuevos cambios, actualiza este documento

4. **Usar extensiones cuando sea posible**: Para nueva funcionalidad, preferir crear módulos en `chroma_mcp/extensions/` en lugar de modificar código core

## Contacto

Si tienes dudas sobre cómo resolver conflictos durante una actualización, consulta este documento primero. Los bloques EXTENSION están claramente marcados y documentados.

