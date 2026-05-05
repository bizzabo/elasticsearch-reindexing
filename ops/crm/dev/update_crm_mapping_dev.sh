#!/usr/bin/env bash
#
# update_crm_mapping_dev.sh
#
# Updates the CRM index mapping on dev to add the payment_method field
# to the person_ticket document type.
#
# Dev uses a single shared CRM index named 'crm_v1' running in Kubernetes
# at elasticsearch:9200.
#
# Usage:
#   ./update_crm_mapping_dev.sh [ES_HOST]
#
# Arguments:
#   ES_HOST  - Elasticsearch host (default: elasticsearch:9200)
#
# This script must be run from within the dev Kubernetes environment
# (e.g., via kubectl exec or a pod with network access to ES).
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ES_HOST="${1:-elasticsearch:9200}"
INDEX="crm_v1"
DOC_TYPE="person_ticket"
MAPPING_FILE="${SCRIPT_DIR}/../mappings/person_ticket_payment_method.json"

if [ ! -f "$MAPPING_FILE" ]; then
    echo "ERROR: Mapping file not found: $MAPPING_FILE"
    exit 1
fi

echo "=== Updating CRM mapping on dev ==="
echo "  Host:     $ES_HOST"
echo "  Index:    $INDEX"
echo "  DocType:  $DOC_TYPE"
echo "  Mapping:  $MAPPING_FILE"
echo ""

HTTP_CODE=$(curl -s -o /tmp/es_response.json -w "%{http_code}" \
    -X PUT "http://${ES_HOST}/${INDEX}/_mapping/${DOC_TYPE}" \
    -H 'Content-Type: application/json' \
    -d @"$MAPPING_FILE")

RESPONSE=$(cat /tmp/es_response.json)

if [ "$HTTP_CODE" -ge 200 ] && [ "$HTTP_CODE" -lt 300 ]; then
    echo "SUCCESS: Mapping updated (HTTP $HTTP_CODE)"
    echo "  Response: $RESPONSE"
else
    echo "FAILED: HTTP $HTTP_CODE"
    echo "  Response: $RESPONSE"
    exit 1
fi
