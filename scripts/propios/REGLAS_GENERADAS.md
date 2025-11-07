# Reglas Generadas por el Script `generate_cursor_rules.py`

El script `generate_cursor_rules.py` copia las reglas optimizadas desde `scripts/propios/cursor-rules/` a `.cursor/rules/`, renombrando las optimizadas quitando el sufijo `_optimized`.

## Reglas Optimizadas Generadas (8 reglas)

### 1. `main_memory_rule.mdc` (desde `main_memory_rule_optimized.mdc`)
**Estado:** `alwaysApply: true` ✅

**Descripción:**
Regla principal consolidada que integra funcionalidades de memoria persistente. Define el comportamiento obligatorio de búsqueda automática en ChromaDB antes de responder cada prompt.

**Funcionalidades:**
- Búsqueda automática en `codebase_v1` y `derived_learnings_v1` al inicio de cada prompt
- Integración con Enhanced Context Capture (Code Diff Extraction, Tool Sequence Tracking, Bidirectional Linking)
- Workflow de Derived Learnings (promoción de aprendizajes validados)
- Integración con Thinking Sessions
- Integración con Validation Evidence y Test Results
- Auto-guardado inteligente basado en palabras clave
- Optimización de rendimiento con colecciones prioritarias

**Colecciones usadas:**
- `codebase_v1` ✅
- `chat_history_v1` ✅
- `derived_learnings_v1` ✅
- `thinking_sessions_v1` ✅
- `validation_evidence_v1` ✅
- `test_results_v1` ✅

---

### 2. `auto_log_chat.mdc` (desde `auto_log_chat_optimized.mdc`)
**Estado:** `alwaysApply: true` ✅

**Descripción:**
Regla que automatiza el logging de conversaciones en la colección `chat_history_v1` con contexto enriquecido. Captura automáticamente resúmenes, cambios de código, secuencias de herramientas y enlaces bidireccionales.

**Funcionalidades:**
- Logging automático después de cada respuesta del AI
- Captura de resúmenes de prompt y respuesta
- Extracción de contexto enriquecido (diffs, tool sequences)
- Bidirectional Linking entre chat y código
- Confidence Scoring basado en calidad del contexto
- Integración con Enhanced Context Capture

**Colecciones usadas:**
- `chat_history_v1` ✅
- `codebase_v1` (referenciado en bidirectional linking) ✅

---

### 3. `workflow.mdc` (desde `workflow_optimized.mdc`)
**Estado:** `alwaysApply: true` ✅

**Descripción:**
Regla de workflow de testing que garantiza la calidad del código mediante testing exhaustivo y cobertura adecuada. Define reglas obligatorias para testing en cada implementación.

**Funcionalidades:**
- Testing obligatorio en cada implementación
- Ejecución de tests post-implementación
- Corrección obligatoria de tests fallidos
- Objetivos de cobertura por capa (Domain: 100%, Application: 95%, Infrastructure: 90%, Command: 85%)
- Integración con `test_results_v1` y `validation_evidence_v1`
- Promoción de patrones de testing exitosos a `derived_learnings_v1`
- Checklist completo de testing

**Colecciones usadas:**
- `test_results_v1` ✅
- `validation_evidence_v1` ✅
- `codebase_v1` ✅
- `derived_learnings_v1` ✅

---

### 4. `thinking_sessions.mdc`
**Estado:** `alwaysApply: false` ⚠️

**Descripción:**
Regla específica para usar sesiones de pensamiento estructurado cuando se necesita capturar cadenas de razonamiento complejas o decisiones arquitectónicas importantes.

**Funcionalidades:**
- Registrar pensamientos secuenciales usando `mcp_chroma_sequential_thinking`
- Crear ramas de pensamiento alternativas
- Encontrar pensamientos similares usando `mcp_chroma_find_similar_thoughts`
- Obtener resumen de sesión usando `mcp_chroma_get_session_summary`
- Integración con Enhanced Context Capture
- Promoción a Derived Learnings

**Cuándo usar:**
- Decisiones arquitectónicas importantes
- Troubleshooting complejo
- Análisis de trade-offs
- Diseño de algoritmos
- Aprendizaje de conceptos nuevos

**Colecciones usadas:**
- `thinking_sessions_v1` ✅
- `chat_history_v1` (vinculación) ✅
- `codebase_v1` (vinculación) ✅
- `validation_evidence_v1` (vinculación) ✅
- `derived_learnings_v1` (promoción) ✅

---

### 5. `derived_learnings.mdc`
**Estado:** `alwaysApply: false` ⚠️

**Descripción:**
Regla específica para identificar, validar y promover aprendizajes derivados desde `chat_history_v1` y `validation_evidence_v1` hacia `derived_learnings_v1`.

**Funcionalidades:**
- Identificar candidatos para promoción (alta confianza, evidencia de validación)
- Revisar contexto completo antes de promover
- Formular aprendizajes con metadata rica
- Promover aprendizajes a `derived_learnings_v1`
- Actualizar estado de entradas originales
- Uso de Derived Learnings en RAG (búsqueda priorizada)
- Mantenimiento de Derived Learnings

**Cuándo usar:**
- Cuando se identifica un patrón validado y reutilizable
- Cuando hay evidencia de validación que respalda una solución
- Cuando se quiere priorizar soluciones validadas en búsquedas RAG

**Colecciones usadas:**
- `derived_learnings_v1` ✅
- `chat_history_v1` (fuente de promoción) ✅
- `validation_evidence_v1` (evidencia de validación) ✅
- `codebase_v1` (referencias de código) ✅

---

### 6. `validation_evidence.mdc`
**Estado:** `alwaysApply: false` ⚠️

**Descripción:**
Regla específica para capturar, vincular y usar evidencia de validación para respaldar soluciones y promover aprendizajes.

**Funcionalidades:**
- Capturar transiciones de tests (test fallido → test pasado)
- Registrar resoluciones de errores runtime
- Documentar mejoras de calidad de código
- Vincular evidencia con chat history y code chunks
- Integración con Derived Learnings workflow
- Scoring de evidencia (transiciones de tests: 50%, resoluciones de errores: 30%, mejoras de calidad: 20%)

**Cuándo usar:**
- Cuando un test pasa después de haber fallado
- Cuando se corrige un bug y se verifica la solución
- Cuando se mejora una métrica de calidad de código
- Cuando se necesita respaldar un aprendizaje con evidencia

**Colecciones usadas:**
- `validation_evidence_v1` ✅
- `test_results_v1` (vinculación) ✅
- `chat_history_v1` (vinculación) ✅
- `codebase_v1` (vinculación) ✅
- `derived_learnings_v1` (promoción) ✅

---

### 4. `debug_assist.mdc`
**Estado:** `alwaysApply: false` ⚠️

**Descripción:**
Regla específica para buscar proactivamente soluciones validadas cuando el usuario reporta errores, fallos de tests, o problemas de código.

**Funcionalidades:**
- Búsqueda proactiva en múltiples colecciones cuando se detecta un error
- Priorización de soluciones validadas (derived learnings con validation evidence)
- Búsqueda en chat history, test results, validation evidence y codebase
- Presentación de soluciones con contexto de validación
- Sugerencia de validación para soluciones nuevas

**Cuándo usar:**
- Cuando el usuario pega un mensaje de error o stacktrace
- Cuando el usuario reporta que un test está fallando
- Cuando el usuario menciona un problema o bug
- Cuando el usuario pregunta "¿por qué falla...?" o "¿cómo arreglar...?"

**Colecciones usadas:**
- `derived_learnings_v1` ✅ (prioridad alta)
- `chat_history_v1` ✅
- `test_results_v1` ✅
- `validation_evidence_v1` ✅
- `codebase_v1` ✅

---

### 5. `daily_workflow.mdc`
**Estado:** `alwaysApply: false` ⚠️

**Descripción:**
Regla específica para integrar activamente el "Second Brain" (ChromaDB) en el flujo de trabajo diario de desarrollo, aprovechando el conocimiento acumulado para acelerar el desarrollo.

**Funcionalidades:**
- Contextual Code Understanding & Troubleshooting
- Recalling Design Rationale & Past Decisions
- Leveraging Validated Solutions from Test Data
- Starting a New Feature (buscar patrones existentes)
- Code Review (verificar consistencia con patrones)
- Morning Review workflow
- Post-Testing Analysis workflow

**Cuándo usar:**
- Al revisar código complejo o recibir bug reports
- Al necesitar recordar el razonamiento detrás de decisiones
- Al buscar soluciones validadas para problemas conocidos
- Al comenzar una nueva funcionalidad
- Al revisar Pull Requests
- Durante rutinas diarias de revisión y análisis

**Colecciones usadas:**
- `codebase_v1` ✅
- `chat_history_v1` ✅
- `derived_learnings_v1` ✅
- `thinking_sessions_v1` ✅
- `test_results_v1` ✅
- `validation_evidence_v1` ✅

---

## Reglas Específicas del Proyecto (NO generadas por el script)

### 7. `chroma-mcp.mdc`
**Estado:** `alwaysApply: true` ✅

**Descripción:**
Regla específica que define restricciones sobre la carpeta `chroma_mcp_server`. Solo permite modificar archivos dentro de `scripts/propios/` y recuerda que se usa `uvx` para el cliente MCP.

---

### 8. `autobiz.mdc`
**Estado:** `alwaysApply: false` ⚠️

**Descripción:**
Regla específica del AutobizBundle que define la arquitectura hexagonal implementada, estructura de capas, y reglas de desarrollo específicas del bundle.

---

## Resumen de Reglas por Estado

### Reglas con `alwaysApply: true` (4 reglas)
1. ✅ `main_memory_rule.mdc` - Regla principal de memoria
2. ✅ `auto_log_chat.mdc` - Auto-logging de chat
3. ✅ `workflow.mdc` - Workflow de testing
4. ✅ `chroma-mcp.mdc` - Restricciones de Chroma MCP

### Reglas con `alwaysApply: false` (6 reglas)
1. ⚠️ `thinking_sessions.mdc` - Sesiones de pensamiento
2. ⚠️ `derived_learnings.mdc` - Promoción de aprendizajes
3. ⚠️ `validation_evidence.mdc` - Evidencia de validación
4. ⚠️ `debug_assist.mdc` - Asistencia proactiva en debugging
5. ⚠️ `daily_workflow.mdc` - Integración del "Second Brain" en flujo diario
6. ⚠️ `autobiz.mdc` - Regla específica de AutobizBundle

---

## Verificación de Nombres de Colecciones

Todas las reglas generadas usan los nombres correctos de colecciones según `reset-collections.sh`:

✅ **Colecciones correctas:**
- `codebase_v1` ✅
- `chat_history_v1` ✅
- `derived_learnings_v1` ✅
- `thinking_sessions_v1` ✅
- `validation_evidence_v1` ✅
- `test_results_v1` ✅

❌ **Colecciones incorrectas (eliminadas):**
- `symfony_codebase` ❌
- `development_discussions` ❌
- `architectural_decisions` ❌
- `bug_fixes` ❌
- `test_results` (sin `_v1`) ❌

---

## Cobertura de Workflows

### Enhanced Context Capture
✅ **Cubierto en:** `auto_log_chat.mdc`
- Code Diff Extraction
- Tool Sequence Tracking
- Bidirectional Linking
- Confidence Scoring

### Derived Learnings Workflow
✅ **Cubierto en:** `derived_learnings.mdc`
- Identificación de candidatos
- Revisión de contexto
- Formulación de aprendizajes
- Promoción a `derived_learnings_v1`
- Uso en RAG

### Thinking Sessions
✅ **Cubierto en:** `thinking_sessions.mdc`
- Registrar pensamientos secuenciales
- Crear ramas de pensamiento
- Encontrar pensamientos similares
- Obtener resumen de sesión
- Integración con otras colecciones

### Validation Evidence
✅ **Cubierto en:** `validation_evidence.mdc`
- Capturar transiciones de tests
- Registrar resoluciones de errores
- Documentar mejoras de calidad
- Vincular con otras colecciones
- Scoring de evidencia

### Debug Assist
✅ **Cubierto en:** `debug_assist.mdc`
- Búsqueda proactiva de soluciones cuando hay errores
- Priorización de soluciones validadas
- Búsqueda en múltiples colecciones simultáneamente
- Presentación de soluciones con contexto de validación
- Sugerencia de validación para soluciones nuevas

### Daily Workflow Integration
✅ **Cubierto en:** `daily_workflow.mdc`
- Contextual Code Understanding & Troubleshooting
- Recalling Design Rationale & Past Decisions
- Leveraging Validated Solutions from Test Data
- Starting a New Feature (buscar patrones existentes)
- Code Review (verificar consistencia)
- Morning Review workflow
- Post-Testing Analysis workflow

---

## Nota Importante

El script solo genera las reglas optimizadas que usan los nombres correctos de colecciones. Las reglas originales con nombres incorrectos han sido eliminadas de `cursor-rules/` y no se generan.
