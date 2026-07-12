# ITR-2 Capital Gains Skill

A [VS Code Copilot agent skill](https://code.visualstudio.com/docs/copilot/copilot-customization)
that helps you compute Indian **ITR-2** capital gains and other-source income from your broker / AIS
documents, build the **Schedule 112A** upload CSV, and map every value to the right box in the
Income-Tax offline utility.

It handles:

- **STCG / LTCG** on listed shares and mutual funds (111A / 112A / slab), post-23-Jul-2024 rates.
- **Other sources** — dividends, bank interest, pension.
- **Foreign stocks / ESPP / RSU / foreign dividends** — capital gains, Schedule FA, FTC (Form 67).
- **Schedule 112A CSV** generation with the byte-exact header the utility demands.
- **AIS / TIS reconciliation**, the quarterly (234C) breakup grid, and **OLD vs NEW regime** comparison.
- **ITR form selection** (ITR-1 / 2 / 3 / 4) based on your income mix.

> **Not tax advice.** This is a computation aid. Always verify every figure against the official
> Income-Tax utility and your source documents before filing. Rates reflect FY2024-25 / AY2025-26
> (post-23-Jul-2024) and may change in later years.

## Install

The skill folder is `itr-capital-gains/`. Drop it into a skills directory:

- **Personal (all workspaces):** `~/.agents/skills/`
- **Repo-scoped:** `.github/skills/` inside a workspace

### PowerShell (Windows)

```powershell
git clone https://github.com/<you>/itr-capital-gains-skill.git
$dest = "$env:USERPROFILE\.agents\skills"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
Copy-Item .\itr-capital-gains-skill\itr-capital-gains -Destination $dest -Recurse -Force
```

### bash (macOS / Linux)

```bash
git clone https://github.com/<you>/itr-capital-gains-skill.git
mkdir -p ~/.agents/skills
cp -r itr-capital-gains-skill/itr-capital-gains ~/.agents/skills/
```

Restart VS Code (or reload the window) so Copilot picks up the new skill.

## Usage

Point Copilot at the folder containing your tax documents and ask, for example:

> Compute my ITR-2 capital gains for the documents in `./tax-docs/`.

The skill will ask for whatever documents apply (broker capital-gains reports, Form 16, AIS, TIS,
dividend and bank-interest statements, foreign broker / ESPP statements), then walk the workflow and
produce a data-entry sheet plus the 112A CSV.

## What's inside

| Path | Purpose |
|---|---|
| `itr-capital-gains/SKILL.md` | The 8-step workflow and triggers |
| `itr-capital-gains/scripts/read_xlsx.ps1` | Dump any `.xlsx` (even extension-stripped) without Excel/Python |
| `itr-capital-gains/scripts/build_112a_csv.ps1` | Build a BOM-free, template-exact Schedule 112A CSV |
| `itr-capital-gains/references/schedule-mapping.md` | Where each value goes; form selection; quarterly grid |
| `itr-capital-gains/references/112a-csv.md` | CSV column codes and upload-failure fixes |
| `itr-capital-gains/references/output-template.md` | Output artifacts and tax-slab reference |

## Privacy

This skill runs **inside folders that contain sensitive personal data** (PAN, AIS PDFs, broker CSVs).
Never commit those. The included `.gitignore` blocks common tax-document patterns, but review your
commits before pushing.

## License

[MIT](./LICENSE)
