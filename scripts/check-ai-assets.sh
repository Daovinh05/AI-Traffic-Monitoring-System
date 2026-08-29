#!/usr/bin/env sh
set -eu

project_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$project_root"

python3 -c "from backend.app.ai.status import missing_assets; missing = missing_assets(); print('\n'.join(missing) if missing else 'AI assets OK'); raise SystemExit(bool(missing))"
