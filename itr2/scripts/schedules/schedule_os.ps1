# Schedule OS (Other Sources) emitter. Reads tax_input.json, writes schedule_os.csv.
# Sums dividends and interest (savings + FD) at slab rate. Reconcile the totals to
# AIS before finalising; report the AIS figure for tiny (rounding) differences.
# The 234C quarterly split of dividends lives in the OS grid (by credit date) —
# supply other_sources.dividend_quarterly if you want it emitted. Usage:
#   powershell -File schedule_os.ps1 -InputJson tax_input.json [-OutDir .\out]
param(
    [Parameter(Mandatory)][string]$InputJson,
    [string]$OutDir
)
. "$PSScriptRoot\_common.ps1"
$in = Read-Input $InputJson
$os = Prop $in 'other_sources'

$dividend = Num (Prop $os 'dividend')
$savings = Num (Prop $os 'savings_interest')
$fd = Num (Prop $os 'fd_interest')
$genInterest = Num (Prop $os 'interest')   # if not split into savings/fd
$otherOs = Num (Prop $os 'other')
$interestTotal = $savings + $fd + $genInterest
$total = $dividend + $interestTotal + $otherOs

if ($total -eq 0) { Write-Host "No other-source income; Schedule OS not required." -ForegroundColor DarkGray; return }

$rows = @(
    [pscustomobject]@{ Field = 'Dividend income (reconcile to AIS)'; Value = [math]::Round($dividend) }
    [pscustomobject]@{ Field = 'Savings-bank interest'; Value = [math]::Round($savings) }
    [pscustomobject]@{ Field = 'FD/term-deposit interest'; Value = [math]::Round($fd) }
)
if ($genInterest -gt 0) { $rows += [pscustomobject]@{ Field = 'Interest (unsplit)'; Value = [math]::Round($genInterest) } }
if ($otherOs -gt 0) { $rows += [pscustomobject]@{ Field = 'Other'; Value = [math]::Round($otherOs) } }
$rows += [pscustomobject]@{ Field = 'Total income from other sources'; Value = [math]::Round($total) }

Show-Section 'Schedule OS — Other Sources' $rows
if ($OutDir) { Write-Section $rows $OutDir 'schedule_os.csv' | Out-Null }
