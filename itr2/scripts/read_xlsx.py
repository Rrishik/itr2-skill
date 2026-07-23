#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from itr2lib.common import InputError
from itr2lib.xlsx import read_workbook


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Print non-empty XLSX cells without requiring Excel."
    )
    parser.add_argument("--path", required=True, type=Path)
    args = parser.parse_args()
    path = args.path.expanduser().resolve()
    if not path.is_file():
        raise InputError(f"Workbook not found: {path}")
    for sheet_name, rows in read_workbook(path):
        print(f"===== {sheet_name} =====")
        for cells in rows:
            print(" | ".join(f"{reference}={value}" for reference, value in cells))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (InputError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
