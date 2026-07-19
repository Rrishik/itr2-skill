---
name: itr2
description: 'Compute Indian ITR-2 capital gains and other-source income from broker/AIS documents and map them into the Income-Tax offline utility. USE WHEN: user is filing an Indian income-tax return (ITR-2/AY), has capital gains from stocks or mutual funds, needs STCG/LTCG/OS figures computed, needs a Schedule 112A CSV built for upload, asks where to enter values in the ITR utility, wants to reconcile broker statements against AIS/TIS, or holds foreign stocks/ESPP/RSU/foreign dividends needing Schedule FA and FTC. Handles Groww/Zerodha/broker capital-gains reports, Form 16, AIS, TIS, dividend reports, bank interest certificates, and foreign broker/ESPP statements. DO NOT USE FOR: business/professional income (needs ITR-3), non-Indian tax returns, or GST.'
argument-hint: 'Point to the folder containing the tax documents'
---

# ITR-2 Capital Gains & Income Computation

Compute capital gains (STCG/LTCG), other-source income, and produce the Schedule 112A
CSV for India's ITR-2, then tell the user exactly where each value goes in the offline utility.

## When to Use
- Filing an Indian ITR-2 with capital gains from listed shares and/or mutual funds.
- Building an uploadable Schedule 112A CSV.
- Reconciling broker statements against AIS/TIS.
- Deciding OLD vs NEW regime.

## Step 1 — Collect documents
Ask the user to provide (whatever applies). Note which are missing and proceed with what's available:

| Document | Provides |
|---|---|
| Stocks capital-gains report (broker) | STCG/LTCG on shares, charges (brokerage/STT/etc.) |
| Mutual-fund capital-gains report (broker) | Equity & debt MF STCG/LTCG, grandfathered NAV |
| Stocks P&L / trade report | Intraday (speculative) vs delivery split, unrealised holdings |
| Form 16 / Form 12BA | Salary, perquisites, TDS, exemptions |
| AIS (PDF, password-protected) | Dept-reported dividend/interest/sale figures — the reconciliation baseline |
| TIS | Summarised income the dept expects |
| Dividend report | Dividend income (Schedule OS) |
| Bank interest certificate / passbook | Savings + FD interest (Schedule OS) |
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

## Step 2 — Decide which ITR form
Before computing anything, confirm the right form for the taxpayer's income mix (see
[references/schedule-mapping.md](./references/schedule-mapping.md#itr-form-selection) for the full table):

| Form | Fits when | Blocks / notes |
|---|---|---|
| **ITR-1 (Sahaj)** | Resident, income ≤₹50L, only salary/one house/other sources, **LTCG 112A ≤₹1.25L** | No STCG, no foreign assets, not a company director |
| **ITR-2** | Salary/pension + capital gains + other sources + foreign assets; no business income | **This skill's default.** Any capital gain beyond the ITR-1 112A cap → ITR-2 |
| **ITR-3** | Any of the above **plus** business/professional income — incl. **intraday** (speculative) or **F&O** | Required if intraday/F&O exists; not covered by this skill |
| **ITR-4 (Sugam)** | Presumptive business (44AD/ADA/AE), resident, income ≤₹50L | No capital gains (except LTCG 112A ≤₹1.25L), no foreign assets |

Decision order: **intraday/F&O/business → ITR-3** (stop, out of scope). Else **capital gains present or
foreign assets held → ITR-2**. Else only salary + minor 112A → ITR-1 may suffice. State the chosen form
and *why* to the user, and flag if a disqualifier (e.g. intraday) forces a form they didn't expect.

## Step 3 — Read the documents
- Broker reports are often `.xlsx` **with the extension stripped** — check magic bytes (`50 4B` = xlsx/zip).
- Read xlsx without Excel/Python using [read_xlsx.ps1](./scripts/read_xlsx.ps1) (extracts sharedStrings + sheet rows).
- **Password-protected PDFs** — each source uses its own scheme, so try them per-source:
  AIS/TIS/26AS = PAN-lowercase + DOB `DDMMYYYY` (e.g. `abcde1234f01011980`); Form 16 is often
  PAN-uppercase only; CAS/CAMS/broker statements may use a user-set password. Extract with
  `pdftotext -layout -upw "<pwd>" in.pdf out.txt`.

## Step 4 — Compute and bucket the gains
See [references/schedule-mapping.md](./references/schedule-mapping.md) for the full rules. Summary:

| Bucket | Section | Rate | Where in utility |
|---|---|---|---|
| Listed equity/equity-MF STCG (STT paid) | 111A | 20%* | Schedule CG → STCG item 2 |
| Other STCG (debt MF, unlisted, etc.) | slab | slab | Schedule CG → STCG item 5 |
| Listed equity/equity-MF LTCG (STT paid) | 112A | 12.5%* (first ₹1.25L exempt) | Schedule CG → LTCG item 3 |
| Listed bonds / SGB / ZCB LTCG (non-STT) | 112 | 12.5% no indexation, **no ₹1.25L exempt** | Schedule CG → LTCG item 2 |
| Dividends, interest | — | slab | Schedule OS |

*Post-23-Jul-2024 rates. Sales before that date use old rates — split if any exist.

- **Foreign stocks / ESPP / RSU** on sale = capital gains but **NOT** 111A/112A (no STT): >24 months
  held → LTCG at 12.5% (**no ₹1.25L exemption** — that shield is 112A-only; foreign LTCG is **s.112**);
  ≤24 months → STCG at slab. Holding period runs from the **vest date, not the grant date**; confirm it
  and the per-lot cost from the broker's **closed-lots report** — the US LONG/SHORT tag ≠ India's
  24-month test. The ESPP/RSU vesting value is a **salary perquisite**; if the employer is foreign it's
  usually missing from Form 16 and must be added to salary manually.
- **Currency conversion (Rule 115/128):** SBI TT buying rate on the relevant date (transaction date for a
  sale/purchase; last day of the *preceding* month for income/foreign-tax); holiday → prior working day.
  Use the **RBI reference-rate archive** as the citable proxy and log every rate.
- **Foreign dividends** → Schedule OS at slab (gross); foreign tax withheld → **FTC via Form 67** (file
  *before* the return). For **US dividends the India–US DTAA rate is 25% for individuals** (15% is
  company-≥10%-voting-stock only) and fully creditable. A resident's global income is taxable.
- **Schedule FA** — list every foreign asset held any time in the calendar year (not FY): shares, ESPP/RSU
  (including unvested per the relevant table), and foreign accounts. Mandatory for Resident & Ordinarily Resident.
- Full foreign rules (holding test, Rule 115/128, DTAA rates, 1042-S CY-vs-FY timing) in
  [references/schedule-mapping.md](./references/schedule-mapping.md#foreign-stocks--espp--rsu--foreign-dividends).
- **Intraday** equity = **speculative business income** → strictly ITR-3, not ITR-2. Flag it explicitly.
- **Charges** (brokerage, exchange, SEBI, stamp duty, GST, IPFT) are deductible u/s 48 as
  "expenditure in connection with transfer". **STT is NOT deductible.**
- Enter **aggregate sale value and cost** in each grid, not the net gain — the utility computes balance.

## Step 5 — Build the Schedule 112A CSV
Use the user's downloaded template header **verbatim** and follow the official column codes.
See [references/112a-csv.md](./references/112a-csv.md) for the exact rules and the common
upload-failure causes (BOM, non-breaking spaces, `AE`/`BE` codes, forbidden characters).
Build with [build_112a_csv.ps1](./scripts/build_112a_csv.ps1).

## Step 6 — Reconcile against AIS
Always compare computed dividend/interest/sale totals to AIS. Small (≈₹ tens) differences are
rounding — **report the AIS figure** to avoid mismatch notices. Large differences need investigation
(FY-basis vs ex-date vs payment-date; missing transactions).

## Step 7 — Quarterly breakup (Section F / OS 234C grid)
Gains and dividends must be split by the quarter the **sale/credit** occurred, for 234C interest.
FY quarters: ≤15-Jun, 16-Jun–15-Sep, 16-Sep–15-Dec, 16-Dec–15-Mar, 16-Mar–31-Mar.
The utility rejects negatives — net a loss-quarter into a later positive quarter so each row still
sums to the annual total. Full grid layout (the 5 periods × 6 CG rows and the netting rule) is in
[references/schedule-mapping.md](./references/schedule-mapping.md#quarterly-breakup--schedule-cg-section-f-and-os-234c-grid).

## Step 8 — Regime comparison & output
Compute tax under OLD and NEW and recommend the lower. Produce a data-entry sheet
(see [references/output-template.md](./references/output-template.md)) and a machine-readable
`tax_input.json` mirroring the computed values. Also give the user a **schedule tick-list** for the
utility's "Select Schedule" step — which schedules to add/remove for their income mix (see
[references/schedule-mapping.md](./references/schedule-mapping.md#which-schedules-to-select-in-the-utility)).
Common misses: **FSI + TR** unticked while claiming FTC; **112A** ticked with no 112A income; **ESOP**
ticked for ordinary RSUs; **80D/VI-A** ticked under the NEW regime.

## Key gotchas (learned)
- CSV upload rejects: UTF-8 BOM, header not byte-identical to template (non-breaking spaces),
  wrong 1a code (`AE` after 31-Jan-2018 / `BE` before), and any of `, / - _ ( ) & @ \ ' " ; :`
  inside data — so a consolidated `AE` row (ISIN `INNOTREQUIRD`, name `CONSOLIDATED`) avoids the
  minus signs from loss-making lots.
- 80TTA (non-senior) vs 80TTB (senior, ₹50k) for interest.
- Grandfathering (31-Jan-2018 NAV) applies only to `BE` lots.
- **Listed bonds / SGB / ZCB are s.112, not 112A** — 12.5% with no indexation and no ₹1.25L exemption
  (LTCG item 2). AIS often **mislabels** them as "listed debenture/securities"; classify by instrument.
- **The employer's regime choice doesn't bind the return** — Form 16 may deduct TDS under old regime
  (opted out of 115BAC), but always recompute both regimes fresh and pick the lower for the filing.
- **Foreign LTCG (s.112) gets no ₹1.25L exemption** — that shield is 112A (listed Indian equity) only.
- **US dividend DTAA rate is 25% for individuals** (15% is company-≥10%-voting-stock only), fully creditable.
- Broker legacy `.xls` files may be **OLE (magic `D0 CF 11 E0`)**, not ZIP `.xlsx` — read_xlsx.ps1 only
  handles ZIP-based xlsx; use another reader (e.g. Excel COM) for OLE.
- **Foreign dividend timing:** 1042-S is by US *calendar year*, but India taxes by *FY receipt date* —
  Jan–Mar dividends belong to the Indian FY even before that year's 1042-S is issued.
