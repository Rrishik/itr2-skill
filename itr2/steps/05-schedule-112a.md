# Step 5 — Build the Schedule 112A CSV

Only when there is listed-equity / equity-MF **LTCG (112A)**. Otherwise skip.

Use the user's downloaded template header **verbatim** and follow the official column codes.
See [../references/112a-csv.md](../references/112a-csv.md) for the exact rules and the common
upload-failure causes (BOM, non-breaking spaces, `AE`/`BE` codes, forbidden characters).

Build with [../scripts/schedules/schedule_112a.ps1](../scripts/schedules/schedule_112a.ps1) — it reads the
`schedule_112a` block of `tax_input.json` (`template_path`, `full_value`, `cost`, `expenditure`) and emits
`Schedule112A.csv` with the verbatim template header, no BOM, CRLF. It self-skips when the block is absent.

Key gotchas:
- CSV rejects: UTF-8 BOM, header not byte-identical to template (non-breaking spaces), wrong 1a code
  (`AE` after 31-Jan-2018 / `BE` before), and any of `, / - _ ( ) & @ \ ' " ; :` inside data — so a
  consolidated `AE` row (ISIN `INNOTREQUIRD`, name `CONSOLIDATED`) avoids the minus signs from loss lots.
- Grandfathering (31-Jan-2018 NAV) applies only to `BE` lots.
