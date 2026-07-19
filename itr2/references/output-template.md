# Output templates

The deliverables are driven by a single **`tax_input.json`** (one source of truth) and the scripts:
`compute_tax.ps1` + the per-schedule emitters in `scripts/schedules/` each merge a section into a single
**`return.json`**, and `build_return.ps1` renders that into the combined `ITR2_data_entry.md`. Mirror any
existing project convention first.

Keep inputs and outputs in separate folders in the working folder: **`sources/`** for every input (raw
documents and anything derived from them, incl. `tax_input.json` and a broker sheet exported to CSV), and
**`skill_output/`** for the regenerable outputs (`return.json`, `ITR2_data_entry.md`, `Schedule112A.csv`).
The pieces:

- **`tax_input.json`** — the machine-readable input (schema below).
- **`return.json`** — the single structured output. Each emitter writes one section key: `tax_computation`,
  `recommended_regime`, `salary`, `house_property`, `other_sources`, `deductions`, `capital_gains_head`,
  `capital_gains_234c`, plus `meta`. Section rows carry a **`Where`** column naming the exact utility field
  the value goes into (e.g. `Schedule S: 4(a) standard deduction u/s 16(ia)`, `Schedule CG A2 (STCG 111A)`),
  so the user knows precisely which box to populate.
- **`ITR2_data_entry.md`** — the combined data-entry sheet (rendered from `return.json`).
- **`Schedule112A.csv`** — the uploadable 112A file, when there's 112A LTCG (`schedules/schedule_112a.ps1`).
  This stays a CSV because the portal requires that exact format.

## 1. Data-entry sheet (Markdown)
A schedule-by-schedule sheet showing each figure and how it was derived, with caveats. Sections:

- **Header**: taxpayer, PAN, DOB/age (senior?), form, residential status, regime chosen, bottom line
  (total tax / TDS / refund-or-payable).
- **Part A — General**: AY, section (139(1)), regime opt-out, foreign-asset flag, ITR-form note.
- **Schedule selection tick-list**: which schedules to add/remove in the utility's "Select Schedule"
  step for this income mix (see [schedule-mapping.md](./schedule-mapping.md#which-schedules-to-select-in-the-utility)).
- **Schedule S** (salary/pension): gross, exemptions, standard deduction, chargeable.
- **Schedule CG**: STCG 111A, STCG slab, LTCG 112A (gross and taxable-after-1.25L), total CG.
- **Schedule CG Section F** (234C quarterly grid): the `capital_gains_234c` rows are also rendered as the
  utility's grid — one row per Section F rate-row, columns Q1–Q5 — so the sheet mirrors the input screen:

  | Section F row | Q1 (≤15-Jun) | Q2 (16-Jun–15-Sep) | Q3 (16-Sep–15-Dec) | Q4 (16-Dec–15-Mar) | Q5 (16-Mar–31-Mar) | Total |
  |---|---|---|---|---|---|---|
  | Row 1 (STCG @20%, 111A) | 0 | … | 0 | 0 | 0 | = annual 111A gain |
  | Row 3 (STCG applicable rate) | … | … | … | … | … | = annual slab CG |
  | Row 5 (LTCG @12.5%) | … | … | … | … | … | = annual 112A+112 |

  Only rows with gains appear. Each row must sum to that head's annual gain; the utility rejects negatives
  (net a loss-quarter into a later positive one). Full row→rate map in
  [schedule-mapping.md](./schedule-mapping.md#quarterly-breakup--schedule-cg-section-f-and-os-234c-grid).
- **Schedule OS**: dividends, interest — reconciled to AIS.
- **Deductions**: 80C/80D/80TTA/80TTB as applicable (regime-dependent).
- **Regime comparison table**: OLD vs NEW, line by line, with the recommendation.
- **Taxes paid / payable**: TDS, advance tax, self-assessment tax, 234B/234C note.
- **Pre-filing checklist**: pay SA tax, reconcile AIS, quarterly breakup, proofs, e-verify.

Mark any USD/forex or estimated items clearly (e.g. `§`) so they can be refreshed.

**Format for each CG sub-head:** show the source detail table, then a plain **field → value** table of
the exact utility inputs under that section header — nothing more. Do **not** add "where exactly in the
utility" prose or item codes. Enter aggregate consideration/cost (never the net gain); the utility
computes the balance. Example:

```
### STCG at slab — assets other than A1–A4
| Source | Sale date | Consideration ₹ | Cost ₹ | Gain ₹ |
| ...detail rows... |

| Field | Value |
|---|---|
| Full value of consideration | 9,85,928 |
| Cost of acquisition | 7,61,576 |
| Cost of improvement | 0 |
| Expenditure w&e in connection with transfer | 0 |
```

## 2. Machine-readable input (JSON)
`tax_input.json` is the single input consumed by `compute_tax.ps1`, the per-schedule emitters, and
`build_return.ps1`. All amounts in INR; omit what doesn't apply:
```json
{
  "taxpayer": "", "pan": "", "ay": "2026-27", "senior_citizen": false,
  "salary_gross": 0,
  "salary_hra_exemption": 0, "salary_professional_tax": 0,
  "other_sources": { "dividend": 0, "savings_interest": 0, "fd_interest": 0 },
  "house_property": 0,
  "slab_rate_gains": 0,
  "special_rate_gains": { "stcg_111a": 0, "ltcg_112a": 0, "ltcg_112": 0 },
  "deduction_80ccd2": 0,
  "deductions_old": { "80c": 0, "80d": 0, "80tta_ttb": 0, "other": 0 },
  "taxes_paid": { "tds": 0, "advance_tax": 0, "self_assessment_tax": 0, "ftc": 0 }
}
```
- `special_rate_gains` come from `schedules/schedule_cg.ps1` (STT already excluded): 111a=listed-equity STCG,
  112a=listed-equity LTCG (gross, before the ₹1.25L exemption the script applies), 112=bonds/SGB/foreign LTCG.
- `slab_rate_gains` = capital gains taxed at slab rate, not a special rate: specified debt MFs (s.50AA),
  foreign equity held <24m, unlisted-share STCG. They add to slab income (never to `other_sources`).
- `capital_gains_manual` (optional) — CG heads **not** in a broker tradewise CSV (debt MF, foreign
  equity, unlisted). `schedule_cg.ps1` appends each to the Schedule CG table. Each entry:
  `{ "head": "...", "consideration": N, "cost": N, "expenditure": N (opt), "where": "Schedule CG A5 (STCG slab)", "quarter": "Q2 (16-Jun..15-Sep)" (opt) }`.
  This makes the CG grid complete; the tax itself still comes from `slab_rate_gains`/`special_rate_gains`.
- `deduction_80ccd2` (employer NPS) is allowed under **both** regimes; everything in `deductions_old`
  is OLD-regime only.
- `salary_hra_exemption` (s.10(13A)) and `salary_professional_tax` (s.16(iii)) reduce **salary** under the
  **OLD regime only** — put them here, NOT in `deductions_old` (they are salary deductions, not Chapter VI-A).

## Tax calc reference (AY 2026-27)
- **New regime slabs**: 0–4L nil; 4–8L 5%; 8–12L 10%; 12–16L 15%; 16–20L 20%; 20–24L 25%; >24L 30%.
  Standard deduction ₹75,000. 87A rebate up to ₹12L total income (excludes special-rate income).
- **Old regime slabs**: 0–2.5L nil (senior 0–3L); 2.5/3–5L 5%; 5–10L 20%; >10L 30%.
  Standard deduction ₹50,000.
- **Special rates** (both regimes): STCG 111A 20%; LTCG 112A 12.5% over ₹1.25L.
- **Surcharge**: 10% >₹50L, 15% >₹1Cr, 25% >₹2Cr (capped at 15% for 111A/112A gains).
- **Cess**: 4% health & education on tax+surcharge.
- Confirm current-year slabs against the utility before finalising — rates change yearly.
