from __future__ import annotations

import re
from collections import OrderedDict
from decimal import Decimal
from typing import Any

from .common import QUARTERS, money, number


def _display(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def rows_to_table(rows: Any) -> str | None:
    if not isinstance(rows, list) or not rows:
        return None
    if not all(isinstance(row, dict) for row in rows):
        return None
    columns = list(rows[0])
    lines = [
        "| " + " | ".join(columns) + " |",
        "|" + "|".join("---" for _ in columns) + "|",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_display(row.get(column)) for column in columns) + " |")
    return "\n".join(lines)


def _section_f_grid(rows: list[dict[str, Any]]) -> str | None:
    if not rows:
        return None
    grouped: OrderedDict[str, list[dict[str, Any]]] = OrderedDict()
    for row in rows:
        grouped.setdefault(str(row.get("SectionF") or "classify by rate"), []).append(row)

    def sort_key(item: tuple[str, list[dict[str, Any]]]) -> tuple[int, str]:
        match = re.search(r"\d+", item[0])
        return (int(match.group()) if match else 99, item[0])

    lines = [
        "| Section F row | " + " | ".join(QUARTERS) + " | Total |",
        "|" + "---|" * (len(QUARTERS) + 2),
    ]
    column_totals = [Decimal(0) for _ in QUARTERS]
    grand_total = Decimal(0)
    for label, group in sorted(grouped.items(), key=sort_key):
        cells: list[int] = []
        for index, quarter in enumerate(QUARTERS):
            amount = sum(
                (
                    number(row.get("Gain"))
                    for row in group
                    if row.get("Quarter") == quarter
                ),
                Decimal(0),
            )
            column_totals[index] += amount
            cells.append(money(amount))
        total = sum((number(row.get("Gain")) for row in group), Decimal(0))
        grand_total += total
        lines.append(
            f"| {_display(label)} | "
            + " | ".join(str(value) for value in cells)
            + f" | {money(total)} |"
        )
    lines.append(
        "| **Total** | "
        + " | ".join(f"**{money(value)}**" for value in column_totals)
        + f" | **{money(grand_total)}** |"
    )
    return "\n".join(lines)


def _os_grid(rows: list[dict[str, Any]]) -> str | None:
    if not rows:
        return None
    grouped: OrderedDict[str, list[dict[str, Any]]] = OrderedDict()
    for row in rows:
        grouped.setdefault(str(row.get("Item") or "Other"), []).append(row)
    lines = [
        "| OS item | " + " | ".join(QUARTERS) + " | Total | Source |",
        "|" + "---|" * (len(QUARTERS) + 3),
    ]
    column_totals = [Decimal(0) for _ in QUARTERS]
    grand_total = Decimal(0)
    for label, group in grouped.items():
        cells: list[int] = []
        for index, quarter in enumerate(QUARTERS):
            amount = sum(
                (
                    number(row.get("Amount"))
                    for row in group
                    if row.get("Quarter") == quarter
                ),
                Decimal(0),
            )
            column_totals[index] += amount
            cells.append(money(amount))
        total = sum((number(row.get("Amount")) for row in group), Decimal(0))
        grand_total += total
        source = str(group[0].get("Source") or "")
        lines.append(
            f"| {_display(label)} | "
            + " | ".join(str(value) for value in cells)
            + f" | {money(total)} | {_display(source)} |"
        )
    lines.append(
        "| **Total** | "
        + " | ".join(f"**{money(value)}**" for value in column_totals)
        + f" | **{money(grand_total)}** | |"
    )
    return "\n".join(lines)


def _document_readiness(readiness: Any) -> list[str]:
    if not isinstance(readiness, dict):
        return []
    status = str(readiness.get("status") or "unknown")
    lines = [
        "## Source-document readiness",
        "",
        f"- Status: **{status.upper()}**",
        "",
    ]
    items = readiness.get("items")
    if not isinstance(items, list) or not items:
        lines.extend(
            (
                "No applicable document checklist was recorded.",
                "",
            )
        )
        return lines
    rows = [
        {
            "Document": item.get("document", ""),
            "Status": item.get("status", ""),
            "Reference": item.get("reference", ""),
            "Note": item.get("note", ""),
            "Why required": item.get("reason", ""),
        }
        for item in items
        if isinstance(item, dict)
    ]
    table = rows_to_table(rows)
    if table:
        lines.extend((table, ""))
    if status != "ready":
        lines.extend(
            (
                "_This working set is not filing-ready until every applicable "
                "document is reviewed._",
                "",
            )
        )
    return lines


def render(data: dict[str, Any], result: dict[str, Any], regime: str) -> str:
    recommendation = str(result.get("recommended_regime") or regime.upper())
    regime_note = (
        "recommended"
        if recommendation == regime.upper()
        else f"override; computed recommendation is {recommendation}"
    )
    lines = [
        "# ITR-2 data-entry sheet",
        "",
        f"- Taxpayer: {data.get('taxpayer', '')}",
        f"- PAN: {data.get('pan', '')}",
        f"- AY: {data.get('ay', '')}",
        f"- Regime: **{regime.upper()}** ({regime_note})",
        "",
    ]
    lines.extend(_document_readiness(result.get("document_readiness")))

    sections = (
        ("##", "Schedule S — Salary", "salary"),
        ("##", "Schedule HP — House Property", "house_property"),
        ("##", "Schedule CG — Capital Gains", None),
        ("###", "Head aggregates", "capital_gains_head"),
        ("###", "234C quarterly split (by head)", "capital_gains_234c"),
        ("##", "Schedule OS — Other Sources", "other_sources"),
        ("##", "Schedule FSI — Foreign Source Income", "foreign_source_income"),
        ("##", "Schedule TR — Tax Relief", "tax_relief"),
        ("##", "Schedule VI-A — Deductions", "deductions"),
        (
            "##",
            "Part B-TI / TTI — Tax computation & regime comparison",
            "tax_computation",
        ),
    )
    for level, title, key in sections:
        if key is None:
            if not result.get("capital_gains_head") and not result.get("capital_gains_234c"):
                continue
            lines.extend((f"{level} {title}", ""))
            continue
        table = rows_to_table(result.get(key))
        if table is None:
            continue
        lines.extend((f"{level} {title}", "", table, ""))
        if key == "capital_gains_234c":
            grid = _section_f_grid(result[key])
            if grid:
                lines.extend(
                    (
                        "### Section F — as the utility grid (enter these cells)",
                        "",
                        grid,
                        "",
                        "_Each row must sum to that head's annual taxable balance; "
                        "review negative-quarter loss netting before entry._",
                        "",
                    )
                )
        if key == "other_sources" and result.get("other_sources_234c"):
            grid = _os_grid(result["other_sources_234c"])
            if grid:
                lines.extend(
                    (
                        "### 234C accrual/receipt grid (enter these cells)",
                        "",
                        grid,
                        "",
                        "_Dividend uses its actual credit quarter. Ordinary interest "
                        "has no dedicated 234C cell in this grid._",
                        "",
                    )
                )
    lines.extend(
        (
            "---",
            "_Verify all figures against AIS/TIS and the official utility before "
            "filing. Rates are AY-specific._",
            "",
        )
    )
    return "\n".join(lines)
