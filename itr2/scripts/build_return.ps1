# Orchestrator: runs every per-schedule emitter against a shared tax_input.json,
# then stitches all the section CSVs into one Markdown data-entry sheet.
#
# It runs (when the relevant input is present):
#   schedules/schedule_s.ps1     -> schedule_s.csv     (Salary)
#   schedules/schedule_hp.ps1    -> schedule_hp.csv    (House Property)
#   schedules/schedule_os.ps1    -> schedule_os.csv    (Other Sources)
#   schedules/schedule_via.ps1   -> schedule_via.csv   (Deductions)
#   schedules/schedule_112a.ps1  -> Schedule112A.csv   (uploadable 112A, if present)
#   schedules/schedule_cg.ps1    -> cg_head_aggregates.csv, cg_234c_split.csv
#   compute_tax.ps1              -> tax_regime_comparison.csv (Part B-TI/TTI + regime)
# then writes ITR2_data_entry.md combining them all.
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
$taxCsv = Join-Path $OutDir 'tax_regime_comparison.csv'
$tax = Import-Csv $taxCsv
if (-not $Regime) {
    $rec = ($tax | Where-Object LineItem -eq 'Recommended regime').NEW
    $Regime = if ($rec -eq 'OLD') { 'old' } else { 'new' }
}
Write-Host "Using regime: $Regime" -ForegroundColor Cyan

# 2. Per-schedule emitters.
& "$scripts\schedules\schedule_s.ps1"   -InputJson $InputJson -Regime $Regime -OutDir $OutDir | Out-Null
& "$scripts\schedules\schedule_hp.ps1"  -InputJson $InputJson -OutDir $OutDir | Out-Null
& "$scripts\schedules\schedule_os.ps1"  -InputJson $InputJson -OutDir $OutDir | Out-Null
& "$scripts\schedules\schedule_via.ps1" -InputJson $InputJson -Regime $Regime -OutDir $OutDir | Out-Null
& "$scripts\schedules\schedule_112a.ps1" -InputJson $InputJson -OutDir $OutDir | Out-Null
if ($TradewiseCsv) { & "$scripts\schedules\schedule_cg.ps1" -Path $TradewiseCsv -OutDir $OutDir | Out-Null }
else { & "$scripts\schedules\schedule_cg.ps1" -InputJson $InputJson -OutDir $OutDir | Out-Null }

# 3. Stitch the CSVs into one MD.
function Csv-ToMdTable([string]$path) {
    if (-not (Test-Path $path)) { return $null }
    $rows = Import-Csv $path
    if (-not $rows) { return $null }
    $cols = $rows[0].PSObject.Properties.Name
    $sb = New-Object System.Text.StringBuilder
    [void]$sb.AppendLine('| ' + ($cols -join ' | ') + ' |')
    [void]$sb.AppendLine('|' + (($cols | ForEach-Object { '---' }) -join '|') + '|')
    foreach ($r in $rows) {
        $vals = $cols | ForEach-Object { $r.$_ }
        [void]$sb.AppendLine('| ' + ($vals -join ' | ') + ' |')
    }
    return $sb.ToString()
}

$md = New-Object System.Text.StringBuilder
function PropOr($obj, $name, $default) { if ($obj.PSObject.Properties.Name -contains $name) { return $obj.$name } else { return $default } }
$pan = PropOr $in 'pan' ''
$name = PropOr $in 'taxpayer' ''
$ay = PropOr $in 'ay' ''
[void]$md.AppendLine("# ITR-2 data-entry sheet")
[void]$md.AppendLine("")
[void]$md.AppendLine("- Taxpayer: $name")
[void]$md.AppendLine("- PAN: $pan")
[void]$md.AppendLine("- AY: $ay")
[void]$md.AppendLine("- Regime: **$($Regime.ToUpper())** (recommended)")
[void]$md.AppendLine("")

$sections = @(
    @('Schedule S — Salary', 'schedule_s.csv'),
    @('Schedule HP — House Property', 'schedule_hp.csv'),
    @('Schedule CG — Capital Gains (head aggregates)', 'cg_head_aggregates.csv'),
    @('Schedule CG — 234C quarterly split', 'cg_234c_split.csv'),
    @('Schedule OS — Other Sources', 'schedule_os.csv'),
    @('Schedule VI-A — Deductions', 'schedule_via.csv'),
    @('Part B-TI / TTI — Tax computation & regime comparison', 'tax_regime_comparison.csv')
)
foreach ($s in $sections) {
    $tbl = Csv-ToMdTable (Join-Path $OutDir $s[1])
    if ($null -eq $tbl) { continue }
    [void]$md.AppendLine("## $($s[0])")
    [void]$md.AppendLine("")
    [void]$md.AppendLine($tbl)
}
[void]$md.AppendLine("---")
[void]$md.AppendLine("_Verify all figures against AIS/TIS and the utility before filing. Rates are AY-specific._")

$mdPath = Join-Path $OutDir 'ITR2_data_entry.md'
Set-Content -Path $mdPath -Value $md.ToString() -Encoding UTF8
Write-Host ""
Write-Host ("Wrote combined sheet: {0}" -f $mdPath) -ForegroundColor Green
