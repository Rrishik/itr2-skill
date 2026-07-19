# Deterministic capital-gains aggregator for a Zerodha-style "Tradewise Exits" CSV.
#
# Reads the broker's tax-P&L tradewise sheet (exported to CSV) and, for each
# section (Equity - Short Term / Long Term / Intraday / Buyback / Non-equity /
# Mutual Funds), sums the exact figures the ITR utility asks for:
#   - Full value of consideration = SUM(Sell Value)
#   - Cost of acquisition         = SUM(Buy Value)
#   - Expenditure on transfer     = SUM(sell-side charges), i.e. Brokerage +
#     Exchange Transaction Charges + IPFT + SEBI + CGST + SGST + IGST + Stamp Duty
#     *** STT is deliberately EXCLUDED (never deductible u/s 48) ***
#   - Gain = consideration - cost  (matches the broker's Profit column)
# It also prints the 234C quarterly split of consideration & gain by Exit Date.
#
# The section layout is Zerodha's: a lone section-title row, then a header row
# starting with "Symbol", then data rows (Symbol + ISIN populated). Other
# brokers differ — export to the same columns or adapt the $sections map.
#
# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File schedule_cg.ps1 `
#       -Path "Tradewise_Exits.csv" [-OutDir ".\out"]
#   or resolve the CSV path from tax_input.json ("tradewise_csv"):
#       -InputJson tax_input.json [-OutDir ".\out"]
#
# Prints a readable summary. With -OutDir, also writes two CSVs there:
#   cg_head_aggregates.csv  (one row per head)
#   cg_234c_split.csv       (one row per head x quarter)
# Verify against the broker's own head-wise totals before entering the utility.
param(
    [string]$Path,
    [string]$InputJson,
    [string]$OutDir
)
. "$PSScriptRoot\_common.ps1"

if (-not $Path -and $InputJson) {
    $in = Get-Content (Resolve-Path $InputJson).Path -Raw | ConvertFrom-Json
    if ($in.PSObject.Properties.Name -contains 'tradewise_csv') { $Path = $in.tradewise_csv }
} elseif ($InputJson) {
    # Path given too: still load JSON so manual CG heads can be merged in.
    $in = Get-Content (Resolve-Path $InputJson).Path -Raw | ConvertFrom-Json
}

# Manual CG heads: gains not in a broker tradewise CSV (debt MF, foreign equity,
# unlisted) supplied directly in tax_input.json as capital_gains_manual[]:
#   { "head": "...", "consideration": N, "cost": N, "expenditure": N (opt),
#     "where": "Schedule CG A5 (STCG slab)", "quarter": "Q2 (16-Jun..15-Sep)" (opt) }
$manual = @()
if ($in -and ($in.PSObject.Properties.Name -contains 'capital_gains_manual')) {
    $manual = @($in.capital_gains_manual)
}
function MProp($obj, $name) { if ($obj -and ($obj.PSObject.Properties.Name -contains $name)) { return $obj.$name } else { return $null } }
function MNum($v) { if ($null -eq $v) { return 0.0 } else { return [double]$v } }

if (-not $Path -and $manual.Count -eq 0) { Write-Host "No tradewise CSV (Path/tradewise_csv) or capital_gains_manual; Schedule CG aggregation skipped." -ForegroundColor DarkGray; return }

$lines = if ($Path) { [System.IO.File]::ReadAllLines((Resolve-Path $Path).Path) } else { @() }
$full = if ($Path) { (Resolve-Path $Path).Path } else { '(manual entries only)' }

# Column indices in the Zerodha tradewise layout (0-based).
$COL = @{
    Symbol = 0; ISIN = 1; EntryDate = 2; ExitDate = 3; Qty = 4
    BuyValue = 5; SellValue = 6; Profit = 7
    Brokerage = 12; ExchTxn = 13; IPFT = 14; SEBI = 15
    CGST = 16; SGST = 17; IGST = 18; Stamp = 19; STT = 20
}
$CHARGE_COLS = @($COL.Brokerage, $COL.ExchTxn, $COL.IPFT, $COL.SEBI, $COL.CGST, $COL.SGST, $COL.IGST, $COL.Stamp)

# Known section titles (a row whose first cell equals one of these, rest blank).
$SECTIONS = @(
    'Equity - Intraday', 'Equity - Short Term', 'Equity - Long Term',
    'Equity - Buyback', 'Non-equity', 'Mutual Funds', 'F&O', 'Currency', 'Commodity'
)

function Get-Field([string[]]$cells, [int]$i) {
    if ($i -lt $cells.Count) { return $cells[$i] } else { return '' }
}
function To-Num([string]$s) {
    $s = ($s -replace '[",]', '').Trim()
    $n = 0.0
    if ([double]::TryParse($s, [ref]$n)) { return $n } else { return 0.0 }
}
function Quarter-Of([datetime]$d) {
    # FY 234C periods. FY runs Apr..Mar; Apr-Dec and Jan-Mar need separate handling.
    $md = $d.Month * 100 + $d.Day
    if ($d.Month -ge 4) {
        if ($md -le 615) { return 'Q1 (<=15-Jun)' }
        elseif ($md -le 915) { return 'Q2 (16-Jun..15-Sep)' }
        elseif ($md -le 1215) { return 'Q3 (16-Sep..15-Dec)' }
        else { return 'Q4 (16-Dec..15-Mar)' }
    } else {
        if ($md -le 315) { return 'Q4 (16-Dec..15-Mar)' }
        else { return 'Q5 (16-Mar..31-Mar)' }
    }
}

# Simple CSV splitter that respects double-quoted fields.
function Split-Csv([string]$line) {
    $result = New-Object System.Collections.Generic.List[string]
    $sb = New-Object System.Text.StringBuilder
    $inQ = $false
    foreach ($ch in $line.ToCharArray()) {
        if ($ch -eq '"') { $inQ = -not $inQ }
        elseif ($ch -eq ',' -and -not $inQ) { [void]$result.Add($sb.ToString()); [void]$sb.Clear() }
        else { [void]$sb.Append($ch) }
    }
    [void]$result.Add($sb.ToString())
    return $result.ToArray()
}

$current = $null
$agg = [ordered]@{}   # section -> aggregate hashtable
$rows = @()           # flat list for the quarterly grid

foreach ($line in $lines) {
    $cells = Split-Csv $line
    $first = (Get-Field $cells 0).Trim()

    # Section-title row: first cell is a known section, the rest are blank.
    if ($SECTIONS -contains $first) {
        $rest = @($cells[1..($cells.Count - 1)] | Where-Object { $_.Trim() -ne '' })
        if ($rest.Count -eq 0) {
            $current = $first
            if (-not $agg.Contains($current)) {
                $agg[$current] = @{ Count = 0; Cons = 0.0; Cost = 0.0; Charges = 0.0; STT = 0.0; Gain = 0.0 }
            }
            continue
        }
    }
    if ($first -eq 'Symbol') { continue }        # column header
    if ($null -eq $current) { continue }
    if ((Get-Field $cells $COL.ISIN).Trim() -eq '' -and (Get-Field $cells $COL.Symbol).Trim() -eq '') { continue }

    $cons = To-Num (Get-Field $cells $COL.SellValue)
    $cost = To-Num (Get-Field $cells $COL.BuyValue)
    if ($cons -eq 0 -and $cost -eq 0) { continue }

    $charges = 0.0
    foreach ($c in $CHARGE_COLS) { $charges += To-Num (Get-Field $cells $c) }
    $stt = To-Num (Get-Field $cells $COL.STT)

    $a = $agg[$current]
    $a.Count++
    $a.Cons += $cons; $a.Cost += $cost; $a.Charges += $charges; $a.STT += $stt
    $a.Gain += ($cons - $cost)

    $exit = [datetime]::MinValue
    $hasDate = [datetime]::TryParse((Get-Field $cells $COL.ExitDate), [ref]$exit)
    $rows += [pscustomobject]@{
        Section = $current; Symbol = (Get-Field $cells $COL.Symbol)
        ExitDate = $(if ($hasDate) { $exit } else { $null }); Cons = $cons; Gain = ($cons - $cost)
    }
}

Write-Host ""
Write-Host "=== Capital-gains head aggregates (enter these in Schedule CG) ===" -ForegroundColor Cyan
Write-Host ("Source: {0}" -f $full)
Write-Host ""
$fmt = "{0,-22} {1,5} {2,15} {3,15} {4,12} {5,14} {6,10}"
Write-Host ($fmt -f 'Head', 'Rows', 'Consideration', 'Cost', 'Expend.*', 'Gain', 'STT(excl)') -ForegroundColor Yellow
foreach ($k in $agg.Keys) {
    $a = $agg[$k]
    if ($a.Count -eq 0) { continue }
    Write-Host ($fmt -f $k, $a.Count,
        ('{0:N2}' -f $a.Cons), ('{0:N2}' -f $a.Cost),
        ('{0:N2}' -f $a.Charges), ('{0:N2}' -f $a.Gain), ('{0:N2}' -f $a.STT))
}
foreach ($m in $manual) {
    $mc = MNum (MProp $m 'consideration'); $mk = MNum (MProp $m 'cost'); $me = MNum (MProp $m 'expenditure')
    Write-Host ($fmt -f (MProp $m 'head'), 1,
        ('{0:N2}' -f $mc), ('{0:N2}' -f $mk),
        ('{0:N2}' -f $me), ('{0:N2}' -f ($mc - $mk - $me)), ('{0:N2}' -f 0)) -ForegroundColor Gray
}
Write-Host ""
Write-Host "* Expenditure = sell-side charges (brokerage/exchange/SEBI/GST/stamp/IPFT). STT is EXCLUDED." -ForegroundColor DarkGray

# Quarterly split (234C) by exit date, per head.
$withDates = $rows | Where-Object { $_.ExitDate -ne $null }
if ($withDates.Count -gt 0) {
    Write-Host ""
    Write-Host "=== 234C quarterly split (by Exit Date) ===" -ForegroundColor Cyan
    foreach ($k in $agg.Keys) {
        $hr = $withDates | Where-Object { $_.Section -eq $k }
        if (-not $hr) { continue }
        Write-Host ""
        Write-Host $k -ForegroundColor Yellow
        $hr | Group-Object { Quarter-Of $_.ExitDate } | Sort-Object Name | ForEach-Object {
            $g = $_.Group | Measure-Object -Property Gain -Sum
            Write-Host ("  {0,-24} gain {1,14}" -f $_.Name, ('{0:N2}' -f $g.Sum))
        }
    }
}
Write-Host ""

# Optional CSV output.
if ($OutDir) {
    if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir | Out-Null }
    $OutDir = (Resolve-Path $OutDir).Path

    $headRows = foreach ($k in $agg.Keys) {
        $a = $agg[$k]
        if ($a.Count -eq 0) { continue }
        [pscustomobject]@{
            Head = $k; Rows = $a.Count
            Consideration = [math]::Round($a.Cons, 2); Cost = [math]::Round($a.Cost, 2)
            Expenditure = [math]::Round($a.Charges, 2); Gain = [math]::Round($a.Gain, 2)
            STT_Excluded = [math]::Round($a.STT, 2)
            Where = $(switch ($k) {
                'Equity - Short Term' { 'Schedule CG A2 (STCG 111A, STT paid)' }
                'Equity - Long Term'  { 'Schedule CG B3 (LTCG 112A, opens 112A grid)' }
                'Equity - Buyback'    { 'Schedule CG A8 (buyback)' }
                'Mutual Funds'        { 'Schedule CG A5 or B (by fund type/holding); debt MF = A5 slab' }
                'Non-equity'          { 'Schedule CG B2 (listed bonds/SGB/ZCB u/s 112(1)); debt MF STCG = A5' }
                'F&O'                 { 'NOT CG - business income, ITR-3 (out of scope)' }
                'Currency'            { 'NOT CG - business income, ITR-3 (out of scope)' }
                'Commodity'           { 'NOT CG - business income, ITR-3 (out of scope)' }
                'Equity - Intraday'   { 'NOT CG - speculative business income, ITR-3 (out of scope)' }
                default               { 'Schedule CG - classify by instrument' }
            })
        }
    }
    $headRows = @($headRows)
    foreach ($m in $manual) {
        $mc = MNum (MProp $m 'consideration'); $mk = MNum (MProp $m 'cost'); $me = MNum (MProp $m 'expenditure')
        $headRows += [pscustomobject]@{
            Head = (MProp $m 'head'); Rows = 1
            Consideration = [math]::Round($mc, 2); Cost = [math]::Round($mk, 2)
            Expenditure = [math]::Round($me, 2); Gain = [math]::Round($mc - $mk - $me, 2)
            STT_Excluded = 0
            Where = $(if (MProp $m 'where') { MProp $m 'where' } else { 'Schedule CG - classify by instrument' })
        }
    }
    Merge-Return $OutDir 'capital_gains_head' $headRows | Out-Null

    # Map a head (built-in section name, or a manual entry's 'where') to its
    # Schedule CG Section F quarterly-grid row (by tax rate).
    function SectionF-Row($label) {
        switch -Regex ($label) {
            'Short Term|A2|111A'        { 'Row 1 (STCG @20%)'; break }
            'A5|slab|debt|Foreign|<24m' { 'Row 3 (STCG applicable rate)'; break }
            'Long Term|112A|A8|B3'      { 'Row 5 (LTCG @12.5%)'; break }
            'Non-equity|B2|SGB|112'     { 'Row 5 (LTCG @12.5%)'; break }
            default                     { 'classify by rate (see schedule-mapping Section F)' }
        }
    }

    $splitRows = foreach ($k in $agg.Keys) {
        $hr = $withDates | Where-Object { $_.Section -eq $k }
        if (-not $hr) { continue }
        $hr | Group-Object { Quarter-Of $_.ExitDate } | Sort-Object Name | ForEach-Object {
            $g = $_.Group | Measure-Object -Property Gain -Sum
            $c = $_.Group | Measure-Object -Property Cons -Sum
            [pscustomobject]@{
                Head = $k; Quarter = $_.Name
                Consideration = [math]::Round($c.Sum, 2); Gain = [math]::Round($g.Sum, 2)
                SectionF = SectionF-Row $k
            }
        }
    }
    $splitRows = @($splitRows)
    foreach ($m in $manual) {
        $q = MProp $m 'quarter'
        if ($q) {
            $mc = MNum (MProp $m 'consideration'); $mk = MNum (MProp $m 'cost'); $me = MNum (MProp $m 'expenditure')
            $splitRows += [pscustomobject]@{
                Head = (MProp $m 'head'); Quarter = $q
                Consideration = [math]::Round($mc, 2); Gain = [math]::Round($mc - $mk - $me, 2)
                SectionF = SectionF-Row ("$(MProp $m 'head') $(MProp $m 'where')")
            }
        }
    }
    Merge-Return $OutDir 'capital_gains_234c' $splitRows | Out-Null

    Write-Host ("Wrote return.json sections: capital_gains_head, capital_gains_234c") -ForegroundColor Green
    Write-Host ""
}
