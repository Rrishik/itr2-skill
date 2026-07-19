---
name: itr2
description: 'Compute Indian ITR-2 capital gains and other-source income from broker/AIS documents and map them into the Income-Tax offline utility. USE WHEN: user is filing an Indian income-tax return (ITR-2/AY), has capital gains from stocks or mutual funds, needs STCG/LTCG/OS figures computed, needs a Schedule 112A CSV built for upload, asks where to enter values in the ITR utility, wants to reconcile broker statements against AIS/TIS, or holds foreign stocks/ESPP/RSU/foreign dividends needing Schedule FA and FTC. Handles Groww/Zerodha/broker capital-gains reports, Form 16, AIS, TIS, dividend reports, bank interest certificates, and foreign broker/ESPP statements. DO NOT USE FOR: business/professional income (needs ITR-3), non-Indian tax returns, or GST.'
argument-hint: 'Point to the folder containing the tax documents'
---

# ITR-2 Capital Gains & Income Computation

Compute capital gains (STCG/LTCG), other-source income, and produce the Schedule 112A CSV for India's
ITR-2, then tell the user exactly where each value goes in the offline utility.

## When to Use
- Filing an Indian ITR-2 with capital gains from listed shares and/or mutual funds.
- Building an uploadable Schedule 112A CSV.
- Reconciling broker statements against AIS/TIS.
- Deciding OLD vs NEW regime.

## How this skill is organised
Each step below is a short instruction here plus a detailed file under [steps/](./steps/). **Load a
step's file only when you reach it** (progressive disclosure) — and skip steps that don't apply to this
taxpayer (e.g. no 112A LTCG → skip Step 5; no foreign assets → skip Step 9). Shared lookup tables live in
[references/](./references/); deterministic computation lives in [scripts/](./scripts/).

## Entry routing
Users often arrive mid-flow. Match the request and jump straight to that step (still capture the shared
work context first — see below); walk the full 1→8 spine only for an open-ended "help me file".

| User intent | Go to |
|---|---|
| "Which ITR form do I file?", intraday/F&O question | Step 2 |
| "Read/open this broker file", password-protected PDF | Step 3 |
| "Compute/classify my capital gains", STCG/LTCG buckets | Step 4 |
| "Build my 112A CSV", upload rejected | Step 5 |
| "Reconcile against AIS/TIS" | Step 6 |
| "Quarterly / 234C breakup" | Step 7 |
| "Compare OLD vs NEW regime", "compute my tax", final sheet | Step 8 |
| Foreign stocks / ESPP / RSU / foreign dividend / Schedule FA / FTC | Step 9 |
| "Which schedules do I tick?" | [steps/schedule-selection.md](./steps/schedule-selection.md) |

## Steps
1. **Collect documents** — gather broker/AIS/salary/foreign docs; clarify residency, age, regime.
   Load [steps/01-collect-docs.md](./steps/01-collect-docs.md). Always ask about foreign holdings.
2. **Select the ITR form** — confirm ITR-2 fits (intraday/F&O → ITR-3, out of scope).
   Load [steps/02-select-itr-form.md](./steps/02-select-itr-form.md).
3. **Read the documents** — xlsx magic bytes, `read_xlsx.ps1`, PDF passwords.
   Load [steps/03-read-documents.md](./steps/03-read-documents.md).
4. **Compute & bucket the gains** — classify each gain into 111A / slab / 112A / 112; run `schedule_cg.ps1`.
   Load [steps/04-compute-bucket-cg.md](./steps/04-compute-bucket-cg.md).
5. **Build the Schedule 112A CSV** — only if there is listed-equity LTCG. `schedule_112a.ps1`.
   Load [steps/05-schedule-112a.md](./steps/05-schedule-112a.md).
6. **Reconcile against AIS** — report the AIS figure for rounding-size differences.
   Load [steps/06-reconcile-ais.md](./steps/06-reconcile-ais.md).
7. **Quarterly breakup (234C)** — split each head by sale-quarter; net losses forward.
   Load [steps/07-quarterly-234c.md](./steps/07-quarterly-234c.md).
8. **Regime comparison & output** — fill `tax_input.json`; run `build_return.ps1`; produce the tick-list.
   Load [steps/08-regime-and-output.md](./steps/08-regime-and-output.md).

Conditional:
- **Foreign assets** (stocks / ESPP / RSU / foreign dividends / Schedule FA / FTC): if any, load
  [steps/09-foreign-assets.md](./steps/09-foreign-assets.md).
- **Schedule tick-list** for the utility's "Select Schedule" step:
  [steps/schedule-selection.md](./steps/schedule-selection.md).

## Pipeline at a glance
`tax_input.json` is the single source of truth. [scripts/build_return.ps1](./scripts/build_return.ps1)
runs `compute_tax.ps1` + every `schedules/schedule_*.ps1` (each self-skips when its input is absent) and
stitches the section CSVs into one `ITR2_data_entry.md`. See
[references/output-template.md](./references/output-template.md) for deliverable shapes.

## Session state (survive long sessions / compaction)
Keep two files in the working folder as the durable context, so a jump to any step or a resumed session
stays consistent:
- **`tax_input.json`** — the numeric inputs (schema in output-template.md).
- **`work-context.json`** — the filing decisions: taxpayer/PAN, AY, **residential status**, senior-citizen
  flag, **chosen ITR form + why**, **chosen regime + why**, foreign-assets yes/no, which schedules apply,
  AIS-reconciliation status, any logged FX rates, and the current step. Write it early (Step 1–2) and
  update it as decisions are made; re-read it before resuming or jumping mid-flow.

## Extending to other ITR forms
This skill is ITR-2-specific but built to generalise. When adding a sibling (e.g. `itr3` for
business/F&O income), reuse rather than fork:
- **Reusable as-is:** `scripts/read_xlsx.ps1`, `scripts/compute_tax.ps1` (slabs/surcharge/regime are
  form-independent), `scripts/schedules/schedule_{s,hp,os,via,cg,112a}.ps1`, `build_return.ps1`, the
  `references/` lookup tables, and steps 1, 3, 6, 7, 8, 9 + `schedule-selection.md` (largely form-agnostic).
- **Form-specific:** the `description`/`name` frontmatter, Step 2 (form selection), and any new schedules
  (e.g. Schedule BP for business income). Add those as new `steps/` files and new `schedules/*.ps1`.
- Keep the same contract: one orchestrator SKILL.md → on-demand `steps/*.md` → shared `scripts/` + a
  single `tax_input.json` + `work-context.json`. Promote genuinely shared assets to a common location
  only when a second form actually needs them (avoid speculative abstraction).

## Security & confirmation boundaries

### CAN (do freely)
- Read the user's tax documents, compute figures, run the scripts, and produce the data-entry sheet and CSVs.
- Recommend a regime/form and explain the reasoning.

### CANNOT (never do)
- **File, submit, or e-verify** the return, or log into the income-tax portal on the user's behalf.
- Invent missing figures, rates, or FX values — if a source is missing, say so and stop at that line.
- Treat computed numbers as final without AIS/TIS reconciliation (Step 6).
- Give definitive legal/tax advice — present computations and cite the rule; the filing decision is the user's.

### MUST CONFIRM (pause and ask)
- Any figure that is **estimated** (e.g. an FX rate proxy, a back-derived cost basis) — flag it clearly.
- Choosing a form that a disqualifier forces unexpectedly (e.g. intraday → ITR-3, out of scope here).
- Overriding the script-recommended regime, or entering net gain instead of aggregate consideration/cost.
- Any action that writes outside the working folder.
