# Step 3 — Read the documents

- Broker reports are often `.xlsx` **with the extension stripped** — check magic bytes (`50 4B` = xlsx/zip).
- Read xlsx without Excel/Python using [../scripts/read_xlsx.ps1](../scripts/read_xlsx.ps1) (extracts sharedStrings + sheet rows).
- Broker legacy `.xls` files are **OLE (magic `D0 CF 11 E0`)**, not ZIP `.xlsx`. `read_xlsx.ps1` now detects
  this and **auto-falls back to Excel COM** — no extra step needed, provided Excel is installed. If it
  isn't, the script tells you to re-save the file as `.xlsx`/`.csv` and retry.
- `read_xlsx.ps1` needs the file **not open/locked in Excel** (uses .NET ZipFile). If locked, export the
  worksheets to CSV via a fresh hidden Excel COM instance instead.
- **Password-protected PDFs** — each source uses its own scheme, so try them per-source:
  AIS/TIS/26AS = PAN-lowercase + DOB `DDMMYYYY` (e.g. `abcde1234f01011980`); Form 16 is often
  PAN-uppercase only; CAS/CAMS/broker statements may use a user-set password. Extract with
  `pdftotext -layout -upw "<pwd>" in.pdf out.txt`.
