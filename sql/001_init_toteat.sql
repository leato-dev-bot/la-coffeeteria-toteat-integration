DROP SCHEMA IF EXISTS toteat CASCADE;
CREATE SCHEMA toteat;

CREATE TABLE toteat.tenants (
  tenant_id text PRIMARY KEY,
  tenant_name text NOT NULL,
  db_name text NOT NULL,
  timezone text NOT NULL DEFAULT 'America/Santiago',
  locale text NOT NULL DEFAULT 'es-CL',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE toteat.ingestion_runs (
  run_id bigserial PRIMARY KEY,
  tenant_id text NOT NULL REFERENCES toteat.tenants(tenant_id),
  mode text NOT NULL,
  endpoint_key text,
  window_start date,
  window_end date,
  started_at timestamptz NOT NULL DEFAULT now(),
  finished_at timestamptz,
  status text NOT NULL DEFAULT 'running',
  rows_loaded integer NOT NULL DEFAULT 0,
  error_message text
);

CREATE TABLE toteat.raw_api_responses (
  raw_id bigserial PRIMARY KEY,
  tenant_id text NOT NULL REFERENCES toteat.tenants(tenant_id),
  endpoint_key text NOT NULL,
  request_params jsonb NOT NULL DEFAULT '{}'::jsonb,
  business_date date,
  fetched_at timestamptz NOT NULL DEFAULT now(),
  response_payload jsonb NOT NULL,
  payload_hash text NOT NULL
);

CREATE TABLE toteat.failed_tasks (
  failed_task_id bigserial PRIMARY KEY,
  tenant_id text NOT NULL REFERENCES toteat.tenants(tenant_id),
  endpoint_key text NOT NULL,
  business_date date,
  request_params jsonb NOT NULL DEFAULT '{}'::jsonb,
  error_message text NOT NULL,
  retry_count integer NOT NULL DEFAULT 0,
  first_failed_at timestamptz NOT NULL DEFAULT now(),
  last_failed_at timestamptz NOT NULL DEFAULT now(),
  resolved_at timestamptz
);

CREATE UNIQUE INDEX idx_failed_tasks_unique_open
  ON toteat.failed_tasks (tenant_id, endpoint_key, business_date, md5(request_params::text))
  WHERE resolved_at IS NULL;

CREATE INDEX idx_raw_endpoint_date ON toteat.raw_api_responses(endpoint_key, business_date);
CREATE INDEX idx_raw_tenant_fetched ON toteat.raw_api_responses(tenant_id, fetched_at DESC);
