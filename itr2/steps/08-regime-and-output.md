# Step 8 — Regime comparison & output

Populate a single **`tax_input.json`** (salary, other sources, house property, special-rate gains,
deductions, taxes paid — schema in [../references/output-template.md](../references/output-template.md))
as the one source of truth, then run the pipeline:

## Coverage check before running (source ↔ field)
Before running the scripts, confirm `tax_input.json` is complete in **both** directions against the
sources confirmed in Step 1:
- **Every confirmed source → a field:** each document contributes at least one value (nothing dropped —
  e.g. the bank certificate's FD interest actually landed in `other_sources.fd_interest`).
- **Every field → a source:** each populated figure traces back to a named document (nothing invented;
  no estimate unless flagged). Watch the recurring traps: a salary figure in the wrong slot (HRA/prof-tax
  belong in `salary_*`, **not** `deductions_old`), and internal totals that must tie
  (`slab_rate_gains` = Σ gains in `capital_gains_manual`; `taxes_paid.tds` = 26AS/Form-16 total).

Then run the pipeline:

- [../scripts/compute_tax.ps1](../scripts/compute_tax.ps1) `-InputJson tax_input.json -OutDir out` computes
  tax under **both** regimes (slabs, special-rate 111A/112A/112, surcharge with the 15% cap on
  special-rate gains, cess, 87A rebate, standard deduction), recommends the lower, and writes
  `tax_regime_comparison.csv`. **Do the tax math with this, not by hand.**
- Per-schedule emitters in [../scripts/schedules/](../scripts/schedules/) each read the same JSON and
  write one CSV: `schedule_s.ps1` (Salary), `schedule_hp.ps1` (House Property), `schedule_os.ps1` (Other
  Sources, reconcile to AIS), `schedule_via.ps1` (Deductions — flags OLD-only items void under NEW),
  `schedule_cg.ps1` (capital gains), `schedule_112a.ps1` (112A CSV). Each self-skips when its input is absent.
- [../scripts/build_return.ps1](../scripts/build_return.ps1) `-InputJson tax_input.json -OutDir out
  [-TradewiseCsv ...]` orchestrates all of the above (auto-picking the recommended regime) and stitches
  every section CSV into one **`ITR2_data_entry.md`**.

Also give the user a **schedule tick-list** for the utility's "Select Schedule" step — see
[schedule-selection.md](./schedule-selection.md).

Notes:
- **The employer's regime choice doesn't bind the return** — Form 16 may deduct TDS under old regime
  (opted out of 115BAC), but always recompute both regimes fresh and pick the lower for the filing.
- 80TTA (non-senior, ₹10k) vs 80TTB (senior, ₹50k) for interest.
