#!/usr/bin/env bash
#
# reindex_crm_dev.sh
#
# Triggers a reindex (_update_by_query) on the dev CRM index for person_ticket
# documents that have the payment_method field. This forces ES to re-index
# those documents so the new mapping takes effect on existing data.
#
# Dev uses a single shared CRM index named 'crm_v1' at elasticsearch:9200.
#
# Usage:
#   ./reindex_crm_dev.sh [ES_HOST]
#
# Arguments:
#   ES_HOST  - Elasticsearch host (default: elasticsearch:9200)
#
set -euo pipefail

ES_HOST="${1:-elasticsearch:9200}"
INDEX="crm_v1"
DOC_TYPE="person_ticket"
QUERY="_exists_:payment_method"

echo "=== Reindexing CRM person_ticket on dev ==="
echo "  Host:     $ES_HOST"
echo "  Index:    $INDEX"
echo "  DocType:  $DOC_TYPE"
echo "  Query:    $QUERY"
echo ""

HTTP_CODE=$(curl -s -o /tmp/es_reindex_response.json -w "%{http_code}" \
    -X POST "http://${ES_HOST}/${INDEX}/${DOC_TYPE}/_update_by_query?q=${QUERY}&conflicts=proceed" \
    -H 'Content-Type: application/json')

RESPONSE=$(cat /tmp/es_reindex_response.json)

if [ "$HTTP_CODE" -ge 200 ] && [ "$HTTP_CODE" -lt 300 ]; then
    echo "SUCCESS: Reindex triggered (HTTP $HTTP_CODE)"
    echo "  Response: $RESPONSE"
else
    echo "FAILED: HTTP $HTTP_CODE"
    echo "  Response: $RESPONSE"
    exit 1
fi
