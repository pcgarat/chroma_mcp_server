# Guía Rápida de Inicio

## Configuración Rápida (Opción 1 - Recomendada)

### Paso 1: Exportar Variables de Entorno

```bash
source ./chroma_mcp_server/scripts/setup-chroma-env.sh
```

### Paso 2: Inicializar Colecciones

```bash
chroma-mcp-client setup-collections
```

### Paso 3: Indexar el Código

```bash
chroma-mcp-client index --all
```

### Paso 4: Verificar

```bash
# Contar documentos indexados
chroma-mcp-client count --collection-name codebase_v1

# Hacer una consulta de prueba
chroma-mcp-client query "autenticación" -n 5
```

## Comandos Útiles

```bash
# Indexar un archivo específico
chroma-mcp-client index ./src/MiClase.php

# Indexar una carpeta específica
chroma-mcp-client index ./src/

# Consultar el código
chroma-mcp-client query "cómo funciona la autenticación" -n 10

# Ver estadísticas
chroma-mcp-client count --collection-name codebase_v1
```

## Notas Importantes

- El comando `index --all` respeta automáticamente `.gitignore`
- No se indexan: `vendor/`, `node_modules/`, `var/`, `logs/`, etc.
- Solo se indexan archivos rastreados por Git

## Más Información

- [Guía Completa de Indexación](INDEXACION_CODIGO.md)
- [Configuración de Variables de Entorno](CONFIGURACION_ENV.md)
- [Documentación del Cliente CLI](../docs/scripts/chroma-mcp-client.md)

