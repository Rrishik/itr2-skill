# Step 7 — Quarterly breakup (Section F / OS 234C grid)

Gains and dividends must be split by the quarter the **sale/credit** occurred, for 234C interest.
FY quarters: ≤15-Jun, 16-Jun–15-Sep, 16-Sep–15-Dec, 16-Dec–15-Mar, 16-Mar–31-Mar.

The utility rejects negatives — net a loss-quarter into a later positive quarter so each row still
sums to the annual total. Full grid layout (the 5 periods × 6 CG rows and the netting rule) is in
[../references/schedule-mapping.md](../references/schedule-mapping.md#quarterly-breakup--schedule-cg-section-f-and-os-234c-grid).

`schedule_cg.ps1 -OutDir out` already emits `cg_234c_split.csv` (per head × quarter) from the tradewise
CSV — use it as the starting point and apply the loss-netting rule for any negative quarter.
