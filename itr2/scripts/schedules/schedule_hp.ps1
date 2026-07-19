# Schedule HP (House Property) emitter. Reads tax_input.json, writes schedule_hp.csv.
# Net annual value less 30% standard deduction less home-loan interest. The set-off
# of house-property loss against other heads is capped at -2,00,000 (applied in
# compute_tax.ps1, not here). Usage:
#   powershell -File schedule_hp.ps1 -InputJson tax_input.json [-OutDir .\out]
param(
    [Parameter(Mandatory)][string]$InputJson,
    [string]$OutDir
)
. "$PSScriptRoot\_common.ps1"
$in = Read-Input $InputJson

$hpObj = Prop $in 'house_property_detail'
$hpNet = Prop $in 'house_property'
if ($null -eq $hpObj -and ($null -eq $hpNet -or (Num $hpNet) -eq 0)) {
    Write-Host "No house-property income/loss; Schedule HP not required (untick it)." -ForegroundColor DarkGray; return
}

if ($hpObj) {
    $rent = Num (Prop $hpObj 'annual_value')
    $municipal = Num (Prop $hpObj 'municipal_tax')
    $nav = [math]::Max(0.0, $rent - $municipal)
    $stdDed = [math]::Round($nav * 0.30)
    $interest = Num (Prop $hpObj 'home_loan_interest')
    $income = $nav - $stdDed - $interest
    $rows = @(
        [pscustomobject]@{ Field = 'Annual value (rent received)'; Value = [math]::Round($rent) }
        [pscustomobject]@{ Field = 'Less: municipal taxes'; Value = [math]::Round($municipal) }
        [pscustomobject]@{ Field = 'Net annual value'; Value = [math]::Round($nav) }
        [pscustomobject]@{ Field = 'Less: 30% standard deduction'; Value = $stdDed }
        [pscustomobject]@{ Field = 'Less: home-loan interest'; Value = [math]::Round($interest) }
        [pscustomobject]@{ Field = 'Income from house property'; Value = [math]::Round($income) }
    )
} else {
    $rows = @([pscustomobject]@{ Field = 'Income from house property (net)'; Value = [math]::Round((Num $hpNet)) })
}
Show-Section 'Schedule HP — House Property' $rows
if ($OutDir) { Write-Section $rows $OutDir 'schedule_hp.csv' | Out-Null }
