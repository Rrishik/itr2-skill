# Deterministic ITR-2 tax computation and OLD-vs-NEW regime comparison.
#
# Reads a tax_input.json (schema below), computes tax under both regimes, and
# prints a line-by-line comparison. With -OutDir it also writes
# tax_regime_comparison.csv (one row per line item, an OLD and a NEW column).
#
# It removes the single most error-prone hand-calc in the skill: slabs,
# special-rate gains (111A/112A/112), surcharge with the 15% cap on special-rate
# income, cess, 87A rebate and standard deduction are all applied here.
#
# Special-rate gains are ALWAYS taxed at their statutory rate (regime-independent)
# and are EXCLUDED from slab income and from the 87A rebate ceiling.
#
# tax_input.json (all amounts in INR; omit what doesn't apply):
#   {
#     "ay": "2026-27", "senior_citizen": false,
#     "salary_gross": 0,                 // before standard deduction
#     "other_sources": { "dividend": 0, "savings_interest": 0, "fd_interest": 0, "interest": 0, "other": 0 },
#     "house_property": 0,               // net (can be negative, capped -2L)
#     "slab_rate_gains": 0,              // CG taxed at slab (debt MF s.50AA, foreign equity <24m, unlisted STCG)
#     "special_rate_gains": {
#        "stcg_111a": 0,                 // 20%
#        "ltcg_112a": 0,                 // 12.5% over 1.25L exemption
#        "ltcg_112":  0                  // 12.5% no exemption (bonds/SGB/foreign)
#     },
#     "deductions_old": { "80c": 0, "80d": 0, "80tta_ttb": 0, "other": 0 },
#     "deduction_80ccd2": 0,             // employer NPS - allowed in BOTH regimes
#     "taxes_paid": { "tds": 0, "advance_tax": 0, "self_assessment_tax": 0, "ftc": 0 }
#   }
#
# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File compute_tax.ps1 `
#       -InputJson tax_input.json [-OutDir .\out]
#
# Rates are AY2026-27. Verify against the utility before finalising.
param(
    [Parameter(Mandatory)][string]$InputJson,
    [string]$OutDir
)

$full = (Resolve-Path $InputJson).Path
$in = Get-Content $full -Raw | ConvertFrom-Json

function Num($v) { if ($null -eq $v) { return 0.0 } else { return [double]$v } }
function Prop($obj, $name) { if ($obj -and ($obj.PSObject.Properties.Name -contains $name)) { return $obj.$name } else { return $null } }

$senior = [bool](Prop $in 'senior_citizen')
$salaryGross = Num (Prop $in 'salary_gross')
$os = Prop $in 'other_sources'
$dividend = Num (Prop $os 'dividend')
# Interest can be split (savings_interest/fd_interest) or unsplit (interest); mirror schedule_os.ps1.
$interest = (Num (Prop $os 'savings_interest')) + (Num (Prop $os 'fd_interest')) + (Num (Prop $os 'interest')) + (Num (Prop $os 'other'))
$hp = Num (Prop $in 'house_property')
if ($hp -lt -200000) { $hp = -200000 }   # set-off cap
$slabGains = Num (Prop $in 'slab_rate_gains')

$sr = Prop $in 'special_rate_gains'
$stcg111a = Num (Prop $sr 'stcg_111a')
$ltcg112a = Num (Prop $sr 'ltcg_112a')
$ltcg112 = Num (Prop $sr 'ltcg_112')

$dOld = Prop $in 'deductions_old'
$old80c = [math]::Min((Num (Prop $dOld '80c')), 150000)
$old80d = Num (Prop $dOld '80d')
$oldTta = Num (Prop $dOld '80tta_ttb')
$oldOther = Num (Prop $dOld 'other')
$nps = Num (Prop $in 'deduction_80ccd2')

$taxes = Prop $in 'taxes_paid'
$tds = Num (Prop $taxes 'tds')
$adv = Num (Prop $taxes 'advance_tax')
$sat = Num (Prop $taxes 'self_assessment_tax')
$ftc = Num (Prop $taxes 'ftc')

# --- Slab engines --------------------------------------------------------------
function Tax-New([double]$ti) {
    # AY2026-27 new-regime slabs.
    $slabs = @(@(400000,0.0),@(400000,0.05),@(400000,0.10),@(400000,0.15),@(400000,0.20),@(400000,0.25))
    $tax = 0.0; $rem = $ti
    foreach ($s in $slabs) { if ($rem -le 0) { break }; $band = [math]::Min($rem, $s[0]); $tax += $band * $s[1]; $rem -= $band }
    if ($rem -gt 0) { $tax += $rem * 0.30 }   # >24L
    return $tax
}
function Tax-Old([double]$ti, [bool]$sr) {
    $exempt = if ($sr) { 300000 } else { 250000 }
    $tax = 0.0
    if ($ti -gt $exempt) { $tax += ([math]::Min($ti,500000) - $exempt) * 0.05 }
    if ($ti -gt 500000) { $tax += ([math]::Min($ti,1000000) - 500000) * 0.20 }
    if ($ti -gt 1000000) { $tax += ($ti - 1000000) * 0.30 }
    return $tax
}

# Special-rate tax is regime-independent.
$ltcg112aTaxable = [math]::Max(0.0, $ltcg112a - 125000)
$specialTax = $stcg111a * 0.20 + $ltcg112aTaxable * 0.125 + $ltcg112 * 0.125
$specialIncome = $stcg111a + $ltcg112a + $ltcg112

function Surcharge([double]$totalIncome, [double]$normalTax, [double]$specialTax) {
    # Rate by total income; special-rate (111A/112A/112) portion capped at 15%.
    $rate = 0.0
    if ($totalIncome -gt 20000000) { $rate = 0.25 }
    elseif ($totalIncome -gt 10000000) { $rate = 0.15 }
    elseif ($totalIncome -gt 5000000) { $rate = 0.10 }
    $specRate = [math]::Min($rate, 0.15)
    return ($normalTax * $rate) + ($specialTax * $specRate)
}

function Compute-Regime([string]$name) {
    $stdDed = if ($name -eq 'new') { 75000 } else { 50000 }
    $salaryNet = [math]::Max(0.0, $salaryGross - $stdDed)
    $grossSlab = $salaryNet + $dividend + $interest + $hp + $slabGains
    if ($name -eq 'new') {
        $chapVI = $nps
    } else {
        $chapVI = $old80c + $old80d + $oldTta + $oldOther + $nps
    }
    $slabIncome = [math]::Max(0.0, $grossSlab - $chapVI)
    $totalIncome = $slabIncome + $specialIncome

    if ($name -eq 'new') { $normalTax = Tax-New $slabIncome } else { $normalTax = Tax-Old $slabIncome $senior }

    # 87A rebate. New: TI<=12L -> rebate on normal-rate tax only (not special). Old: TI<=5L.
    $rebate = 0.0
    if ($name -eq 'new' -and $totalIncome -le 1200000) { $rebate = $normalTax }
    elseif ($name -eq 'old' -and $totalIncome -le 500000) { $rebate = [math]::Min($normalTax + $specialTax, 12500) }
    $normalTaxAfterRebate = [math]::Max(0.0, $normalTax - $rebate)
    $specialAfterRebate = $specialTax
    if ($name -eq 'old' -and $rebate -gt $normalTax) { $specialAfterRebate = [math]::Max(0.0, $specialTax - ($rebate - $normalTax)) }

    $baseTax = $normalTaxAfterRebate + $specialAfterRebate
    $surcharge = Surcharge $totalIncome $normalTaxAfterRebate $specialAfterRebate
    $cess = ($baseTax + $surcharge) * 0.04
    $totalTax = $baseTax + $surcharge + $cess
    $afterFtc = [math]::Max(0.0, $totalTax - $ftc)
    $payable = $afterFtc - $tds - $adv - $sat

    return [ordered]@{
        Regime = $name
        'Slab income' = [math]::Round($slabIncome)
        '  of which slab-rate CG' = [math]::Round($slabGains)
        'Special-rate income' = [math]::Round($specialIncome)
        'Total income' = [math]::Round($totalIncome)
        'Tax on slab income' = [math]::Round($normalTax)
        'Tax on special-rate gains' = [math]::Round($specialTax)
        '87A rebate' = [math]::Round($rebate)
        'Surcharge' = [math]::Round($surcharge)
        'Cess (4%)' = [math]::Round($cess)
        'Total tax liability' = [math]::Round($totalTax)
        'Less: FTC' = [math]::Round($ftc)
        'Less: TDS/advance/SA' = [math]::Round($tds + $adv + $sat)
        'Net payable (+) / refund (-)' = [math]::Round($payable)
    }
}

$new = Compute-Regime 'new'
$old = Compute-Regime 'old'

$recommend = if ($new.'Total tax liability' -le $old.'Total tax liability') { 'NEW' } else { 'OLD' }

Write-Host ""
Write-Host "=== Regime comparison (AY $((Prop $in 'ay')) ) ===" -ForegroundColor Cyan
$fmt = "{0,-32} {1,16} {2,16}"
Write-Host ($fmt -f 'Line item', 'OLD', 'NEW') -ForegroundColor Yellow
foreach ($k in $new.Keys) {
    if ($k -eq 'Regime') { continue }
    Write-Host ($fmt -f $k, ('{0:N0}' -f $old[$k]), ('{0:N0}' -f $new[$k]))
}
Write-Host ""
Write-Host ("Recommended regime: {0} (lower total tax)" -f $recommend) -ForegroundColor Green
Write-Host ""

if ($OutDir) {
    if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir | Out-Null }
    $OutDir = (Resolve-Path $OutDir).Path
    $rows = foreach ($k in $new.Keys) {
        if ($k -eq 'Regime') { continue }
        [pscustomobject]@{ LineItem = $k; OLD = $old[$k]; NEW = $new[$k] }
    }
    $rows += [pscustomobject]@{ LineItem = 'Recommended regime'; OLD = ''; NEW = $recommend }
    $outPath = Join-Path $OutDir 'tax_regime_comparison.csv'
    $rows | Export-Csv -Path $outPath -NoTypeInformation
    Write-Host ("Wrote: {0}" -f $outPath) -ForegroundColor Green
    Write-Host ""
}
