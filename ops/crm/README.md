# CRM Index Update Scripts

Scripts for updating CRM Elasticsearch index mappings and reindexing documents.

Created for [CC-2591] — adding `payment_method` to the `person_ticket` mapping.

## Directory Structure

```
ops/crm/
├── config.ini                          # Prod cluster host mapping + MySQL config
├── mappings/
│   └── person_ticket_payment_method.json  # The mapping body for payment_method
├── lib/
│   ├── elastic_util.py                 # ES helper functions
│   └── mysql_util.py                   # MySQL helper functions
├── dev/
│   ├── update_crm_mapping_dev.sh       # (1) Update mapping on dev
│   ├── reindex_crm_dev.sh             # (2) Reindex on dev
│   └── update_and_reindex_crm_dev.sh  # (3) Combined: mapping + reindex on dev
└── prod/
    ├── add_mapping_prod.py             # (4) Update mapping on all prod indexes
    └── reindex_by_scope_prod.py        # (5) Reindex by account/event on prod
```

## Dev Scripts

### Prerequisites

You need network access to the dev Elasticsearch service. Either:
- Run from within the dev k8s cluster, OR
- Port-forward the ES service: `kubectl port-forward svc/elasticsearch 9200:9200`

### (1) Update CRM mapping on dev

Adds the `payment_method` field to the `person_ticket` mapping on the single `crm_v1` index:

```bash
# From within k8s (default host: elasticsearch:9200)
./ops/crm/dev/update_crm_mapping_dev.sh

# With port-forward
./ops/crm/dev/update_crm_mapping_dev.sh localhost:9200
```

### (2) Reindex on dev

Triggers `_update_by_query` on person_ticket documents that have a `payment_method` field:

```bash
./ops/crm/dev/reindex_crm_dev.sh
# or
./ops/crm/dev/reindex_crm_dev.sh localhost:9200
```

### (3) Combined: Update + Reindex on dev (recommended)

Runs both steps sequentially — **this is the easiest way for any engineer to apply the change**:

```bash
./ops/crm/dev/update_and_reindex_crm_dev.sh
# or
./ops/crm/dev/update_and_reindex_crm_dev.sh localhost:9200
```

## Prod Scripts

### Prerequisites

- Python 3.6+
- MySQL client (`mysql` CLI) installed
- Network access to prod ES clusters and MySQL
- **Review and approval before running**

### (4) Update mapping on all prod CRM indexes

Queries MySQL for all account/index/cluster mappings and applies the mapping update to every unique index:

```bash
# Dry run first (always recommended)
python3 ops/crm/prod/add_mapping_prod.py \
  --doc_type person_ticket \
  --mapping_file ops/crm/mappings/person_ticket_payment_method.json \
  --dry_run

# Actual run
python3 ops/crm/prod/add_mapping_prod.py \
  --doc_type person_ticket \
  --mapping_file ops/crm/mappings/person_ticket_payment_method.json
```

### (5) Reindex by account or event on prod

After updating the mapping, reindex specific accounts/events that need the data re-processed:

```bash
# Reindex a specific account (dry run)
python3 ops/crm/prod/reindex_by_scope_prod.py \
  --account_id 12345 \
  --cluster crm-cluster-1 \
  --index crm_account_12345 \
  --dry_run

# Reindex a specific event
python3 ops/crm/prod/reindex_by_scope_prod.py \
  --event_id 67890 \
  --cluster crm-cluster-2 \
  --index crm_account_99999

# With custom query
python3 ops/crm/prod/reindex_by_scope_prod.py \
  --account_id 12345 \
  --cluster crm-cluster-1 \
  --index crm_account_12345 \
  --query "_exists_:payment_method"
```

## Config

`config.ini` maps cluster names to hostnames. Currently configured with all three prod CRM clusters:

- `crm-cluster-1` → `es0-prod-crm-1.db.bizzabo.com`
- `crm-cluster-2` → `es0-prod-crm-2.db.bizzabo.com`
- `crm-cluster-3` → `es0-prod-crm-3.db.bizzabo.com`

## Adding New Mappings

To add a different field mapping in the future:

1. Create a new JSON file in `mappings/` with the field definition
2. For dev: update the `MAPPING_FILE` path in the dev scripts, or modify the scripts to accept it as a parameter
3. For prod: pass `--mapping_file` pointing to your new JSON file
