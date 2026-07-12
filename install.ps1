<#
  Install the itr2 skill into the chosen agent's skills directory.
  Usage: .\install.ps1 [copilot|claude|copilot-cli]   (default: copilot)
#>
param([ValidateSet('copilot','claude','copilot-cli')][string]$Target = 'copilot')

$dest = switch ($Target) {
  'copilot'     { Join-Path $env:USERPROFILE '.agents\skills' }
  'claude'      { Join-Path $env:USERPROFILE '.claude\skills' }
  'copilot-cli' { Join-Path $env:USERPROFILE '.copilot\skills' }
}

$src = Join-Path $PSScriptRoot 'itr2'
New-Item -ItemType Directory -Force -Path $dest | Out-Null
Copy-Item $src -Destination $dest -Recurse -Force
Write-Host "Installed itr2 -> $dest\itr2"
Write-Host "Reload your agent to pick up the skill."
