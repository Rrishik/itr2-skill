<#
  Install the ITR skills (itr umbrella + itr2) into the chosen agent's skills directory.
  Usage: .\install.ps1 [copilot|claude|copilot-cli]   (default: copilot)
#>
param([ValidateSet('copilot','claude','copilot-cli')][string]$Target = 'copilot')

$dest = switch ($Target) {
  'copilot'     { Join-Path $env:USERPROFILE '.agents\skills' }
  'claude'      { Join-Path $env:USERPROFILE '.claude\skills' }
  'copilot-cli' { Join-Path $env:USERPROFILE '.copilot\skills' }
}

New-Item -ItemType Directory -Force -Path $dest | Out-Null
foreach ($skill in 'itr', 'itr2') {
  Copy-Item (Join-Path $PSScriptRoot $skill) -Destination $dest -Recurse -Force
  Write-Host "Installed $skill -> $dest\$skill"
}
Write-Host "Reload your agent to pick up the skills."
