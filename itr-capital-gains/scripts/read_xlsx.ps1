# Reads an .xlsx file (even with the extension stripped) and prints every sheet's
# rows as "A1=val | B1=val | ...", resolving shared strings. No Excel/Python needed.
#
# Usage:  powershell -NoProfile -ExecutionPolicy Bypass -File read_xlsx.ps1 -Path "<file>"
param([Parameter(Mandatory)][string]$Path)

Add-Type -AssemblyName System.IO.Compression.FileSystem | Out-Null

$full = (Resolve-Path $Path).Path
$zip = [System.IO.Compression.ZipFile]::OpenRead($full)
try {
    $shared = @()
    $ss = $zip.Entries | Where-Object { $_.FullName -eq 'xl/sharedStrings.xml' }
    if ($ss) {
        $sr = New-Object System.IO.StreamReader($ss.Open())
        $xml = [xml]$sr.ReadToEnd(); $sr.Close()
        foreach ($si in $xml.sst.si) {
            if ($si.t -is [string]) { $shared += $si.t }
            elseif ($si.t.'#text') { $shared += $si.t.'#text' }
            else { $shared += (($si.r | ForEach-Object { $_.t.'#text' }) -join '') }
        }
    }
    $sheets = $zip.Entries | Where-Object { $_.FullName -match '^xl/worksheets/sheet\d+\.xml$' } | Sort-Object FullName
    foreach ($sheet in $sheets) {
        Write-Output "===== $($sheet.FullName) ====="
        $sr = New-Object System.IO.StreamReader($sheet.Open())
        $xml = [xml]$sr.ReadToEnd(); $sr.Close()
        foreach ($row in $xml.worksheet.sheetData.row) {
            $cells = @()
            foreach ($c in $row.c) {
                $v = $c.v
                if ($c.t -eq 's' -and $null -ne $v) { $v = $shared[[int]$v] }
                $cells += "$($c.r)=$v"
            }
            if ($cells.Count) { Write-Output ($cells -join ' | ') }
        }
    }
} finally { $zip.Dispose() }
