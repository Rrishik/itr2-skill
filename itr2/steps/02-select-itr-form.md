# Step 2 — Decide which ITR form

Before computing anything, confirm the right form for the taxpayer's income mix (full table in
[../references/schedule-mapping.md](../references/schedule-mapping.md#itr-form-selection)):

| Form | Fits when | Blocks / notes |
|---|---|---|
| **ITR-1 (Sahaj)** | Resident, income ≤₹50L, only salary/one house/other sources, **LTCG 112A ≤₹1.25L** | No STCG, no foreign assets, not a company director |
| **ITR-2** | Salary/pension + capital gains + other sources + foreign assets; no business income | **This skill's default.** Any capital gain beyond the ITR-1 112A cap → ITR-2 |
| **ITR-3** | Any of the above **plus** business/professional income — incl. **intraday** (speculative) or **F&O** | Required if intraday/F&O exists; not covered by this skill |
| **ITR-4 (Sugam)** | Presumptive business (44AD/ADA/AE), resident, income ≤₹50L | No capital gains (except LTCG 112A ≤₹1.25L), no foreign assets |

Decision order: **intraday/F&O/business → ITR-3** (stop, out of scope). Else **capital gains present or
foreign assets held → ITR-2**. Else only salary + minor 112A → ITR-1 may suffice. State the chosen form
and *why* to the user, and flag if a disqualifier (e.g. intraday) forces a form they didn't expect.
