from __future__ import annotations

import posixpath
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from .common import InputError

MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PACKAGE_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
NS = {"m": MAIN_NS, "r": REL_NS, "p": PACKAGE_REL_NS}


def _xml(archive: zipfile.ZipFile, name: str) -> ET.Element:
    try:
        return ET.fromstring(archive.read(name))
    except KeyError as exc:
        raise InputError(f"XLSX is missing required part {name}.") from exc
    except ET.ParseError as exc:
        raise InputError(f"XLSX part {name} contains invalid XML.") from exc


def _shared_strings(archive: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = _xml(archive, "xl/sharedStrings.xml")
    return [
        "".join(node.text or "" for node in item.findall(".//m:t", NS))
        for item in root.findall("m:si", NS)
    ]


def _sheets(archive: zipfile.ZipFile) -> list[tuple[str, str]]:
    if "xl/workbook.xml" not in archive.namelist():
        names = sorted(
            name
            for name in archive.namelist()
            if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")
        )
        if not names:
            raise InputError("XLSX contains no worksheets.")
        return [(name, name) for name in names]

    workbook = _xml(archive, "xl/workbook.xml")
    relationships = _xml(archive, "xl/_rels/workbook.xml.rels")
    targets = {
        relationship.attrib["Id"]: relationship.attrib["Target"]
        for relationship in relationships.findall("p:Relationship", NS)
    }
    result: list[tuple[str, str]] = []
    for sheet in workbook.findall("m:sheets/m:sheet", NS):
        relation_id = sheet.attrib.get(f"{{{REL_NS}}}id")
        if relation_id not in targets:
            continue
        target = targets[relation_id].lstrip("/")
        if not target.startswith("xl/"):
            target = posixpath.normpath(posixpath.join("xl", target))
        result.append((sheet.attrib.get("name", target), target))
    return result


def read_workbook(path: Path) -> list[tuple[str, list[list[tuple[str, str]]]]]:
    try:
        signature = path.read_bytes()[:4]
    except OSError as exc:
        raise InputError(f"Cannot read workbook {path}: {exc}") from exc
    if signature == bytes.fromhex("d0cf11e0"):
        raise InputError(
            "Legacy OLE .xls is unsupported; re-export the workbook as .xlsx or .csv."
        )
    if signature[:2] != b"PK":
        raise InputError("The file is not an XLSX ZIP workbook.")

    try:
        with zipfile.ZipFile(path) as archive:
            shared = _shared_strings(archive)
            output: list[tuple[str, list[list[tuple[str, str]]]]] = []
            for sheet_name, part_name in _sheets(archive):
                root = _xml(archive, part_name)
                rows: list[list[tuple[str, str]]] = []
                for row in root.findall("m:sheetData/m:row", NS):
                    cells: list[tuple[str, str]] = []
                    for cell in row.findall("m:c", NS):
                        reference = cell.attrib.get("r", "")
                        cell_type = cell.attrib.get("t")
                        if cell_type == "inlineStr":
                            value = "".join(
                                node.text or "" for node in cell.findall(".//m:t", NS)
                            )
                        else:
                            value_node = cell.find("m:v", NS)
                            value = (
                                value_node.text
                                if value_node is not None
                                and value_node.text is not None
                                else ""
                            )
                            if cell_type == "s" and value:
                                try:
                                    value = shared[int(value)]
                                except (IndexError, ValueError) as exc:
                                    raise InputError(
                                        f"Cell {reference} has an invalid shared-string index."
                                    ) from exc
                        cells.append((reference, value))
                    if cells:
                        rows.append(cells)
                output.append((sheet_name, rows))
            return output
    except zipfile.BadZipFile as exc:
        raise InputError("The file is not a valid XLSX ZIP workbook.") from exc
