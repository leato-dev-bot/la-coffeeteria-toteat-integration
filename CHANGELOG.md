# Changelog

## Unreleased
- Bootstrapped Toteat integration project for La Coffeeteria
- Added PostgreSQL schema bootstrap for `toteat`
- Added Python CLI pipeline for backfill, daily sync, and custom ranges
- Added raw ingestion tables and tenant registry
- Added Chile timezone handling assumptions (`America/Santiago`)
- Added endpoint priorities to favor sales integration
- Added endpoint window checkpoints for resumable backfills
- Added richer status output and project memory in `cloud.md`
- Added gradual request-rate ramping with automatic slowdown on failures
- Added initial reporting layer for sales with Chile timezone conversion and Chilean number formatting
- Deduplicated reporting sales layer using logical key `order_id + payment_id`
