# Schedule S (Salary) emitter. Reads tax_input.json, writes schedule_s.csv.
# Gross salary less standard deduction (regime-dependent) = chargeable salary.
# Add any foreign-employer RSU/ESPP perquisite into salary_gross first (often
# missing from Form 16). Usage:
#   powershell -File schedule_s.ps1 -InputJson tax_input.json [-Regime new|old] [-OutDir .\out]
param(
    [Parameter(Mandatory)][string]$InputJson,
    [ValidateSet('new', 'old')][string]$Regime = 'new',
    [string]$OutDir
)
. "$PSScriptRoot\_common.ps1"
$in = Read-Input $InputJson

$gross = Num (Prop $in 'salary_gross')
if ($gross -le 0) { Write-Host "No salary income; Schedule S not required." -ForegroundColor DarkGray; return }
$std = if ($Regime -eq 'new') { 75000 } else { 50000 }
$hra = if ($Regime -eq 'old') { Num (Prop $in 'salary_hra_exemption') } else { 0 }
$ptax = if ($Regime -eq 'old') { Num (Prop $in 'salary_professional_tax') } else { 0 }
$chargeable = [math]::Max(0.0, $gross - $std - $hra - $ptax)

$rows = @(
    [pscustomobject]@{ Field = 'Gross salary (incl. perquisites)'; Value = [math]::Round($gross); Where = 'Schedule S: 1(a) Salary u/s 17(1) + 1(b) perquisites u/s 17(2)' }
    [pscustomobject]@{ Field = "Standard deduction ($Regime)"; Value = $std; Where = 'Schedule S: 4(a) standard deduction u/s 16(ia)' }
)
if ($hra -gt 0) { $rows += [pscustomobject]@{ Field = 'HRA exemption (old only)'; Value = [math]::Round($hra); Where = 'Schedule S: 2(iii) exempt allowance u/s 10(13A)' } }
if ($ptax -gt 0) { $rows += [pscustomobject]@{ Field = 'Professional tax (old only)'; Value = [math]::Round($ptax); Where = 'Schedule S: 4(c) professional tax u/s 16(iii)' } }
$rows += [pscustomobject]@{ Field = 'Income chargeable under Salaries'; Value = [math]::Round($chargeable); Where = 'Schedule S: 6 (net salary) -> Part B-TI item 1' }
Show-Section 'Schedule S — Salary' $rows
if ($OutDir) { Write-Section $rows $OutDir 'schedule_s.csv' | Out-Null }
