#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from itr2lib.common import InputError, load_json
from itr2lib.validation import validate


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the mechanical AY 2026-27 tax_input.json contract."
    )
    parser.add_argument("--input-json", required=True, type=Path)
    args = parser.parse_args()
    path = args.input_json.expanduser().resolve()
    if not path.is_file():
        raise InputError(f"Input JSON not found: {path}")

    report = validate(load_json(path), path)
    print(f"=== Verifying {path} ===")
    for message in report.passes:
        print(f"PASS: {message}")
    for message in report.warnings:
        print(f"WARN: {message}")
    for message in report.failures:
        print(f"FAIL: {message}")
    if report.failures:
        print(
            f"VERIFY: {len(report.failures)} FAIL, {len(report.warnings)} WARN",
            file=sys.stderr,
        )
        return 1
    print(f"VERIFY: 0 FAIL, {len(report.warnings)} WARN")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (InputError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
