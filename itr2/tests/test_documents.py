from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from itr2lib.documents import assess_document_checklist


class DocumentChecklistTests(unittest.TestCase):
    @staticmethod
    def base_input() -> dict:
        return {
            "foreign_assets_held": False,
            "salary_gross": 0,
            "other_sources": {},
            "house_property": 0,
            "slab_rate_gains": 0,
            "special_rate_gains": {},
            "capital_gains_manual": [],
            "deduction_80ccd2": 0,
            "deductions_old": {},
            "taxes_paid": {},
            "foreign_sources": [],
        }

    @staticmethod
    def reviewed(reference: str = "Synthetic evidence") -> dict:
        return {"status": "reviewed", "reference": reference}

    def test_absent_checklist_and_foreign_answer_are_unknown(self) -> None:
        data = self.base_input()
        del data["foreign_assets_held"]

        assessment = assess_document_checklist(data)

        self.assertEqual(assessment.status, "unknown")
        self.assertTrue(
            any("document_checklist is absent" in item for item in assessment.warnings)
        )
        self.assertTrue(any("foreign_assets_held" in item for item in assessment.warnings))
        self.assertEqual(
            {item["id"] for item in assessment.items},
            {"ais_tis", "form_26as"},
        )

    def test_complete_applicable_checklist_is_ready(self) -> None:
        data = self.base_input()
        data.update(
            {
                "salary_gross": 1_000_000,
                "other_sources": {
                    "dividend": 10_000,
                    "savings_interest": 2_000,
                    "other": 500,
                },
                "house_property": -20_000,
                "slab_rate_gains": 15_000,
                "deduction_80ccd2": 10_000,
                "taxes_paid": {"advance_tax": 5_000},
                "foreign_assets_held": True,
                "foreign_sources": [
                    {
                        "foreign_tax_paid": 2_000,
                        "relief_claimed": 1_500,
                    }
                ],
            }
        )
        expected = {
            "ais_tis",
            "form_26as",
            "salary_evidence",
            "dividend_evidence",
            "interest_evidence",
            "other_income_evidence",
            "house_property_evidence",
            "capital_gains_working",
            "deduction_evidence",
            "tax_payment_challans",
            "foreign_asset_inventory",
            "foreign_source_working",
            "foreign_tax_proof",
        }
        data["document_checklist"] = {
            document_id: self.reviewed() for document_id in expected
        }

        assessment = assess_document_checklist(data)

        self.assertEqual(assessment.status, "ready")
        self.assertEqual({item["id"] for item in assessment.items}, expected)
        self.assertFalse(assessment.failures)
        self.assertFalse(assessment.warnings)

    def test_missing_and_provided_documents_make_draft_not_ready(self) -> None:
        data = self.base_input()
        data["document_checklist"] = {
            "ais_tis": {"status": "missing", "note": "Not downloaded"},
            "form_26as": {
                "status": "provided",
                "reference": "Synthetic Form 26AS",
            },
        }

        assessment = assess_document_checklist(data)

        self.assertEqual(assessment.status, "not_ready")
        self.assertFalse(assessment.failures)
        self.assertTrue(any("is missing" in item for item in assessment.warnings))
        self.assertTrue(any("not reviewed" in item for item in assessment.warnings))
        self.assertEqual(assessment.as_dict()["missing"], ["ais_tis"])
        self.assertEqual(assessment.as_dict()["unreviewed"], ["form_26as"])

    def test_contradictory_or_malformed_entries_fail(self) -> None:
        cases = (
            (
                {"ais_tis": {"status": "not_applicable"}},
                "cannot be not_applicable",
            ),
            (
                {"ais_tis": {"status": "reviewed", "extra": True}},
                "unknown document_checklist.ais_tis key",
            ),
            (
                {"ais_tis": {"status": "complete"}},
                "status must be missing, provided, reviewed, or not_applicable",
            ),
            (
                {"unknown_document": {"status": "reviewed"}},
                "unknown document_checklist key",
            ),
        )
        for checklist, message in cases:
            with self.subTest(message=message):
                data = self.base_input()
                data["document_checklist"] = checklist
                assessment = assess_document_checklist(data)
                self.assertTrue(
                    any(message in failure for failure in assessment.failures),
                    assessment.failures,
                )

    def test_conditional_document_cannot_be_not_applicable(self) -> None:
        data = self.base_input()
        data["salary_gross"] = 500_000
        data["document_checklist"] = {
            "ais_tis": self.reviewed(),
            "form_26as": self.reviewed(),
            "salary_evidence": {"status": "not_applicable"},
        }

        assessment = assess_document_checklist(data)

        self.assertTrue(
            any("salary_evidence cannot be not_applicable" in item for item in assessment.failures)
        )

    def test_foreign_assets_without_income_require_only_inventory(self) -> None:
        data = self.base_input()
        data["foreign_assets_held"] = True
        data["document_checklist"] = {
            "ais_tis": self.reviewed(),
            "form_26as": self.reviewed(),
            "foreign_asset_inventory": self.reviewed(),
        }

        assessment = assess_document_checklist(data)

        self.assertEqual(assessment.status, "ready")
        ids = {item["id"] for item in assessment.items}
        self.assertIn("foreign_asset_inventory", ids)
        self.assertNotIn("foreign_source_working", ids)
        self.assertNotIn("foreign_tax_proof", ids)


if __name__ == "__main__":
    unittest.main()