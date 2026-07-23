from __future__ import annotations

from decimal import Decimal
from typing import Any

from .common import QUARTERS, money, number, obj

ZERO = Decimal(0)


def salary(data: dict[str, Any], regime: str) -> list[dict[str, Any]]:
    gross = number(data.get("salary_gross"), "salary_gross")
    if gross <= 0:
        return []
    standard = Decimal(75000 if regime == "new" else 50000)
    hra = (
        number(data.get("salary_hra_exemption"), "salary_hra_exemption")
        if regime == "old"
        else ZERO
    )
    professional_tax = (
        number(data.get("salary_professional_tax"), "salary_professional_tax")
        if regime == "old"
        else ZERO
    )
    chargeable = max(ZERO, gross - standard - hra - professional_tax)
    rows = [
        {
            "Field": "Gross salary (incl. perquisites)",
            "Value": money(gross),
            "Source": "Form 16 Part B (gross salary) + any foreign RSU/ESPP perquisite",
            "Where": "Schedule S: 1(a) Salary u/s 17(1) + 1(b) perquisites u/s 17(2)",
        },
        {
            "Field": f"Standard deduction ({regime})",
            "Value": money(standard),
            "Source": "Statutory (auto)",
            "Where": "Schedule S: 4(a) standard deduction u/s 16(ia)",
        },
    ]
    if hra > 0:
        rows.append(
            {
                "Field": "HRA exemption (old only)",
                "Value": money(hra),
                "Source": "Form 16 / rent proofs (s.10(13A) working)",
                "Where": "Schedule S: 2(iii) exempt allowance u/s 10(13A)",
            }
        )
    if professional_tax > 0:
        rows.append(
            {
                "Field": "Professional tax (old only)",
                "Value": money(professional_tax),
                "Source": "Form 16 / salary slips",
                "Where": "Schedule S: 4(c) professional tax u/s 16(iii)",
            }
        )
    rows.append(
        {
            "Field": "Income chargeable under Salaries",
            "Value": money(chargeable),
            "Source": "Computed (gross - deductions)",
            "Where": "Schedule S: 6 (net salary) -> Part B-TI item 1",
        }
    )
    return rows


def house_property_value(data: dict[str, Any]) -> Decimal:
    detail = obj(data.get("house_property_detail"), "house_property_detail")
    if not detail:
        return number(data.get("house_property"), "house_property")
    annual_value = number(detail.get("annual_value"), "house_property_detail.annual_value")
    municipal_tax = number(detail.get("municipal_tax"), "house_property_detail.municipal_tax")
    net_annual_value = max(ZERO, annual_value - municipal_tax)
    standard_deduction = net_annual_value * Decimal("0.30")
    interest = number(
        detail.get("home_loan_interest"), "house_property_detail.home_loan_interest"
    )
    return net_annual_value - standard_deduction - interest


def house_property(data: dict[str, Any]) -> list[dict[str, Any]]:
    detail = obj(data.get("house_property_detail"), "house_property_detail")
    net = house_property_value(data)
    if not detail and net == 0:
        return []
    if not detail:
        return [
            {
                "Field": "Income from house property (net)",
                "Value": money(net),
                "Source": "tax_input.json house_property (pre-computed net)",
                "Where": "Schedule HP: 1f -> Part B-TI item 2",
            }
        ]

    annual_value = number(detail.get("annual_value"))
    municipal_tax = number(detail.get("municipal_tax"))
    net_annual_value = max(ZERO, annual_value - municipal_tax)
    standard_deduction = net_annual_value * Decimal("0.30")
    interest = number(detail.get("home_loan_interest"))
    return [
        {
            "Field": "Annual value (rent received)",
            "Value": money(annual_value),
            "Source": "Rent receipts / lease agreement",
            "Where": "Schedule HP: 1a annual value",
        },
        {
            "Field": "Less: municipal taxes",
            "Value": money(municipal_tax),
            "Source": "Municipal tax receipts",
            "Where": "Schedule HP: 1b municipal taxes paid",
        },
        {
            "Field": "Net annual value",
            "Value": money(net_annual_value),
            "Source": "Computed (rent - municipal)",
            "Where": "Schedule HP: 1c (auto)",
        },
        {
            "Field": "Less: 30% standard deduction",
            "Value": money(standard_deduction),
            "Source": "Statutory (auto, 30% of NAV)",
            "Where": "Schedule HP: 1d 30% u/s 24(a)",
        },
        {
            "Field": "Less: home-loan interest",
            "Value": money(interest),
            "Source": "Home-loan interest certificate (lender)",
            "Where": "Schedule HP: 1e interest u/s 24(b)",
        },
        {
            "Field": "Income from house property",
            "Value": money(net),
            "Source": "Computed",
            "Where": "Schedule HP: 1f -> Part B-TI item 2",
        },
    ]


def _quarterly(value: Any) -> list[Decimal] | None:
    if value is None:
        return None
    quarter_data = obj(value, "quarterly split")
    return [
        number(
            quarter_data.get(f"q{index}", quarter_data.get(f"Q{index}")),
            f"quarterly split q{index}",
        )
        for index in range(1, 6)
    ]


def other_sources(data: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    source = obj(data.get("other_sources"), "other_sources")
    dividend = number(source.get("dividend"), "other_sources.dividend")
    savings = number(source.get("savings_interest"), "other_sources.savings_interest")
    fixed_deposit = number(source.get("fd_interest"), "other_sources.fd_interest")
    unsplit_interest = number(source.get("interest"), "other_sources.interest")
    other = number(source.get("other"), "other_sources.other")
    interest_total = savings + fixed_deposit + unsplit_interest
    total = dividend + interest_total + other
    if total == 0:
        return {}

    rows = [
        {
            "Field": "Dividend income (reconcile to AIS)",
            "Value": money(dividend),
            "Source": "Dividend report / AIS (Indian + foreign dividends, at slab)",
            "Where": "Schedule OS: 1a dividends (gross)",
        },
        {
            "Field": "Savings-bank interest",
            "Value": money(savings),
            "Source": "Bank interest certificate / passbook / AIS",
            "Where": "Schedule OS: 1b(i) savings-bank interest",
        },
        {
            "Field": "FD/term-deposit interest",
            "Value": money(fixed_deposit),
            "Source": "Bank/FD interest certificate / AIS",
            "Where": "Schedule OS: 1b(ii) term-deposit interest",
        },
    ]
    if unsplit_interest > 0:
        rows.append(
            {
                "Field": "Interest (unsplit)",
                "Value": money(unsplit_interest),
                "Source": "Bank certificates / AIS",
                "Where": "Schedule OS: 1b interest income",
            }
        )
    if other > 0:
        rows.append(
            {
                "Field": "Other",
                "Value": money(other),
                "Source": "As applicable (see source doc)",
                "Where": "Schedule OS: 1d any other income",
            }
        )
    rows.append(
        {
            "Field": "Total income from other sources",
            "Value": money(total),
            "Source": "Computed (sum of above)",
            "Where": "Schedule OS: total -> Part B-TI item 5",
        }
    )

    split_rows: list[dict[str, Any]] = []
    split_specs = (
        (
            "Dividend",
            "dividend_quarterly",
            "Dividend report / AIS (credit dates)",
            "Schedule OS 234C: 3a Dividend income (Sl.no. 1a(i))",
        ),
        (
            "Other",
            "other_quarterly",
            "As applicable (see source doc)",
            "Schedule OS 234C: other income row",
        ),
    )
    for label, key, evidence, destination in split_specs:
        values = _quarterly(source.get(key))
        if values is None:
            continue
        for quarter, amount in zip(QUARTERS, values):
            if amount == 0:
                continue
            split_rows.append(
                {
                    "Item": label,
                    "Quarter": quarter,
                    "Amount": money(amount),
                    "Source": evidence,
                    "Where": destination,
                }
            )

    sections = {"other_sources": rows}
    if split_rows:
        sections["other_sources_234c"] = split_rows
    return sections


def deductions(data: dict[str, Any], regime: str) -> list[dict[str, Any]]:
    old = obj(data.get("deductions_old"), "deductions_old")
    nps = number(data.get("deduction_80ccd2"), "deduction_80ccd2")
    section_80c = min(number(old.get("80c"), "deductions_old.80c"), Decimal(150000))
    section_80d = number(old.get("80d"), "deductions_old.80d")
    tta_ttb = number(old.get("80tta_ttb"), "deductions_old.80tta_ttb")
    other = number(old.get("other"), "deductions_old.other")

    rows = [
        {
            "Field": "80CCD(2) employer NPS (both regimes)",
            "Value": money(nps),
            "Allowed": "Yes",
            "Source": "Form 16 (employer NPS contribution)",
            "Where": "Schedule VI-A: 80CCD(2)",
        }
    ]
    if regime == "old":
        rows.extend(
            [
                {
                    "Field": "80C",
                    "Value": money(section_80c),
                    "Allowed": "Yes",
                    "Source": "80C proofs (EPF/PPF/ELSS/LIC/tuition etc.)",
                    "Where": "Schedule VI-A: 80C",
                },
                {
                    "Field": "80D",
                    "Value": money(section_80d),
                    "Allowed": "Yes",
                    "Source": "Health-insurance premium receipts",
                    "Where": "Schedule VI-A: 80D",
                },
                {
                    "Field": "80TTA/80TTB",
                    "Value": money(tta_ttb),
                    "Allowed": "Yes",
                    "Source": "Bank interest certificate (savings/deposit)",
                    "Where": "Schedule VI-A: 80TTA/80TTB",
                },
            ]
        )
        if other > 0:
            rows.append(
                {
                    "Field": "Other Chapter VI-A",
                    "Value": money(other),
                    "Allowed": "Yes",
                    "Source": "As applicable (see source doc)",
                    "Where": "Schedule VI-A: as applicable",
                }
            )
        total = nps + section_80c + section_80d + tta_ttb + other
    else:
        old_only = (
            ("80C", section_80c, "80C proofs (EPF/PPF/ELSS/LIC etc.)"),
            ("80D", section_80d, "Health-insurance premium receipts"),
            ("80TTA/80TTB", tta_ttb, "Bank interest certificate"),
            ("Other Chapter VI-A", other, "As applicable"),
        )
        for label, amount, evidence in old_only:
            if amount > 0:
                rows.append(
                    {
                        "Field": label,
                        "Value": money(amount),
                        "Allowed": "NO - void under NEW (untick)",
                        "Source": evidence,
                        "Where": "n/a under NEW regime",
                    }
                )
        total = nps
    rows.append(
        {
            "Field": f"Total deductions allowed ({regime})",
            "Value": money(total),
            "Allowed": "",
            "Source": "Computed (sum of allowed)",
            "Where": "Schedule VI-A: total -> Part B-TI",
        }
    )
    return rows
