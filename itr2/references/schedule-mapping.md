# Schedule CG / OS — where each value goes in the ITR-2 offline utility

## Short-Term Capital Gains (Schedule CG → Section A)
| Item | Use for | Key input fields |
|---|---|---|
| **2. Equity/equity-MF, STT paid — 111A [for others]** | Listed shares + equity MF sold with STT | 2a Full value of consideration (aggregate sale); 2bi Cost of acquisition (aggregate cost); 2bii improvement=0; 2biii expenditure (deductible charges); 2d loss disallowed u/s 94(7)/(8) |
| **5. Assets other than A1–A4** | Debt MF (specified/unspecified), unlisted, other | i.a/i.b (unquoted shares) = 0; ii Full value of consideration; bi Cost of acquisition; balance auto |
| 6 Amount deemed STCG | rare | 0 |
| 7 Pass-through (PTI) | only if PTI slips | 0 |
| 8 DTAA / A(A) buyback | NR / buyback only | 0 |

- Enter **aggregate sale and cost**, not net gain. Utility computes balance = sale − (cost + expenditure).
- **Specified debt MF** (bought on/after 1-Apr-2023): always slab rate regardless of holding → item 5.

## Long-Term Capital Gains (Schedule CG → Section B)
| Item | Use for |
|---|---|
| 2. Listed securities/ZCB u/s 112(1) | bonds/GDR, non-STT — NOT ordinary equity |
| **3. Equity/equity-MF, STT paid — 112A** | all listed equity + equity MF LTCG (opens Schedule 112A) |
| 8 Assets where B1–B7 N/A | other LTCG |
| 9/10/11 | deemed / PTI / DTAA — usually 0 |

- ₹1.25L (post-FY24) LTCG exemption under 112A is applied by the utility at tax computation — do
  NOT subtract it in the CG grid; enter gross LTCG.

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
  112(1) at 12.5% (no ₹1.25L exemption, no grandfathering) → LTCG item 8 ("assets where B1–B7 N/A").
  ≤24 months → STCG at slab → STCG item 5. Convert cost/sale using SBI TT buying rate on the relevant dates.
- **ESPP discount / RSU vesting** = salary perquisite. If via an Indian employer it's usually in
  Form 16/12BA; a foreign employer often omits it — add to salary manually. That perquisite value
  becomes the cost basis for the later sale.
- **Foreign dividends** → Schedule OS at slab (gross, before foreign withholding). Foreign tax withheld
  (e.g. US 25%) → claim **FTC** in Schedule TR/FSI; **Form 67 must be filed before the return**.
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

Rows in Section F (fill only those with gains):
| Row | Head |
|---|---|
| 1 | STCG taxable @15%/20% (111A) |
| 2 | STCG @ DTAA rates |
| 3 | STCG taxable at applicable/slab rate (debt MF, other) |
| 4 | LTCG taxable @10%/12.5% (112A) |
| 5 | LTCG taxable @20% |
| 6 | LTCG @ DTAA rates |

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

