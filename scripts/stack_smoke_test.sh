#!/usr/bin/env bash
# =============================================================================
# Stack smoke test
#
# Verifies all 3 services (converge, orchestrator, UI) are running and
# connected. Can work against Docker Compose or locally started services.
#
# Usage:
#   ./scripts/stack_smoke_test.sh                  # default ports
#   CONVERGE_URL=http://host:9876 ./scripts/stack_smoke_test.sh
# =============================================================================

set -euo pipefail

CONVERGE_URL="${CONVERGE_URL:-http://127.0.0.1:9876}"
ORCHESTRATOR_URL="${ORCHESTRATOR_URL:-http://127.0.0.1:8787}"
UI_URL="${UI_URL:-http://127.0.0.1:9988}"

PASS=0
FAIL=0

check() {
    local name="$1"
    local url="$2"
    local expected_status="${3:-200}"

    status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$url" 2>/dev/null || echo "000")
    if [ "$status" = "$expected_status" ]; then
        echo "  PASS  $name ($url) -> $status"
        PASS=$((PASS + 1))
    else
        echo "  FAIL  $name ($url) -> $status (expected $expected_status)"
        FAIL=$((FAIL + 1))
    fi
}

check_json_field() {
    local name="$1"
    local url="$2"
    local field="$3"
    local expected="$4"

    value=$(curl -s --max-time 5 "$url" 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('$field',''))" 2>/dev/null || echo "ERROR")
    if [ "$value" = "$expected" ]; then
        echo "  PASS  $name ($field=$value)"
        PASS=$((PASS + 1))
    else
        echo "  FAIL  $name ($field=$value, expected $expected)"
        FAIL=$((FAIL + 1))
    fi
}

echo "=== Stack Smoke Test ==="
echo ""
echo "--- 1. Health checks ---"
check "Converge /health"       "$CONVERGE_URL/health"
check "Orchestrator /health"   "$ORCHESTRATOR_URL/health"
check "UI /health/live"        "$UI_URL/health/live"
check "UI /health/ready"       "$UI_URL/health/ready"

echo ""
echo "--- 2. Service status ---"
check_json_field "Converge health status" "$CONVERGE_URL/health" "status" "ok"
check_json_field "Orchestrator health status" "$ORCHESTRATOR_URL/health" "status" "healthy"
check_json_field "UI live status" "$UI_URL/health/live" "status" "ok"

echo ""
echo "--- 3. UI overview loads ---"
check "UI overview" "$UI_URL/api/v1/overview"

echo ""
echo "--- 4. UI serves frontend ---"
check "UI SPA shell" "$UI_URL/"

echo ""
echo "--- 5. Cross-service connectivity ---"
# UI overview should report service connectivity
orch_reachable=$(curl -s --max-time 5 "$UI_URL/api/v1/overview" 2>/dev/null | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('services', {}).get('orchestrator', {}).get('reachable', False))
except:
    print('ERROR')
" 2>/dev/null || echo "ERROR")

if [ "$orch_reachable" = "True" ]; then
    echo "  PASS  UI can reach orchestrator"
    PASS=$((PASS + 1))
else
    echo "  FAIL  UI cannot reach orchestrator (reachable=$orch_reachable)"
    FAIL=$((FAIL + 1))
fi

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
