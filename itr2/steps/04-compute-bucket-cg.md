# Step 4 — Compute and bucket the gains

Full rules in [../references/schedule-mapping.md](../references/schedule-mapping.md). Summary:

| Bucket | Section | Rate | Where in utility |
|---|---|---|---|
| Listed equity/equity-MF STCG (STT paid) | 111A | 20%* | Schedule CG → STCG item 2 |
| Other STCG (debt MF, unlisted, etc.) | slab | slab | Schedule CG → STCG item 5 |
| Listed equity/equity-MF LTCG (STT paid) | 112A | 12.5%* (first ₹1.25L exempt) | Schedule CG → LTCG item 3 |
| Listed bonds / SGB / ZCB LTCG (non-STT) | 112 | 12.5% no indexation, **no ₹1.25L exempt** | Schedule CG → LTCG item 2 |
| Dividends, interest | — | slab | Schedule OS |

*Post-23-Jul-2024 rates. Sales before that date use old rates — split if any exist.

- **Intraday** equity = **speculative business income** → strictly ITR-3, not ITR-2. Flag it explicitly.
- **Charges** (brokerage, exchange, SEBI, stamp duty, GST, IPFT) are deductible u/s 48 as
  "expenditure in connection with transfer". **STT is NOT deductible.**
- **Listed bonds / SGB / ZCB are s.112, not 112A** — 12.5%, no indexation, no ₹1.25L exemption (LTCG
  item 2). AIS often **mislabels** them as "listed debenture/securities"; classify by instrument.
- Enter **aggregate sale value and cost** in each grid, not the net gain — the utility computes balance.
- For a Zerodha-style broker tax-P&L, aggregate the heads deterministically with
  [../scripts/schedules/schedule_cg.ps1](../scripts/schedules/schedule_cg.ps1): export the "Tradewise
  Exits" sheet to CSV, then `schedule_cg.ps1 -Path <csv> -OutDir out` writes per-head
  consideration/cost/expenditure (STT excluded) and the 234C quarterly split. Cross-check its totals
  against the broker's own head-wise summary.

**Foreign holdings** (stocks / ESPP / RSU / foreign dividends / Schedule FA / FTC): if the taxpayer has
any, load [09-foreign-assets.md](./09-foreign-assets.md) and follow it. If none, skip it.
