from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any

from .capital_gains import manual_bucket
from .common import InputError, QUARTERS, array, number, obj, resolve_path
from .schedules import house_property_value

KNOWN_TOP_LEVEL = {
    "taxpayer",
    "pan",
    "ay",
    "residential_status",
    "senior_citizen",
    "salary_gross",
    "salary_hra_exemption",
    "salary_professional_tax",
    "other_sources",
    "house_property",
    "house_property_detail",
    "slab_rate_gains",
    "special_rate_gains",
    "deduction_80ccd2",
    "deductions_old",
    "taxes_paid",
    "capital_gains_manual",
    "schedule_112a",
    "foreign_sources",
}
OS_KEYS = {
    "dividend",
    "savings_interest",
    "fd_interest",
    "interest",
    "other",
    "dividend_quarterly",
    "interest_quarterly",
    "other_quarterly",
}
SPECIAL_GAIN_KEYS = {"stcg_111a", "ltcg_112a", "ltcg_112"}
DEDUCTION_KEYS = {"80c", "80d", "80tta_ttb", "other"}
TAX_KEYS = {"tds", "advance_tax", "self_assessment_tax", "ftc"}
HOUSE_PROPERTY_KEYS = {"annual_value", "municipal_tax", "home_loan_interest"}
SCHEDULE_112A_KEYS = {"template_path", "full_value", "cost", "expenditure"}
CAPITAL_GAIN_KEYS = {
    "head",
    "tax_bucket",
    "consideration",
    "cost",
    "expenditure",
    "stt",
    "rows",
    "source",
    "where",
    "quarter",
    "quarterly",
}
FOREIGN_SOURCE_KEYS = {
    "country",
    "country_code",
    "income_head",
    "gross_income",
    "foreign_tax_paid",
    "indian_tax_on_income",
    "relief_claimed",
    "relief_section",
    "dtaa_article",
    "dtaa_tax_limit",
    "form67_status",
    "form67_acknowledgement",
    "source",
}
QUARTER_KEYS = {f"q{index}" for index in range(1, 6)} | {
    f"Q{index}" for index in range(1, 6)
}


@dataclass
class ValidationReport:
    failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    passes: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.failures

    def fail(self, message: str) -> None:
        self.failures.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def passed(self, message: str) -> None:
        self.passes.append(message)


def _safe_number(report: ValidationReport, value: Any, field_name: str) -> Decimal:
    try:
        return number(value, field_name)
    except InputError as exc:
        report.fail(str(exc))
        return Decimal(0)


def _check_unknown(
    report: ValidationReport,
    value: Any,
    field_name: str,
    known: set[str],
) -> dict[str, Any]:
    try:
        fields = obj(value, field_name)
    except InputError as exc:
        report.fail(str(exc))
        return {}
    unknown = sorted(set(fields) - known)
    if unknown:
        report.fail(f"unknown {field_name} key(s): {', '.join(unknown)}")
    return fields


def validate(data: dict[str, Any], input_path: Path) -> ValidationReport:
    report = ValidationReport()
    unknown = sorted(set(data) - KNOWN_TOP_LEVEL)
    if unknown:
        report.fail(f"unknown top-level key(s): {', '.join(unknown)}")
    else:
        report.passed("no unknown top-level keys")

    ay = data.get("ay")
    if ay != "2026-27":
        report.fail("ay must be 2026-27; this assembler's rates are AY-specific")

    non_negative = (
        "salary_gross",
        "salary_hra_exemption",
        "salary_professional_tax",
        "slab_rate_gains",
        "deduction_80ccd2",
    )
    for key in non_negative:
        if _safe_number(report, data.get(key), key) < 0:
            report.fail(f"{key} must be non-negative")
    if (
        _safe_number(
            report, data.get("salary_hra_exemption"), "salary_hra_exemption"
        )
        > 0
        and _safe_number(report, data.get("salary_gross"), "salary_gross") <= 0
    ):
        report.fail("salary_hra_exemption is set but salary_gross is zero")

    old_deductions = _check_unknown(
        report, data.get("deductions_old"), "deductions_old", DEDUCTION_KEYS
    )
    for key in DEDUCTION_KEYS:
        if _safe_number(report, old_deductions.get(key), f"deductions_old.{key}") < 0:
            report.fail(f"deductions_old.{key} must be non-negative")
    if _safe_number(report, old_deductions.get("other"), "deductions_old.other") > 100000:
        report.warn(
            "deductions_old.other is large; confirm it excludes HRA and professional tax"
        )

    special = _check_unknown(
        report, data.get("special_rate_gains"), "special_rate_gains", SPECIAL_GAIN_KEYS
    )
    for key in SPECIAL_GAIN_KEYS:
        value = _safe_number(report, special.get(key), f"special_rate_gains.{key}")
        if value < 0:
            report.warn(f"special_rate_gains.{key} is negative; review loss set-off")

    taxes = _check_unknown(report, data.get("taxes_paid"), "taxes_paid", TAX_KEYS)
    for key in TAX_KEYS:
        if _safe_number(report, taxes.get(key), f"taxes_paid.{key}") < 0:
            report.fail(f"taxes_paid.{key} must be non-negative")

    try:
        os_data = _check_unknown(
            report, data.get("other_sources"), "other_sources", OS_KEYS
        )
        if "interest_quarterly" in os_data:
            report.fail(
                "other_sources.interest_quarterly is unsupported; ordinary interest "
                "has no dedicated 234C cell"
            )
        annuals = {
            "dividend_quarterly": _safe_number(
                report, os_data.get("dividend"), "other_sources.dividend"
            ),
            "other_quarterly": _safe_number(
                report, os_data.get("other"), "other_sources.other"
            ),
        }
        if (
            annuals["dividend_quarterly"] != 0
            and "dividend_quarterly" not in os_data
        ):
            report.fail(
                "other_sources.dividend_quarterly is required when dividend is non-zero"
            )
        for key, annual in annuals.items():
            if key not in os_data:
                continue
            split = _check_unknown(
                report, os_data.get(key), f"other_sources.{key}", QUARTER_KEYS
            )
            split_sum = sum(
                (
                    _safe_number(
                        report,
                        split.get(f"q{index}", split.get(f"Q{index}")),
                        f"other_sources.{key}.q{index}",
                    )
                    for index in range(1, 6)
                ),
                Decimal(0),
            )
            if abs(split_sum - annual) > 1:
                report.fail(
                    f"other_sources.{key} sums to {split_sum} but annual total is {annual}"
                )
            else:
                report.passed(f"other_sources.{key} ties to annual total")
    except InputError as exc:
        report.fail(str(exc))
        os_data = {}

    try:
        manual_raw = array(data.get("capital_gains_manual"), "capital_gains_manual")
        manual_totals: dict[str, Decimal] = {}
        for index, raw in enumerate(manual_raw, 1):
            row = _check_unknown(
                report,
                raw,
                f"capital_gains_manual[{index}]",
                CAPITAL_GAIN_KEYS,
            )
            if not str(row.get("head") or "").strip():
                report.warn(f"capital_gains_manual[{index}] has no head label")
            if not str(row.get("where") or "").strip():
                report.warn(f"capital_gains_manual[{index}] has no utility destination")
            consideration = _safe_number(
                report,
                row.get("consideration"),
                f"capital_gains_manual[{index}].consideration",
            )
            cost = _safe_number(
                report, row.get("cost"), f"capital_gains_manual[{index}].cost"
            )
            expenditure = _safe_number(
                report, row.get("expenditure"), f"capital_gains_manual[{index}].expenditure"
            )
            if min(consideration, cost, expenditure) < 0:
                report.fail(f"capital_gains_manual[{index}] inputs must be non-negative")
            stt = _safe_number(
                report, row.get("stt"), f"capital_gains_manual[{index}].stt"
            )
            if stt < 0:
                report.fail(f"capital_gains_manual[{index}].stt must be non-negative")
            rows = _safe_number(
                report,
                row.get("rows"),
                f"capital_gains_manual[{index}].rows",
            )
            if "rows" in row and (rows <= 0 or rows != rows.to_integral_value()):
                report.fail(
                    f"capital_gains_manual[{index}].rows must be a positive integer"
                )
            quarter = str(row.get("quarter") or "").strip()
            if quarter and quarter not in QUARTERS:
                report.fail(
                    f"capital_gains_manual[{index}].quarter is not a supported period"
                )
            if quarter and row.get("quarterly") is not None:
                report.fail(
                    f"capital_gains_manual[{index}] cannot use both quarter and quarterly"
                )
            try:
                bucket = manual_bucket(row)
                gain = consideration - cost - expenditure
                manual_totals[bucket] = manual_totals.get(bucket, Decimal(0)) + gain
                if row.get("quarterly") is not None:
                    quarterly = _check_unknown(
                        report,
                        row.get("quarterly"),
                        f"capital_gains_manual[{index}].quarterly",
                        QUARTER_KEYS,
                    )
                    split_total = sum(
                        (
                            _safe_number(
                                report,
                                quarterly.get(
                                    f"q{position}", quarterly.get(f"Q{position}")
                                ),
                                f"capital_gains_manual[{index}].quarterly.q{position}",
                            )
                            for position in range(1, 6)
                        ),
                        Decimal(0),
                    )
                    if abs(split_total - gain) > 1:
                        report.fail(
                            f"capital_gains_manual[{index}].quarterly sums to "
                            f"{split_total}, not gain {gain}"
                        )
            except InputError as exc:
                report.fail(str(exc))
        expected = {
            "slab_rate_gains": _safe_number(
                report, data.get("slab_rate_gains"), "slab_rate_gains"
            ),
            "stcg_111a": _safe_number(
                report,
                special.get("stcg_111a"),
                "special_rate_gains.stcg_111a",
            ),
            "ltcg_112a": _safe_number(
                report,
                special.get("ltcg_112a"),
                "special_rate_gains.ltcg_112a",
            ),
            "ltcg_112": _safe_number(
                report,
                special.get("ltcg_112"),
                "special_rate_gains.ltcg_112",
            ),
        }
        if manual_raw or any(value != 0 for value in expected.values()):
            for bucket, expected_total in expected.items():
                contribution_total = manual_totals.get(bucket, Decimal(0))
                if abs(contribution_total - expected_total) > 1:
                    report.fail(
                        f"capital-gain {bucket} contributions ({contribution_total}) "
                        f"do not tie to tax input ({expected_total})"
                    )
    except InputError as exc:
        report.fail(str(exc))

    try:
        detail = _check_unknown(
            report,
            data.get("house_property_detail"),
            "house_property_detail",
            HOUSE_PROPERTY_KEYS,
        )
        if detail and "house_property" in data:
            calculated = house_property_value(data)
            supplied = _safe_number(
                report, data.get("house_property"), "house_property"
            )
            if abs(calculated - supplied) > 1:
                report.fail(
                    f"house_property_detail computes {calculated}, not supplied "
                    f"house_property {supplied}"
                )
    except InputError as exc:
        report.fail(str(exc))

    try:
        schedule_112a = _check_unknown(
            report,
            data.get("schedule_112a"),
            "schedule_112a",
            SCHEDULE_112A_KEYS,
        )
        if schedule_112a:
            template_value = schedule_112a.get("template_path")
            if not isinstance(template_value, str) or not template_value.strip():
                report.fail("schedule_112a.template_path is required")
            else:
                template = resolve_path(template_value, input_path.parent)
                if not template.is_file():
                    report.fail(f"Schedule 112A template not found: {template}")
            balance = (
                _safe_number(
                    report,
                    schedule_112a.get("full_value"),
                    "schedule_112a.full_value",
                )
                - _safe_number(
                    report, schedule_112a.get("cost"), "schedule_112a.cost"
                )
                - _safe_number(
                    report,
                    schedule_112a.get("expenditure"),
                    "schedule_112a.expenditure",
                )
            )
            if balance < 0:
                report.fail("schedule_112a consolidated balance cannot be negative")
            ltcg = _safe_number(
                report,
                special.get("ltcg_112a"),
                "special_rate_gains.ltcg_112a",
            )
            if abs(balance - ltcg) > 1:
                report.fail(
                    f"schedule_112a balance ({balance}) does not tie to "
                    f"special_rate_gains.ltcg_112a ({ltcg})"
                )
    except InputError as exc:
        report.fail(str(exc))

    try:
        foreign_raw = array(data.get("foreign_sources"), "foreign_sources")
        relief_total = Decimal(0)
        foreign_os_total = Decimal(0)
        for index, raw in enumerate(foreign_raw, 1):
            prefix = f"foreign_sources[{index}]"
            source = _check_unknown(
                report, raw, prefix, FOREIGN_SOURCE_KEYS
            )
            for key in (
                "country",
                "country_code",
                "income_head",
                "relief_section",
                "form67_status",
            ):
                if not str(source.get(key) or "").strip():
                    report.fail(f"{prefix}.{key} is required")
            code = str(source.get("country_code") or "")
            if code and not re.fullmatch(r"\d+", code):
                report.fail(f"{prefix}.country_code must be numeric")
            section = str(source.get("relief_section") or "")
            if section and section not in {"90", "91"}:
                report.fail(f"{prefix}.relief_section must be 90 or 91")
            gross = _safe_number(report, source.get("gross_income"), f"{prefix}.gross_income")
            foreign_tax = _safe_number(
                report, source.get("foreign_tax_paid"), f"{prefix}.foreign_tax_paid"
            )
            indian_tax = _safe_number(
                report, source.get("indian_tax_on_income"), f"{prefix}.indian_tax_on_income"
            )
            relief = _safe_number(
                report, source.get("relief_claimed"), f"{prefix}.relief_claimed"
            )
            dtaa_limit = _safe_number(
                report, source.get("dtaa_tax_limit"), f"{prefix}.dtaa_tax_limit"
            )
            if gross <= 0:
                report.fail(f"{prefix}.gross_income must be greater than zero")
            if min(foreign_tax, indian_tax, relief, dtaa_limit) < 0:
                report.fail(f"{prefix} tax and relief values must be non-negative")
            if relief > foreign_tax + 1 or relief > indian_tax + 1:
                report.fail(f"{prefix}.relief_claimed exceeds the FTC lower-of limit")
            if section == "90" and relief > 0:
                if "dtaa_tax_limit" not in source:
                    report.fail(
                        f"{prefix}.dtaa_tax_limit is required for section 90 relief"
                    )
                elif relief > dtaa_limit + 1:
                    report.fail(
                        f"{prefix}.relief_claimed exceeds the DTAA tax limit"
                    )
            status = str(source.get("form67_status") or "").lower()
            if status and status not in {"pending", "filed", "not_claiming"}:
                report.fail(
                    f"{prefix}.form67_status must be pending, filed, or not_claiming"
                )
            if relief > 0 and status == "not_claiming":
                report.fail(
                    f"{prefix}.relief_claimed must be zero when Form 67 status is not_claiming"
                )
            if relief > 0 and status and status != "filed":
                report.warn(f"{prefix} claims relief but Form 67 status is {status}")
            if status == "filed" and not str(
                source.get("form67_acknowledgement") or ""
            ).strip():
                report.warn(
                    f"{prefix} says Form 67 is filed but has no acknowledgement"
                )
            relief_total += relief
            if str(source.get("income_head") or "").strip().lower() == "other sources":
                foreign_os_total += gross

        configured_ftc = _safe_number(report, taxes.get("ftc"), "taxes_paid.ftc")
        if foreign_raw:
            residential_status = str(data.get("residential_status") or "").lower()
            if not residential_status:
                report.warn("residential_status is missing for foreign-source income")
            elif residential_status != "resident_and_ordinarily_resident":
                report.fail(
                    "foreign_sources currently require "
                    "resident_and_ordinarily_resident status"
                )
            if "ftc" in taxes and abs(configured_ftc - relief_total) > 1:
                report.fail(
                    f"taxes_paid.ftc ({configured_ftc}) does not tie to "
                    f"foreign_sources relief ({relief_total})"
                )
            os_total = sum(
                (
                    _safe_number(report, os_data.get(key), f"other_sources.{key}")
                    for key in (
                        "dividend",
                        "savings_interest",
                        "fd_interest",
                        "interest",
                        "other",
                    )
                ),
                Decimal(0),
            )
            if foreign_os_total > os_total + 1:
                report.fail(
                    "foreign Other Sources income exceeds the amount included in other_sources"
                )
        elif configured_ftc > 0:
            report.fail("taxes_paid.ftc is claimed but foreign_sources is absent")
    except InputError as exc:
        report.fail(str(exc))

    return report
