#!/usr/bin/env bash
#
# update_and_reindex_crm_dev.sh
#
# Convenience script that runs both the mapping update and reindex steps
# for the CRM index on dev. This is the recommended way for any engineer
# to apply the payment_method mapping change on dev.
#
# Usage:
#   ./update_and_reindex_crm_dev.sh [ES_HOST]
#
# Arguments:
#   ES_HOST  - Elasticsearch host (default: elasticsearch:9200)
#
# Prerequisites:
#   - Run from within the dev Kubernetes environment (e.g., kubectl exec
#     into a pod with network access to the ES service, or port-forward
#     the ES service locally).
#
# Example (port-forward):
#   kubectl port-forward svc/elasticsearch 9200:9200 &
#   ./update_and_reindex_crm_dev.sh localhost:9200
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ES_HOST="${1:-elasticsearch:9200}"

echo "============================================="
echo "  CRM Dev: Update Mapping + Reindex"
echo "  Host: $ES_HOST"
echo "============================================="
echo ""

echo "--- Step 1/2: Update mapping ---"
bash "${SCRIPT_DIR}/update_crm_mapping_dev.sh" "$ES_HOST"

echo ""
echo "--- Step 2/2: Reindex person_ticket documents ---"
bash "${SCRIPT_DIR}/reindex_crm_dev.sh" "$ES_HOST"

echo ""
echo "============================================="
echo "  Done! payment_method mapping applied on dev"
echo "============================================="
