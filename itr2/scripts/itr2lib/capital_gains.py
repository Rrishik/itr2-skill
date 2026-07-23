from __future__ import annotations

from decimal import Decimal
from typing import Any

from .common import InputError, QUARTERS, array, decimal_json, number, obj

SECTION_F_BY_BUCKET = {
    "stcg_111a": "Row 1 (STCG @20%)",
    "slab_rate_gains": "Row 3 (STCG applicable rate)",
    "ltcg_112a": "Row 5 (LTCG @12.5%)",
    "ltcg_112": "Row 5 (LTCG @12.5%)",
}
BUCKET_ALIASES = {
    "slab": "slab_rate_gains",
    "slab_rate_gains": "slab_rate_gains",
    "stcg_111a": "stcg_111a",
    "ltcg_112a": "ltcg_112a",
    "ltcg_112": "ltcg_112",
}


def manual_bucket(row: dict[str, Any]) -> str:
    value = str(row.get("tax_bucket") or "").strip().lower()
    if not value:
        raise InputError("capital-gain contributions require tax_bucket.")
    if value not in BUCKET_ALIASES:
        raise InputError(f"Unsupported capital-gain tax_bucket {value!r}.")
    return BUCKET_ALIASES[value]


def _quarterly_values(row: dict[str, Any], index: int) -> list[tuple[str, Decimal]]:
    quarterly = obj(
        row.get("quarterly"), f"capital_gains_manual[{index}].quarterly"
    )
    if quarterly:
        return [
            (
                quarter,
                number(
                    quarterly.get(f"q{position}", quarterly.get(f"Q{position}")),
                    f"capital_gains_manual[{index}].quarterly.q{position}",
                ),
            )
            for position, quarter in enumerate(QUARTERS, 1)
        ]

    quarter = str(row.get("quarter") or "").strip()
    if not quarter:
        return []
    consideration = number(
        row.get("consideration"),
        f"capital_gains_manual[{index}].consideration",
    )
    cost = number(row.get("cost"), f"capital_gains_manual[{index}].cost")
    expenditure = number(
        row.get("expenditure"), f"capital_gains_manual[{index}].expenditure"
    )
    return [(quarter, consideration - cost - expenditure)]


def build_capital_gains(
    data: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    raw_contributions = array(
        data.get("capital_gains_manual"), "capital_gains_manual"
    )
    if not raw_contributions:
        return {}

    head_rows: list[dict[str, Any]] = []
    split_rows: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_contributions, 1):
        row = obj(raw, f"capital_gains_manual[{index}]")
        bucket = manual_bucket(row)
        consideration = number(
            row.get("consideration"),
            f"capital_gains_manual[{index}].consideration",
        )
        cost = number(row.get("cost"), f"capital_gains_manual[{index}].cost")
        expenditure = number(
            row.get("expenditure"),
            f"capital_gains_manual[{index}].expenditure",
        )
        gain = consideration - cost - expenditure
        head = str(row.get("head") or "Capital gain contribution")
        head_rows.append(
            {
                "Head": head,
                "Rows": int(number(row.get("rows"), default=Decimal(1))),
                "Consideration": decimal_json(consideration),
                "Cost": decimal_json(cost),
                "Expenditure": decimal_json(expenditure),
                "Gain": decimal_json(gain),
                "STT_Excluded": decimal_json(number(row.get("stt"))),
                "Source": str(row.get("source") or "Reviewed source contribution"),
                "Where": str(row.get("where") or "Schedule CG"),
            }
        )

        quarterly = _quarterly_values(row, index)
        if quarterly and abs(sum((value for _, value in quarterly), Decimal(0)) - gain) > 1:
            raise InputError(
                f"capital_gains_manual[{index}].quarterly does not tie to its gain."
            )
        for quarter, value in quarterly:
            if value == 0:
                continue
            split_rows.append(
                {
                    "Head": head,
                    "Quarter": quarter,
                    "Gain": decimal_json(value),
                    "SectionF": SECTION_F_BY_BUCKET[bucket],
                }
            )

    head_rows.append(
        {
            "Head": "TOTAL (all CG heads)",
            "Rows": sum(int(row["Rows"]) for row in head_rows),
            "Consideration": decimal_json(
                sum((number(row["Consideration"]) for row in head_rows), Decimal(0))
            ),
            "Cost": decimal_json(
                sum((number(row["Cost"]) for row in head_rows), Decimal(0))
            ),
            "Expenditure": decimal_json(
                sum((number(row["Expenditure"]) for row in head_rows), Decimal(0))
            ),
            "Gain": decimal_json(
                sum((number(row["Gain"]) for row in head_rows), Decimal(0))
            ),
            "STT_Excluded": decimal_json(
                sum((number(row["STT_Excluded"]) for row in head_rows), Decimal(0))
            ),
            "Source": "Computed (sum of reviewed contributions)",
            "Where": "Cross-check against source-skill handoffs",
        }
    )

    sections = {"capital_gains_head": head_rows}
    if split_rows:
        sections["capital_gains_234c"] = split_rows
    return sections
