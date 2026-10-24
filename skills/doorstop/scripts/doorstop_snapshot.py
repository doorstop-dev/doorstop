#!/usr/bin/env python
# SPDX-License-Identifier: LGPL-3.0-only
"""Dump a doorstop tree as JSON for agent consumption.

Writes a single JSON object to stdout with the following shape:

    {
      "root": "/abs/path/to/project",
      "documents": {
        "REQ": {
          "path": ".../reqs/req",
          "parent": null,
          "prefix": "REQ",
          "sep": "",
          "digits": 3,
          "itemformat": "yaml",
          "items": {
            "REQ001": {
              "level": "1.0",
              "active": true,
              "derived": false,
              "normative": true,
              "header": "",
              "text": "...",
              "ref": "",
              "references": null,
              "links": ["SYS001", ...],
              "reviewed": "abc...==" | null,
              "reviewed_current": "abc...==",
              "reviewed_ok": true | false,
              "path": ".../reqs/req/REQ001.yml",
              "extended": { ... }
            },
            ...
          }
        },
        ...
      },
      "issues": [
        {"severity": "INFO" | "WARNING" | "ERROR",
         "document": "REQ" | null,
         "item": "REQ001" | null,
         "message": "..."}
      ],
      "valid": true | false
    }

Run from anywhere inside a doorstop project:

    python doorstop_snapshot.py
    python doorstop_snapshot.py --root /path/to/project
    python doorstop_snapshot.py --pretty
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List

import doorstop
from doorstop.common import DoorstopError, DoorstopInfo, DoorstopWarning


STANDARD_ATTRS = {
    "active",
    "derived",
    "header",
    "level",
    "links",
    "normative",
    "ref",
    "references",
    "reviewed",
    "text",
}


def _item_snapshot(item) -> Dict[str, Any]:
    data = dict(item.data)
    extended = {k: v for k, v in data.items() if k not in STANDARD_ATTRS}

    current_stamp = str(item.stamp())
    stored_stamp = data.get("reviewed")
    stored_stamp = str(stored_stamp) if stored_stamp else None

    return {
        "uid": str(item.uid),
        "path": item.path,
        "level": str(item.level),
        "active": bool(item.active),
        "derived": bool(item.derived),
        "normative": bool(item.normative),
        "header": str(data.get("header", "")),
        "text": str(data.get("text", "")),
        "ref": data.get("ref", ""),
        "references": data.get("references"),
        "links": [str(uid) for uid in item.links],
        "reviewed": stored_stamp,
        "reviewed_current": current_stamp,
        "reviewed_ok": bool(item.reviewed),
        "extended": extended,
    }


def _document_snapshot(document) -> Dict[str, Any]:
    return {
        "prefix": str(document.prefix),
        "parent": str(document.parent) if document.parent else None,
        "sep": document.sep,
        "digits": document.digits,
        "itemformat": document.itemformat,
        "path": document.path,
        "items": {
            str(item.uid): _item_snapshot(item) for item in document
        },
    }


def _collect_issues(tree) -> (List[Dict[str, Any]], bool):
    issues: List[Dict[str, Any]] = []
    # tree.issues is a generator of Doorstop{Info,Warning,Error}; call issues()
    # via validate() so hooks run.
    valid = True

    def record(exc, document=None, item=None):
        nonlocal valid
        if isinstance(exc, DoorstopInfo):
            severity = "INFO"
        elif isinstance(exc, DoorstopWarning):
            severity = "WARNING"
        elif isinstance(exc, DoorstopError):
            severity = "ERROR"
            valid = False
        else:
            severity = type(exc).__name__
        issues.append(
            {
                "severity": severity,
                "document": str(document.prefix) if document else None,
                "item": str(item.uid) if item else None,
                "message": str(exc),
            }
        )

    # Walk issues via tree.get_issues() — returns a generator over all.
    for issue in tree.get_issues():
        record(issue)

    return issues, valid


def snapshot(root: str = None) -> Dict[str, Any]:
    tree = doorstop.build(root=root) if root else doorstop.build()
    tree.load()

    documents = {str(d.prefix): _document_snapshot(d) for d in tree}
    issues, valid = _collect_issues(tree)

    return {
        "root": tree.root,
        "documents": documents,
        "issues": issues,
        "valid": valid,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        help="project root (defaults to git root / cwd)",
        default=None,
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="indent JSON output",
    )
    args = parser.parse_args()

    try:
        data = snapshot(root=args.root)
    except DoorstopError as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 1

    kwargs = {"indent": 2, "sort_keys": True} if args.pretty else {"sort_keys": True}
    json.dump(data, sys.stdout, default=str, **kwargs)
    sys.stdout.write("\n")
    return 0 if data["valid"] else 0  # never fail on validation — snapshot is read-only


if __name__ == "__main__":
    sys.exit(main())
