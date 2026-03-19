# La Coffeeteria Toteat Integration

Integración de Toteat hacia PostgreSQL para **La Coffeeteria**.

## Objetivo
- cargar histórico de los últimos **3 años**
- dejar un pipeline de actualización **diaria**
- preparar la base para reportes
- mantener arquitectura lista para futuros tenants/clientes

## Base de datos
- database: `la_coffeeteria`
- schema: `toteat`
- timezone de negocio: `America/Santiago`
- locale de referencia para presentación/normalización: `es-CL`

## Cobertura actual de endpoints
- `products`
- `tables`
- `shiftstatus`
- `sales`
- `salesbywaiter`
- `collection`
- `fiscaldocuments`
- `inventorystate`
- `accountingmovements`
- `orders/cancellation-report`

## Modelo de almacenamiento
Esta primera versión deja una capa **raw** para ingestión segura y trazable:
- `toteat.tenants`
- `toteat.ingestion_runs`
- `toteat.raw_api_responses`

La idea es desacoplar:
1. extracción desde Toteat
2. persistencia cruda audit-able
3. normalización y métricas para reportes

## Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
# completar credenciales si hiciera falta
psql la_coffeeteria -f sql/001_init_toteat.sql
```

## Variables esperadas
- `DATABASE_URL`
- `TOTEAT_BASE_URL`
- `TOTEAT_XIR`
- `TOTEAT_XIL`
- `TOTEAT_XIU`
- `TOTEAT_XAPITOKEN` o `TOTEAT_API_TOKEN`
- `TZ=America/Santiago`

## Ejecución
Backfill 3 años:
```bash
toteat-sync sync --mode backfill
```

Carga diaria:
```bash
toteat-sync sync --mode daily
```

Rango manual:
```bash
toteat-sync sync --mode range --start 2026-03-01 --end 2026-03-15
```

## Programación diaria sugerida
Ejemplo con cron a las 05:15 hora Chile:
```cron
15 5 * * * cd /Users/leatoagent/Projects/la-coffeeteria-toteat-integration && . .venv/bin/activate && toteat-sync sync --mode daily >> logs/daily.log 2>&1
```

## Supervisor de backfill resistente
Para completar el histórico aunque haya errores transitorios del proveedor:
```bash
./scripts/run_until_complete.sh
```
Este supervisor relanza pasadas, mantiene log en `logs/supervisor.log` y continúa hasta resolver tareas pendientes.

## Consideraciones importantes de fechas
- Toteat agrupa varias respuestas por lógica de turno, no solo por fecha calendario.
- Para consultas por rango se usa hora de negocio de Chile (`America/Santiago`).
- Los endpoints de ventas y reportes tienen ventanas máximas cortas; por eso el backfill se trocea en bloques.

## Siguiente capa recomendada
Sobre `toteat.raw_api_responses`, crear vistas/tablas normalizadas para:
- ventas
- productos
- recaudación
- documentos fiscales
- inventario
- movimientos contables
