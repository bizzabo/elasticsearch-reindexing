"""
MySQL utility functions for querying CRM account/cluster mappings.
"""

import subprocess
import sys


def get_account_crm_indexes(mysql_host, mysql_user, mysql_db):
    """
    Query the account_crm_cluster table to get all (account_id, index_name, cluster_name) tuples.

    Uses the mysql CLI client to avoid requiring the mysqlclient Python package.

    Returns:
        List of dicts with keys: account_id, index_name, cluster_name
    """
    query = "SELECT account_id, index_name, cluster_name FROM account_crm_cluster"
    try:
        result = subprocess.run(
            [
                "mysql",
                "-h", mysql_host,
                "-u", mysql_user,
                "-D", mysql_db,
                "--batch",
                "--skip-column-names",
                "-e", query,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            print(f"MySQL error: {result.stderr}", file=sys.stderr)
            return []

        rows = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) == 3:
                rows.append({
                    "account_id": parts[0],
                    "index_name": parts[1],
                    "cluster_name": parts[2],
                })
        return rows
    except FileNotFoundError:
        print("ERROR: mysql client not found. Install mysql-client.", file=sys.stderr)
        return []
    except Exception as e:
        print(f"ERROR querying MySQL: {e}", file=sys.stderr)
        return []
