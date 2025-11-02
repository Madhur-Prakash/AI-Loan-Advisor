#!/usr/bin/env bash
set -euo pipefail

# Configurable parameters via env vars
BASE=${BASE_URL:-http://localhost:8001}
CUSTOMER_ID=${CUSTOMER_ID:-CUST020}
NAME=${NAME:-Rahul}
LOAN_AMOUNT=${LOAN_AMOUNT:-300000}
TENURE=${TENURE:-36}
PAN=${PAN:-ABCDE1234F}
AADHAR=${AADHAR:-123456789012}
SALARY=${SALARY:-80000}
OUT_DIR=${OUT_DIR:-/tmp}
APP_ID=${APP_ID:-}
FORCE_AUTO=${FORCE_AUTO:-}

# Optional arg: --app-id <ID>
while [[ $# -gt 0 ]]; do
  case "$1" in
    --app-id)
      APP_ID="$2"; shift 2;;
    --force-auto)
      FORCE_AUTO="true"; shift;;
    *)
      echo "Unknown argument: $1"; shift;;
  esac
done

curl_s() { curl -s -S "$@"; }

echo "Checking server health at $BASE..."
if ! curl_s "$BASE/health" | python -c 'import sys,json; d=json.load(sys.stdin); sys.exit(0 if d.get("status")=="healthy" else 1)'; then
  echo "Error: server not healthy at $BASE" >&2
  exit 1
fi

if [[ -z "$APP_ID" ]]; then
  echo "1) Start conversation"
  FIRST=$(curl_s -X POST "$BASE/chat" -H "Content-Type: application/json" -d "{\"customer_id\":\"$CUSTOMER_ID\",\"message\":\"Hello\"}")
  echo "$FIRST"
  APP_ID=$(printf '%s' "$FIRST" | python -c 'import sys,json; d=json.load(sys.stdin); print(d.get("application_id",""))')
  if [[ -z "$APP_ID" ]]; then
    echo "Failed to obtain application_id" >&2
    exit 1
  fi
  echo "App ID: $APP_ID"
fi

step() {
  local label="$1"; shift
  local msg="$1"; shift || true
  echo "$label"
  curl_s -X POST "$BASE/chat" -H "Content-Type: application/json" \
    -d "{\"customer_id\":\"$CUSTOMER_ID\",\"application_id\":\"$APP_ID\",\"message\":$msg}"
}

if [[ -z "${RESUME_ONLY:-}" && -z "${RESUME:-}" ]]; then
  # Run guided steps when initiating a fresh application
  step "2) Provide name" "\"My name is $NAME\""
  step "3) Express interest" "\"I am interested in a personal loan\""
  step "4) Provide loan amount" "\"I need $LOAN_AMOUNT rupees\""
  step "5) Provide tenure" "\"$TENURE months\""
  step "6) Provide PAN" "\"$PAN\""
  step "7) Provide Aadhar" "\"$AADHAR\""
  step "8) Continue workflow" "\"Continue\""
  step "9) Provide salary" "\"My salary is $SALARY\""
else
  echo "Resuming existing application: $APP_ID"
  # Ensure we use the correct customer_id from application when resuming
  APP_JSON_INIT=$(curl_s -X GET "$BASE/application/$APP_ID")
  CUST_FROM_APP=$(printf '%s' "$APP_JSON_INIT" | python -c 'import sys,json; d=json.load(sys.stdin); print(d.get("customer",{}).get("customer_id",""))')
  if [[ -n "$CUST_FROM_APP" ]]; then
    CUSTOMER_ID="$CUST_FROM_APP"
    echo "Using customer_id from application: $CUSTOMER_ID"
  else
    echo "Warning: could not derive customer_id from application; using env: $CUSTOMER_ID"
  fi
fi

echo "10) Get application status"
APP_JSON=$(curl_s -X GET "$BASE/application/$APP_ID")
echo "$APP_JSON"
STATUS_INITIAL=$(printf '%s' "$APP_JSON" | python -c 'import sys,json; d=json.load(sys.stdin); print(d.get("status",""))')

SANCTION_PATH=$(printf '%s' "$APP_JSON" | python -c 'import sys,json; d=json.load(sys.stdin); print(d.get("sanction_letter_path",""))')
if [[ "$FORCE_AUTO" == "true" || -z "$SANCTION_PATH" || ( "$STATUS_INITIAL" != "completed" && "$STATUS_INITIAL" != "approved" ) ]]; then
  [[ "$FORCE_AUTO" == "true" ]] && echo "Force auto-advance enabled; driving workflow to completion..." || echo "Auto-completing workflow until approval..."
  # Helper to extract a value from JSON
  jget() { printf '%s' "$1" | python -c "import sys,json; d=json.load(sys.stdin); print(d.get('$2',''))"; }
  # Poll and drive workflow towards completion
  for i in {1..10}; do
    APP_JSON=$(curl_s -X GET "$BASE/application/$APP_ID")
    STATUS=$(jget "$APP_JSON" status)
    echo "[poll $i] Status: $STATUS"
    [[ -z "$STATUS" ]] && sleep 1 && continue
    if [[ "$STATUS" == "completed" || "$STATUS" == "approved" ]]; then
      break
    fi
    case "$STATUS" in
      kyc_verification)
        step "- Resend PAN" "\"$PAN\""
        step "- Resend Aadhar" "\"$AADHAR\""
        ;;
      eligibility_check)
        step "- Provide salary" "\"My salary is $SALARY\""
        ;;
      underwriting)
        step "- Continue underwriting" "\"Continue\""
        ;;
      sales_discussion)
        step "- Continue sales" "\"Continue\""
        ;;
      initiated)
        step "- Continue initiated" "\"Continue\""
        ;;
      *)
        step "- Continue workflow" "\"Continue\""
        ;;
    esac
    sleep 1
  done
  # Refresh sanction path and status after loop
  APP_JSON=$(curl_s -X GET "$BASE/application/$APP_ID")
  SANCTION_PATH=$(printf '%s' "$APP_JSON" | python -c 'import sys,json; d=json.load(sys.stdin); print(d.get("sanction_letter_path",""))')
  STATUS_FINAL=$(printf '%s' "$APP_JSON" | python -c 'import sys,json; d=json.load(sys.stdin); print(d.get("status",""))')
  echo "Final status after auto-advance: $STATUS_FINAL"
else
  echo "Skipping auto-advance (status: $STATUS_INITIAL, sanction path present)."
fi

echo "11) Download sanction letter"
OUT_FILE="$OUT_DIR/sanction_letter_${APP_ID}.pdf"
curl -L -o "$OUT_FILE" "$BASE/sanction-letter/$APP_ID"
ls -l "$OUT_FILE"

echo
echo "Summary:"
echo "- application_id: $APP_ID"
STATUS=$(printf '%s' "$APP_JSON" | python -c 'import sys,json; d=json.load(sys.stdin); print(d.get("status",""))')
echo "- status: $STATUS"
echo "- remote path: $SANCTION_PATH"
echo "- local file: $OUT_FILE"