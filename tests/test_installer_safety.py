"""Comprueba que el instalador de skills no destruye trabajo del usuario.

Defecto INSTALLER-SKILLS-01 de la validacion v0.5.0: el instalador eliminaba una
skill existente con `Remove-Item -Recurse -Force` / `rm -rf` sin aviso ni respaldo.

Las pruebas de comportamiento usan la version Bash sobre un HOME aislado. La version
PowerShell se comprueba de forma estructural aqui y de forma funcional en CI sobre
`windows-latest`.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SH = ROOT / "adapters/install-skills.sh"
PS1 = ROOT / "adapters/install-skills.ps1"

EXIT_OK, EXIT_BAD_ARGS, EXIT_CONFLICT = 0, 2, 3
SKILL_NAMES = {
    "ai-image-studio-user-guide", "image-export-packager", "image-intake-router",
    "image-quality-gates", "photographer-capture-guide", "product-image-pipeline",
}

bash_only = pytest.mark.skipif(
    os.name == "nt" or shutil.which("bash") is None, reason="requiere bash"
)


@pytest.fixture
def sandbox(tmp_path):
    """Copia del proyecto con el .sh normalizado a LF y un HOME aislado."""
    stage = tmp_path / "pkg"
    (stage / "adapters").mkdir(parents=True)
    shutil.copytree(ROOT / "skills", stage / "skills")
    script = stage / "adapters/install-skills.sh"
    script.write_bytes(SH.read_bytes().replace(b"\r\n", b"\n"))
    script.chmod(0o755)

    home = tmp_path / "home"
    home.mkdir()
    env = dict(os.environ, HOME=str(home))
    return {"script": script, "home": home, "env": env, "project": tmp_path / "proyecto"}


def run(sandbox, *args):
    return subprocess.run(
        ["bash", str(sandbox["script"]), *args],
        capture_output=True, text=True, env=sandbox["env"],
    )


# --------------------------------------------------------------------------- basico

@bash_only
def test_clean_install_places_the_six_skills(sandbox):
    result = run(sandbox, "claude")
    assert result.returncode == EXIT_OK, result.stderr
    dest = sandbox["home"] / ".claude/skills"
    assert {p.name for p in dest.iterdir() if p.is_dir()} == SKILL_NAMES


@bash_only
@pytest.mark.parametrize("target,relative", [
    ("claude", ".claude/skills"),
    ("codex", ".agents/skills"),
])
def test_home_targets(sandbox, target, relative):
    assert run(sandbox, target).returncode == EXIT_OK
    assert (sandbox["home"] / relative / "image-intake-router/SKILL.md").is_file()


@bash_only
@pytest.mark.parametrize("target,relative", [
    ("project-claude", ".claude/skills"),
    ("project-codex", ".agents/skills"),
])
def test_project_targets(sandbox, target, relative):
    project = sandbox["project"]
    project.mkdir(parents=True)
    assert run(sandbox, target, str(project)).returncode == EXIT_OK
    assert (project / relative / "image-intake-router/SKILL.md").is_file()


# --------------------------------------------------------------------- no destructivo

@bash_only
def test_existing_skill_is_never_replaced_silently(sandbox):
    """El nucleo del defecto: sin --force no se puede perder trabajo del usuario."""
    run(sandbox, "claude")
    marker = sandbox["home"] / ".claude/skills/image-intake-router/DEL_USUARIO.txt"
    marker.write_text("contenido que no se debe perder", encoding="utf-8")

    result = run(sandbox, "claude")

    assert result.returncode == EXIT_CONFLICT
    assert marker.is_file(), "el instalador borro contenido del usuario sin --force"
    assert marker.read_text(encoding="utf-8") == "contenido que no se debe perder"
    assert "--force" in (result.stdout + result.stderr)


@bash_only
def test_dry_run_writes_nothing(sandbox):
    result = run(sandbox, "claude", "--dry-run")
    assert result.returncode == EXIT_OK
    assert not (sandbox["home"] / ".claude/skills").exists()
    assert "no se ha escrito nada" in result.stdout


@bash_only
def test_force_replaces_and_creates_a_recoverable_backup(sandbox):
    run(sandbox, "claude")
    dest = sandbox["home"] / ".claude/skills"
    marker = dest / "image-intake-router/DEL_USUARIO.txt"
    marker.write_text("estado anterior", encoding="utf-8")

    result = run(sandbox, "claude", "--force")
    assert result.returncode == EXIT_OK

    backups = sorted((dest / ".ai-image-studio-backup").iterdir())
    assert backups, "--force no creo copia de seguridad"
    saved = backups[-1] / "image-intake-router/DEL_USUARIO.txt"
    assert saved.is_file(), "la copia de seguridad no conserva el contenido sustituido"
    assert saved.read_text(encoding="utf-8") == "estado anterior"
    assert not marker.exists(), "--force deberia haber sustituido la skill"


@bash_only
def test_no_backup_requires_force(sandbox):
    assert run(sandbox, "claude", "--no-backup").returncode == EXIT_BAD_ARGS


@bash_only
@pytest.mark.parametrize("args", [(), ("destino-inventado",), ("claude", "--opcion-rara")])
def test_invalid_arguments_exit_with_code_two(sandbox, args):
    assert run(sandbox, *args).returncode == EXIT_BAD_ARGS


@bash_only
def test_installer_never_touches_paths_outside_the_destination(sandbox):
    outside = sandbox["home"] / "documento-importante.txt"
    outside.write_text("intacto", encoding="utf-8")
    run(sandbox, "claude")
    run(sandbox, "claude", "--force")
    assert outside.read_text(encoding="utf-8") == "intacto"


# --------------------------------------------------------------- paridad PowerShell

def test_powershell_installer_declares_the_same_safety_contract():
    """Comprobacion estructural; el comportamiento se valida en CI sobre Windows."""
    text = PS1.read_text(encoding="utf-8", errors="ignore")
    for token in ("[switch]$Force", "SupportsShouldProcess", "ShouldProcess",
                  "$NoBackup", "BackupRoot", "$VALID_TARGETS"):
        assert token in text, f"install-skills.ps1 no declara '{token}'"
    for code in ("$EXIT_CONFLICT = 3", "$EXIT_BAD_ARGS = 2", "$EXIT_IO = 4"):
        assert code in text, f"install-skills.ps1 no define '{code}'"
    assert "exit $EXIT_CONFLICT" in text, "no hay salida por conflicto sin -Force"


def test_both_installers_reject_an_invalid_target_with_the_same_exit_code():
    """La validacion del destino vive en el cuerpo de los dos instaladores.

    Si el `.ps1` usara [ValidateSet], el validador de parametros de PowerShell
    abortaria antes de ejecutar el script y devolveria 1, mientras que el `.sh`
    devuelve 2 para el mismo error del usuario.
    """
    ps1 = PS1.read_text(encoding="utf-8", errors="ignore")
    # Se inspecciona el codigo, no los comentarios: el encabezado <# .. #> y las notas
    # explican precisamente por que NO se usan [ValidateSet] ni Write-Error, y
    # nombrarlos ahi es documentacion, no uso.
    body = ps1[ps1.index("[CmdletBinding"):]
    code = "\n".join(
        line for line in body.splitlines() if not line.lstrip().startswith("#")
    )

    assert "ValidateSet" not in code, (
        "[ValidateSet] aborta en el binder con codigo 1 y rompe la paridad con install-skills.sh"
    )
    assert "Write-Error" not in code, (
        "Write-Error es terminante con $ErrorActionPreference = 'Stop' y mata el script "
        "antes de su `exit`, dejando inalcanzables los codigos 2 y 4; usa Write-Fallo"
    )
    assert "-notcontains $Target" in code, "el .ps1 no valida el destino en el cuerpo"
    assert code.count("exit $EXIT_BAD_ARGS") >= 2, (
        "faltan las salidas por destino ausente y destino no valido"
    )

    sh = SH.read_text(encoding="utf-8", errors="ignore")
    assert "EXIT_BAD_ARGS=2" in sh, "install-skills.sh no declara el mismo codigo 2"


def test_powershell_installer_has_no_unconditional_destructive_removal():
    """Ninguna eliminacion recursiva puede ejecutarse fuera del camino con -Force."""
    lines = PS1.read_text(encoding="utf-8", errors="ignore").splitlines()
    removals = [
        (i + 1, line) for i, line in enumerate(lines)
        if "Remove-Item" in line and "-Recurse" in line
    ]
    assert removals, "se esperaba al menos una eliminacion controlada"
    guard = next(i for i, line in enumerate(lines, 1) if "exit $EXIT_CONFLICT" in line)
    for number, line in removals:
        assert number > guard, (
            f"linea {number} elimina contenido antes de la puerta de seguridad: {line.strip()}"
        )
