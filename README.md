# ITR-2 Final Return Assembler

A portable agent skill that validates reviewed AY 2026-27 ITR-2 contributions and creates a single return working set:

- `return.json` — structured schedule and tax-comparison rows.
- `ITR2_data_entry.md` — a schedule-by-schedule utility entry sheet.
- `Schedule112A.csv` — optional strict utility CSV using the downloaded template header.

The assembler does not parse broker statements or compute source-level Indian or foreign equity. Those calculations belong in the companion `indian-listed-equity` and `foreign-equity` skills. Copy only their reviewed filing contributions into the immutable `tax_input.json` contract.

> **Not tax advice.** Verify every figure against source documents, AIS/TIS, Form 26AS, and the official utility before filing. Rates are fixed to FY 2025-26 / AY 2026-27.

## Requirements

- Python 3.9 or later.
- No third-party packages.
- `pdftotext` remains optional for reading source PDFs outside this assembler.

## Install

The repository bundles the thin `itr` form router and the `itr2` final assembler:

```shell
python install.py copilot
python install.py claude
python install.py copilot-cli
```

The default target is `copilot`. Reload the agent after installation.

## Run

```shell
python itr2/scripts/verify_input.py --input-json sources/tax_input.json
python itr2/scripts/build_return.py --input-json sources/tax_input.json --out-dir skill_output
```

Use `--regime old` or `--regime new` only after reviewing an override of the computed recommendation.

To inspect a modern Excel workbook without Excel:

```shell
python itr2/scripts/read_xlsx.py --path source.xlsx
```

Legacy binary `.xls` files are rejected with a request to re-export as `.xlsx` or `.csv`.

## Design boundaries

- `tax_input.json` is read-only and never rewritten.
- Source calculations and Schedule FA A2/A3 CSVs stay in the companion source skills.
- FSI/TR rows use explicit reviewed income, tax, DTAA cap, relief, and Form 67 status. The assembler validates the lower-of limits; it does not estimate them.
- Intraday, F&O, and business income require ITR-3 and are out of scope.
- The scripts never file, submit, or e-verify a return.

See [itr2/references/output-template.md](itr2/references/output-template.md) for the input contract and [itr2/references/schedule-mapping.md](itr2/references/schedule-mapping.md) for utility mappings.

## Tests

```shell
cd itr2
python -B -m unittest discover -s tests -p "test_*.py" -v
```

All fixtures are synthetic.

## Privacy

The skill runs in folders containing PAN, salary, AIS, and broker data. The bundled ignore rules block common personal artifacts, but always inspect pending changes before committing.

## License

[MIT](LICENSE)
