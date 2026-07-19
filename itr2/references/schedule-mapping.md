# Schedule CG / OS — where each value goes in the ITR-2 offline utility

## Short-Term Capital Gains (Schedule CG → Section A)
| Item | Use for | Key input fields |
|---|---|---|
| **A2. Equity/equity-MF, STT paid — 111A [for others]** | Listed shares + equity MF sold with STT | 2a Full value of consideration (aggregate sale); 2bi Cost of acquisition (aggregate cost); 2bii improvement=0; 2biii expenditure (deductible charges); 2d loss disallowed u/s 94(7)/(8) |
| **A5. Assets other than A1–A4** | Debt MF (specified/unspecified), unlisted, **foreign shares held ≤24m** | i.a/i.b (unquoted shares) = 0; ii Full value of consideration; bi Cost of acquisition; balance auto |
| A6 Amount deemed STCG | rare | 0 |
| A7 Pass-through (PTI) | only if PTI slips | 0 |
| A8 DTAA / A(A) buyback | NR / buyback only | 0 |

- Enter **aggregate sale and cost**, not net gain. Utility computes balance = sale − (cost + expenditure).
- **Specified debt MF** (bought on/after 1-Apr-2023): always slab rate regardless of holding → item 5.
- **Expenditure field (biii)** = only **sell-side** transfer charges (brokerage, exchange txn, SEBI,
  IGST/GST, stamp duty, IPFT on the *sell* leg). **Buy-side** charges instead add to **cost of
  acquisition (bi)**. **STT is never entered** anywhere. These charges are usually a few rupees — enter
  them for exactness but they rarely move the tax. The broker tax-P&L lists each charge per trade.
- **One block per head:** Section A5 (and each LTCG item) has a single consideration/cost block, so
  **sum all sources in that head** into one entry (e.g. debt-MF + foreign-share STCG both go into A5).

## Long-Term Capital Gains (Schedule CG → Section B)
| Item | Use for |
|---|---|
| **B2. Listed securities/ZCB u/s 112(1)** | listed bonds, **SGB sold on the exchange**, ZCB, GDR — non-STT; NOT ordinary equity |
| **B3. Equity/equity-MF, STT paid — 112A** | all listed equity + equity MF LTCG (opens Schedule 112A) |
| **B8. Assets where B1–B7 N/A** | other LTCG incl. **foreign shares held >24 months** (no STT) |
| B9/B10/B11 | deemed / PTI / DTAA — usually 0 |

- ₹1.25L (post-FY24) LTCG exemption under 112A is applied by the utility at tax computation — do
  NOT subtract it in the CG grid; enter gross LTCG.
- **SGB (Sovereign Gold Bond):** a **secondary-market sale on the exchange** → B2 (s.112, 12.5%, no
  indexation, no ₹1.25L exemption). But **held to maturity (8 yr)** or **premature redemption to RBI
  (after 5 yr)** → the gain is **fully exempt** → report in the **Exempt Income (EI)** schedule, not CG.

## Rate reference (post 23-Jul-2024)
| Head | Rate |
|---|---|
| STCG 111A | 20% |
| LTCG 112A | 12.5% on amount over ₹1.25L |
| STCG slab / debt MF | slab |

If any disposal occurred **before 23-Jul-2024**, split into pre/post buckets (old rates: 111A 15%,
112A 10% over ₹1L).

## Schedule OS (Other Sources)
| Field | Value |
|---|---|
| 1a Dividend income | total dividends (reconcile to AIS) |
| 1b / interest | savings-bank + FD/term-deposit interest |
| Quarterly breakup grid | split dividends by credit-date quarter (234C) |

## Foreign stocks / ESPP / RSU / foreign dividends
- **Sale of foreign shares** = capital gains but NOT 111A/112A (no STT). Holding >24 months → LTCG u/s
  112(1) at 12.5% (no ₹1.25L exemption, no grandfathering) → LTCG **item B8** ("assets where B1–B7 N/A").
  ≤24 months → STCG at slab → STCG **item A5**. Convert cost/sale using SBI TT buying rate on the relevant dates.
  - **Holding period runs from the vest date, not the grant/award date.** Confirm the exact acquisition
    date and per-lot cost basis from the broker's **closed-lots / gain-loss report**; a lot near the
    24-month boundary can flip STCG↔LTCG. The broker's US **LONG/SHORT** tag is a US >12-month concept
    and does not map to India's 24-month test — ignore it.
- **Currency conversion (Rule 115 / 128):** transaction date for a sale/purchase; **last day of the month
  preceding** receipt (income, Rule 115) or deduction (foreign tax, Rule 128); holiday → preceding working
  day. Use the **SBI TT buying rate**; SBI doesn't publish historical TTBR openly, so the **RBI
  reference-rate archive** is the standard citable proxy (RBI mid ≈ 0.5–1% above TTBR). Log each rate+date.
- **ESPP discount / RSU vesting** = salary perquisite. If via an Indian employer it's usually in
  Form 16/12BA; a foreign employer often omits it — add to salary manually. That perquisite value
  becomes the cost basis for the later sale.
- **Foreign dividends** → Schedule OS at slab (gross, before foreign withholding). Foreign tax withheld
  → claim **FTC** in Schedule TR/FSI; **Form 67 must be filed before the return**. FTC = lower of Indian
  tax on that income and foreign tax paid, capped at the **DTAA treaty rate**. **India–US DTAA Art. 10(2):**
  dividend treaty rate is **15% only for a *company* owning ≥10% voting stock; 25% in all other cases** —
  so for an individual/portfolio investor 25% is the treaty rate and fully creditable (a valid W-8BEN
  still gives 25%; nothing to reclaim as "excess"). 1042-S is by US **calendar year**, but India taxes by
  **FY receipt date** — Jan–Mar dividends belong to the Indian FY even before that year's 1042-S issues.
- **Schedule FA** — mandatory for Resident & Ordinarily Resident holding any foreign asset at any time in
  the **calendar** year (shares, ESPP/RSU incl. unvested, foreign accounts), even if unsold and even if
  income is nil. Report in the appropriate table (A3 foreign equity/debt, etc.).
- **Schedule FSI / TR** — report foreign-source income and the corresponding tax relief claimed.

## Deductions
| Section | Who | Cap |
|---|---|---|
| 80TTA | non-senior | ₹10,000 savings interest |
| 80TTB | senior (≥60) | ₹50,000 interest (savings+FD) |
| 80C / 80D | old regime only | as applicable |

New regime: none of the above except employer NPS 80CCD(2); standard deduction ₹75,000 vs ₹50,000 old.

## Set-off (Schedule CGL / Section E)
Broker reports usually net losing lots within each head already. Only residual **net losses** per head
flow into the set-off grid. If every head is net positive, nothing to set off.

## Quarterly breakup — Schedule CG Section F (and OS 234C grid)
The utility makes you split each capital-gains head across the **five 234C periods** by the date the
**sale/transfer** happened (dividends split by credit date in the OS grid).

| Col | Period (dates of sale/transfer) |
|---|---|
| **1 (Q1)** | Upto 15-Jun |
| **2 (Q2)** | 16-Jun to 15-Sep |
| **3 (Q3)** | 16-Sep to 15-Dec |
| **4 (Q4)** | 16-Dec to 15-Mar |
| **5 (Q5)** | 16-Mar to 31-Mar |

Section F rows (the utility labels each "Enter value from item 3… of schedule BFLA"). Fill only the rows
that have gains, and map each of **our computed heads** to its row:

| Row | Utility label | Which of our heads goes here |
|---|---|---|
| 1 | STCG taxable @ **20%** (from 3iii BFLA) | Equity STCG 111A (`stcg_111a` / CG head A2) |
| 2 | STCG taxable @ **30%** (from 3iv) | usually **0** (e.g. non-resident unlisted); leave blank if none |
| 3 | STCG taxable at **applicable/slab rate** (from 3v) | slab-rate STCG: debt MF (s.50AA), foreign equity <24m, unlisted — i.e. `slab_rate_gains` / `capital_gains_manual` (CG head A5) |
| 4 | STCG at **DTAA** rates (from 3vi) | only if claiming treaty relief on STCG; else 0 |
| 5 | LTCG taxable @ **12.5%** (from 3vii) | LTCG 112A (`ltcg_112a`, equity over ₹1.25L) **and** LTCG 112 (`ltcg_112`: SGB/bonds/foreign) — both are 12.5% now |
| 6 | LTCG at **DTAA** rates (from 3viii) | only if claiming treaty relief on LTCG; else 0 |
| 7 | VDA (crypto) @ **30%** (from item 16 of SI) | virtual digital assets, if any; else 0 |

To fill a row, take that head's per-quarter figures from `capital_gains_234c` (our `schedule_cg.ps1`
output groups by head × quarter) and enter them across columns 1–5. Example from our output — Equity STCG
111A ₹1,650 all in Q2 → **Row 1**: col 2 = 1650, rest 0. Debt-MF + foreign STCG (slab) → **Row 3**, split
by their quarters. SGB LTCG ₹34,972 in Q3 → **Row 5**: col 3 = 34972.

- Each row **must sum to that head's annual gain** in Schedule CG, else the utility errors.
- The grid **rejects negatives**: if a quarter is a net loss, net it into a later positive quarter so the
  quarter stays ≥0 and the row total still matches. (Only the annual figure is taxed; the quarterly split
  only drives 234C interest.)
- If a head's annual result is a net loss, leave its Section F row blank (nothing to allocate).

Worked example (LTCG 112A total ₹8,00,000): Q1 ₹5,00,000 + Q3 ₹3,00,000, others 0 → sums to total. ✓

## ITR form selection
Pick the form from the taxpayer's full income mix — the presence of a single disqualifier can force a
higher form. Decide in this order:

1. **Business/professional income** — regular trading, F&O, or **intraday equity (speculative)**, or
   professional receipts → **ITR-3** (or ITR-4 if opting for presumptive 44AD/ADA and eligible).
   Intraday/F&O cannot be crammed into ITR-2; do not silently omit unless the user explicitly accepts
   the limitation.
2. **Capital gains or foreign assets** (and no business income) → **ITR-2**. Any STCG, any LTCG above the
   ITR-1 cap, holding foreign shares/ESPP/RSU, or being a company director/unlisted-shareholder all force ITR-2.
3. **Simple case** — resident, total income ≤₹50L, only salary/pension, one house property, other sources,
   and **LTCG u/s 112A ≤₹1.25L with no other capital gains** → **ITR-1 (Sahaj)** is allowed.

| Form | Fits | Hard blocks |
|---|---|---|
| ITR-1 Sahaj | Resident ≤₹50L; salary/1 house/OS; LTCG 112A ≤₹1.25L only | Any STCG; LTCG >₹1.25L or non-112A; foreign assets; director; >1 house; business |
| ITR-2 | Salary/pension + all capital gains + OS + foreign assets | Any business/professional income |
| ITR-3 | ITR-2 income **+** business/professional, incl. intraday/F&O | — |
| ITR-4 Sugam | Presumptive business 44AD/ADA/AE; resident ≤₹50L | Capital gains (except LTCG 112A ≤₹1.25L); foreign assets; >1 house |

State the chosen form **and the reason** to the user, and warn when a disqualifier (typically intraday)
pushes them to a form they didn't anticipate.

## Which schedules to select in the utility
After picking ITR-2, the utility's **"Select Schedule"** step pre-ticks the mandatory ones and lets you
add/remove optional ones. Produce a tick-list mapped to the taxpayer's actual income. Rules of thumb:

| Schedule | Select when |
|---|---|
| Part A-Gen, Part B-TI, Part B-TTI, Tax-Paid (TP) | always (mandatory) |
| CYLA, BFLA, CFL, AMTC | always (mandatory, even if nil) |
| Schedule Salary (S) | any salary/pension (incl. RSU/ESPP perquisite) |
| Schedule House Property (HP) | only if house-property income/loss — else untick |
| Schedule Capital Gains (CG) | any capital gain/loss |
| **Schedule 112A** | **only if listed equity/equity-MF LTCG with STT** — untick if there's none, even when CG is used |
| Schedule 115AD | non-residents only |
| Schedule Other Sources (OS) | dividends/interest/other income |
| Schedule SI | any special-rate income (111A, 112, 112A, DTAA-rate gains) |
| **Schedule FSI + Schedule TR** | **whenever foreign income + FTC is claimed** — both needed or the FTC won't flow (easy to miss; not auto-ticked) |
| Schedule FA | Resident & Ordinarily Resident holding any foreign asset in the calendar year |
| Schedule 80D / VI-A / other 80-x | **OLD regime only**; under NEW only 80CCD(2) employer-NPS survives — untick the rest |
| **Schedule ESOP** | **only** tax *deferred* on ESOPs from an **eligible start-up (s.80-IAC)** — not ordinary MNC RSUs; untick otherwise |
| Schedule AL | only if **total income > ₹1 Cr** |
| Schedule AMT | only if s.115JC AMT applies (certain deductions) |
| VDA / SPI / PTI / EI / 5A | crypto / clubbed income / pass-through / exempt income / Portuguese-Civil-Code spouse — only if applicable |

Common misses: **FSI + TR** unticked while claiming FTC; **112A** left ticked with no 112A income;
**ESOP** ticked for ordinary RSUs; **80D/VI-A** ticked under the NEW regime where they don't apply.

