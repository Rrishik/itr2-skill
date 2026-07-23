# Schedule 112A CSV

The final assembler preserves the V1 consolidated Schedule 112A output for AY 2026-27.

## Requirements

1. Export the Schedule 112A template from the current official utility.
2. Save its exact first header line as UTF-8 without BOM.
3. Add a reviewed consolidated block to `tax_input.json`:

   ```json
   {
     "schedule_112a": {
       "template_path": "112a-header.csv",
       "full_value": 120000,
       "cost": 100000,
       "expenditure": 0
     }
   }
   ```

4. Ensure `full_value - cost - expenditure` reconciles to `special_rate_gains.ltcg_112a` within ₹1.
5. Keep the source skill's per-scrip and grandfathering working papers separately.

## Build

```shell
python scripts/build_return.py --input-json tax_input.json --out-dir skill_output
```

When `schedule_112a` is present, the output includes `Schedule112A.csv`.

The builder validates:

- the template exists, is UTF-8, has no BOM, and has the expected 15 columns;
- consideration, cost, and expenditure are non-negative;
- the consolidated balance is not negative;
- the balance reconciles to the annual section 112A gain;
- output header bytes exactly match the supplied template header.

The generated consolidated row uses the utility's aggregate-entry markers. Use this mode only when the reviewed filing supports a consolidated entry; otherwise enter or upload reviewed per-scrip rows through the official utility. The assembler does not infer lot matching, grandfathering values, or security-level data from broker statements.
