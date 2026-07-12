# Output templates

Produce two artifacts for the user (mirror any existing project convention first).

## 1. Data-entry sheet (Markdown)
A schedule-by-schedule sheet showing each figure and how it was derived, with caveats. Sections:

- **Header**: taxpayer, PAN, DOB/age (senior?), form, residential status, regime chosen, bottom line
  (total tax / TDS / refund-or-payable).
- **Part A — General**: AY, section (139(1)), regime opt-out, foreign-asset flag, ITR-form note.
- **Schedule S** (salary/pension): gross, exemptions, standard deduction, chargeable.
- **Schedule CG**: STCG 111A, STCG slab, LTCG 112A (gross and taxable-after-1.25L), total CG.
- **Schedule OS**: dividends, interest — reconciled to AIS.
- **Deductions**: 80C/80D/80TTA/80TTB as applicable (regime-dependent).
- **Regime comparison table**: OLD vs NEW, line by line, with the recommendation.
- **Taxes paid / payable**: TDS, advance tax, self-assessment tax, 234B/234C note.
- **Pre-filing checklist**: pay SA tax, reconcile AIS, quarterly breakup, proofs, e-verify.

Mark any USD/forex or estimated items clearly (e.g. `§`) so they can be refreshed.

## 2. Machine-readable input (JSON)
A compact `tax_input.json` with the computed values, e.g.:
```json
{
  "taxpayer": "", "pan": "", "dob": "", "senior_citizen": false,
  "ay": "2026-27", "regime": "new",
  "salary_or_pension_gross": 0,
  "other_sources": { "dividend": 0, "bank_interest": 0 },
  "capital_gains": {
    "stcg_equity_111a": 0, "stcg_slab": 0,
    "ltcg_equity_112a": 0, "ltcg_112a_pre_rate_change": 0
  },
  "deductions": {},
  "taxes_paid": { "tds": 0, "advance_tax": 0, "self_assessment_tax": 0 },
  "notes": {}
}
```

## Tax calc reference (AY 2026-27)
- **New regime slabs**: 0–4L nil; 4–8L 5%; 8–12L 10%; 12–16L 15%; 16–20L 20%; 20–24L 25%; >24L 30%.
  Standard deduction ₹75,000. 87A rebate up to ₹12L total income (excludes special-rate income).
- **Old regime slabs**: 0–2.5L nil (senior 0–3L); 2.5/3–5L 5%; 5–10L 20%; >10L 30%.
  Standard deduction ₹50,000.
- **Special rates** (both regimes): STCG 111A 20%; LTCG 112A 12.5% over ₹1.25L.
- **Surcharge**: 10% >₹50L, 15% >₹1Cr, 25% >₹2Cr (capped at 15% for 111A/112A gains).
- **Cess**: 4% health & education on tax+surcharge.
- Confirm current-year slabs against the utility before finalising — rates change yearly.
