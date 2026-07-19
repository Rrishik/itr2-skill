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
        [pscustomobject]@{ Field = 'Annual value (rent received)'; Value = [math]::Round($rent); Source = 'Rent receipts / lease agreement'; Where = 'Schedule HP: 1a annual value' }
        [pscustomobject]@{ Field = 'Less: municipal taxes'; Value = [math]::Round($municipal); Source = 'Municipal tax receipts'; Where = 'Schedule HP: 1b municipal taxes paid' }
        [pscustomobject]@{ Field = 'Net annual value'; Value = [math]::Round($nav); Source = 'Computed (rent - municipal)'; Where = 'Schedule HP: 1c (auto)' }
        [pscustomobject]@{ Field = 'Less: 30% standard deduction'; Value = $stdDed; Source = 'Statutory (auto, 30% of NAV)'; Where = 'Schedule HP: 1d 30% u/s 24(a)' }
        [pscustomobject]@{ Field = 'Less: home-loan interest'; Value = [math]::Round($interest); Source = 'Home-loan interest certificate (lender)'; Where = 'Schedule HP: 1e interest u/s 24(b)' }
        [pscustomobject]@{ Field = 'Income from house property'; Value = [math]::Round($income); Source = 'Computed'; Where = 'Schedule HP: 1f -> Part B-TI item 2' }
    )
} else {
    $rows = @([pscustomobject]@{ Field = 'Income from house property (net)'; Value = [math]::Round((Num $hpNet)); Source = 'tax_input.json house_property (pre-computed net)'; Where = 'Schedule HP: 1f -> Part B-TI item 2' })
}
Show-Section 'Schedule HP — House Property' $rows
if ($OutDir) { Merge-Return $OutDir 'house_property' $rows | Out-Null }
