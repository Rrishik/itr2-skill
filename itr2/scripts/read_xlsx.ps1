# Reads an .xlsx file (even with the extension stripped) and prints every sheet's
# rows as "A1=val | B1=val | ...", resolving shared strings. No Excel/Python needed
# for ZIP-based .xlsx. Legacy OLE .xls (magic D0 CF 11 E0) is not a ZIP; when one is
# detected the script falls back to Excel COM (if Excel is installed) to dump rows.
#
# Usage:  powershell -NoProfile -ExecutionPolicy Bypass -File read_xlsx.ps1 -Path "<file>"
param([Parameter(Mandatory)][string]$Path)

Add-Type -AssemblyName System.IO.Compression.FileSystem | Out-Null

$full = (Resolve-Path $Path).Path

# Detect legacy OLE .xls (D0 CF 11 E0) vs ZIP xlsx (50 4B) by magic bytes.
$sig = [System.IO.File]::ReadAllBytes($full) | Select-Object -First 4
$isOle = ($sig.Count -ge 4 -and $sig[0] -eq 0xD0 -and $sig[1] -eq 0xCF -and $sig[2] -eq 0x11 -and $sig[3] -eq 0xE0)

if ($isOle) {
    # ZipFile can't read OLE; use Excel COM if available.
    try { $excel = New-Object -ComObject Excel.Application }
    catch { Write-Error "Legacy OLE .xls detected but Excel COM is unavailable. Open in Excel and re-save as .xlsx or .csv, then retry."; exit 1 }
    $excel.Visible = $false; $excel.DisplayAlerts = $false
    try {
        $wb = $excel.Workbooks.Open($full, $false, $true)  # UpdateLinks=0, ReadOnly=$true
        foreach ($ws in $wb.Worksheets) {
            Write-Output "===== $($ws.Name) ====="
            $used = $ws.UsedRange
            $rows = $used.Rows.Count; $cols = $used.Columns.Count
            $data = $used.Value2
            for ($r = 1; $r -le $rows; $r++) {
                $cells = @()
                for ($c = 1; $c -le $cols; $c++) {
                    $v = if ($rows -eq 1 -and $cols -eq 1) { $data } else { $data.GetValue($r, $c) }
                    if ($null -ne $v) { $cells += "R${r}C${c}=$v" }
                }
                if ($cells.Count) { Write-Output ($cells -join ' | ') }
            }
        }
        $wb.Close($false)
    } finally {
        $excel.Quit()
        [System.Runtime.InteropServices.Marshal]::ReleaseComObject($excel) | Out-Null
    }
    return
}

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
