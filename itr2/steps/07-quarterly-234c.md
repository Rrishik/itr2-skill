# Step 7 — Quarterly breakup (Section F / OS 234C grid)

Gains and dividends must be split by the quarter the **sale/credit** occurred, for 234C interest.
FY quarters: ≤15-Jun, 16-Jun–15-Sep, 16-Sep–15-Dec, 16-Dec–15-Mar, 16-Mar–31-Mar.

The utility rejects negatives — net a loss-quarter into a later positive quarter so each row still
sums to the annual total. Full grid layout (the 5 periods × 7 CG rows and the netting rule) is in
[../references/schedule-mapping.md](../references/schedule-mapping.md#quarterly-breakup--schedule-cg-section-f-and-os-234c-grid).

Section F has one row per **tax rate**, so map each computed head to its row before entering the quarters:
| Our head | Section F row |
|---|---|
| Equity STCG 111A (`stcg_111a`) | **Row 1** — STCG @20% |
| Slab-rate STCG: debt MF / foreign equity <24m / unlisted (`slab_rate_gains`) | **Row 3** — STCG at applicable rate |
| LTCG 112A (equity) + LTCG 112 (SGB/bonds/foreign) | **Row 5** — LTCG @12.5% |
| DTAA-relief STCG / LTCG | Rows 4 / 6 (only if claiming treaty relief) |
| VDA (crypto) | **Row 7** — @30% |

`schedule_cg.ps1 -OutDir out` already emits the `capital_gains_234c` section (per head × quarter) from the
tradewise CSV — use it as the starting point, drop each head into its Section F row above, and apply the
loss-netting rule for any negative quarter.
