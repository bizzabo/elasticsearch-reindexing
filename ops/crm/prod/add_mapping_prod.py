#!/usr/bin/env python3
"""
add_mapping_prod.py

Updates the CRM index mapping on ALL production accounts.

Queries the MySQL account_crm_cluster table to discover all
(account_id, index_name, cluster_name) tuples, then issues a
PUT _mapping request for each unique (index, cluster) pair.

This script fixes the import path bug from the original add_mapping.py
and supports all three prod CRM clusters (crm-cluster-1, -2, -3).

Usage:
    python3 add_mapping_prod.py --doc_type person_ticket --mapping_file ../mappings/person_ticket_payment_method.json [--dry_run]

Arguments:
    --doc_type       Document type to update (e.g. person_ticket)
    --mapping_file   Path to the JSON mapping body file
    --dry_run        Print what would be done without making changes
    --config         Path to config.ini (default: ../config.ini)

WARNING: This script modifies PRODUCTION indexes. Review carefully before running.
         DO NOT run this without approval.
"""

import argparse
import configparser
import json
import os
import sys

# Fix import path: ensure lib/ is on sys.path regardless of working directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LIB_DIR = os.path.join(SCRIPT_DIR, "..", "lib")
sys.path.insert(0, LIB_DIR)

from elastic_util import put_mapping
from mysql_util import get_account_crm_indexes


def load_config(config_path):
    """Load cluster host mapping and MySQL config from config.ini."""
    config = configparser.ConfigParser()
    config.read(config_path)

    host_map = {}
    for key, value in config.items("clusters"):
        host_map[key.strip()] = value.strip()

    mysql_config = {
        "host": config.get("mysql", "host"),
        "user": config.get("mysql", "user"),
        "database": config.get("mysql", "database"),
    }

    return host_map, mysql_config


def main():
    parser = argparse.ArgumentParser(
        description="Add a field mapping to all CRM indexes in production"
    )
    parser.add_argument(
        "--doc_type",
        required=True,
        help="Document type to update (e.g. person_ticket)",
    )
    parser.add_argument(
        "--mapping_file",
        required=True,
        help="Path to JSON file containing the mapping body",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Print actions without executing them",
    )
    parser.add_argument(
        "--config",
        default=os.path.join(SCRIPT_DIR, "..", "config.ini"),
        help="Path to config.ini (default: ../config.ini)",
    )
    parser.add_argument(
        "--update_query",
        default=None,
        help="If provided, also run _update_by_query with this query on each index "
             "(e.g. '_exists_:payment_method')",
    )
    args = parser.parse_args()

    # Load mapping body
    if not os.path.isfile(args.mapping_file):
        print(f"ERROR: Mapping file not found: {args.mapping_file}", file=sys.stderr)
        sys.exit(1)

    with open(args.mapping_file) as f:
        mapping_body = json.load(f)

    # Load config
    config_path = os.path.abspath(args.config)
    if not os.path.isfile(config_path):
        print(f"ERROR: Config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    host_map, mysql_config = load_config(config_path)
    print(f"Loaded {len(host_map)} cluster(s) from config: {list(host_map.keys())}")

    # Get all account/index/cluster tuples from MySQL
    print(f"Querying MySQL at {mysql_config['host']}...")
    rows = get_account_crm_indexes(
        mysql_config["host"], mysql_config["user"], mysql_config["database"]
    )
    if not rows:
        print("ERROR: No accounts found in account_crm_cluster table.", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(rows)} account-index mappings")

    # Deduplicate by (index_name, cluster_name) — many accounts share the same index
    unique_pairs = {}
    for row in rows:
        key = (row["index_name"], row["cluster_name"])
        if key not in unique_pairs:
            unique_pairs[key] = []
        unique_pairs[key].append(row["account_id"])

    print(f"Unique (index, cluster) pairs to update: {len(unique_pairs)}")
    print("")

    # Process each unique index/cluster pair
    successes = 0
    failures = 0

    for (index_name, cluster_name), account_ids in sorted(unique_pairs.items()):
        if cluster_name not in host_map:
            print(
                f"  SKIP {index_name} on {cluster_name}: "
                f"cluster not found in config.ini (accounts: {account_ids[:3]}...)",
                file=sys.stderr,
            )
            failures += 1
            continue

        host = host_map[cluster_name]

        if args.dry_run:
            print(
                f"  DRY RUN: PUT http://{host}:9200/{index_name}/_mapping/{args.doc_type} "
                f"(accounts: {len(account_ids)})"
            )
            successes += 1
            continue

        print(f"  Updating {index_name} on {host} ({len(account_ids)} accounts)...")
        ok, response = put_mapping(host, index_name, args.doc_type, mapping_body)

        if ok:
            print(f"    OK: {response}")
            successes += 1
        else:
            print(f"    FAILED: {response}", file=sys.stderr)
            failures += 1

    print("")
    print(f"=== Results: {successes} succeeded, {failures} failed ===")

    if failures > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
