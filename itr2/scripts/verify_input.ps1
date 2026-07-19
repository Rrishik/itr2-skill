# Deterministic sanity check for tax_input.json BEFORE running the pipeline.
# Catches the MECHANICAL half of the Step 8 coverage check: internal
# inconsistencies, misplaced fields, typo'd keys, and broken references.
# The source<->field completeness half stays an agent judgement (a script
# cannot know a document is missing).
#
# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File verify_input.ps1 -InputJson tax_input.json
#
# Exit code 0 = no FAILs (WARNs allowed); 1 = at least one FAIL (fix before filing).

param(
    [Parameter(Mandatory)] [string]$InputJson
)

$ErrorActionPreference = 'Stop'
$full = (Resolve-Path $InputJson).Path
$in = Get-Content $full -Raw | ConvertFrom-Json

$fails = @(); $warns = @()
function Fail($m) { $script:fails += $m; Write-Host "  FAIL  $m" -ForegroundColor Red }
function Warn($m) { $script:warns += $m; Write-Host "  WARN  $m" -ForegroundColor Yellow }
function Pass($m) { Write-Host "  PASS  $m" -ForegroundColor Green }
function Has($obj, $name) { $obj -and ($obj.PSObject.Properties.Name -contains $name) }
function N($v) { if ($null -eq $v) { 0.0 } else { [double]$v } }
function Prop($obj, $name) { if ($obj -and ($obj.PSObject.Properties.Name -contains $name)) { $obj.$name } else { $null } }

Write-Host ""
Write-Host "=== Verifying $full ===" -ForegroundColor Cyan

# 1. Unknown top-level keys (catches typos that silently read as zero).
$known = @(
    'taxpayer', 'pan', 'ay', 'senior_citizen',
    'salary_gross', 'salary_hra_exemption', 'salary_professional_tax',
    'other_sources', 'house_property', 'slab_rate_gains', 'special_rate_gains',
    'deduction_80ccd2', 'deductions_old', 'taxes_paid',
    'capital_gains_manual', 'tradewise_csv'
)
$unknown = $in.PSObject.Properties.Name | Where-Object { $_ -notin $known }
if ($unknown) { Fail ("unknown top-level key(s): {0} - typo? these are ignored by the scripts" -f ($unknown -join ', ')) }
else { Pass "no unknown top-level keys" }

# 2. slab_rate_gains must equal the sum of capital_gains_manual gains (the bug
#    from this session: A5 block present in one place but not the other).
if (Has $in 'capital_gains_manual') {
    $manualGain = 0.0
    foreach ($m in @($in.capital_gains_manual)) {
        $manualGain += (N (Prop $m 'consideration')) - (N (Prop $m 'cost')) - (N (Prop $m 'expenditure'))
    }
    $slab = N $in.slab_rate_gains
    if ([math]::Abs($slab - $manualGain) -gt 1) {
        Fail ("slab_rate_gains ({0:N0}) != sum of capital_gains_manual gains ({1:N0}) - they must tie" -f $slab, $manualGain)
    } else { Pass ("slab_rate_gains ties to capital_gains_manual ({0:N0})" -f $slab) }
}

# 3. Salary deductions must live in salary_* not deductions_old (HRA misplacement bug).
if (Has $in 'deductions_old') {
    $other = N (Prop $in.deductions_old 'other')
    if ($other -gt 100000) {
        Warn ("deductions_old.other = {0:N0} is large - confirm it is a real Chapter VI-A item, not HRA/professional tax (those go in salary_hra_exemption / salary_professional_tax)" -f $other)
    }
}
if ((N $in.salary_hra_exemption) -gt 0 -and (N $in.salary_gross) -le 0) {
    Fail "salary_hra_exemption set but salary_gross is 0 - HRA without salary is invalid"
}

# 4. No negative amounts where only non-negative makes sense.
foreach ($k in @('salary_gross', 'salary_hra_exemption', 'salary_professional_tax', 'house_property')) {
    if ((N $in.$k) -lt 0 -and $k -ne 'house_property') { Fail "$k is negative" }
}
if (Has $in 'special_rate_gains') {
    foreach ($k in 'stcg_111a', 'ltcg_112a', 'ltcg_112') {
        if ((N (Prop $in.special_rate_gains $k)) -lt 0) { Warn "special_rate_gains.$k is negative - special-rate heads normally net to >=0 (losses set off within the head)" }
    }
}

# 5. Referenced tradewise CSV must exist.
if ((Has $in 'tradewise_csv') -and $in.tradewise_csv) {
    if (Test-Path $in.tradewise_csv) { Pass "tradewise_csv path exists" }
    else { Fail ("tradewise_csv not found: {0}" -f $in.tradewise_csv) }
}

# 6. capital_gains_manual entries are well-formed.
if (Has $in 'capital_gains_manual') {
    $i = 0
    foreach ($m in @($in.capital_gains_manual)) {
        $i++
        if (-not (Prop $m 'head')) { Warn "capital_gains_manual[$i] has no 'head' label" }
        if (-not (Prop $m 'where')) { Warn "capital_gains_manual[$i] has no 'where' (utility field) - Schedule CG row will be unlabelled" }
    }
}

# 7. AY sanity.
if ((Has $in 'ay') -and $in.ay -and $in.ay -notmatch '^\d{4}-\d{2}$') { Warn ("ay '{0}' is not in YYYY-YY form" -f $in.ay) }

# 8. OS 234C quarterly splits (if supplied) must sum to their annual totals.
if (Has $in 'other_sources') {
    $os = $in.other_sources
    $qKeys = @('q1', 'q2', 'q3', 'q4', 'q5')
    $checks = @(
        @('dividend_quarterly', (N (Prop $os 'dividend'))),
        @('interest_quarterly', ((N (Prop $os 'savings_interest')) + (N (Prop $os 'fd_interest')) + (N (Prop $os 'interest')))),
        @('other_quarterly', (N (Prop $os 'other')))
    )
    foreach ($c in $checks) {
        $qObj = Prop $os $c[0]
        if ($null -eq $qObj) { continue }
        $sum = 0.0
        foreach ($qk in $qKeys) { $v = Prop $qObj $qk; if ($null -eq $v) { $v = Prop $qObj ($qk.ToUpper()) }; $sum += N $v }
        $annual = N $c[1]
        if ([math]::Abs($sum - $annual) -gt 1) {
            Fail ("{0} sums to {1:N0} but the annual total is {2:N0} - the 234C split must tie" -f $c[0], $sum, $annual)
        } else { Pass ("{0} ties to its annual total ({1:N0})" -f $c[0], $annual) }
    }
}

Write-Host ""
if ($fails.Count -gt 0) {
    Write-Host ("VERIFY: {0} FAIL, {1} WARN - fix FAILs before running the pipeline." -f $fails.Count, $warns.Count) -ForegroundColor Red
    exit 1
} elseif ($warns.Count -gt 0) {
    Write-Host ("VERIFY: 0 FAIL, {0} WARN - review warnings, then proceed." -f $warns.Count) -ForegroundColor Yellow
    exit 0
} else {
    Write-Host "VERIFY: all checks passed." -ForegroundColor Green
    exit 0
}
