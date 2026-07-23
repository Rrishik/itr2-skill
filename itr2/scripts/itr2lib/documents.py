from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from .common import InputError, number

CHECKLIST_KEYS = {"status", "reference", "note"}
CHECKLIST_STATUSES = {"missing", "provided", "reviewed", "not_applicable"}


@dataclass(frozen=True)
class DocumentRequirement:
    document_id: str
    label: str
    reason: str
    applies: Callable[[dict[str, Any]], bool]


@dataclass
class DocumentAssessment:
    status: str
    items: list[dict[str, str]] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    passes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "items": self.items,
            "missing": [
                item["id"]
                for item in self.items
                if item["status"] in {"missing", "unknown"}
            ],
            "unreviewed": [
                item["id"] for item in self.items if item["status"] == "provided"
            ],
        }


def _amount_is_nonzero(value: Any) -> bool:
    try:
        return number(value) != 0
    except InputError:
        return False


def _salary_applies(data: dict[str, Any]) -> bool:
    return _amount_is_nonzero(data.get("salary_gross"))


def _dividend_applies(data: dict[str, Any]) -> bool:
    other = data.get("other_sources")
    return isinstance(other, dict) and _amount_is_nonzero(other.get("dividend"))


def _interest_applies(data: dict[str, Any]) -> bool:
    other = data.get("other_sources")
    if not isinstance(other, dict):
        return False
    return any(
        _amount_is_nonzero(other.get(key))
        for key in ("savings_interest", "fd_interest", "interest")
    )


def _other_income_applies(data: dict[str, Any]) -> bool:
    other = data.get("other_sources")
    return isinstance(other, dict) and _amount_is_nonzero(other.get("other"))


def _house_property_applies(data: dict[str, Any]) -> bool:
    if _amount_is_nonzero(data.get("house_property")):
        return True
    detail = data.get("house_property_detail")
    return isinstance(detail, dict) and any(
        _amount_is_nonzero(detail.get(key))
        for key in ("annual_value", "municipal_tax", "home_loan_interest")
    )


def _capital_gains_apply(data: dict[str, Any]) -> bool:
    manual = data.get("capital_gains_manual")
    if isinstance(manual, list) and manual:
        return True
    if _amount_is_nonzero(data.get("slab_rate_gains")):
        return True
    special = data.get("special_rate_gains")
    return isinstance(special, dict) and any(
        _amount_is_nonzero(special.get(key))
        for key in ("stcg_111a", "ltcg_112a", "ltcg_112")
    )


def _deductions_apply(data: dict[str, Any]) -> bool:
    if _amount_is_nonzero(data.get("deduction_80ccd2")):
        return True
    deductions = data.get("deductions_old")
    return isinstance(deductions, dict) and any(
        _amount_is_nonzero(value) for value in deductions.values()
    )


def _tax_challans_apply(data: dict[str, Any]) -> bool:
    taxes = data.get("taxes_paid")
    if not isinstance(taxes, dict):
        return False
    return any(
        _amount_is_nonzero(taxes.get(key))
        for key in ("advance_tax", "self_assessment_tax")
    )


def _foreign_sources_apply(data: dict[str, Any]) -> bool:
    sources = data.get("foreign_sources")
    return isinstance(sources, list) and bool(sources)


def _foreign_assets_apply(data: dict[str, Any]) -> bool:
    return data.get("foreign_assets_held") is True


def _foreign_tax_proof_applies(data: dict[str, Any]) -> bool:
    sources = data.get("foreign_sources")
    if not isinstance(sources, list):
        return False
    return any(
        isinstance(source, dict)
        and (
            _amount_is_nonzero(source.get("foreign_tax_paid"))
            or _amount_is_nonzero(source.get("relief_claimed"))
        )
        for source in sources
    )


def _always(_: dict[str, Any]) -> bool:
    return True


DOCUMENT_REQUIREMENTS = (
    DocumentRequirement(
        "ais_tis",
        "AIS and TIS",
        "reconcile income reported by the department",
        _always,
    ),
    DocumentRequirement(
        "form_26as",
        "Form 26AS",
        "reconcile TDS, TCS, and tax payments",
        _always,
    ),
    DocumentRequirement(
        "salary_evidence",
        "Form 16, Form 12BA, pension certificate, or equivalent salary evidence",
        "salary or pension income is present",
        _salary_applies,
    ),
    DocumentRequirement(
        "dividend_evidence",
        "Dividend statement or equivalent evidence",
        "dividend income is present",
        _dividend_applies,
    ),
    DocumentRequirement(
        "interest_evidence",
        "Bank interest certificate, passbook, or equivalent evidence",
        "interest income is present",
        _interest_applies,
    ),
    DocumentRequirement(
        "other_income_evidence",
        "Evidence for other income",
        "other-source income is present",
        _other_income_applies,
    ),
    DocumentRequirement(
        "house_property_evidence",
        "House-property rent, municipal-tax, and loan-interest evidence",
        "house-property income or loss is present",
        _house_property_applies,
    ),
    DocumentRequirement(
        "capital_gains_working",
        "Reviewed capital-gain source-skill working",
        "capital gains or losses are present",
        _capital_gains_apply,
    ),
    DocumentRequirement(
        "deduction_evidence",
        "Deduction supporting evidence",
        "deductions are included in the regime comparison",
        _deductions_apply,
    ),
    DocumentRequirement(
        "tax_payment_challans",
        "Advance-tax and self-assessment-tax challans",
        "advance or self-assessment tax is present",
        _tax_challans_apply,
    ),
    DocumentRequirement(
        "foreign_asset_inventory",
        "Reviewed foreign-asset inventory or Schedule FA working",
        "foreign assets were held during the relevant calendar year",
        _foreign_assets_apply,
    ),
    DocumentRequirement(
        "foreign_source_working",
        "Reviewed foreign-income working",
        "foreign-source income is present",
        _foreign_sources_apply,
    ),
    DocumentRequirement(
        "foreign_tax_proof",
        "Foreign tax-paid proof and Form 67 acknowledgement, if filed",
        "foreign tax or tax relief is present",
        _foreign_tax_proof_applies,
    ),
)

DOCUMENT_REQUIREMENTS_BY_ID = {
    requirement.document_id: requirement for requirement in DOCUMENT_REQUIREMENTS
}


def applicable_requirements(data: dict[str, Any]) -> list[DocumentRequirement]:
    return [requirement for requirement in DOCUMENT_REQUIREMENTS if requirement.applies(data)]


def assess_document_checklist(data: dict[str, Any]) -> DocumentAssessment:
    requirements = applicable_requirements(data)
    foreign_assets_confirmed = "foreign_assets_held" in data
    foreign_assets_value = data.get("foreign_assets_held")
    foreign_assets_failure = (
        foreign_assets_confirmed and not isinstance(foreign_assets_value, bool)
    )
    foreign_assets_warning = not foreign_assets_confirmed
    if "document_checklist" not in data:
        assessment = DocumentAssessment(
            status="unknown",
            items=[
                {
                    "id": requirement.document_id,
                    "document": requirement.label,
                    "reason": requirement.reason,
                    "status": "unknown",
                    "reference": "",
                    "note": "",
                }
                for requirement in requirements
            ],
            warnings=[
                "document_checklist is absent; confirm applicable source documents "
                "before filing"
            ],
        )
        if foreign_assets_failure:
            assessment.failures.append("foreign_assets_held must be true or false")
            assessment.status = "not_ready"
        elif foreign_assets_warning:
            assessment.warnings.append(
                "foreign_assets_held is not confirmed; ask about all foreign assets"
            )
        return assessment

    raw_checklist = data.get("document_checklist")
    if not isinstance(raw_checklist, dict):
        return DocumentAssessment(
            status="not_ready",
            failures=["document_checklist must be an object"],
        )

    assessment = DocumentAssessment(status="not_ready")
    if foreign_assets_failure:
        assessment.failures.append("foreign_assets_held must be true or false")
    elif foreign_assets_warning:
        assessment.warnings.append(
            "foreign_assets_held is not confirmed; ask about all foreign assets"
        )
    unknown_ids = sorted(set(raw_checklist) - set(DOCUMENT_REQUIREMENTS_BY_ID))
    if unknown_ids:
        assessment.failures.append(
            f"unknown document_checklist key(s): {', '.join(unknown_ids)}"
        )

    parsed: dict[str, dict[str, str]] = {}
    for document_id, raw_entry in raw_checklist.items():
        prefix = f"document_checklist.{document_id}"
        if not isinstance(raw_entry, dict):
            assessment.failures.append(f"{prefix} must be an object")
            continue
        unknown_keys = sorted(set(raw_entry) - CHECKLIST_KEYS)
        if unknown_keys:
            assessment.failures.append(
                f"unknown {prefix} key(s): {', '.join(unknown_keys)}"
            )
        status_value = raw_entry.get("status")
        status = status_value.strip().lower() if isinstance(status_value, str) else ""
        if status not in CHECKLIST_STATUSES:
            assessment.failures.append(
                f"{prefix}.status must be missing, provided, reviewed, or not_applicable"
            )
        fields: dict[str, str] = {"status": status, "reference": "", "note": ""}
        for key in ("reference", "note"):
            value = raw_entry.get(key)
            if value is not None and not isinstance(value, str):
                assessment.failures.append(f"{prefix}.{key} must be text")
            elif isinstance(value, str):
                fields[key] = value.strip()
        if status in {"missing", "not_applicable"} and fields["reference"]:
            assessment.failures.append(
                f"{prefix}.reference must be empty when status is {status}"
            )
        if status in {"provided", "reviewed"} and not fields["reference"]:
            assessment.warnings.append(
                f"{prefix} is {status} but has no reference"
            )
        parsed[document_id] = fields

    for requirement in requirements:
        fields = parsed.get(
            requirement.document_id,
            {"status": "missing", "reference": "", "note": ""},
        )
        status = fields["status"] or "missing"
        item = {
            "id": requirement.document_id,
            "document": requirement.label,
            "reason": requirement.reason,
            "status": status,
            "reference": fields["reference"],
            "note": fields["note"],
        }
        assessment.items.append(item)
        prefix = f"document_checklist.{requirement.document_id}"
        if status == "not_applicable":
            assessment.failures.append(
                f"{prefix} cannot be not_applicable because {requirement.reason}"
            )
        elif status == "missing":
            assessment.warnings.append(
                f"{prefix} is missing: {requirement.label}"
            )
        elif status == "provided":
            assessment.warnings.append(
                f"{prefix} is provided but not reviewed: {requirement.label}"
            )

    if assessment.failures:
        assessment.status = "not_ready"
    elif foreign_assets_warning:
        assessment.status = "unknown"
    elif all(item["status"] == "reviewed" for item in assessment.items):
        assessment.status = "ready"
        assessment.passes.append("all applicable source documents are reviewed")
    else:
        assessment.status = "not_ready"
    return assessment
