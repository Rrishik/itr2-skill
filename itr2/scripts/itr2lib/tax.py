from __future__ import annotations

from decimal import Decimal
from typing import Any

from .common import array, money, number, obj
from .schedules import house_property_value

ZERO = Decimal(0)


def _tax_new(income: Decimal) -> Decimal:
    slabs = (
        (Decimal(400000), ZERO),
        (Decimal(400000), Decimal("0.05")),
        (Decimal(400000), Decimal("0.10")),
        (Decimal(400000), Decimal("0.15")),
        (Decimal(400000), Decimal("0.20")),
        (Decimal(400000), Decimal("0.25")),
    )
    remaining = max(ZERO, income)
    tax = ZERO
    for width, rate in slabs:
        band = min(remaining, width)
        tax += band * rate
        remaining -= band
        if remaining <= 0:
            break
    if remaining > 0:
        tax += remaining * Decimal("0.30")
    return tax


def _tax_old(income: Decimal, senior: bool) -> Decimal:
    exempt = Decimal(300000 if senior else 250000)
    tax = ZERO
    if income > exempt:
        tax += (min(income, Decimal(500000)) - exempt) * Decimal("0.05")
    if income > 500000:
        tax += (min(income, Decimal(1000000)) - Decimal(500000)) * Decimal("0.20")
    if income > 1000000:
        tax += (income - Decimal(1000000)) * Decimal("0.30")
    return max(ZERO, tax)


def _surcharge(
    total_income: Decimal, normal_tax: Decimal, special_tax: Decimal
) -> Decimal:
    rate = ZERO
    if total_income > 20000000:
        rate = Decimal("0.25")
    elif total_income > 10000000:
        rate = Decimal("0.15")
    elif total_income > 5000000:
        rate = Decimal("0.10")
    special_rate = min(rate, Decimal("0.15"))
    return normal_tax * rate + special_tax * special_rate


def effective_ftc(data: dict[str, Any]) -> Decimal:
    foreign_sources = array(data.get("foreign_sources"), "foreign_sources")
    if foreign_sources:
        return sum(
            (
                number(obj(row, f"foreign_sources[{index}]").get("relief_claimed"))
                for index, row in enumerate(foreign_sources, 1)
            ),
            ZERO,
        )
    return number(obj(data.get("taxes_paid"), "taxes_paid").get("ftc"))


def compute_tax(data: dict[str, Any]) -> tuple[list[dict[str, Any]], str]:
    senior = bool(data.get("senior_citizen", False))
    salary_gross = number(data.get("salary_gross"), "salary_gross")
    hra_exempt = number(data.get("salary_hra_exemption"), "salary_hra_exemption")
    professional_tax = number(
        data.get("salary_professional_tax"), "salary_professional_tax"
    )

    other_sources = obj(data.get("other_sources"), "other_sources")
    dividend = number(other_sources.get("dividend"), "other_sources.dividend")
    interest = sum(
        (
            number(other_sources.get(key), f"other_sources.{key}")
            for key in ("savings_interest", "fd_interest", "interest", "other")
        ),
        ZERO,
    )
    house_property = max(Decimal(-200000), house_property_value(data))
    slab_gains = number(data.get("slab_rate_gains"), "slab_rate_gains")

    special = obj(data.get("special_rate_gains"), "special_rate_gains")
    stcg_111a = number(special.get("stcg_111a"), "special_rate_gains.stcg_111a")
    ltcg_112a = number(special.get("ltcg_112a"), "special_rate_gains.ltcg_112a")
    ltcg_112 = number(special.get("ltcg_112"), "special_rate_gains.ltcg_112")

    deductions = obj(data.get("deductions_old"), "deductions_old")
    old_80c = min(number(deductions.get("80c"), "deductions_old.80c"), Decimal(150000))
    old_80d = number(deductions.get("80d"), "deductions_old.80d")
    old_tta = number(deductions.get("80tta_ttb"), "deductions_old.80tta_ttb")
    old_other = number(deductions.get("other"), "deductions_old.other")
    nps = number(data.get("deduction_80ccd2"), "deduction_80ccd2")

    taxes = obj(data.get("taxes_paid"), "taxes_paid")
    tds = number(taxes.get("tds"), "taxes_paid.tds")
    advance = number(taxes.get("advance_tax"), "taxes_paid.advance_tax")
    self_assessment = number(
        taxes.get("self_assessment_tax"), "taxes_paid.self_assessment_tax"
    )
    ftc = effective_ftc(data)

    taxable_112a = max(ZERO, ltcg_112a - Decimal(125000))
    special_tax = (
        stcg_111a * Decimal("0.20")
        + taxable_112a * Decimal("0.125")
        + ltcg_112 * Decimal("0.125")
    )
    special_income = stcg_111a + ltcg_112a + ltcg_112

    def regime(name: str) -> dict[str, int]:
        standard_deduction = Decimal(75000 if name == "new" else 50000)
        salary_deductions = standard_deduction
        if name == "old":
            salary_deductions += hra_exempt + professional_tax
        salary_net = max(ZERO, salary_gross - salary_deductions)
        gross_slab = salary_net + dividend + interest + house_property + slab_gains
        chapter_six = nps
        if name == "old":
            chapter_six += old_80c + old_80d + old_tta + old_other
        slab_income = max(ZERO, gross_slab - chapter_six)
        total_income = slab_income + special_income

        normal_tax = _tax_new(slab_income) if name == "new" else _tax_old(slab_income, senior)
        rebate = ZERO
        if name == "new" and total_income <= 1200000:
            rebate = normal_tax
        elif name == "old" and total_income <= 500000:
            rebate = min(normal_tax + special_tax, Decimal(12500))

        normal_after_rebate = max(ZERO, normal_tax - rebate)
        special_after_rebate = special_tax
        if name == "old" and rebate > normal_tax:
            special_after_rebate = max(ZERO, special_tax - (rebate - normal_tax))

        base_tax = normal_after_rebate + special_after_rebate
        surcharge = _surcharge(total_income, normal_after_rebate, special_after_rebate)
        cess = (base_tax + surcharge) * Decimal("0.04")
        total_tax = base_tax + surcharge + cess
        payable = max(ZERO, total_tax - ftc) - tds - advance - self_assessment

        return {
            "Slab income": money(slab_income),
            "  of which slab-rate CG": money(slab_gains),
            "Special-rate income": money(special_income),
            "Total income": money(total_income),
            "Tax on slab income": money(normal_tax),
            "Tax on special-rate gains": money(special_tax),
            "87A rebate": money(rebate),
            "Surcharge": money(surcharge),
            "Cess (4%)": money(cess),
            "Total tax liability": money(total_tax),
            "Less: FTC": money(ftc),
            "Less: TDS/advance/SA": money(tds + advance + self_assessment),
            "Net payable (+) / refund (-)": money(payable),
        }

    old = regime("old")
    new = regime("new")
    recommendation = (
        "NEW"
        if new["Total tax liability"] <= old["Total tax liability"]
        else "OLD"
    )
    rows = [
        {"LineItem": label, "OLD": old[label], "NEW": new[label]}
        for label in new
    ]
    rows.append({"LineItem": "Recommended regime", "OLD": "", "NEW": recommendation})
    return rows, recommendation
