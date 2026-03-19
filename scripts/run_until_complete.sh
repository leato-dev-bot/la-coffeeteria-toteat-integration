#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p logs runtime
. .venv/bin/activate

while true; do
  python -m toteat_integration.cli sync --mode backfill >> logs/backfill.log 2>&1 || true
  remaining=$(psql la_coffeeteria -Atc "SELECT count(*) FROM toteat.failed_tasks WHERE resolved_at IS NULL;" )
  progress=$(python -m toteat_integration.cli status || true)
  echo "$(date '+%F %T') remaining_failed_tasks=${remaining} progress=${progress}" >> logs/supervisor.log
  if [ "${remaining}" = "0" ]; then
    pending=$(python - <<'PY'
import json
from pathlib import Path
p = Path('runtime/progress.json')
if not p.exists():
    print('unknown')
else:
    data = json.loads(p.read_text())
    total = data.get('total_tasks', 0)
    completed = data.get('completed_tasks', 0)
    print('done' if total == completed else 'pending')
PY
)
    if [ "$pending" = "done" ]; then
      echo "$(date '+%F %T') supervisor completed all known tasks" >> logs/supervisor.log
      exit 0
    fi
  fi
  sleep 120
done
