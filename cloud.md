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

## Reporting
Primera capa de reporting creada en schema `reporting` con foco en ventas.

Vistas disponibles:
- `reporting.sales_orders_v`
- `reporting.sales_products_v`
- `reporting.sales_payments_v`
- `reporting.sales_daily_summary_v`

Reglas aplicadas:
- timestamps convertidos a `America/Santiago`
- montos con columnas formateadas en convención chilena
- raw preservado como fuente de verdad técnica

## Próximos pasos
- completar backfill estable del resto de endpoints
- ampliar reporting para recaudación, fiscal, inventario y contabilidad
- separar `collection` como flujo independiente si sigue generando fricción
