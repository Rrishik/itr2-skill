# ITR-2 Capital Gains Skill

A portable [Agent Skill](https://code.visualstudio.com/docs/copilot/copilot-customization) that
computes Indian **ITR-2** capital gains and other-source income from your broker / AIS documents,
builds the **Schedule 112A** upload CSV, and maps every value to the right box in the Income-Tax
offline utility. Covers STCG/LTCG (111A/112A/112/slab), dividends & interest, foreign stocks/ESPP/RSU
(vest-date holding test, Rule 115/128 currency conversion, Schedule FA, DTAA FTC via Form 67),
AIS/TIS reconciliation, the 234C quarterly grid, OLD vs NEW regime, and ITR-1/2/3/4 form selection.

> **Not tax advice.** A computation aid — verify every figure against the official utility and your
> source documents before filing. Rates reflect FY2025-26 / AY2026-27 (post-23-Jul-2024).

## Install

The skill lives in `itr2/`. Clone, then drop it into your agent's skills directory:

| Agent | Skills directory |
|---|---|
| VS Code Copilot | `~/.agents/skills/` |
| Claude Code | `~/.claude/skills/` |
| GitHub Copilot CLI | `~/.copilot/skills/` |

Easiest — from the cloned repo, run the helper (or just open the repo and tell your agent
**"install this skill"**, per [AGENTS.md](./AGENTS.md)):

```bash
./install.sh claude        # copilot (default) | claude | copilot-cli
.\install.ps1 claude       # same, on Windows
```

Reload your agent afterward. The bundled scripts need **PowerShell** (and `pdftotext` for AIS PDFs);
without them those steps just become manual.

## Recommendations

- **Model:** run this skill with **Claude Opus 4.8** — the multi-step reconciliation, regime
  comparison, and tax-law reasoning benefit from the stronger model.
- **Playwright MCP** (for foreign income): SBI does not publish historical TT buying rates openly and
  the RBI/FBIL rate pages are JavaScript date-picker forms that a plain fetch can't read. Install the
  [Playwright MCP server](https://github.com/microsoft/playwright-mcp) so the agent can drive the
  **RBI reference-rate archive** (rbi.org.in → Reference Rate Archive) to pull authentic USD/INR rates
  for each transaction/month-end date (RBI mid is the standard citable proxy for SBI TTBR).

## Usage

Point your agent at the folder with your tax documents:

> Compute my ITR-2 capital gains for the documents in `./tax-docs/`.

It asks for whatever applies (broker reports, Form 16, AIS, TIS, dividend / bank-interest / foreign
broker statements), then produces a data-entry sheet and the 112A CSV.

## Privacy

The skill runs **inside folders holding sensitive data** (PAN, AIS PDFs, broker CSVs). Never commit
those — the bundled `.gitignore` blocks common patterns, but review before pushing.

## License

[MIT](./LICENSE)
