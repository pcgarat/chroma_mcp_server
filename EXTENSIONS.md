# Extensiones Personalizadas

Este documento explica cómo se han integrado las extensiones personalizadas en el fork para mantener la máxima compatibilidad con el repositorio original.

## Estructura de Extensiones

Las extensiones personalizadas están en `src/chroma_mcp/extensions/`:

- **`database_manager.py`**: Verificación y creación automática de bases de datos
- **`config_loader.py`**: Cargador de configuración mejorado
- **`README.md`**: Documentación detallada de las extensiones

## Integración Mínima en el Código Core

La única modificación en el código core está en `server.py`, en la función `_initialize_chroma_client()`:

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

### Características de la Integración

1. **Opcional**: Si las extensiones no están disponibles, el código continúa normalmente
2. **No bloqueante**: Si hay errores en las extensiones, solo se loguean, no fallan
3. **Bien documentado**: El bloque está claramente marcado con `# EXTENSION:`
4. **Mínimo impacto**: Solo se agregan ~20 líneas en un punto estratégico

## Actualización del Fork

### Proceso de Actualización

1. **Agregar upstream remoto** (si no existe):
   ```bash
   git remote add upstream <url-del-repo-original>
   ```

2. **Obtener cambios**:
   ```bash
   git fetch upstream
   ```

3. **Mergear cambios**:
   ```bash
   git merge upstream/main  # o la rama principal
   ```

### Resolución de Conflictos

Si hay conflictos en `server.py`:

1. Buscar el bloque marcado con `# EXTENSION:`
2. Mantener ese bloque en tu versión
3. Resolver cualquier conflicto en el código circundante
4. Verificar que las extensiones sigan funcionando

### Si el Código Core Cambia

Si la función `_initialize_chroma_client()` cambia significativamente:

1. Buscar el bloque `elif client_type == "http":`
2. Agregar el bloque de extensión justo después de extraer las variables de configuración
3. Antes de crear el `HttpClient`

## Dependencias Opcionales

Las extensiones usan `requests` para verificar/crear bases de datos, pero es **opcional**:

- Si `requests` no está instalado, la verificación se omite silenciosamente
- El código continúa normalmente sin verificación
- Para habilitar la verificación automática, instalar: `pip install requests`

## Ventajas de esta Estructura

1. **Mínimos conflictos**: Solo un punto de integración en el código core
2. **Fácil mantenimiento**: Todo el código personalizado está separado
3. **Robusto**: Si las extensiones fallan, el código continúa
4. **Documentado**: Cada punto de integración está claramente marcado
5. **Escalable**: Fácil agregar nuevas extensiones sin tocar el core

## Agregar Nuevas Extensiones

Para agregar nueva funcionalidad:

1. Crear módulo en `src/chroma_mcp/extensions/`
2. Exportar en `extensions/__init__.py`
3. Integrar en punto estratégico con `try/except ImportError`
4. Documentar claramente con comentarios `# EXTENSION:`

Ver `extensions/README.md` para más detalles.

