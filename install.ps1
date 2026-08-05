param(
  [ValidateSet("claude","codex","project-claude","project-codex","cli","all")]
  [string]$Target = "all",
  [string]$ProjectRoot = (Get-Location).Path,
  [string]$Python = "python"
)
$ErrorActionPreference = "Stop"
$RepoRoot = $PSScriptRoot

function Install-Skills([string]$SkillTarget) {
  & (Join-Path $RepoRoot "adapters\install-skills.ps1") -Target $SkillTarget -ProjectRoot $ProjectRoot
}

function Install-Cli {
  $Venv = Join-Path $RepoRoot ".venv"
  if (-not (Test-Path $Venv)) { & $Python -m venv $Venv }
  $Py = Join-Path $Venv "Scripts\python.exe"
  & $Py -m pip install --upgrade pip
  & $Py -m pip install -e "$RepoRoot[mcp]"
  & $Py -m ai_image_studio.cli doctor
  Write-Host "CLI instalada en $Venv"
}

switch ($Target) {
  "claude" { Install-Skills "claude" }
  "codex" { Install-Skills "codex" }
  "project-claude" { Install-Skills "project-claude" }
  "project-codex" { Install-Skills "project-codex" }
  "cli" { Install-Cli }
  "all" {
    Install-Cli
    Install-Skills "claude"
    Install-Skills "codex"
  }
}
