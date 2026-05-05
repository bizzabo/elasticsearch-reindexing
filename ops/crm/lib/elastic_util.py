"""
Elasticsearch utility functions for CRM index operations.
Provides helpers for talking to Elasticsearch clusters.
"""

import json
import urllib.request
import urllib.error
import sys


def put_mapping(host, index, doc_type, mapping_body, port=9200, scheme="http"):
    """
    Add or update a mapping for a given index and doc type.

    Args:
        host: Elasticsearch host
        index: Index name
        doc_type: Document type (e.g. 'person_ticket')
        mapping_body: Dict or JSON string of the mapping body
        port: ES port (default 9200)
        scheme: http or https (default http)
    Returns:
        Tuple of (success: bool, response: dict)
    """
    url = f"{scheme}://{host}:{port}/{index}/_mapping/{doc_type}"
    if isinstance(mapping_body, dict):
        mapping_body = json.dumps(mapping_body)

    req = urllib.request.Request(
        url,
        data=mapping_body.encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="PUT",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return True, result
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        print(f"  ERROR [{e.code}] PUT {url}: {body}", file=sys.stderr)
        return False, {"error": body, "status": e.code}
    except Exception as e:
        print(f"  ERROR PUT {url}: {e}", file=sys.stderr)
        return False, {"error": str(e)}


def update_by_query(host, index, doc_type, query, port=9200, scheme="http"):
    """
    Run an _update_by_query on a given index/doc_type.

    Args:
        host: Elasticsearch host
        index: Index name
        doc_type: Document type (e.g. 'person_ticket')
        query: Query string (e.g. '_exists_:payment_method')
        port: ES port (default 9200)
        scheme: http or https (default http)
    Returns:
        Tuple of (success: bool, response: dict)
    """
    url = f"{scheme}://{host}:{port}/{index}/{doc_type}/_update_by_query?q={query}&conflicts=proceed"

    req = urllib.request.Request(
        url,
        data=b"",
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return True, result
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        print(f"  ERROR [{e.code}] POST {url}: {body}", file=sys.stderr)
        return False, {"error": body, "status": e.code}
    except Exception as e:
        print(f"  ERROR POST {url}: {e}", file=sys.stderr)
        return False, {"error": str(e)}
