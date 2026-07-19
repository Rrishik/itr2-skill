# Shared helpers for the per-schedule emitters. Dot-source this.
#   . "$PSScriptRoot\_common.ps1"
# Each schedule_*.ps1 reads the shared tax_input.json (single source of truth)
# and writes schedule_<x>.csv as Field,Value rows into -OutDir.

function Read-Input([string]$InputJson) {
    $full = (Resolve-Path $InputJson).Path
    return (Get-Content $full -Raw | ConvertFrom-Json)
}
function Num($v) { if ($null -eq $v) { return 0.0 } else { return [double]$v } }
function Prop($obj, $name) {
    if ($obj -and ($obj.PSObject.Properties.Name -contains $name)) { return $obj.$name } else { return $null }
}
function Write-Section([object[]]$rows, [string]$OutDir, [string]$fileName) {
    if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir | Out-Null }
    $OutDir = (Resolve-Path $OutDir).Path
    $path = Join-Path $OutDir $fileName
    $rows | Export-Csv -Path $path -NoTypeInformation
    Write-Host ("Wrote: {0}" -f $path) -ForegroundColor Green
    return $path
}
function Show-Section([string]$title, [object[]]$rows) {
    Write-Host ""
    Write-Host "=== $title ===" -ForegroundColor Cyan
    $rows | Format-Table -AutoSize | Out-String | Write-Host
}
