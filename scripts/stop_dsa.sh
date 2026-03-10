#!/usr/bin/env bash
# stop_dsa.sh — Stop (and optionally remove) the DSA / HistomicsUI stack.
#
# Usage:
#   ./scripts/stop_dsa.sh           # stops containers, keeps volumes
#   ./scripts/stop_dsa.sh --clean   # stops containers AND removes all volumes

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$REPO_ROOT/dsa/docker-compose.yml"

CLEAN=false
for arg in "$@"; do
    [[ "$arg" == "--clean" ]] && CLEAN=true
done

if $CLEAN; then
    echo "⚠️  Removing all containers AND volumes (data will be lost)…"
    docker compose -f "$COMPOSE_FILE" down --volumes --remove-orphans
    echo "✅ DSA stack removed (volumes deleted)."
else
    echo "▶  Stopping DSA stack…"
    docker compose -f "$COMPOSE_FILE" down --remove-orphans
    echo "✅ DSA stack stopped (data volumes preserved)."
fi
