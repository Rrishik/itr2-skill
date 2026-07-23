from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from itr2lib.capital_gains import build_capital_gains
from itr2lib.common import InputError, QUARTERS


class CapitalGainsTests(unittest.TestCase):
    @staticmethod
    def contributions() -> dict:
        return {
            "capital_gains_manual": [
                {
                    "head": "Indian equity STCG",
                    "tax_bucket": "stcg_111a",
                    "consideration": 1_000,
                    "cost": 800,
                    "expenditure": 8,
                    "stt": 10,
                    "rows": 2,
                    "source": "Reviewed Indian-equity contribution",
                    "where": "Schedule CG A2",
                    "quarterly": {
                        "q1": 192,
                        "q2": 0,
                        "q3": 0,
                        "q4": 0,
                        "q5": 0,
                    },
                },
                {
                    "head": "Indian equity LTCG",
                    "tax_bucket": "ltcg_112a",
                    "consideration": 2_000,
                    "cost": 1_500,
                    "expenditure": 0,
                    "source": "Reviewed Indian-equity contribution",
                    "where": "Schedule CG B3",
                    "quarter": QUARTERS[2],
                },
                {
                    "head": "Foreign STCG",
                    "tax_bucket": "slab",
                    "consideration": 500,
                    "cost": 300,
                    "expenditure": 10,
                    "source": "Reviewed foreign-equity contribution",
                    "where": "Schedule CG A5",
                    "quarter": QUARTERS[1],
                },
            ]
        }

    def test_aggregates_reviewed_contributions_and_quarters(self) -> None:
        sections = build_capital_gains(self.contributions())

        heads = sections["capital_gains_head"]
        self.assertEqual(heads[0]["Gain"], 192)
        self.assertEqual(heads[0]["Expenditure"], 8)
        self.assertEqual(heads[0]["STT_Excluded"], 10)
        self.assertEqual(heads[0]["Rows"], 2)
        self.assertEqual(heads[1]["Gain"], 500)
        self.assertEqual(heads[2]["Gain"], 190)
        self.assertEqual(heads[-1]["Head"], "TOTAL (all CG heads)")
        self.assertEqual(heads[-1]["Rows"], 4)
        self.assertEqual(heads[-1]["Gain"], 882)

        split = sections["capital_gains_234c"]
        self.assertEqual(split[0]["Quarter"], QUARTERS[0])
        self.assertEqual(split[0]["SectionF"], "Row 1 (STCG @20%)")
        self.assertEqual(split[1]["Quarter"], QUARTERS[2])
        self.assertEqual(split[1]["SectionF"], "Row 5 (LTCG @12.5%)")
        self.assertEqual(split[2]["Quarter"], QUARTERS[1])
        self.assertEqual(split[2]["SectionF"], "Row 3 (STCG applicable rate)")

    def test_tax_bucket_and_quarterly_tie_are_required(self) -> None:
        data = self.contributions()
        del data["capital_gains_manual"][0]["tax_bucket"]
        with self.assertRaisesRegex(InputError, "require tax_bucket"):
            build_capital_gains(data)

        data = self.contributions()
        data["capital_gains_manual"][0]["quarterly"]["q1"] = 190
        with self.assertRaisesRegex(InputError, "does not tie"):
            build_capital_gains(data)


if __name__ == "__main__":
    unittest.main()
