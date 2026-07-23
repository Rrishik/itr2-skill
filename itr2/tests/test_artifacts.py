from __future__ import annotations

import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from itr2lib.common import InputError
from itr2lib.schedule_112a import build_schedule_112a
from itr2lib.xlsx import read_workbook


class ArtifactTests(unittest.TestCase):
    def test_schedule_112a_exact_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            header = ",".join([f"Column\u00a0{index}" for index in range(1, 16)]).encode(
                "utf-8"
            )
            template = root / "template.csv"
            template.write_bytes(header + b"\r\n")
            out = root / "out"
            artifact = build_schedule_112a(
                {
                    "schedule_112a": {
                        "template_path": "template.csv",
                        "full_value": 1_000,
                        "cost": 700,
                        "expenditure": 20,
                    }
                },
                root,
                out,
            )
            payload = (out / "Schedule112A.csv").read_bytes()

        expected_row = b"AE,INNOTREQUIRD,CONSOLIDATED,,,1000,700,700,,,,20,720,280,"
        self.assertEqual(payload, header + b"\r\n" + expected_row)
        self.assertFalse(payload.startswith(b"\xef\xbb\xbf"))
        self.assertEqual(artifact["balance"], 280)
        self.assertTrue(artifact["header_byte_identical"])

    def test_schedule_112a_rejects_bom_and_negative_balance(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            template = root / "template.csv"
            template.write_bytes(b"\xef\xbb\xbf" + b",".join([b"H"] * 15))
            data = {
                "schedule_112a": {
                    "template_path": "template.csv",
                    "full_value": 100,
                    "cost": 200,
                    "expenditure": 0,
                }
            }
            with self.assertRaisesRegex(InputError, "must not contain"):
                build_schedule_112a(data, root, root / "out")
            template.write_bytes(b",".join([b"H"] * 15))
            with self.assertRaisesRegex(InputError, "negative balance"):
                build_schedule_112a(data, root, root / "out")

    @staticmethod
    def write_xlsx(path: Path) -> None:
        workbook = """<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
 <sheets><sheet name="Summary" sheetId="1" r:id="rId1"/></sheets>
</workbook>"""
        relationships = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Id="rId1" Type="worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>"""
        shared = """<?xml version="1.0" encoding="UTF-8"?>
<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="1" uniqueCount="1">
 <si><t>Heading</t></si>
</sst>"""
        sheet = """<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
 <sheetData>
  <row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1"><v>42</v></c></row>
  <row r="2"><c r="A2" t="inlineStr"><is><t>Inline</t></is></c></row>
 </sheetData>
</worksheet>"""
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("xl/workbook.xml", workbook)
            archive.writestr("xl/_rels/workbook.xml.rels", relationships)
            archive.writestr("xl/sharedStrings.xml", shared)
            archive.writestr("xl/worksheets/sheet1.xml", sheet)

    def test_xlsx_reader_supports_shared_and_inline_strings(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "workbook-without-extension"
            self.write_xlsx(path)
            workbook = read_workbook(path)
        self.assertEqual(workbook[0][0], "Summary")
        self.assertEqual(workbook[0][1][0], [("A1", "Heading"), ("B1", "42")])
        self.assertEqual(workbook[0][1][1], [("A2", "Inline")])

    def test_xlsx_reader_rejects_legacy_ole(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "legacy.xls"
            path.write_bytes(bytes.fromhex("d0cf11e0") + b"synthetic")
            with self.assertRaisesRegex(InputError, "re-export"):
                read_workbook(path)

    def test_xlsx_reader_rejects_archive_without_worksheets(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "empty.xlsx"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("placeholder", "synthetic")
            with self.assertRaisesRegex(InputError, "no worksheets"):
                read_workbook(path)


if __name__ == "__main__":
    unittest.main()
