#!/usr/bin/env python3
"""Validate JSON-LD syntax for staged entry files. Used by the pre-commit hook."""
import json
import sys
from pathlib import Path

errors = []

for path in sys.argv[1:]:
    try:
        with open(path, encoding="utf-8") as f:
            json.load(f)
    except json.JSONDecodeError as e:
        errors.append(f"{path}: {e}")
    except OSError as e:
        errors.append(f"{path}: cannot read file — {e}")

if errors:
    for msg in errors:
        print(f"  JSON-LD syntax error: {msg}", file=sys.stderr)
    sys.exit(1)
