---
name: itr2
version: 2.0.0
description: Assemble and validate an Indian AY 2026-27 ITR-2 working set from reviewed salary, house-property, other-source, capital-gain, FSI/TR, tax-paid, and optional Schedule 112A contributions. Use when the user needs final ITR-2 schedule mapping, old/new regime comparison, tax computation, reconciliation, or data-entry artifacts. Do not use it to parse Indian or foreign broker statements, create Schedule FA A2/A3 CSVs, file a return, or handle business income requiring ITR-3.
allowed-tools: Read, Write, Bash, Glob, Grep
---

# ITR-2 Final Return Assembler

Build the final return working set from immutable, reviewed contributions. Keep source-level computation in the relevant source skill.

## Boundaries

Use a companion source skill first when the user has raw broker data:

- Indian listed shares or equity mutual funds: use `indian-listed-equity`.
- Foreign shares, ESPP, RSU, dividends, Schedule FA, and foreign-currency conversion: use `foreign-equity`, then hand off its reviewed figures using the [foreign-source contribution contract](references/output-template.md#foreign-source-contribution).

This skill accepts the reviewed outputs of those skills. It must not reproduce their lot matching, grandfathering, fair-market-value, exchange-rate, or FA CSV logic.

Stop and route to ITR-3 for intraday, F&O, or other business/professional income. Never submit or e-verify the return.

## Workflow

1. Confirm the filing context and source documents before calculating anything:
   - Confirm AY 2026-27, individual taxpayer, ITR-2 eligibility, residential status, and the income mix.
   - Always ask whether the taxpayer held foreign shares, ESPP/RSU, bank/broker accounts, or any other foreign asset during the relevant calendar year, including assets with no sale or income.
   - Read the canonical requirements in `scripts/itr2lib/documents.py`, derive the applicable documents from the income mix, and inventory what the user already supplied.
   - When the user points to a working folder, list its files and match obvious documents by filename and type. Do not read every file before deciding what is missing, and do not treat filename matching as review.
   - Ask one grouped question for only the applicable documents that are missing. Let the user identify unavailable documents; do not invent evidence or repeatedly request the same item.
   - Record the foreign-asset answer in `foreign_assets_held` and each document answer in `document_checklist` as `missing`, `provided`, `reviewed`, or `not_applicable`. Missing documents may remain in a draft, but must be disclosed as not filing-ready.
2. Preserve all source documents. Create or update a separate `tax_input.json`; never modify source statements.
3. Enter reviewed annual and quarterly contributions using the contract in [references/output-template.md](references/output-template.md).
4. For each section 90/91 FSI item, obtain explicit Indian tax on that income, foreign tax paid, relief claimed, and Form 67 status. Section 90 also requires the reviewed DTAA tax limit.
5. Validate before calculating:

   ```shell
   python scripts/verify_input.py --input-json <path/to/tax_input.json>
   ```

6. Resolve every failure. Warnings require review and disclosure but do not block a draft.
7. Build once:

   ```shell
   python scripts/build_return.py --input-json <path/to/tax_input.json> --out-dir <output-directory>
   ```

8. Review both regime columns in `ITR2_data_entry.md`. Use `--regime old` or `--regime new` only for an informed override.
9. Reconcile income and tax with Form 16, AIS/TIS, Form 26AS, broker/source-skill outputs, and bank records.
10. Enter the reviewed figures into the official utility and run its own validation.

## Input rules

- `document_checklist` records taxpayer-specific intake state. The canonical document names and applicability rules live only in `scripts/itr2lib/documents.py`.
- A missing checklist makes document readiness `unknown`. Missing or merely provided applicable documents make it `not_ready`; only reviewed applicable documents make it `ready`.
- Never treat a filename or declared status as proof that the underlying figures are correct. Reconcile the contents before marking a document reviewed.
- `capital_gains_manual[]` means reviewed schedule contributions, not arbitrary overrides.
- Every capital-gain entry needs `tax_bucket`, consideration, cost, expenditure if any, and its utility destination.
- Annual capital-gain fields must tie to the sum of contributions.
- If contribution-level quarters are supplied, they must tie to that contribution's gain.
- `other_sources.dividend_quarterly` is required when dividends are non-zero. Do not add `interest_quarterly`; current Schedule OS quarterly disclosure for ordinary interest is intentionally absent.
- `foreign_sources[]` must tie to the appropriate annual other-source or capital-gain figure.
- A claimed FTC must equal the sum of reviewed source relief and cannot exceed the applicable lower-of limits.
- The optional Schedule 112A block emits the preserved consolidated V1 row. Its balance must reconcile to `special_rate_gains.ltcg_112a`.
- Schedule FA remains outside this skill. Use the source skill's strict FA output directly.

## Output

The build produces:

- `return.json`
- `ITR2_data_entry.md`
- optional `Schedule112A.csv`

Both standard outputs include source-document readiness. Treat them as working papers, not a filed return. Never silently correct or overwrite `tax_input.json`.
