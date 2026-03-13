# Handoff de Implementacion - Robustez RAG

Fecha: 2026-03-13
Estado: Listo para ejecucion
Objetivo: Eliminar respuestas vacias por fallos silenciosos y desalineacion de estado entre UI, API e indices.

## Alcance

Este handoff implementa mejoras generales y sistemicas. No esta afinado a consultas puntuales fallidas.

## Resultado esperado

- La API debe diferenciar entre:
  - repositorio listado
  - repositorio realmente consultable
- La consulta debe fallar de forma explicita cuando el repo no esta listo.
- Deben reducirse los casos de respuesta: "No se encontro informacion en el repositorio." por causas operativas.
- Debe existir trazabilidad diagnsotica por etapa de pipeline.

## Fase 1 - Readiness de repositorio y contrato API

Prioridad: Critica
Duracion estimada: 0.5 a 1.5 dias

### Cambios

1. Validacion de readiness antes de consulta
- Archivo: coderag/api/server.py
- Archivo: coderag/core/storage_health.py
- Implementar chequeo por repo_id para consulta:
  - Chroma con documentos para repo_id
  - BM25 presente para repo_id
  - Neo4j opcional como warning
- Si repo no esta listo:
  - devolver 422 con detail estructurado
  - incluir codigo de causa y accion sugerida

2. Endpoint de estado por repositorio
- Archivo: coderag/api/server.py
- Archivo: coderag/core/models.py
- Crear endpoint:
  - GET /repos/{repo_id}/status
- Respuesta recomendada:
  - repo_id
  - listed_in_catalog
  - query_ready
  - chroma_counts por coleccion
  - bm25_loaded
  - graph_available
  - warnings

3. Alinear catalogo con disponibilidad real
- Archivo: coderag/jobs/worker.py
- Archivo: coderag/storage/metadata_store.py
- Mantener listado de repos y agregar estado consultable derivado
- Evitar asumir que presencia en workspace implica readiness

### Criterios de aceptacion

- POST /query para repo inexistente en indices retorna 422, no respuesta vacia.
- GET /repos/{repo_id}/status refleja estado real por indice.
- UI puede consumir este estado sin inferencias ambiguas.

### Pruebas

- tests/test_api.py
  - nuevo caso: query_repo_not_ready_returns_422
  - nuevo caso: repo_status_endpoint_reports_partial

## Fase 2 - Robustez de retrieval y fallbacks

Prioridad: Critica
Duracion estimada: 1 a 2 dias

### Cambios

1. Hardening en hybrid search
- Archivo: coderag/retrieval/hybrid_search.py
- Mejorar manejo de errores:
  - no swallow silencioso
  - incluir señal diagnostica
- Revisar fusion de score vector y BM25 para evitar sesgo de escala.
- Registrar cuando no hubo vector search activa.

2. Guardas en query pipeline
- Archivo: coderag/api/query_service.py
- Si retrieval y contexto son insuficientes:
  - responder con fallback explicativo
  - incluir reason code operativo
- Si filtrado de citas deja 0:
  - reintentar con citas crudas priorizadas

3. Verificacion LLM menos fragil
- Archivo: coderag/llm/openai_client.py
- Fortalecer parseo de veredicto para evitar falsos negativos por texto ambiguo.
- Exponer decision de verificacion en diagnostics.

4. Graph expand con telemetria
- Archivo: coderag/retrieval/graph_expand.py
- Conservar fallback, pero con logging y causa explicita.

### Criterios de aceptacion

- Diagnostics siempre incluye:
  - retrieved
  - reranked
  - context_size
  - fallback_reason
  - verify_valid
  - stage_timings_ms
- No hay retorno silencioso de error en etapas criticas.

### Pruebas

- tests/test_query_service_modules.py
  - nuevo caso: fallback_reason_present_when_context_empty
  - nuevo caso: citations_not_empty_after_filter_retry

## Fase 3 - Calidad de ingesta e indexacion

Prioridad: Alta
Duracion estimada: 1 a 2 dias

### Cambios

1. Cobertura de chunking
- Archivo: coderag/ingestion/chunker.py
- Mantener estrategia actual y agregar extraccion minima para:
  - config estructurada (yaml/json/toml)
  - markdown por secciones
- Evitar ruptura de formato actual de SymbolChunk.

2. Transparencia de filtros de escaneo
- Archivo: coderag/ingestion/pipeline.py
- Archivo: coderag/ingestion/repo_scanner.py
- Loggear:
  - archivos escaneados
  - archivos excluidos por razon
  - chunks extraidos por lenguaje

3. BM25 supervivencia operativa
- Archivo: coderag/ingestion/index_bm25.py
- Definir estrategia:
  - reconstruccion al arranque desde artefactos indexados
  - o persistencia dedicada
- Recomendado inicial: reconstruccion al arranque.

4. Mismatch de dimensiones en Chroma
- Archivo: coderag/ingestion/index_chroma.py
- Evitar borrado destructivo automatico como primera reaccion.
- Convertir en error controlado con mensaje accionable.

### Criterios de aceptacion

- Ingesta produce metricas claras de cobertura.
- Reinicio del servicio no degrada a consulta inutil por ausencia de BM25.

### Pruebas

- tests/test_ingestion_pipeline.py
- tests/test_repo_scanner.py
- tests/test_index_chroma.py

## Fase 4 - UX operativa y observabilidad

Prioridad: Media
Duracion estimada: 0.5 a 1.5 dias

### Cambios

1. Readiness visible en UI
- Archivo: coderag/ui/main_window.py
- Bloquear boton de consulta si repo no esta ready.
- Mostrar mensaje con estado y accion sugerida.

2. Timeline de job mas fiel
- Archivo: coderag/jobs/worker.py
- Estado partial cuando haya incompletitud de indices.
- Evitar mostrar "Completado" si no esta query-ready.

3. Diagnostics operativo
- Archivo: coderag/api/query_service.py
- Extender detalles por etapa para debugging real.

### Criterios de aceptacion

- El usuario puede entender por que no hay respuesta y como corregirlo.
- Menor ambiguedad entre estado de ingesta y capacidad de consulta.

## Orden recomendado de implementacion

1. Fase 1
2. Fase 2
3. Fase 3
4. Fase 4

## Definicion de Done global

- Sin fallos silenciosos en paths criticos de query.
- Errores operativos con codigos y detalle accionable.
- Repo status disponible via API y consumible por UI.
- Pruebas nuevas pasando en API, query e ingesta.
- Benchmark de regresion sin incremento notable de latencia p95.

## Checklist de ejecucion rapida

- [ ] Implementar readiness por repo en API
- [ ] Exponer endpoint de estado por repo
- [ ] Bloquear query cuando repo no esta ready
- [ ] Instrumentar diagnostics minimo obligatorio
- [ ] Reforzar fallback de citas y verificador
- [ ] Agregar pruebas de regresion para estados parciales

## Comandos de validacion sugeridos

- pytest -q
- pytest tests/test_api.py tests/test_query_service_modules.py -q
- pytest tests/test_ingestion_pipeline.py tests/test_repo_scanner.py tests/test_index_chroma.py -q
- python scripts/benchmark_api_live.py --repo-id kdb-vector-grafo-v2 --base-url http://127.0.0.1:8000 --iterations 20 --warmup 2 --output-dir benchmark_reports

## Riesgos y mitigacion

1. Riesgo: aumento de errores 422 al inicio por validacion estricta
- Mitigacion: incluir endpoint de estado y mensajes de accion en UI.

2. Riesgo: cambio de comportamiento en fallback
- Mitigacion: tests de regresion y flag de rollout si se requiere.

3. Riesgo: latencia por chequeos adicionales
- Mitigacion: cache de health por TTL corto y metricas por etapa.
