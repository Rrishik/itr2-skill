# `tax_input.json` contract

Use a fresh JSON file for AY 2026-27. Values are rupees. Preserve source statements separately; the build never rewrites this file.

```json
{
  "taxpayer": "Synthetic Taxpayer",
  "pan": "AAAAA0000A",
  "ay": "2026-27",
  "residential_status": "resident_and_ordinarily_resident",
  "senior_citizen": false,
  "salary_gross": 0,
  "salary_hra_exemption": 0,
  "salary_professional_tax": 0,
  "other_sources": {
    "dividend": 0,
    "savings_interest": 0,
    "fd_interest": 0,
    "interest": 0,
    "other": 0,
    "dividend_quarterly": {}
  },
  "house_property": 0,
  "slab_rate_gains": 0,
  "special_rate_gains": {
    "stcg_111a": 0,
    "ltcg_112a": 0,
    "ltcg_112": 0
  },
  "capital_gains_manual": [],
  "deduction_80ccd2": 0,
  "deductions_old": {
    "80c": 0,
    "80d": 0,
    "80tta_ttb": 0,
    "other": 0
  },
  "taxes_paid": {
    "tds": 0,
    "advance_tax": 0,
    "self_assessment_tax": 0,
    "ftc": 0
  },
  "foreign_sources": []
}
```

Omit optional empty blocks. Unknown top-level and nested keys fail validation.

## House property

`house_property` is the reviewed net amount. Optionally supply the components and make them reconcile:

```json
{
  "house_property": -100000,
  "house_property_detail": {
    "annual_value": 0,
    "municipal_tax": 0,
    "home_loan_interest": 100000
  }
}
```

The computed value is annual value less municipal tax, 30% of net annual value, and home-loan interest. The tax engine limits house-property set-off against other income to ₹2,00,000.

## Reviewed capital-gain contributions

`capital_gains_manual[]` is a handoff from reviewed source computations. It is not a broker-ingestion surface.

```json
{
  "head": "Indian equity STCG",
  "tax_bucket": "stcg_111a",
  "consideration": 120000,
  "cost": 100000,
  "expenditure": 100,
  "stt": 500,
  "rows": 4,
  "source": "Reviewed Indian-equity contribution",
  "where": "Schedule CG A2",
  "quarter": "Q2 (16-Jun..15-Sep)"
}
```

Allowed `tax_bucket` values:

| Value | Annual field | Schedule CG / Section F |
|---|---|---|
| `stcg_111a` | `special_rate_gains.stcg_111a` | A2 / Row 1 |
| `ltcg_112a` | `special_rate_gains.ltcg_112a` | B3 / Row 5 |
| `ltcg_112` | `special_rate_gains.ltcg_112` | B8 / Row 5 |
| `slab` or `slab_rate_gains` | `slab_rate_gains` | A5 / Row 3 |

Instead of `quarter`, an entry may contain a `quarterly` object keyed by `q1` through `q5`. The quarterly sum must equal consideration minus cost and expenditure within ₹1.

All contributions in each bucket must reconcile to its annual field. STT is tracked separately and is not deductible expenditure.

Quarter labels, in order:

1. `Q1 (<=15-Jun)`
2. `Q2 (16-Jun..15-Sep)`
3. `Q3 (16-Sep..15-Dec)`
4. `Q4 (16-Dec..15-Mar)`
5. `Q5 (16-Mar..31-Mar)`

## Other-source quarterly disclosure

When `other_sources.dividend` is non-zero, `dividend_quarterly` is required. Key it by `q1` through `q5`; it must tie to the annual figure. `other_quarterly` is available for the corresponding Schedule OS disclosure when applicable.

Do not add `interest_quarterly`. It is intentionally rejected because the current Schedule OS quarterly disclosure used by this assembler is dividend-only for ordinary interest.

## Foreign-source contribution

Use one entry per country, income head, and relief basis:

```json
{
  "country": "United States of America",
  "country_code": "2",
  "income_head": "Other Sources",
  "gross_income": 50000,
  "foreign_tax_paid": 12500,
  "indian_tax_on_income": 15000,
  "dtaa_tax_limit": 12500,
  "relief_claimed": 12500,
  "relief_section": "90",
  "dtaa_article": "Article 10",
  "form67_status": "filed",
  "form67_acknowledgement": "SYNTHETIC-ACK",
  "source": "Reviewed foreign-tax working"
}
```

Rules:

- `income_head` identifies the Schedule FSI income head; use the official utility wording such as `Other Sources` or `Capital Gains`.
- `relief_section` must be `90` or `91`.
- `form67_status` is mandatory: `pending`, `filed`, or `not_claiming`.
- `not_claiming` requires zero `relief_claimed`.
- Claimed section 90 relief requires `dtaa_tax_limit`.
- `relief_claimed` cannot exceed foreign tax, Indian tax on that income, or the DTAA limit where applicable.
- If present, `taxes_paid.ftc` must equal total `relief_claimed`.
- Foreign gross income under `Other Sources` must already be included in `other_sources`.
- Foreign sources currently require `resident_and_ordinarily_resident` status.

## Optional consolidated Schedule 112A

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

Use the exact one-line header exported by the current official utility. The assembler emits the preserved V1 consolidated row and verifies that the balance reconciles to `special_rate_gains.ltcg_112a`.

This compact mode is suitable only when a reviewed consolidated entry is accepted for the filing. Keep per-scrip source workings separately. Schedule FA A2/A3 is not part of this contract; use the foreign-equity skill's strict FA artifact directly.

## Generate the working set

```shell
python scripts/verify_input.py --input-json tax_input.json
python scripts/build_return.py --input-json tax_input.json --out-dir skill_output
```

Outputs:

```text
skill_output/
  return.json
  ITR2_data_entry.md
  Schedule112A.csv   # only when schedule_112a is present
```
