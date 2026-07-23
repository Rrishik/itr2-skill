---
name: itr
description: 'Umbrella entry point for filing an Indian income-tax return (ITR). USE WHEN: the user wants to file an Indian ITR but the correct form is not yet decided, asks "which ITR form do I need", or starts open-ended tax-filing work spanning salary, capital gains, business/F&O, or foreign income. Routes to the right form-specific skill: itr2 (capital gains + other sources + foreign assets, no business income). DO NOT USE FOR: non-Indian tax returns or GST. Once the form is known, defer to that form''s skill.'
argument-hint: 'Describe the income mix, or point to the folder with tax documents'
---

# India ITR — form router

Thin orchestrator for Indian income-tax filing. Decide which ITR form fits the taxpayer's income mix,
then hand off to the form-specific skill. **Keep this skill thin:** classify the income, route, and
preserve the shared work context across the hand-off. The form skills own all computation detail — do
not duplicate schedule rules, scripts, or utility mappings here.

## Form routing

Ask about the income mix (salary/pension, capital gains, house property, other sources, business/
professional or **intraday/F&O**, foreign assets), then route:

| Income mix | Form | Skill | Status |
|---|---|---|---|
| Salary/pension + capital gains + other sources + foreign assets; **no business income** | **ITR-2** | **itr2** | available |
| Any of the above **plus** business/professional income, incl. **intraday (speculative)** or **F&O** | ITR-3 | itr3 | not yet built — flag as out of scope |
| Presumptive business (44AD/ADA/AE), resident ≤₹50L, no capital gains beyond 112A ≤₹1.25L | ITR-4 | itr4 | not yet built |
| Resident ≤₹50L, only salary/one house/other sources, LTCG 112A ≤₹1.25L, no STCG/foreign | ITR-1 | itr1 | not yet built |

Decision order: **business / F&O / intraday → ITR-3** (route to `itr3` when it exists; until then, state
it's out of scope). Else **capital gains or foreign assets → ITR-2 (`itr2`)**. Else only salary + minor
112A → ITR-1. State the chosen form **and why** before handing off.

Once the form is decided, **invoke the form skill** (e.g. `itr2`) and let it drive the full workflow.
The ITR-2 skill must begin by confirming its applicable source-document checklist before calculating or assembling figures.

## Shared work context

Pass the chosen form, reason, AY, residential status, senior-citizen flag, and income-mix findings to
the form skill. The ITR-2 assembler persists reviewed filing figures in its immutable
`tax_input.json`; do not create a second source of truth.

## Security & confirmation boundaries

### CAN
- Ask about the income mix, decide the form, and route to the form skill.
- Explain why a form fits or is disqualified.

### CANNOT
- File, submit, or e-verify a return, or log into the income-tax portal.
- Give definitive legal/tax advice — present the rule and let the user decide.
- Perform form-specific computation here — that belongs to the form skill.

### MUST CONFIRM
- Routing to a form the user didn't expect because a disqualifier forces it (e.g. intraday → ITR-3).
- Proceeding when a required form skill (itr3/itr4/itr1) does not yet exist — say so and stop.

## See also
- **itr2** — capital gains + other sources + foreign assets (the built form skill).
