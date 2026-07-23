#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from itr2lib.capital_gains import build_capital_gains
from itr2lib.common import InputError, load_json, write_json, write_text
from itr2lib.documents import assess_document_checklist
from itr2lib.fsi import build_fsi
from itr2lib.renderer import render
from itr2lib.schedule_112a import OUTPUT_NAME, build_schedule_112a
from itr2lib.schedules import deductions, house_property, other_sources, salary
from itr2lib.tax import compute_tax
from itr2lib.validation import ValidationReport, validate


def _print_report(report: ValidationReport) -> None:
    for message in report.passes:
        print(f"PASS: {message}")
    for message in report.warnings:
        print(f"WARN: {message}")
    for message in report.failures:
        print(f"FAIL: {message}", file=sys.stderr)


def build(
    input_path: Path,
    out_dir: Path,
    regime_override: str | None = None,
) -> dict:
    data = load_json(input_path)
    report = validate(data, input_path)
    _print_report(report)
    if not report.ok:
        raise InputError(
            f"Input validation failed with {len(report.failures)} error(s)."
        )

    tax_rows, recommendation = compute_tax(data)
    regime = regime_override or recommendation.lower()
    result: dict = {
        "tax_computation": tax_rows,
        "recommended_regime": recommendation,
        "document_readiness": assess_document_checklist(data).as_dict(),
    }

    salary_rows = salary(data, regime)
    if salary_rows:
        result["salary"] = salary_rows
    house_rows = house_property(data)
    if house_rows:
        result["house_property"] = house_rows
    result.update(other_sources(data))
    result["deductions"] = deductions(data, regime)
    result.update(build_fsi(data))
    result.update(build_capital_gains(data))
    result["meta"] = {
        "taxpayer": str(data.get("taxpayer") or ""),
        "pan": str(data.get("pan") or ""),
        "ay": str(data.get("ay") or ""),
        "regime": regime.upper(),
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    artifact = build_schedule_112a(data, input_path.parent, out_dir)
    stale_112a = out_dir / OUTPUT_NAME
    if artifact is None:
        stale_112a.unlink(missing_ok=True)

    write_json(out_dir / "return.json", result)
    write_text(out_dir / "ITR2_data_entry.md", render(data, result, regime))
    print(f"Wrote: {out_dir / 'return.json'}")
    print(f"Wrote: {out_dir / 'ITR2_data_entry.md'}")
    if artifact:
        print(f"Wrote: {artifact['path']}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate an AY 2026-27 ITR-2 input and build reviewable return artifacts."
    )
    parser.add_argument("--input-json", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--regime", choices=("new", "old"))
    args = parser.parse_args()

    input_path = args.input_json.expanduser().resolve()
    if not input_path.is_file():
        raise InputError(f"Input JSON not found: {input_path}")
    build(
        input_path,
        args.out_dir.expanduser().resolve(),
        args.regime,
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (InputError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
