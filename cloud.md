# cloud.md

## Objetivo
Integrar datos de Toteat para La Coffeeteria con prioridad de negocio en ventas.

## Estado actual
- Base de datos: `la_coffeeteria`
- Schema: `toteat`
- Prioridad de endpoints: ventas primero (`sales`, `salesbywaiter`)
- `collection` se trata como endpoint degradado cuando afecta la estabilidad del backfill principal

## Arquitectura
- Python CLI: `toteat-sync`
- Persistencia raw: `toteat.raw_api_responses`
- Ejecuciones: `toteat.ingestion_runs`
- Fallos pendientes: `toteat.failed_tasks`
- Checkpoints por ventana: `toteat.endpoint_checkpoints`

## Reanudación
- Se saltan ventanas ya marcadas como exitosas en checkpoints
- Las ventanas fallidas quedan registradas para reintento posterior

## Monitoreo
- `python -m toteat_integration.cli status`
- `runtime/progress.json`
- logs en `logs/`

## Riesgos conocidos
- `collection` tiene comportamiento inestable del proveedor
- El throughput depende del rate limit de Toteat

## Próximos pasos
- completar backfill estable del resto de endpoints
- crear tablas normalizadas para reporting de ventas
- separar `collection` como flujo independiente si sigue generando fricción
