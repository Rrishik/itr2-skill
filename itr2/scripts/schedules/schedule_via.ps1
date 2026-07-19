# Schedule VI-A (Deductions) emitter. Reads tax_input.json, writes schedule_via.csv.
# Under the NEW regime only 80CCD(2) (employer NPS) survives; everything else is
# OLD-regime only. This emitter therefore reports the allowed set per regime and
# flags any OLD-only deduction that is void under NEW. Usage:
#   powershell -File schedule_via.ps1 -InputJson tax_input.json [-Regime new|old] [-OutDir .\out]
param(
    [Parameter(Mandatory)][string]$InputJson,
    [ValidateSet('new', 'old')][string]$Regime = 'new',
    [string]$OutDir
)
. "$PSScriptRoot\_common.ps1"
$in = Read-Input $InputJson
$d = Prop $in 'deductions_old'

$nps = Num (Prop $in 'deduction_80ccd2')
$c80 = [math]::Min((Num (Prop $d '80c')), 150000)
$d80 = Num (Prop $d '80d')
$tta = Num (Prop $d '80tta_ttb')
$other = Num (Prop $d 'other')

$rows = @()
$rows += [pscustomobject]@{ Field = '80CCD(2) employer NPS (both regimes)'; Value = [math]::Round($nps); Allowed = 'Yes'; Source = 'Form 16 (employer NPS contribution)'; Where = 'Schedule VI-A: 80CCD(2)' }
if ($Regime -eq 'old') {
    $rows += [pscustomobject]@{ Field = '80C'; Value = [math]::Round($c80); Allowed = 'Yes'; Source = '80C proofs (EPF/PPF/ELSS/LIC/tuition etc.)'; Where = 'Schedule VI-A: 80C' }
    $rows += [pscustomobject]@{ Field = '80D'; Value = [math]::Round($d80); Allowed = 'Yes'; Source = 'Health-insurance premium receipts'; Where = 'Schedule VI-A: 80D' }
    $rows += [pscustomobject]@{ Field = '80TTA/80TTB'; Value = [math]::Round($tta); Allowed = 'Yes'; Source = 'Bank interest certificate (savings/deposit)'; Where = 'Schedule VI-A: 80TTA/80TTB' }
    if ($other -gt 0) { $rows += [pscustomobject]@{ Field = 'Other Chapter VI-A'; Value = [math]::Round($other); Allowed = 'Yes'; Source = 'As applicable (see source doc)'; Where = 'Schedule VI-A: as applicable' }}
    $total = $nps + $c80 + $d80 + $tta + $other
} else {
    foreach ($x in @(@('80C', $c80, '80C proofs (EPF/PPF/ELSS/LIC etc.)'), @('80D', $d80, 'Health-insurance premium receipts'), @('80TTA/80TTB', $tta, 'Bank interest certificate'), @('Other Chapter VI-A', $other, 'As applicable'))) {
        if ($x[1] -gt 0) { $rows += [pscustomobject]@{ Field = $x[0]; Value = [math]::Round($x[1]); Allowed = 'NO - void under NEW (untick)'; Source = $x[2]; Where = 'n/a under NEW regime' } }
    }
    $total = $nps
}
$rows += [pscustomobject]@{ Field = "Total deductions allowed ($Regime)"; Value = [math]::Round($total); Allowed = ''; Source = 'Computed (sum of allowed)'; Where = 'Schedule VI-A: total -> Part B-TI' }

Show-Section 'Schedule VI-A — Deductions' $rows
if ($OutDir) { Merge-Return $OutDir 'deductions' $rows | Out-Null }
