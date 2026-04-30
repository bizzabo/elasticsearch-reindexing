#!/usr/bin/env python3
"""
reindex_by_scope_prod.py

Reindex (via _update_by_query) person_ticket documents on production,
scoped to a specific account or event.

This is used after adding a new mapping field to re-process existing documents
so the new field takes effect.

Usage:
    # Reindex all person_tickets for a specific account
    python3 reindex_by_scope_prod.py --account_id 12345 --cluster crm-cluster-1

    # Reindex all person_tickets for a specific event
    python3 reindex_by_scope_prod.py --event_id 67890 --cluster crm-cluster-1

    # Dry run
    python3 reindex_by_scope_prod.py --account_id 12345 --cluster crm-cluster-1 --dry_run

Arguments:
    --account_id    Account ID to scope reindexing to
    --event_id      Event ID to scope reindexing to (alternative to account_id)
    --cluster       Cluster name (e.g. crm-cluster-1) or direct host:port
    --index         Index name (default: looked up from MySQL for the account)
    --doc_type      Document type (default: person_ticket)
    --query         Override the reindex query (default: account/event scoped)
    --config        Path to config.ini (default: ../config.ini)
    --dry_run       Print what would be done without making changes

WARNING: This script runs queries on PRODUCTION. Review carefully.
         DO NOT run without approval.
"""

import argparse
import configparser
import json
import os
import sys
import urllib.request
import urllib.error

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LIB_DIR = os.path.join(SCRIPT_DIR, "..", "lib")
sys.path.insert(0, LIB_DIR)

from elastic_util import update_by_query


def load_host_map(config_path):
    """Load cluster -> host mapping from config.ini."""
    config = configparser.ConfigParser()
    config.read(config_path)
    host_map = {}
    for key, value in config.items("clusters"):
        host_map[key.strip()] = value.strip()
    return host_map


def resolve_host(cluster_or_host, config_path):
    """Resolve a cluster name to a host, or return as-is if it looks like a host."""
    if "." in cluster_or_host or ":" in cluster_or_host:
        # Looks like a direct host or host:port
        return cluster_or_host

    host_map = load_host_map(config_path)
    if cluster_or_host not in host_map:
        print(
            f"ERROR: Cluster '{cluster_or_host}' not found in config.ini. "
            f"Available: {list(host_map.keys())}",
            file=sys.stderr,
        )
        sys.exit(1)
    return host_map[cluster_or_host]


def main():
    parser = argparse.ArgumentParser(
        description="Reindex person_ticket documents on prod, scoped by account or event"
    )
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--account_id", help="Account ID to reindex")
    scope.add_argument("--event_id", help="Event ID to reindex")

    parser.add_argument(
        "--cluster",
        required=True,
        help="Cluster name (e.g. crm-cluster-1) or direct host",
    )
    parser.add_argument(
        "--index",
        required=True,
        help="Index name for this account (e.g. crm_account_12345)",
    )
    parser.add_argument(
        "--doc_type",
        default="person_ticket",
        help="Document type (default: person_ticket)",
    )
    parser.add_argument(
        "--query",
        default=None,
        help="Override the reindex query (default: built from account/event scope)",
    )
    parser.add_argument(
        "--config",
        default=os.path.join(SCRIPT_DIR, "..", "config.ini"),
        help="Path to config.ini",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Print actions without executing them",
    )
    args = parser.parse_args()

    # Resolve host
    host = resolve_host(args.cluster, os.path.abspath(args.config))

    # Build query
    if args.query:
        query = args.query
    elif args.account_id:
        query = f"account_id:{args.account_id} AND _exists_:payment_method"
    elif args.event_id:
        query = f"event_id:{args.event_id} AND _exists_:payment_method"

    print(f"=== Reindex on prod ===")
    print(f"  Host:     {host}")
    print(f"  Index:    {args.index}")
    print(f"  DocType:  {args.doc_type}")
    print(f"  Query:    {query}")
    print("")

    if args.dry_run:
        print(
            f"DRY RUN: POST http://{host}:9200/{args.index}/{args.doc_type}/"
            f"_update_by_query?q={query}&conflicts=proceed"
        )
        return

    ok, response = update_by_query(host, args.index, args.doc_type, query)

    if ok:
        print(f"SUCCESS: {json.dumps(response, indent=2)}")
    else:
        print(f"FAILED: {response}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
