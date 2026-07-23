from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from itr2lib.common import QUARTERS, quarter_for_date
from itr2lib.schedules import other_sources, salary
from itr2lib.tax import compute_tax
from itr2lib.validation import validate


class CoreTests(unittest.TestCase):
    @staticmethod
    def base_input() -> dict:
        return {
            "taxpayer": "Synthetic",
            "pan": "AAAAA0000A",
            "ay": "2026-27",
            "senior_citizen": False,
            "salary_gross": 2_000_000,
            "salary_hra_exemption": 100_000,
            "salary_professional_tax": 2_500,
            "other_sources": {
                "dividend": 100_000,
                "savings_interest": 10_000,
                "fd_interest": 20_000,
                "dividend_quarterly": {
                    "q1": 10_000,
                    "q2": 20_000,
                    "q3": 30_000,
                    "q4": 40_000,
                    "q5": 0,
                },
            },
            "house_property": -100_000,
            "slab_rate_gains": 50_000,
            "special_rate_gains": {
                "stcg_111a": 100_000,
                "ltcg_112a": 200_000,
                "ltcg_112": 100_000,
            },
            "capital_gains_manual": [
                {
                    "head": "Slab-rate STCG",
                    "tax_bucket": "slab_rate_gains",
                    "consideration": 100_000,
                    "cost": 50_000,
                    "where": "Schedule CG A5",
                },
                {
                    "head": "STCG 111A",
                    "tax_bucket": "stcg_111a",
                    "consideration": 200_000,
                    "cost": 100_000,
                    "where": "Schedule CG A2",
                },
                {
                    "head": "LTCG 112A",
                    "tax_bucket": "ltcg_112a",
                    "consideration": 300_000,
                    "cost": 100_000,
                    "where": "Schedule CG B3",
                },
                {
                    "head": "LTCG 112",
                    "tax_bucket": "ltcg_112",
                    "consideration": 200_000,
                    "cost": 100_000,
                    "where": "Schedule CG B8",
                },
            ],
            "deduction_80ccd2": 50_000,
            "deductions_old": {
                "80c": 150_000,
                "80d": 25_000,
                "80tta_ttb": 10_000,
                "other": 0,
            },
            "taxes_paid": {
                "tds": 100_000,
                "advance_tax": 0,
                "self_assessment_tax": 0,
                "ftc": 0,
            },
        }

    def test_234c_boundaries(self) -> None:
        cases = {
            date(2025, 6, 15): QUARTERS[0],
            date(2025, 6, 16): QUARTERS[1],
            date(2025, 9, 15): QUARTERS[1],
            date(2025, 9, 16): QUARTERS[2],
            date(2025, 12, 15): QUARTERS[2],
            date(2025, 12, 16): QUARTERS[3],
            date(2026, 3, 15): QUARTERS[3],
            date(2026, 3, 16): QUARTERS[4],
            date(2026, 3, 31): QUARTERS[4],
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(quarter_for_date(value), expected)

    def test_tax_engine_known_values(self) -> None:
        rows, recommendation = compute_tax(self.base_input())
        values = {row["LineItem"]: row for row in rows}
        self.assertEqual(recommendation, "NEW")
        self.assertEqual(values["Total income"]["NEW"], 2_355_000)
        self.assertEqual(values["Tax on slab income"]["NEW"], 191_000)
        self.assertEqual(values["Tax on special-rate gains"]["NEW"], 41_875)
        self.assertEqual(values["Total tax liability"]["NEW"], 242_190)
        self.assertEqual(values["Net payable (+) / refund (-)"]["NEW"], 142_190)
        self.assertEqual(values["Total income"]["OLD"], 2_092_500)
        self.assertEqual(values["Total tax liability"]["OLD"], 376_610)

    def test_schedules_and_dividend_only_quarterly_grid(self) -> None:
        data = self.base_input()
        salary_rows = salary(data, "new")
        self.assertEqual(salary_rows[-1]["Value"], 1_925_000)
        sections = other_sources(data)
        self.assertEqual(sections["other_sources"][-1]["Value"], 130_000)
        split = sections["other_sources_234c"]
        self.assertEqual(sum(row["Amount"] for row in split), 100_000)
        self.assertEqual({row["Item"] for row in split}, {"Dividend"})

    def test_validation_rejects_interest_quarterly(self) -> None:
        data = self.base_input()
        data["other_sources"]["interest_quarterly"] = {
            "q1": 30_000,
            "q2": 0,
            "q3": 0,
            "q4": 0,
            "q5": 0,
        }
        with tempfile.TemporaryDirectory() as temp:
            report = validate(data, Path(temp) / "tax_input.json")
        self.assertFalse(report.ok)
        self.assertTrue(
            any("interest_quarterly is unsupported" in item for item in report.failures)
        )

    def test_validation_requires_dividend_quarterly(self) -> None:
        data = self.base_input()
        del data["other_sources"]["dividend_quarterly"]
        with tempfile.TemporaryDirectory() as temp:
            report = validate(data, Path(temp) / "tax_input.json")
        self.assertFalse(report.ok)
        self.assertTrue(
            any("dividend_quarterly is required" in item for item in report.failures)
        )

    def test_validation_rejects_contradictory_document_status(self) -> None:
        data = self.base_input()
        data["foreign_assets_held"] = False
        data["document_checklist"] = {
            "ais_tis": {"status": "not_applicable"},
            "form_26as": {
                "status": "reviewed",
                "reference": "Synthetic Form 26AS",
            },
        }
        with tempfile.TemporaryDirectory() as temp:
            report = validate(data, Path(temp) / "tax_input.json")
        self.assertFalse(report.ok)
        self.assertTrue(
            any("cannot be not_applicable" in item for item in report.failures)
        )

    def test_foreign_sources_lower_of_and_form67(self) -> None:
        data = self.base_input()
        data["residential_status"] = "resident_and_ordinarily_resident"
        data["other_sources"]["dividend"] += 50_000
        data["other_sources"]["dividend_quarterly"]["q5"] = 50_000
        data["foreign_sources"] = [
            {
                "country": "Exampleland",
                "country_code": "9",
                "income_head": "Other Sources",
                "gross_income": 50_000,
                "foreign_tax_paid": 12_500,
                "indian_tax_on_income": 15_000,
                "relief_claimed": 12_500,
                "relief_section": "90",
                "dtaa_article": "Article 10",
                "dtaa_tax_limit": 12_500,
                "form67_status": "pending",
                "source": "Synthetic certificate",
            }
        ]
        data["taxes_paid"]["ftc"] = 12_500
        with tempfile.TemporaryDirectory() as temp:
            report = validate(data, Path(temp) / "tax_input.json")
        self.assertTrue(report.ok, report.failures)
        self.assertTrue(any("Form 67 status is pending" in item for item in report.warnings))

        del data["foreign_sources"][0]["dtaa_tax_limit"]
        with tempfile.TemporaryDirectory() as temp:
            report = validate(data, Path(temp) / "tax_input.json")
        self.assertFalse(report.ok)
        self.assertTrue(
            any("dtaa_tax_limit is required" in item for item in report.failures)
        )
        data["foreign_sources"][0]["dtaa_tax_limit"] = 12_500

        del data["foreign_sources"][0]["form67_status"]
        with tempfile.TemporaryDirectory() as temp:
            report = validate(data, Path(temp) / "tax_input.json")
        self.assertFalse(report.ok)
        self.assertTrue(
            any("form67_status is required" in item for item in report.failures)
        )
        data["foreign_sources"][0]["form67_status"] = "pending"

        data["foreign_sources"][0]["form67_status"] = "not_claiming"
        with tempfile.TemporaryDirectory() as temp:
            report = validate(data, Path(temp) / "tax_input.json")
        self.assertFalse(report.ok)
        self.assertTrue(
            any("must be zero" in item for item in report.failures)
        )

        data["foreign_sources"][0]["form67_status"] = "pending"
        data["foreign_sources"][0]["relief_claimed"] = 16_000
        with tempfile.TemporaryDirectory() as temp:
            report = validate(data, Path(temp) / "tax_input.json")
        self.assertFalse(report.ok)
        self.assertTrue(any("lower-of" in item for item in report.failures))

    def test_validation_rejects_nested_typos_and_dtaa_overclaim(self) -> None:
        data = self.base_input()
        data["taxes_paid"]["advance_taax"] = 1
        with tempfile.TemporaryDirectory() as temp:
            report = validate(data, Path(temp) / "tax_input.json")
        self.assertFalse(report.ok)
        self.assertTrue(
            any("unknown taxes_paid key" in item for item in report.failures)
        )

        data = self.base_input()
        data["residential_status"] = "resident_and_ordinarily_resident"
        data["other_sources"]["dividend"] += 50_000
        data["other_sources"]["dividend_quarterly"]["q5"] = 50_000
        data["foreign_sources"] = [
            {
                "country": "Exampleland",
                "country_code": "9",
                "income_head": "Other Sources",
                "gross_income": 50_000,
                "foreign_tax_paid": 15_000,
                "indian_tax_on_income": 15_000,
                "relief_claimed": 12_500,
                "relief_section": "90",
                "dtaa_article": "Article 10",
                "dtaa_tax_limit": 10_000,
                "form67_status": "filed",
                "form67_acknowledgement": "SYNTHETIC-ACK",
            }
        ]
        data["taxes_paid"]["ftc"] = 12_500
        with tempfile.TemporaryDirectory() as temp:
            report = validate(data, Path(temp) / "tax_input.json")
        self.assertFalse(report.ok)
        self.assertTrue(
            any("exceeds the DTAA tax limit" in item for item in report.failures)
        )


if __name__ == "__main__":
    unittest.main()
