# Step 9 — Foreign stocks / ESPP / RSU / foreign dividends

Load this only when the taxpayer holds or sold foreign assets. Full detail in
[../references/schedule-mapping.md](../references/schedule-mapping.md#foreign-stocks--espp--rsu--foreign-dividends).

- **Sale of foreign shares** = capital gains but **NOT** 111A/112A (no STT). >24 months held → LTCG at
  12.5% (**no ₹1.25L exemption** — that shield is 112A-only; foreign LTCG is **s.112**, LTCG item 8);
  ≤24 months → STCG at slab (STCG item 5). Convert cost/sale using SBI TT buying rate on the relevant dates.
- **Holding period runs from the vest date, not the grant/award date.** Confirm the exact acquisition date
  and per-lot cost from the broker's **closed-lots / gain-loss report** — a lot near the 24-month boundary
  can flip STCG↔LTCG. The broker's US **LONG/SHORT** tag is a US >12-month concept and does **not** map to
  India's 24-month test — ignore it.
- **ESPP/RSU vesting value is a salary perquisite.** If the employer is foreign it's usually missing from
  Form 16 and must be added to salary manually. That perquisite value becomes the cost basis for the sale.
- **Currency conversion (Rule 115/128):** SBI TT buying rate on the relevant date (transaction date for a
  sale/purchase; **last day of the preceding month** for income (Rule 115) / foreign tax (Rule 128));
  holiday → prior working day. SBI doesn't publish historical TTBR openly, so the **RBI reference-rate
  archive** is the standard citable proxy (RBI mid ≈ 0.5–1% above TTBR). Log every rate + date.
- **Foreign dividends** → Schedule OS at slab (gross, before withholding). Foreign tax withheld → claim
  **FTC** in Schedule TR/FSI; **Form 67 must be filed before the return.** FTC = lower of Indian tax on
  that income and foreign tax paid, capped at the DTAA rate. **India–US DTAA Art. 10(2): the dividend
  treaty rate is 25% for individuals** (15% is company-≥10%-voting-stock only), fully creditable.
- **Schedule FA** — mandatory for Resident & Ordinarily Resident holding any foreign asset at any time in
  the **calendar** year (shares, ESPP/RSU incl. unvested, foreign accounts), even if unsold and income nil.
- **Schedule FSI / TR** — report foreign-source income and the tax relief claimed. Both are needed for FTC
  to flow, and are easy to miss (not auto-ticked).
