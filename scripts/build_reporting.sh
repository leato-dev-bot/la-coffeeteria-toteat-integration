#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
. .venv/bin/activate
psql la_coffeeteria -f sql/010_reporting.sql
