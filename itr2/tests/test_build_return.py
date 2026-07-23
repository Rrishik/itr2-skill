from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_return import build


class BuildReturnTests(unittest.TestCase):
    @staticmethod
    def input_data() -> dict:
        return {
            "taxpayer": "Synthetic Taxpayer",
            "pan": "AAAAA0000A",
            "ay": "2026-27",
            "residential_status": "resident_and_ordinarily_resident",
            "senior_citizen": False,
            "foreign_assets_held": True,
            "salary_gross": 1_500_000,
            "salary_hra_exemption": 0,
            "salary_professional_tax": 0,
            "other_sources": {
                "dividend": 60_000,
                "savings_interest": 5_000,
                "fd_interest": 0,
                "dividend_quarterly": {
                    "q1": 10_000,
                    "q2": 20_000,
                    "q3": 30_000,
                    "q4": 0,
                    "q5": 0,
                },
            },
            "house_property": 0,
            "slab_rate_gains": 0,
            "special_rate_gains": {
                "stcg_111a": 0,
                "ltcg_112a": 0,
                "ltcg_112": 0,
            },
            "deduction_80ccd2": 0,
            "deductions_old": {
                "80c": 0,
                "80d": 0,
                "80tta_ttb": 0,
                "other": 0,
            },
            "taxes_paid": {
                "tds": 50_000,
                "advance_tax": 0,
                "self_assessment_tax": 0,
            },
            "foreign_sources": [
                {
                    "country": "Exampleland",
                    "country_code": "9",
                    "income_head": "Other Sources",
                    "gross_income": 50_000,
                    "foreign_tax_paid": 10_000,
                    "indian_tax_on_income": 15_000,
                    "relief_claimed": 10_000,
                    "relief_section": "90",
                    "dtaa_article": "Article 10",
                    "dtaa_tax_limit": 12_500,
                    "form67_status": "filed",
                    "form67_acknowledgement": "SYNTHETIC-ACK",
                    "source": "Synthetic certificate",
                }
            ],
            "document_checklist": {
                "ais_tis": {
                    "status": "reviewed",
                    "reference": "Synthetic AIS and TIS",
                },
                "form_26as": {
                    "status": "reviewed",
                    "reference": "Synthetic Form 26AS",
                },
                "salary_evidence": {
                    "status": "reviewed",
                    "reference": "Synthetic Form 16",
                },
                "dividend_evidence": {
                    "status": "reviewed",
                    "reference": "Synthetic dividend statement",
                },
                "interest_evidence": {
                    "status": "reviewed",
                    "reference": "Synthetic bank certificate",
                },
                "foreign_asset_inventory": {
                    "status": "reviewed",
                    "reference": "Synthetic Schedule FA working",
                },
                "foreign_source_working": {
                    "status": "reviewed",
                    "reference": "Synthetic foreign-source working",
                },
                "foreign_tax_proof": {
                    "status": "reviewed",
                    "reference": "Synthetic tax-paid proof",
                },
            },
        }

    def test_one_pass_idempotent_build_does_not_mutate_input(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            input_path = root / "tax_input.json"
            input_path.write_text(
                json.dumps(self.input_data(), indent=2) + "\n", encoding="utf-8"
            )
            original = input_path.read_bytes()
            out = root / "out"
            out.mkdir()
            stale = out / "Schedule112A.csv"
            stale.write_text("stale", encoding="utf-8")

            result = build(input_path, out)
            first_json = (out / "return.json").read_bytes()
            first_markdown = (out / "ITR2_data_entry.md").read_bytes()
            second = build(input_path, out)

            self.assertEqual(input_path.read_bytes(), original)
            self.assertEqual((out / "return.json").read_bytes(), first_json)
            self.assertEqual((out / "ITR2_data_entry.md").read_bytes(), first_markdown)
            self.assertFalse(stale.exists())

        self.assertEqual(result, second)
        self.assertEqual(result["document_readiness"]["status"], "ready")
        self.assertEqual(result["document_readiness"]["missing"], [])
        self.assertIn("foreign_source_income", result)
        self.assertIn("tax_relief", result)
        self.assertEqual(
            result["foreign_source_income"][0]["DTAATaxLimit"], 12_500
        )
        self.assertEqual(result["tax_relief"][0]["ReliefClaimed"], 10_000)
        tax = {row["LineItem"]: row for row in result["tax_computation"]}
        self.assertEqual(tax["Less: FTC"]["NEW"], 10_000)
        markdown = first_markdown.decode("utf-8")
        self.assertIn("## Schedule FSI — Foreign Source Income", markdown)
        self.assertIn("## Schedule TR — Tax Relief", markdown)
        self.assertIn("### 234C accrual/receipt grid", markdown)
        self.assertIn("## Source-document readiness", markdown)
        self.assertIn("Status: **READY**", markdown)

    def test_public_cli_smoke(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            input_path = root / "tax_input.json"
            input_path.write_text(
                json.dumps(self.input_data()) + "\n", encoding="utf-8"
            )
            scripts = Path(__file__).resolve().parents[1] / "scripts"
            verify = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(scripts / "verify_input.py"),
                    "--input-json",
                    str(input_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(verify.returncode, 0, verify.stderr)
            self.assertIn("VERIFY: 0 FAIL", verify.stdout)

            out = root / "out"
            build_result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(scripts / "build_return.py"),
                    "--input-json",
                    str(input_path),
                    "--out-dir",
                    str(out),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(build_result.returncode, 0, build_result.stderr)
            self.assertTrue((out / "return.json").is_file())
            self.assertTrue((out / "ITR2_data_entry.md").is_file())

    def test_missing_document_builds_visible_not_ready_draft(self) -> None:
        data = self.input_data()
        data["document_checklist"]["ais_tis"] = {
            "status": "missing",
            "note": "Not downloaded",
        }
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            input_path = root / "tax_input.json"
            input_path.write_text(json.dumps(data) + "\n", encoding="utf-8")
            out = root / "out"

            result = build(input_path, out)

            self.assertEqual(result["document_readiness"]["status"], "not_ready")
            self.assertEqual(result["document_readiness"]["missing"], ["ais_tis"])
            markdown = (out / "ITR2_data_entry.md").read_text(encoding="utf-8")
            self.assertIn("Status: **NOT_READY**", markdown)
            self.assertIn("not filing-ready", markdown)


if __name__ == "__main__":
    unittest.main()
