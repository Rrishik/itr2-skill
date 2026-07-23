from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Any

from .common import InputError, atomic_write_bytes, money, obj, resolve_path

OUTPUT_NAME = "Schedule112A.csv"


def build_schedule_112a(
    data: dict[str, Any], input_dir: Path, out_dir: Path
) -> dict[str, Any] | None:
    block = obj(data.get("schedule_112a"), "schedule_112a")
    if not block:
        return None
    template_value = block.get("template_path")
    if not isinstance(template_value, str) or not template_value.strip():
        raise InputError("schedule_112a.template_path is required.")
    template = resolve_path(template_value, input_dir)
    if not template.is_file():
        raise InputError(f"Schedule 112A template not found: {template}")

    raw = template.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise InputError("Schedule 112A template must not contain a UTF-8 BOM.")
    lines = raw.splitlines()
    if not lines:
        raise InputError("Schedule 112A template is empty.")
    header = lines[0]
    try:
        header_text = header.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InputError("Schedule 112A template header must be UTF-8.") from exc

    full_value = money(block.get("full_value"))
    cost = money(block.get("cost"))
    expenditure = money(block.get("expenditure"))
    if min(full_value, cost, expenditure) < 0:
        raise InputError(
            "Schedule 112A consideration, cost, and expenditure must be non-negative."
        )
    total_deductions = cost + expenditure
    balance = full_value - total_deductions
    if balance < 0:
        raise InputError(
            "The consolidated Schedule 112A row has a negative balance; use reviewed "
            "per-scrip/manual entry instead."
        )

    row = [
        "AE",
        "INNOTREQUIRD",
        "CONSOLIDATED",
        "",
        "",
        str(full_value),
        str(cost),
        str(cost),
        "",
        "",
        "",
        str(expenditure),
        str(total_deductions),
        str(balance),
        "",
    ]
    header_fields = next(csv.reader([header_text]))
    if len(header_fields) != len(row):
        raise InputError(
            f"Schedule 112A template has {len(header_fields)} columns; expected {len(row)}."
        )
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="", quoting=csv.QUOTE_MINIMAL)
    writer.writerow(row)
    row_bytes = buffer.getvalue().encode("utf-8")
    payload = header + b"\r\n" + row_bytes
    output = out_dir / OUTPUT_NAME
    atomic_write_bytes(output, payload)
    return {
        "path": str(output),
        "full_value": full_value,
        "cost": cost,
        "expenditure": expenditure,
        "balance": balance,
        "header_byte_identical": payload.startswith(header + b"\r\n"),
    }
