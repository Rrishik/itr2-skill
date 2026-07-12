# Builds an uploadable Schedule 112A CSV using the user's downloaded template header
# VERBATIM (preserves non-breaking spaces), no BOM, CRLF line endings.
#
# Produces a single CONSOLIDATED "AE" row (all lots acquired after 31-Jan-2018),
# which is the safe default: it avoids per-lot minus signs (forbidden characters)
# and blank-ISIN issues. For BE lots (acquired on/before 31-Jan-2018) you must add
# per-scrip rows with grandfathered FMV — see references/112a-csv.md.
#
# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File build_112a_csv.ps1 `
#       -TemplatePath "<downloaded template>.csv" -OutPath "Schedule112A.csv" `
#       -FullValue 3034631 -CostOfAcquisition 2156842 -Expenditure 0
#
# Balance (LTCG) is computed as FullValue - (CostOfAcquisition + Expenditure).
param(
    [Parameter(Mandatory)][string]$TemplatePath,
    [Parameter(Mandatory)][string]$OutPath,
    [Parameter(Mandatory)][long]$FullValue,
    [Parameter(Mandatory)][long]$CostOfAcquisition,
    [long]$Expenditure = 0
)

$tPath = (Resolve-Path $TemplatePath).Path
$headerText = [System.IO.File]::ReadAllText($tPath)   # exact header bytes incl. non-breaking spaces

$totalDed = $CostOfAcquisition + $Expenditure
$balance  = $FullValue - $totalDed

# AE => cols 4,5 (qty/price) and 9,10,11 (grandfathering) blank; ISIN=INNOTREQUIRD; Name=CONSOLIDATED
$row = "AE,INNOTREQUIRD,CONSOLIDATED,,,$FullValue,$CostOfAcquisition,$CostOfAcquisition,,,,$Expenditure,$totalDed,$balance,"

$sb = New-Object System.Text.StringBuilder
[void]$sb.Append($headerText)
[void]$sb.Append("`r`n")
[void]$sb.Append($row)

if ([System.IO.Path]::IsPathRooted($OutPath)) { $outPathFull = $OutPath }
else { $outPathFull = (Join-Path (Get-Location).Path $OutPath) }
$enc = New-Object System.Text.UTF8Encoding($false)    # no BOM
[System.IO.File]::WriteAllText($outPathFull, $sb.ToString(), $enc)

# Verify header is byte-identical to template
$f = [System.IO.File]::ReadAllBytes($outPathFull)
$t = [System.IO.File]::ReadAllBytes($tPath)
$idx = [Array]::IndexOf($f, [byte]13)
$ok = $true
for ($i = 0; $i -lt $t.Length; $i++) { if ($t[$i] -ne $f[$i]) { $ok = $false; break } }
Write-Output "Header byte-identical to template: $ok"
Write-Output "Row: $row"
Write-Output "Balance (LTCG) = $balance"
