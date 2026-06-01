#!/usr/bin/env bash
set -euo pipefail

BASE_URL=${1:-http://127.0.0.1:8000}

echo "[1] Health"
curl -sS "$BASE_URL/health" | python -m json.tool

echo "[2] Create project"
PROJECT=$(curl -sS -X POST "$BASE_URL/projects" \
  -H 'Content-Type: application/json' \
  -d '{"name":"STING Project","target_name":"STING","synonyms":["TMEM173"]}')
echo "$PROJECT" | python -m json.tool
PROJECT_ID=$(echo "$PROJECT" | python -c 'import json,sys;print(json.load(sys.stdin)["id"])')

echo "[3] Create monitor rule"
curl -sS -X POST "$BASE_URL/projects/$PROJECT_ID/rules" \
  -H 'Content-Type: application/json' \
  -d '{"keywords":["STING inhibitor"],"assignees":["Company A"],"ipc_cpc":["C07D"],"severity":"P1","enabled":true}' | python -m json.tool

echo "[4] Create event"
curl -sS -X POST "$BASE_URL/events" \
  -H 'Content-Type: application/json' \
  -d "{\"project_id\":$PROJECT_ID,\"patent_id\":\"WO2026123456\",\"event_type\":\"new_publication\",\"severity\":\"P1\",\"summary\":\"Core company filed new STING series\"}" | python -m json.tool

echo "[5] Project summary"
curl -sS "$BASE_URL/projects/$PROJECT_ID/summary" | python -m json.tool

echo "[6] Project events"
curl -sS "$BASE_URL/projects/$PROJECT_ID/events?severity=P1" | python -m json.tool

echo "Smoke test completed."
