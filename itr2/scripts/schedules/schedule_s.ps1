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
$chargeable = [math]::Max(0.0, $gross - $std)

$rows = @(
    [pscustomobject]@{ Field = 'Gross salary (incl. perquisites)'; Value = [math]::Round($gross) }
    [pscustomobject]@{ Field = "Standard deduction ($Regime)"; Value = $std }
    [pscustomobject]@{ Field = 'Income chargeable under Salaries'; Value = [math]::Round($chargeable) }
)
Show-Section 'Schedule S — Salary' $rows
if ($OutDir) { Write-Section $rows $OutDir 'schedule_s.csv' | Out-Null }
