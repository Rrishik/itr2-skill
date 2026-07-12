# Schedule 112A / 115AD CSV — upload rules & failure modes

Source: official "Instructions for filling Schedule 112A/115AD(1)(b)(iii)(P)" (incometax.gov.in).

## Column codes (per official instructions)
| Col | Field | Rule |
|---|---|---|
| 1a | Share/Unit acquired | `BE` if on/before 31-Jan-2018; `AE` if after. (NOT descriptive text.) |
| 2 | ISIN | starts with `IN`. No ISIN → `INNOTAVAILAB`. If 1a=`AE` → `INNOTREQUIRD`. |
| 3 | Name | alphanumeric only. If 1a=`AE` → `CONSOLIDATED`. |
| 4 | No. of shares/units | numeric ≥0, ≤4 decimals. If `AE` → **blank**. |
| 5 | Sale price per unit | numeric ≥0. If `AE` → **blank**. |
| 6 | Full value of consideration | =4×5 if `BE`; if `AE` enter total sale value. Round to unit. |
| 7 | Cost of acquisition w/o indexation | higher of col 8 and col 9. |
| 8 | Cost of acquisition | numeric ≥0. |
| 9 | (BE only) lower of 11 & 6 | grandfathering. If `AE` → **blank**. |
| 10 | FMV per share on 31-Jan-2018 | `BE` only; if `AE` → **blank**. |
| 11 | Total FMV = 4×10 | `BE` only. |
| 12 | Expenditure on transfer | numeric ≥0. |
| 13 | Total deductions = 7+12 | round to unit. |
| 14 | Balance = 6−13 | round to unit. |

**Forbidden characters anywhere in the file:** `, / - _ ( ) & @ \ ' " ; :` inside data values.
(The minus sign is why loss-making per-lot rows fail — consolidate instead.)

## Why `AE` consolidation is the safe default
When every lot was acquired after 31-Jan-2018 (no grandfathering), a single row:
```
AE,INNOTREQUIRD,CONSOLIDATED,,,<sale>,<cost>,<cost>,,,,<exp>,<cost+exp>,<sale-cost-exp>,
```
avoids: blank-ISIN rejection, minus signs from losing lots, and per-lot rounding drift.
Use per-scrip rows only when there are `BE` lots needing individual FMV.

## Upload failure checklist (in order of likelihood)
1. **UTF-8 BOM** (`EF BB BF`) at file start — strip it. Save as UTF-8 **without BOM**.
2. **Header not byte-identical to the template** — the template header contains **non-breaking
   spaces** (`C2 A0`), not regular spaces. Copy the template's header bytes verbatim; don't retype it.
3. **Wrong 1a code** — must be literal `AE`/`BE`, not "After 31st Jan 2018".
4. **Forbidden characters** in data (esp. `-` on losses).
5. **Line endings** — use CRLF.
6. `common.errors.csv_row_skip` — a data row failed validation (or it's just the header being
   skipped). Confirm whether LTCG actually populated; if not, fall back to the utility's manual
   "Add row" entry (Option 1), which bypasses the CSV parser entirely.

## Manual fallback (Option 1 in the utility)
For a handful of entries, skip the CSV and click **Add** in Schedule 112A. Enter the same
consolidated values (1a=After 31-Jan-2018, Name=CONSOLIDATED, full value, cost, expenditure).
Same result, no parser issues.

## Verifying totals
Aggregate `Full value of consideration`, `Cost`, and `Balance` must reconcile to the broker's
reported LTCG. When back-deriving per-lot cost from reported per-lot gain, do
`cost = sale - reportedGain` so each row and the grand total balance exactly (avoids rounding drift).
