#!/usr/bin/env bash

set -euo pipefail

# Simple end-to-end workflow that results in loan denial
# It drives the chat steps with a deliberately low salary so that
# EMI-to-salary ratio exceeds 50%, triggering rejection in EligibilityAgent.

BASE=${BASE:-"http://localhost:8001"}
CUST=${CUST:-"CUST_DENY01"}
NAME=${NAME:-"Amit Verma"}
LOAN_AMOUNT_MSG=${LOAN_AMOUNT_MSG:-"I need 300000 rupees"}
TENURE_MSG=${TENURE_MSG:-"24 months"}
PAN=${PAN:-"ABCDE1234F"}
AADHAR=${AADHAR:-"123456789012"}
# Low salary to force rejection (EMI ratio > 50%)
SALARY_MSG=${SALARY_MSG:-"My salary is 20000"}

echo "Health:"; curl -s "$BASE/health"; echo

echo "Start chat:"
RESP=$(curl -s -X POST "$BASE/chat" -H "Content-Type: application/json" -d "{\"customer_id\":\"$CUST\",\"message\":\"Hello\"}")
echo "$RESP"

# Extract application_id without relying on jq
APP_ID=$(echo "$RESP" | sed -n 's/.*"application_id"[[:space:]]*:[[:space:]]*"\([^"[:space:]]*\)".*/\1/p')
if [ -z "$APP_ID" ]; then
  echo "Failed to get application_id from response" >&2
  exit 1
fi
echo "App ID: $APP_ID"

send(){ MSG="$1"; echo "Send: $MSG"; RESP=$(curl -s -X POST "$BASE/chat" -H "Content-Type: application/json" -d "{\"customer_id\":\"$CUST\",\"application_id\":\"$APP_ID\",\"message\":\"$MSG\"}"); echo "$RESP"; }

# Provide details step-by-step
send "My name is $NAME"
send "$LOAN_AMOUNT_MSG"
send "$TENURE_MSG"
send "$PAN"
send "$AADHAR"
send "Continue"     # Underwriting response
send "Continue"     # Move into eligibility
send "$SALARY_MSG"  # Trigger rejection via high EMI ratio

echo "Get application status:"
STATUS_JSON=$(curl -s "$BASE/application/$APP_ID")
echo "$STATUS_JSON"

# Print summary
STATUS=$(printf "%s" "$STATUS_JSON" | sed -n 's/.*"status"[[:space:]]*:[[:space:]]*"\([^"[:space:]]*\)".*/\1/p')
REASON=$(printf "%s" "$STATUS_JSON" | sed -n 's/.*"rejection_reason"[[:space:]]*:[[:space:]]*"\([^"[:space:]]*\)".*/\1/p')
echo "\nSummary:"
echo "- application_id: $APP_ID"
echo "- status: ${STATUS:-unknown}"
if [ "${STATUS:-}" = "rejected" ] && [ -n "${REASON:-}" ]; then
  echo "- rejection_reason: $REASON"
fi

if [ "${STATUS:-}" != "rejected" ]; then
  echo "Warning: Expected rejected status but got '$STATUS'" >&2
fi