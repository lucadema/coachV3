#!/bin/bash

set -euo pipefail

# -----------------------------------------------------------------------------
# check_remote.sh
#
# Verifies the current cloud deployment for Coach V3.
#
# What it checks:
# 1. Backend /health
# 2. Backend /session_initialise
# 3. Backend /user_message
# 4. Backend /debug_trace/{session_id}
# 5. Frontend URL reachability (optional)
#
# Usage:
#   ./check_remote.sh <BACKEND_URL> [FRONTEND_URL]
#
# Or with environment variables:
#   BACKEND_URL="https://your-backend.onrender.com" \
#   FRONTEND_URL="https://your-frontend.streamlit.app" \
#   ./check_remote.sh
#
# Notes:
# - BACKEND_URL should be the root URL, without a trailing slash.
# - FRONTEND_URL is optional.
# - This script verifies remote API behaviour and basic frontend reachability.
#   It does not simulate browser clicks inside the Streamlit UI.
# - For Streamlit deployments, HTTP 303 auth redirects are treated as acceptable.
# -----------------------------------------------------------------------------

BACKEND_URL="${1:-${BACKEND_URL:-}}"
FRONTEND_URL="${2:-${FRONTEND_URL:-}}"

if [[ -z "${BACKEND_URL}" ]]; then
  echo "ERROR: BACKEND_URL not provided."
  echo "Usage: ./check_remote.sh <BACKEND_URL> [FRONTEND_URL]"
  echo 'Example: ./check_remote.sh https://your-backend.onrender.com https://your-frontend.streamlit.app'
  exit 1
fi

# Remove any trailing slash for consistency
BACKEND_URL="${BACKEND_URL%/}"
FRONTEND_URL="${FRONTEND_URL%/}"

banner() {
  echo
  echo "========================================================================"
  echo "$1"
  echo "========================================================================"
}

ok() {
  echo "OK: $1"
}

info() {
  echo "INFO: $1"
}

fail() {
  echo "ERROR: $1"
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || fail "Required command not found: $1"
}

http_code() {
  local url="$1"
  curl -sS -o /tmp/check_remote_body.txt -w "%{http_code}" "$url"
}

post_json() {
  local url="$1"
  local json="$2"
  curl -sS -X POST "$url" \
    -H "Content-Type: application/json" \
    -d "$json"
}

require_command curl
require_command python3

banner "Coach V3 remote deployment check"
echo "Backend URL : ${BACKEND_URL}"
if [[ -n "${FRONTEND_URL}" ]]; then
  echo "Frontend URL: ${FRONTEND_URL}"
else
  echo "Frontend URL: not provided (frontend reachability check will be skipped)"
fi

# -----------------------------------------------------------------------------
# 1. Backend /health
# -----------------------------------------------------------------------------
banner "1. Checking backend /health"

HEALTH_CODE=$(http_code "${BACKEND_URL}/health")
HEALTH_BODY=$(cat /tmp/check_remote_body.txt)

[[ "${HEALTH_CODE}" == "200" ]] || fail "/health returned HTTP ${HEALTH_CODE}. Body: ${HEALTH_BODY}"

python3 - <<'PY' "${HEALTH_BODY}"
import json, sys
body = sys.argv[1]
payload = json.loads(body)
assert payload == {"status": "ok"}, f"Unexpected /health payload: {payload}"
print("Parsed /health payload:", payload)
PY

ok "/health returned 200 with expected payload"

# -----------------------------------------------------------------------------
# 2. Backend /session_initialise
# -----------------------------------------------------------------------------
banner "2. Checking backend /session_initialise"

INIT_BODY=$(curl -sS "${BACKEND_URL}/session_initialise")

SESSION_ID=$(python3 - <<'PY' "${INIT_BODY}"
import json, sys
payload = json.loads(sys.argv[1])

# Support both possible shapes:
# A. flat SessionView => {"session_id": "...", "stage": "...", "state": "..."}
# B. nested => {"session": {"session_id": "...", ...}, ...}

if "session_id" in payload:
    session_id = payload["session_id"]
    stage = payload.get("stage")
    state = payload.get("state")
elif "session" in payload and isinstance(payload["session"], dict):
    session_id = payload["session"]["session_id"]
    stage = payload["session"].get("stage")
    state = payload["session"].get("state")
else:
    raise AssertionError(f"Unexpected /session_initialise payload shape: {payload}")

assert session_id, "session_id missing or empty"
print(session_id)
PY
)

echo "Init payload: ${INIT_BODY}"
ok "/session_initialise returned a valid session_id: ${SESSION_ID}"

# -----------------------------------------------------------------------------
# 3. Backend /user_message
# -----------------------------------------------------------------------------
banner "3. Checking backend /user_message"

USER_JSON=$(python3 - <<'PY' "${SESSION_ID}"
import json, sys
session_id = sys.argv[1]
payload = {
    "session_id": session_id,
    "user_message": "Remote smoke test message"
}
print(json.dumps(payload))
PY
)

USER_BODY=$(post_json "${BACKEND_URL}/user_message" "${USER_JSON}")

python3 - <<'PY' "${USER_BODY}" "${SESSION_ID}"
import json, sys
payload = json.loads(sys.argv[1])
session_id = sys.argv[2]

assert "session" in payload, f"Missing session in /user_message payload: {payload}"
session = payload["session"]
assert session["session_id"] == session_id, f"Unexpected session_id in /user_message payload: {payload}"

print("Parsed /user_message payload:", payload)
PY

echo "User message payload: ${USER_BODY}"
ok "/user_message returned a valid session reply"

# -----------------------------------------------------------------------------
# 4. Backend /debug_trace/{session_id}
# -----------------------------------------------------------------------------
banner "4. Checking backend /debug_trace/{session_id}"

DEBUG_BODY=$(curl -sS "${BACKEND_URL}/debug_trace/${SESSION_ID}")

python3 - <<'PY' "${DEBUG_BODY}" "${SESSION_ID}"
import json, sys
payload = json.loads(sys.argv[1])
session_id = sys.argv[2]

assert "session" in payload, f"Missing session in /debug_trace payload: {payload}"
session = payload["session"]
assert session["session_id"] == session_id, f"Unexpected session_id in /debug_trace payload: {payload}"

print("Parsed /debug_trace payload:", payload)
PY

echo "Debug payload: ${DEBUG_BODY}"
ok "/debug_trace returned a valid debug reply"

# -----------------------------------------------------------------------------
# 5. Optional frontend reachability
# -----------------------------------------------------------------------------
if [[ -n "${FRONTEND_URL}" ]]; then
  banner "5. Checking frontend reachability"

  FRONTEND_CODE=$(http_code "${FRONTEND_URL}")
  FRONTEND_BODY=$(cat /tmp/check_remote_body.txt)

  if [[ "${FRONTEND_CODE}" == "200" ]]; then
    echo "Frontend body preview: ${FRONTEND_BODY:0:200}"
    ok "Frontend URL is reachable"
  elif [[ "${FRONTEND_CODE}" == "303" ]]; then
    echo "Frontend body preview: ${FRONTEND_BODY:0:200}"
    info "Frontend returned HTTP 303 (redirect). This is acceptable for Streamlit deployments using auth redirects."
    ok "Frontend deployment is reachable via redirect"
  else
    fail "Frontend returned HTTP ${FRONTEND_CODE}. Body preview: ${FRONTEND_BODY:0:200}"
  fi
else
  banner "5. Frontend reachability"
  echo "Skipped because FRONTEND_URL was not provided."
fi

banner "Remote deployment check passed"
echo "Backend and optional frontend checks completed successfully."
