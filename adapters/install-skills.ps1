<#
.SYNOPSIS
Instala las skills de AI Image Studio en el directorio de skills de un agente.

.DESCRIPTION
Por defecto NO sustituye skills existentes: si detecta alguna con el mismo nombre se
detiene sin escribir nada y explica que usar -Force. Con -Force sustituye, pero antes
guarda una copia de seguridad completa de lo reemplazado.

.PARAMETER Target
Destino: claude, codex, project-claude o project-codex.

.PARAMETER ProjectRoot
Raiz del proyecto para los destinos project-*. Por defecto, el directorio actual.

.PARAMETER Force
Sustituye las skills existentes. Sin este parametro no se sobrescribe nada.

.PARAMETER NoBackup
Omite la copia de seguridad al sustituir. Solo tiene efecto junto con -Force.

.PARAMETER BackupRoot
Directorio donde guardar las copias. Por defecto <destino>\.ai-image-studio-backup.

.EXAMPLE
powershell -ExecutionPolicy Bypass -File adapters\install-skills.ps1 -Target claude

.EXAMPLE
powershell -ExecutionPolicy Bypass -File adapters\install-skills.ps1 -Target claude -WhatIf

.EXAMPLE
powershell -ExecutionPolicy Bypass -File adapters\install-skills.ps1 -Target claude -Force

.NOTES
Codigos de salida, identicos a los de install-skills.sh:
  0  correcto (o nada que hacer)
  2  argumentos invalidos
  3  conflicto: ya existen skills y no se indico -Force
  4  error de entrada/salida al copiar o al respaldar

El destino se valida dentro del script, no con [ValidateSet], a proposito: el
validador de parametros de PowerShell aborta antes de ejecutar el cuerpo y devuelve
1, lo que romperia la paridad con la version Bash. El conjunto permitido se sigue
ofreciendo en el autocompletado.
#>
[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'Medium')]
param(
  [ArgumentCompleter({ "claude", "codex", "project-claude", "project-codex" })]
  [string]$Target,

  [string]$ProjectRoot = (Get-Location).Path,

  [switch]$Force,

  [switch]$NoBackup,

  [string]$BackupRoot
)

$ErrorActionPreference = "Stop"

$EXIT_OK = 0
$EXIT_BAD_ARGS = 2
$EXIT_CONFLICT = 3
$EXIT_IO = 4

# Con $ErrorActionPreference = "Stop", Write-Error lanza un error terminante y el
# script muere ANTES de llegar a su `exit`, devolviendo siempre 1. Los codigos 2 y 4
# quedaban asi inalcanzables. Se escribe a stderr sin lanzar nada.
function Write-Fallo([string]$Mensaje) {
  [Console]::Error.WriteLine("error: $Mensaje")
}

$VALID_TARGETS = @("claude", "codex", "project-claude", "project-codex")

if ([string]::IsNullOrWhiteSpace($Target)) {
  Write-Fallo "falta -Target. Destinos validos: $($VALID_TARGETS -join ', ')"
  exit $EXIT_BAD_ARGS
}
if ($VALID_TARGETS -notcontains $Target) {
  Write-Fallo "destino no valido: '$Target'. Destinos validos: $($VALID_TARGETS -join ', ')"
  exit $EXIT_BAD_ARGS
}

$RepoRoot = Split-Path -Parent $PSScriptRoot
$Source = Join-Path $RepoRoot "skills"

if (-not (Test-Path -LiteralPath $Source)) {
  Write-Fallo "no se encuentra el directorio de skills: $Source"
  exit $EXIT_BAD_ARGS
}

switch ($Target) {
  "claude" { $Destination = Join-Path $HOME ".claude\skills" }
  "codex" { $Destination = Join-Path $HOME ".agents\skills" }
  "project-claude" { $Destination = Join-Path $ProjectRoot ".claude\skills" }
  "project-codex" { $Destination = Join-Path $ProjectRoot ".agents\skills" }
}

$Skills = @(Get-ChildItem -LiteralPath $Source -Directory | Sort-Object Name)
if ($Skills.Count -eq 0) {
  Write-Fallo "no hay skills que instalar en $Source"
  exit $EXIT_BAD_ARGS
}

# ---------------------------------------------------------------- analisis previo
$New = @()
$Existing = @()
foreach ($skill in $Skills) {
  $candidate = Join-Path $Destination $skill.Name
  if (Test-Path -LiteralPath $candidate) { $Existing += $skill } else { $New += $skill }
}

Write-Host "Origen  : $Source"
Write-Host "Destino : $Destination"
Write-Host "Skills  : $($Skills.Count) detectadas -> $($New.Count) nuevas, $($Existing.Count) ya existentes"
foreach ($skill in $New) { Write-Host "  [nueva]     $($skill.Name)" }
foreach ($skill in $Existing) { Write-Host "  [existente] $($skill.Name)" }

# ---------------------------------------------------------------- puerta de seguridad
if ($Existing.Count -gt 0 -and -not $Force) {
  Write-Host ""
  Write-Warning "Se han encontrado $($Existing.Count) skills ya instaladas. No se ha modificado nada."
  Write-Host "Para sustituirlas, vuelve a ejecutar el comando con -Force:"
  Write-Host "  ... -Target $Target -Force"
  Write-Host "Se guardara una copia de seguridad antes de sustituir (usa -NoBackup para omitirla)."
  exit $EXIT_CONFLICT
}

if ($Skills.Count -eq 0) { exit $EXIT_OK }

# ---------------------------------------------------------------- copia de seguridad
$BackupDir = $null
if ($Existing.Count -gt 0 -and -not $NoBackup) {
  $root = if ($BackupRoot) { $BackupRoot } else { Join-Path $Destination ".ai-image-studio-backup" }
  $BackupDir = Join-Path $root (Get-Date -Format "yyyyMMdd-HHmmss")
  if ($PSCmdlet.ShouldProcess($BackupDir, "Crear copia de seguridad de $($Existing.Count) skills")) {
    try {
      New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
      foreach ($skill in $Existing) {
        Copy-Item -Recurse -Force -LiteralPath (Join-Path $Destination $skill.Name) `
          -Destination (Join-Path $BackupDir $skill.Name)
      }
      Write-Host "Copia de seguridad creada en: $BackupDir"
    }
    catch {
      Write-Fallo "no se pudo crear la copia de seguridad: $_"
      exit $EXIT_IO
    }
  }
}

# ---------------------------------------------------------------- instalacion
try {
  if ($PSCmdlet.ShouldProcess($Destination, "Crear directorio de destino")) {
    New-Item -ItemType Directory -Force -Path $Destination | Out-Null
  }
  $installed = 0
  foreach ($skill in $Skills) {
    $dest = Join-Path $Destination $skill.Name
    $verb = if (Test-Path -LiteralPath $dest) { "Sustituir" } else { "Instalar" }
    if ($PSCmdlet.ShouldProcess($dest, "$verb skill $($skill.Name)")) {
      if (Test-Path -LiteralPath $dest) { Remove-Item -Recurse -Force -LiteralPath $dest }
      Copy-Item -Recurse -Force -LiteralPath $skill.FullName -Destination $dest
      $installed++
    }
  }
}
catch {
  Write-Fallo "fallo al instalar las skills: $_"
  if ($BackupDir) { Write-Host "Puedes restaurar el estado anterior desde: $BackupDir" }
  exit $EXIT_IO
}

if ($WhatIfPreference) {
  Write-Host ""
  Write-Host "Simulacion (-WhatIf): no se ha escrito nada."
  exit $EXIT_OK
}

Write-Host ""
Write-Host "$installed skills instaladas en: $Destination"
if ($BackupDir) {
  Write-Host "Rollback: borra las skills instaladas y copia de vuelta el contenido de $BackupDir"
}
exit $EXIT_OK
