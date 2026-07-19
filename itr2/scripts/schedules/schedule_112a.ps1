# Schedule 112A emitter. Reads tax_input.json and builds the uploadable
# Schedule 112A CSV using the user's downloaded template header VERBATIM
# (preserves non-breaking spaces), no BOM, CRLF line endings.
#
# Produces a single CONSOLIDATED "AE" row (all lots acquired after 31-Jan-2018),
# the safe default: avoids per-lot minus signs (forbidden characters) and
# blank-ISIN issues. For BE lots (acquired on/before 31-Jan-2018) add per-scrip
# rows with grandfathered FMV — see references/112a-csv.md.
#
# tax_input.json block (all in INR):
#   "schedule_112a": {
#      "template_path": "<downloaded 112A template>.csv",
#      "full_value": 3034631, "cost": 2156842, "expenditure": 0
#   }
# template_path / OutPath may be overridden by params. Balance (LTCG) =
# full_value - (cost + expenditure). Self-skips when the block is absent.
#
# Usage:
#   powershell -File schedule_112a.ps1 -InputJson tax_input.json -OutDir .\out `
#       [-TemplatePath tpl.csv]
param(
    [Parameter(Mandatory)][string]$InputJson,
    [string]$OutDir,
    [string]$TemplatePath
)
. "$PSScriptRoot\_common.ps1"
$in = Read-Input $InputJson
$blk = Prop $in 'schedule_112a'

if ($null -eq $blk) {
    Write-Host "No schedule_112a block; Schedule 112A CSV not required (no listed-equity LTCG)." -ForegroundColor DarkGray
    return
}

$tpl = if ($TemplatePath) { $TemplatePath } else { Prop $blk 'template_path' }
if (-not $tpl) { Write-Error "schedule_112a needs a template_path (downloaded 112A CSV template) or -TemplatePath."; return }
$tPath = (Resolve-Path $tpl).Path

$fullValue = [long](Num (Prop $blk 'full_value'))
$cost = [long](Num (Prop $blk 'cost'))
$expenditure = [long](Num (Prop $blk 'expenditure'))
$totalDed = $cost + $expenditure
$balance = $fullValue - $totalDed

$headerText = [System.IO.File]::ReadAllText($tPath)   # exact header bytes incl. non-breaking spaces
# AE => cols 4,5 (qty/price) and 9,10,11 (grandfathering) blank; ISIN=INNOTREQUIRD; Name=CONSOLIDATED
$row = "AE,INNOTREQUIRD,CONSOLIDATED,,,$fullValue,$cost,$cost,,,,$expenditure,$totalDed,$balance,"

$sb = New-Object System.Text.StringBuilder
[void]$sb.Append($headerText); [void]$sb.Append("`r`n"); [void]$sb.Append($row)

if (-not $OutDir) { $OutDir = '.' }
if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir | Out-Null }
$OutDir = (Resolve-Path $OutDir).Path
$outPathFull = Join-Path $OutDir 'Schedule112A.csv'
$enc = New-Object System.Text.UTF8Encoding($false)    # no BOM
[System.IO.File]::WriteAllText($outPathFull, $sb.ToString(), $enc)

# Verify header is byte-identical to template.
$f = [System.IO.File]::ReadAllBytes($outPathFull)
$t = [System.IO.File]::ReadAllBytes($tPath)
$ok = $true
for ($i = 0; $i -lt $t.Length; $i++) { if ($t[$i] -ne $f[$i]) { $ok = $false; break } }

Write-Host ""
Write-Host "=== Schedule 112A CSV ===" -ForegroundColor Cyan
Write-Host "Header byte-identical to template: $ok"
Write-Host "Row: $row"
Write-Host "Balance (LTCG) = $balance"
Write-Host ("Wrote: {0}" -f $outPathFull) -ForegroundColor Green
