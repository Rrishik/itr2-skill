from __future__ import annotations

from collections import OrderedDict
from decimal import Decimal
from typing import Any

from .common import array, money, number, obj


def build_fsi(data: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    raw_sources = array(data.get("foreign_sources"), "foreign_sources")
    if not raw_sources:
        return {}

    fsi_rows: list[dict[str, Any]] = []
    grouped: OrderedDict[tuple[str, str], dict[str, Any]] = OrderedDict()
    for index, raw in enumerate(raw_sources, 1):
        source = obj(raw, f"foreign_sources[{index}]")
        country = str(source.get("country") or "")
        code = str(source.get("country_code") or "")
        income_head = str(source.get("income_head") or "")
        gross = number(source.get("gross_income"))
        foreign_tax = number(source.get("foreign_tax_paid"))
        indian_tax = number(source.get("indian_tax_on_income"))
        relief = number(source.get("relief_claimed"))
        dtaa_limit = number(source.get("dtaa_tax_limit"))
        section = str(source.get("relief_section") or "")
        article = str(source.get("dtaa_article") or "")
        form_status = str(source.get("form67_status") or "").lower()
        acknowledgement = str(source.get("form67_acknowledgement") or "")
        evidence = str(source.get("source") or "Foreign income/tax working")

        fsi_rows.append(
            {
                "Country": country,
                "CountryCode": code,
                "IncomeHead": income_head,
                "GrossIncome": money(gross),
                "ForeignTaxPaid": money(foreign_tax),
                "IndianTaxOnIncome": money(indian_tax),
                "DTAATaxLimit": money(dtaa_limit),
                "ReliefClaimed": money(relief),
                "ReliefSection": section,
                "DTAAArticle": article,
                "Form67Status": form_status,
                "Form67Acknowledgement": acknowledgement,
                "Source": evidence,
                "Where": "Schedule FSI: one row per country and income head",
            }
        )

        key = (code, section)
        summary = grouped.setdefault(
            key,
            {
                "country": country,
                "foreign_tax": Decimal(0),
                "relief": Decimal(0),
                "statuses": [],
                "acknowledgements": [],
            },
        )
        summary["foreign_tax"] += foreign_tax
        summary["relief"] += relief
        summary["statuses"].append(form_status)
        if acknowledgement:
            summary["acknowledgements"].append(acknowledgement)

    tr_rows: list[dict[str, Any]] = []
    for (code, section), summary in grouped.items():
        statuses = sorted(set(summary["statuses"]))
        acknowledgements = sorted(set(summary["acknowledgements"]))
        tr_rows.append(
            {
                "Country": summary["country"],
                "CountryCode": code,
                "ForeignTaxPaid": money(summary["foreign_tax"]),
                "ReliefClaimed": money(summary["relief"]),
                "ReliefSection": section,
                "Form67Status": statuses[0] if len(statuses) == 1 else "mixed",
                "Form67Acknowledgement": "; ".join(acknowledgements),
                "Source": "Schedule FSI totals",
                "Where": f"Schedule TR: relief u/s {section}",
            }
        )
    return {"foreign_source_income": fsi_rows, "tax_relief": tr_rows}
