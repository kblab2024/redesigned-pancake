#!/usr/bin/env bash
# start_dsa.sh — Start the Digital Slide Archive / HistomicsUI stack.
#
# Run this script from anywhere inside the dev container:
#   ./scripts/start_dsa.sh
#
# After the stack is up, open http://localhost:8080 in your browser.
# Default credentials: admin / password

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$REPO_ROOT/dsa/docker-compose.yml"

echo "▶  Starting DSA stack (docker compose up)…"
docker compose -f "$COMPOSE_FILE" up -d --remove-orphans

echo ""
echo "⏳ Waiting for HistomicsUI to become ready…"
"$SCRIPT_DIR/wait_for_dsa.sh"

echo ""
echo "✅ HistomicsUI is running at http://localhost:8080"
echo "   Login: admin / password"
echo ""
echo "   Useful commands:"
echo "     Stop stack   : ./scripts/stop_dsa.sh"
echo "     View logs    : docker compose -f dsa/docker-compose.yml logs -f"
echo "     Run API test : python3 scripts/test_dsa_api.py"
