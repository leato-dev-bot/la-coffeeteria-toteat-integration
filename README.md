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
- `toteat.failed_tasks`
- `toteat.endpoint_checkpoints`

## Optimización aplicada para ventas
- prioridad explícita para `sales` y `salesbywaiter`
- checkpoints por ventana para reanudar sin repetir trabajo ya correcto
- exclusión selectiva de endpoints problemáticos cuando haga falta
- estado de monitoreo más útil con conteos raw, fallos abiertos y última ventana exitosa por endpoint
- rampa gradual de requests por minuto para encontrar un punto dulce entre velocidad y error

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
Actualización diaria a la **01:00 AM hora de Chile** para cargar datos del día anterior:
```cron
CRON_TZ=America/Santiago
0 1 * * * /Users/leatoagent/Projects/la-coffeeteria-toteat-integration/scripts/daily_update.sh
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

## Capa de reporting
Se agregó una primera capa de reporting en schema `reporting` con foco en ventas:
- `reporting.sales_orders_v`
- `reporting.sales_products_v`
- `reporting.sales_payments_v`
- `reporting.sales_daily_summary_v`

Reglas aplicadas en esta capa:
- timestamps convertidos a horario de Chile (`America/Santiago`)
- montos formateados con convención chilena para lectura humana
- la capa raw sigue intacta como fuente técnica/auditable
- ventas deduplicadas por llave lógica `order_id + payment_id`

Construcción de la capa:
```bash
./scripts/build_reporting.sh
```

## Siguiente capa recomendada
Sobre `toteat.raw_api_responses`, seguir ampliando reporting para:
- recaudación
- documentos fiscales
- inventario
- movimientos contables
