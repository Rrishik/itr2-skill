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
    [pscustomobject]@{ Field = 'Dividend income (reconcile to AIS)'; Value = [math]::Round($dividend); Source = 'Dividend report / AIS (Indian + foreign dividends, at slab)'; Where = 'Schedule OS: 1a dividends (gross)' }
    [pscustomobject]@{ Field = 'Savings-bank interest'; Value = [math]::Round($savings); Source = 'Bank interest certificate / passbook / AIS'; Where = 'Schedule OS: 1b(i) savings-bank interest' }
    [pscustomobject]@{ Field = 'FD/term-deposit interest'; Value = [math]::Round($fd); Source = 'Bank/FD interest certificate / AIS'; Where = 'Schedule OS: 1b(ii) term-deposit interest' }
)
if ($genInterest -gt 0) { $rows += [pscustomobject]@{ Field = 'Interest (unsplit)'; Value = [math]::Round($genInterest); Source = 'Bank certificates / AIS'; Where = 'Schedule OS: 1b interest income' } }
if ($otherOs -gt 0) { $rows += [pscustomobject]@{ Field = 'Other'; Value = [math]::Round($otherOs); Source = 'As applicable (see source doc)'; Where = 'Schedule OS: 1d any other income' } }
$rows += [pscustomobject]@{ Field = 'Total income from other sources'; Value = [math]::Round($total); Source = 'Computed (sum of above)'; Where = 'Schedule OS: total -> Part B-TI item 5' }

Show-Section 'Schedule OS — Other Sources' $rows
if ($OutDir) { Merge-Return $OutDir 'other_sources' $rows | Out-Null }

# --- OS 234C quarterly grid (Schedule OS accrual/receipt screen) ---
# Advance-tax interest (234C) needs OS income split by the quarter it was
# credited. Supply the split in tax_input.json under other_sources as any of:
#   dividend_quarterly / interest_quarterly / other_quarterly
# each an object keyed by q1..q5 (or Q1..Q5), e.g.:
#   "dividend_quarterly": { "q1": 12000, "q2": 0, "q3": 30120, "q4": 20000, "q5": 0 }
# Each item's quarterly split must sum to that item's annual total above.
$qMap = [ordered]@{
    q1 = 'Q1 (<=15-Jun)'; q2 = 'Q2 (16-Jun..15-Sep)'; q3 = 'Q3 (16-Sep..15-Dec)'
    q4 = 'Q4 (16-Dec..15-Mar)'; q5 = 'Q5 (16-Mar..31-Mar)'
}
function Get-Quarterly($obj, $name) {
    $q = Prop $obj $name
    if ($null -eq $q) { return $null }
    $out = [ordered]@{}
    foreach ($k in $qMap.Keys) {
        # accept q1/Q1 casing
        $v = Prop $q $k; if ($null -eq $v) { $v = Prop $q ($k.ToUpper()) }
        $out[$qMap[$k]] = Num $v
    }
    return $out
}
# item label, OS-screen row (Where), which annual figure it must reconcile to, source
$osItems = @(
    [pscustomobject]@{ Label = 'Dividend'; Key = 'dividend_quarterly'; Where = 'Schedule OS 234C: 3a Dividend income (Sl.no. 1a(i))'; Annual = $dividend; Source = 'Dividend report / AIS (credit dates)' }
    [pscustomobject]@{ Label = 'Interest'; Key = 'interest_quarterly'; Where = 'Schedule OS 234C: interest income row'; Annual = $interestTotal; Source = 'Bank interest certificate / AIS (credit dates)' }
    [pscustomobject]@{ Label = 'Other'; Key = 'other_quarterly'; Where = 'Schedule OS 234C: other income row'; Annual = $otherOs; Source = 'As applicable (see source doc)' }
)
$osSplit = @()
foreach ($it in $osItems) {
    $label = $it.Label; $qObj = Get-Quarterly $os $it.Key; $annual = Num $it.Annual
    if ($null -eq $qObj) { continue }
    $sum = ($qObj.Values | Measure-Object -Sum).Sum
    if ($annual -gt 0 -and [math]::Abs($sum - $annual) -gt 1) {
        Write-Host ("WARN: $label quarterly split ({0}) != annual total ({1})" -f [math]::Round($sum), [math]::Round($annual)) -ForegroundColor Yellow
    }
    foreach ($qk in $qMap.Keys) {
        $lab = $qMap[$qk]; $amt = Num $qObj[$lab]
        if ($amt -eq 0) { continue }
        $osSplit += [pscustomobject]@{ Item = $label; Quarter = $lab; Amount = [math]::Round($amt); Source = $it.Source; Where = $it.Where }
    }
}
if ($osSplit.Count -gt 0) {
    Show-Section 'Schedule OS — 234C quarterly split' $osSplit
    if ($OutDir) { Merge-Return $OutDir 'other_sources_234c' $osSplit | Out-Null }
}
