# La Coffeeteria Toteat Integration

Integration project for Toteat API ingestion into PostgreSQL for La Coffeeteria.

## Goals
- Full historical load for the last 3 years
- Daily incremental refresh pipeline
- PostgreSQL target database: `la_coffeeteria`
- PostgreSQL schema: `toteat`
- Chile timezone handling: `America/Santiago`
- Multi-tenant-ready approach for future clients

## Status
- Bootstrapped
- Credentials validated against Toteat products endpoint
- Endpoint discovery and ingestion implementation in progress
