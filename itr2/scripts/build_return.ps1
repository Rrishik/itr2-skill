# Orchestrator: runs every per-schedule emitter against a shared tax_input.json.
# Each emitter merges its section into a single return.json (the structured
# output); build_return then renders return.json into one Markdown data-entry sheet.
#
# It runs (when the relevant input is present):
#   compute_tax.ps1              -> return.json: tax_computation, recommended_regime
#   schedules/schedule_s.ps1     -> return.json: salary
#   schedules/schedule_hp.ps1    -> return.json: house_property
#   schedules/schedule_os.ps1    -> return.json: other_sources
#   schedules/schedule_via.ps1   -> return.json: deductions
#   schedules/schedule_cg.ps1    -> return.json: capital_gains_head, capital_gains_234c
#   schedules/schedule_112a.ps1  -> Schedule112A.csv   (uploadable artifact, stays CSV)
# then writes ITR2_data_entry.md from return.json.
#
# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File build_return.ps1 `
#       -InputJson tax_input.json -OutDir .\out [-TradewiseCsv Tradewise_Exits.csv]
#
# -Regime is auto-picked from compute_tax's recommendation unless overridden.
param(
    [Parameter(Mandatory)][string]$InputJson,
    [Parameter(Mandatory)][string]$OutDir,
    [string]$TradewiseCsv,
    [ValidateSet('new', 'old')][string]$Regime
)

$ErrorActionPreference = 'Stop'
$scripts = $PSScriptRoot
$in = Get-Content (Resolve-Path $InputJson).Path -Raw | ConvertFrom-Json
if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir | Out-Null }
$OutDir = (Resolve-Path $OutDir).Path

# 1. Tax first, to learn the recommended regime.
& "$scripts\compute_tax.ps1" -InputJson $InputJson -OutDir $OutDir | Out-Null
$returnJson = Join-Path $OutDir 'return.json'
$doc = Get-Content $returnJson -Raw | ConvertFrom-Json
if (-not $Regime) {
    $rec = $doc.recommended_regime
    $Regime = if ($rec -eq 'OLD') { 'old' } else { 'new' }
}
Write-Host "Using regime: $Regime" -ForegroundColor Cyan

# 2. Per-schedule emitters.
& "$scripts\schedules\schedule_s.ps1"   -InputJson $InputJson -Regime $Regime -OutDir $OutDir | Out-Null
& "$scripts\schedules\schedule_hp.ps1"  -InputJson $InputJson -OutDir $OutDir | Out-Null
& "$scripts\schedules\schedule_os.ps1"  -InputJson $InputJson -OutDir $OutDir | Out-Null
& "$scripts\schedules\schedule_via.ps1" -InputJson $InputJson -Regime $Regime -OutDir $OutDir | Out-Null
& "$scripts\schedules\schedule_112a.ps1" -InputJson $InputJson -OutDir $OutDir | Out-Null
if ($TradewiseCsv) { & "$scripts\schedules\schedule_cg.ps1" -Path $TradewiseCsv -InputJson $InputJson -OutDir $OutDir | Out-Null }
else { & "$scripts\schedules\schedule_cg.ps1" -InputJson $InputJson -OutDir $OutDir | Out-Null }

# 3. Stitch the return.json sections into one MD.
function Rows-ToMdTable($rows) {
    $rows = @($rows)
    if (-not $rows -or $rows.Count -eq 0) { return $null }
    $cols = $rows[0].PSObject.Properties.Name
    $esc = { param($v) ("$v") -replace '\|', '\|' }
    $sb = New-Object System.Text.StringBuilder
    [void]$sb.AppendLine('| ' + ($cols -join ' | ') + ' |')
    [void]$sb.AppendLine('|' + (($cols | ForEach-Object { '---' }) -join '|') + '|')
    foreach ($r in $rows) {
        $vals = $cols | ForEach-Object { & $esc $r.$_ }
        [void]$sb.AppendLine('| ' + ($vals -join ' | ') + ' |')
    }
    return $sb.ToString()
}

# Pivot the capital_gains_234c rows into the utility's Section F grid:
# one row per Section F rate-row, one column per 234C quarter (Q1..Q5).
function SectionF-Grid($rows) {
    $rows = @($rows)
    if (-not $rows -or $rows.Count -eq 0) { return $null }
    $qCols = @('Q1 (<=15-Jun)', 'Q2 (16-Jun..15-Sep)', 'Q3 (16-Sep..15-Dec)', 'Q4 (16-Dec..15-Mar)', 'Q5 (16-Mar..31-Mar)')
    # Group by Section F row (sorted by the leading "Row N").
    $bySF = $rows | Group-Object SectionF | Sort-Object { $m = [regex]::Match($_.Name, '\d+'); if ($m.Success) { [int]$m.Value } else { 99 } }
    $sb = New-Object System.Text.StringBuilder
    [void]$sb.AppendLine('| Section F row | ' + ($qCols -join ' | ') + ' | Total |')
    [void]$sb.AppendLine('|' + ('---|' * ($qCols.Count + 2)))
    foreach ($grp in $bySF) {
        $cells = foreach ($q in $qCols) {
            $sum = ($grp.Group | Where-Object { $_.Quarter -eq $q } | Measure-Object -Property Gain -Sum).Sum
            if ($sum) { [math]::Round($sum) } else { 0 }
        }
        $total = ($grp.Group | Measure-Object -Property Gain -Sum).Sum
        [void]$sb.AppendLine('| ' + $grp.Name + ' | ' + ($cells -join ' | ') + ' | ' + [math]::Round($total) + ' |')
    }
    return $sb.ToString()
}

# Pivot the other_sources_234c rows into the OS accrual/receipt grid:
# one row per income item, one column per quarter (Q1..Q5), + Total and Source.
function OS-Grid($rows) {
    $rows = @($rows)
    if (-not $rows -or $rows.Count -eq 0) { return $null }
    $qCols = @('Q1 (<=15-Jun)', 'Q2 (16-Jun..15-Sep)', 'Q3 (16-Sep..15-Dec)', 'Q4 (16-Dec..15-Mar)', 'Q5 (16-Mar..31-Mar)')
    $sb = New-Object System.Text.StringBuilder
    [void]$sb.AppendLine('| OS item | ' + ($qCols -join ' | ') + ' | Total | Source |')
    [void]$sb.AppendLine('|' + ('---|' * ($qCols.Count + 3)))
    foreach ($grp in ($rows | Group-Object Item)) {
        $cells = foreach ($q in $qCols) {
            $sum = ($grp.Group | Where-Object { $_.Quarter -eq $q } | Measure-Object -Property Amount -Sum).Sum
            if ($sum) { [math]::Round($sum) } else { 0 }
        }
        $total = ($grp.Group | Measure-Object -Property Amount -Sum).Sum
        $src = ($grp.Group | Select-Object -First 1).Source
        [void]$sb.AppendLine('| ' + $grp.Name + ' | ' + ($cells -join ' | ') + ' | ' + [math]::Round($total) + ' | ' + $src + ' |')
    }
    return $sb.ToString()
}
. "$scripts\schedules\_common.ps1"
function PropOr($obj, $name, $default) { if ($obj.PSObject.Properties.Name -contains $name) { return $obj.$name } else { return $default } }
$pan = PropOr $in 'pan' ''
$name = PropOr $in 'taxpayer' ''
$ay = PropOr $in 'ay' ''
Merge-Return $OutDir 'meta' ([pscustomobject]@{ taxpayer = $name; pan = $pan; ay = $ay; regime = $Regime.ToUpper() }) | Out-Null

# Re-read the fully populated return.json and render.
$doc = Get-Content $returnJson -Raw | ConvertFrom-Json

$md = New-Object System.Text.StringBuilder
[void]$md.AppendLine("# ITR-2 data-entry sheet")
[void]$md.AppendLine("")
[void]$md.AppendLine("- Taxpayer: $name")
[void]$md.AppendLine("- PAN: $pan")
[void]$md.AppendLine("- AY: $ay")
[void]$md.AppendLine("- Regime: **$($Regime.ToUpper())** (recommended)")
[void]$md.AppendLine("")

# Each entry: heading level ('##' top-level schedule, '###' sub-section), title, return.json key.
$sections = @(
    @('##', 'Schedule S — Salary', 'salary'),
    @('##', 'Schedule HP — House Property', 'house_property'),
    @('##', 'Schedule CG — Capital Gains', $null),
    @('###', 'Head aggregates', 'capital_gains_head'),
    @('###', '234C quarterly split (by head)', 'capital_gains_234c'),
    @('##', 'Schedule OS — Other Sources', 'other_sources'),
    @('##', 'Schedule VI-A — Deductions', 'deductions'),
    @('##', 'Part B-TI / TTI — Tax computation & regime comparison', 'tax_computation')
)
foreach ($s in $sections) {
    $level = $s[0]; $title = $s[1]; $key = $s[2]
    # A heading-only group row (no key) — emit only if a child section has data.
    if (-not $key) {
        if ($title -like 'Schedule CG*' -and -not ($doc.PSObject.Properties.Name -contains 'capital_gains_head' -or $doc.PSObject.Properties.Name -contains 'capital_gains_234c')) { continue }
        [void]$md.AppendLine("$level $title"); [void]$md.AppendLine(""); continue
    }
    if (-not ($doc.PSObject.Properties.Name -contains $key)) { continue }
    $tbl = Rows-ToMdTable $doc.$key
    if ($null -eq $tbl) { continue }
    [void]$md.AppendLine("$level $title")
    [void]$md.AppendLine("")
    [void]$md.AppendLine($tbl)
    # For the 234C split, also emit the utility's Section F grid (rows x quarters).
    if ($key -eq 'capital_gains_234c') {
        $grid = SectionF-Grid $doc.$key
        if ($grid) {
            [void]$md.AppendLine("### Section F — as the utility grid (enter these cells)")
            [void]$md.AppendLine("")
            [void]$md.AppendLine($grid)
            [void]$md.AppendLine("_Each row must sum to that head's annual gain; the utility rejects negatives (net a loss-quarter into a later positive one)._")
            [void]$md.AppendLine("")
        }
    }
    # After Schedule OS, emit its 234C accrual/receipt grid if a split was supplied.
    if ($key -eq 'other_sources' -and ($doc.PSObject.Properties.Name -contains 'other_sources_234c')) {
        $osGrid = OS-Grid $doc.other_sources_234c
        if ($osGrid) {
            [void]$md.AppendLine("### 234C accrual/receipt grid (enter these cells)")
            [void]$md.AppendLine("")
            [void]$md.AppendLine($osGrid)
            [void]$md.AppendLine("_Split OS income by the quarter each amount was credited; each row must sum to that item's annual total. Dividend goes in row 3a (Sl.no. 1a(i))._")
            [void]$md.AppendLine("")
        }
    }
}
[void]$md.AppendLine("---")
[void]$md.AppendLine("_Verify all figures against AIS/TIS and the utility before filing. Rates are AY-specific._")

$mdPath = Join-Path $OutDir 'ITR2_data_entry.md'
Set-Content -Path $mdPath -Value $md.ToString() -Encoding UTF8
Write-Host ""
Write-Host ("Wrote combined sheet: {0}" -f $mdPath) -ForegroundColor Green
