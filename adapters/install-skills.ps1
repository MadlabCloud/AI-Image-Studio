param(
  [Parameter(Mandatory=$true)]
  [ValidateSet("claude","codex","project-claude","project-codex")]
  [string]$Target,
  [string]$ProjectRoot = (Get-Location).Path
)
$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Source = Join-Path $RepoRoot "skills"
switch ($Target) {
  "claude" { $Destination = Join-Path $HOME ".claude\skills" }
  "codex" { $Destination = Join-Path $HOME ".agents\skills" }
  "project-claude" { $Destination = Join-Path $ProjectRoot ".claude\skills" }
  "project-codex" { $Destination = Join-Path $ProjectRoot ".agents\skills" }
}
New-Item -ItemType Directory -Force -Path $Destination | Out-Null
Get-ChildItem $Source -Directory | ForEach-Object {
  $dest = Join-Path $Destination $_.Name
  if (Test-Path $dest) { Remove-Item -Recurse -Force $dest }
  Copy-Item -Recurse -Force $_.FullName $dest
}
Write-Host "Skills instaladas en: $Destination"
