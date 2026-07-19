# Step 4 — Compute and bucket the gains

Full rules in [../references/schedule-mapping.md](../references/schedule-mapping.md). Summary:

| Bucket | Section | Rate | Where in the utility (Schedule CG) |
|---|---|---|---|
| Listed equity/equity-MF STCG (STT paid) | 111A | 20%* | **A → item 2** (Equity/equity-MF, STT paid, 111A) |
| Other STCG — debt MF (s.50AA), unlisted, foreign shares held ≤24m | slab | slab | **A → item 5** (assets other than A1–A4) |
| Listed equity/equity-MF LTCG (STT paid) | 112A | 12.5%* (first ₹1.25L exempt) | **B → item 3** (opens the Schedule 112A grid) |
| Listed bonds / **SGB (sold on exchange)** / ZCB LTCG (non-STT) | 112(1) | 12.5% no indexation, **no ₹1.25L exempt** | **B → item 2** (listed securities/ZCB u/s 112(1)) |
| Foreign shares LTCG (held >24m, no STT) | 112(1) | 12.5% no exemption | **B → item 8** (assets where B1–B7 N/A) |
| Dividends, interest | — | slab | Schedule OS (dividend 1a; interest 1b) |

*Post-23-Jul-2024 rates. Sales before that date use old rates — split if any exist.

- **SGB caveat:** the B2 mapping is for a **secondary-market sale on the exchange**. An SGB **held to
  maturity (8 yr)** or **prematurely redeemed to RBI (after 5 yr)** is **fully exempt** — put it in the
  **Exempt Income (EI)** schedule, not Schedule CG.

- **Intraday** equity = **speculative business income** → strictly ITR-3, not ITR-2. Flag it explicitly.
- **Charges** (brokerage, exchange, SEBI, stamp duty, GST, IPFT) are deductible u/s 48 as
  "expenditure in connection with transfer". **STT is NOT deductible.**
- **Listed bonds / SGB / ZCB are s.112, not 112A** — 12.5%, no indexation, no ₹1.25L exemption (LTCG
  item 2). AIS often **mislabels** them as "listed debenture/securities"; classify by instrument.
- Enter **aggregate sale value and cost** in each grid, not the net gain — the utility computes balance.
- **Slab-rate CG** (specified debt MF s.50AA, foreign equity held <24m, unlisted STCG) goes into
  `tax_input.json` as `slab_rate_gains` — never fold it into `other_sources`; `compute_tax.ps1` adds it
  to slab income as its own line so the Schedule OS totals stay clean.
- For a Zerodha-style broker tax-P&L, aggregate the heads deterministically with
  [../scripts/schedules/schedule_cg.ps1](../scripts/schedules/schedule_cg.ps1): export the "Tradewise
  Exits" sheet to CSV, then `schedule_cg.ps1 -Path <csv> -OutDir out` writes per-head
  consideration/cost/expenditure (STT excluded) and the 234C quarterly split. Cross-check its totals
  against the broker's own head-wise summary.

**Foreign holdings** (stocks / ESPP / RSU / foreign dividends / Schedule FA / FTC): if the taxpayer has
any, load [09-foreign-assets.md](./09-foreign-assets.md) and follow it. If none, skip it.
