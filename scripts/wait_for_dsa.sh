#!/usr/bin/env bash
# wait_for_dsa.sh — Poll until the Girder REST API returns HTTP 200.
#
# Usage:
#   ./scripts/wait_for_dsa.sh [<url>] [<timeout_seconds>]
#
# Defaults:
#   url     = http://localhost:8080/api/v1/system/version
#   timeout = 180 seconds

set -euo pipefail

URL="${1:-http://localhost:8080/api/v1/system/version}"
TIMEOUT="${2:-180}"
INTERVAL=5

elapsed=0
while true; do
    if curl -sf "$URL" -o /dev/null 2>/dev/null; then
        echo "✅ DSA is ready at $URL"
        exit 0
    fi

    if (( elapsed >= TIMEOUT )); then
        echo "❌ DSA did not respond within ${TIMEOUT}s at $URL" >&2
        exit 1
    fi

    printf "   … waiting (%ds elapsed)\r" "$elapsed"
    sleep "$INTERVAL"
    elapsed=$(( elapsed + INTERVAL ))
done
