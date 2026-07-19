# Step 1 — Collect documents

Ask the user to provide (whatever applies). Note which are missing and proceed with what's available:

| Document | Provides |
|---|---|
| Stocks capital-gains report (broker) | STCG/LTCG on shares, charges (brokerage/STT/etc.) |
| Mutual-fund capital-gains report (broker) | Equity & debt MF STCG/LTCG, grandfathered NAV |
| Stocks P&L / trade report | Intraday (speculative) vs delivery split, unrealised holdings |
| Form 16 / Form 12BA | Salary, perquisites, TDS, exemptions |
| AIS (PDF, password-protected) | Dept-reported dividend/interest/sale figures — the reconciliation baseline |
| TIS | Summarised income the dept expects |
| Dividend report | Dividend income (Schedule OS) — capture **credit dates** for the 234C quarterly split |
| Bank interest certificate / passbook | Savings + FD interest (Schedule OS) — capture **credit dates** for the 234C split |
| Pension certificate | Pension (taxed under Salaries) |
| Foreign broker statement (ESPP/RSU/foreign stocks) | Foreign capital gains, holdings for Schedule FA |
| Foreign broker **open/closed lots** report (cost-basis / gain-loss detail) | Exact **acquisition (vest) date** and per-lot cost basis — needed for the 24-month holding test |
| ESPP/RSU vesting or purchase report | Perquisite value (salary) + cost basis for later sale |
| Foreign dividend statement / 1042-S | Foreign dividends (Schedule OS) + tax withheld (FTC) |
| Form 67 / foreign tax-paid proof | Foreign Tax Credit under DTAA |

Clarify: residential status (Schedule FA + global income apply only to **Resident & Ordinarily Resident**),
senior-citizen status (DOB), regime preference, and whether a **separate** return (different PAN) is intended.

**Always ask about foreign holdings** — foreign stocks, ESPP/RSU (even unsold), foreign bank/broker
accounts. A resident holding *any* foreign asset must file **Schedule FA** regardless of sale; omission
triggers Black Money Act penalties. If the user has none, note it and move on.

## Confirm and organize the source set before extracting
List every file found in the folder, map each to its document type (table above), and present a short
two-column status — **Identified** (file → type) and **Missing / unidentified** (expected-but-absent
types, plus any file you couldn't classify). Then ask the user **only** about the Missing / unidentified
line — do not re-confirm files already identified. Proceed once the user supplies the gaps or says there
are none. Example:

```
Identified:
  Salary_Form16.pdf        → Form 16
  Indian_CapitalGains.xlsx → Broker capital-gains report
  AIS.pdf                  → AIS
Missing / unidentified:
  - No bank interest certificate (savings/FD interest) — provide or confirm none
  - mystery_report.xlsx — couldn't classify; what is it?
```

**Organize into a clean layout** (helps the human review what they provided, and keeps inputs separate
from regenerable outputs). Propose — and with the user's OK, put files into — two folders in the working
folder:
- **`sources/`** — every input: the raw documents **and** anything derived from them (e.g. a broker sheet
  exported to CSV, or `tax_input.json`). This is the folder the user reviews.
- **`skill_output/`** — only pipeline outputs (`return.json`, `ITR2_data_entry.md`, `Schedule112A.csv`).
  Safe to delete and regenerate; never put a source here.

Don't move or rename files without the user's confirmation. Once organized, point `tradewise_csv` (and any
other path in `tax_input.json`) at the `sources/` copies.

Once the basics are known, write **`work-context.json`** (see SKILL.md → Session state) capturing
taxpayer/PAN, AY, residential status, senior-citizen flag, regime preference, and foreign-assets yes/no.
Update it as later steps make decisions (chosen form, chosen regime, schedules that apply).
