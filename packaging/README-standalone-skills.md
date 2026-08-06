# AI Image Studio — Skills independientes

Este archivo describe **exclusivamente** el contenido del artefacto
`ai-image-studio-standalone-skills-<versión>.zip`.

Repositorio canónico: <https://github.com/MadlabCloud/AI-Image-Studio>

## Propósito

Las seis skills en formato neutro, junto con los instaladores que las copian al
directorio de skills de un agente. Sirve para cualquier agente compatible con el
formato de Agent Skills, sin pasar por un marketplace.

Si usas Claude Code, el paquete `claude-plugin` es más cómodo.
Si usas Codex, usa `codex-marketplace`.
Si necesitas el CLI o el servidor MCP, usa `full`.

## Contenido real

Al extraer el ZIP obtienes un directorio `ai-image-studio/` con:

| Ruta | Contenido |
|---|---|
| `skills/ai-image-studio-user-guide/` | Guía de uso. |
| `skills/image-intake-router/` | Admisión y enrutado de imágenes. |
| `skills/photographer-capture-guide/` | Guía de captura fotográfica. |
| `skills/product-image-pipeline/` | Flujo estricto de imagen de producto. |
| `skills/image-quality-gates/` | Puertas de calidad. |
| `skills/image-export-packager/` | Exportación y empaquetado. |
| `adapters/install-skills.ps1` | Instalador para Windows (PowerShell). |
| `adapters/install-skills.sh` | Instalador para Linux y macOS. |
| `README.md` | Este archivo. |
| `LICENSE`, `NOTICE` | Licencia Apache-2.0 y avisos. |

Cada skill contiene su `SKILL.md` y, según el caso, `references/`, `scripts/` y
`agents/`. No hay ninguna otra carpeta dentro de este artefacto.

## Requisitos

- Un agente que cargue skills desde `~/.claude/skills/`, `~/.agents/skills/`,
  `<proyecto>/.claude/skills/` o `<proyecto>/.agents/skills/`.
- PowerShell (Windows) o Bash (Linux/macOS) para usar los instaladores.
- Copiar las carpetas a mano también es válido.

## Verificación SHA-256

Windows (PowerShell):

```powershell
Get-FileHash .\ai-image-studio-standalone-skills-<versión>.zip -Algorithm SHA256
```

Linux / macOS:

```bash
shasum -a 256 ai-image-studio-standalone-skills-<versión>.zip
```

Compara el resultado con la línea correspondiente de `SHA256SUMS.txt`.

## Instalación

Extrae el ZIP y ejecuta el instalador del destino que quieras.

Linux / macOS:

```bash
unzip ai-image-studio-standalone-skills-<versión>.zip
cd ai-image-studio
bash adapters/install-skills.sh claude
```

Windows (PowerShell):

```powershell
Expand-Archive .\ai-image-studio-standalone-skills-<versión>.zip -DestinationPath .
cd .\ai-image-studio
powershell -ExecutionPolicy Bypass -File adapters\install-skills.ps1 -Target claude
```

Destinos admitidos:

| Destino | Directorio |
|---|---|
| `claude` | `~/.claude/skills` |
| `codex` | `~/.agents/skills` |
| `project-claude` | `<proyecto>/.claude/skills` |
| `project-codex` | `<proyecto>/.agents/skills` |

Comportamiento de reemplazo: si una skill ya existe, el instalador **se detiene y no
la toca**. Para sustituirla debes pedirlo de forma explícita, y en ese caso se crea
antes una copia de seguridad:

```bash
bash adapters/install-skills.sh claude --force
```

```powershell
powershell -ExecutionPolicy Bypass -File adapters\install-skills.ps1 -Target claude -Force
```

Para ver qué haría sin escribir nada:

```bash
bash adapters/install-skills.sh claude --dry-run
```

```powershell
powershell -ExecutionPolicy Bypass -File adapters\install-skills.ps1 -Target claude -WhatIf
```

Instalación manual, si prefieres no usar los scripts: copia cada carpeta de
`skills/` dentro del directorio de skills de tu agente.

## Validación

Comprueba que las seis carpetas llegaron al destino.

Linux / macOS:

```bash
ls ~/.claude/skills
```

Windows (PowerShell):

```powershell
Get-ChildItem $HOME\.claude\skills
```

Deben figurar: `ai-image-studio-user-guide`, `image-export-packager`,
`image-intake-router`, `image-quality-gates`, `photographer-capture-guide`,
`product-image-pipeline`. Cada una debe contener su `SKILL.md`.

## Actualización

Vuelve a ejecutar el instalador con `--force` (o `-Force`). Se creará una copia de
seguridad de la versión anterior antes de sustituirla.

## Desinstalación

Borra las seis carpetas del directorio de skills de tu agente. Linux / macOS:

```bash
rm -rf ~/.claude/skills/{ai-image-studio-user-guide,image-export-packager,image-intake-router,image-quality-gates,photographer-capture-guide,product-image-pipeline}
```

Windows (PowerShell):

```powershell
"ai-image-studio-user-guide","image-export-packager","image-intake-router","image-quality-gates","photographer-capture-guide","product-image-pipeline" |
  ForEach-Object { Remove-Item -Recurse -Force (Join-Path $HOME ".claude\skills\$_") -ErrorAction SilentlyContinue }
```

## Rollback

El instalador guarda lo que sustituye en
`<destino>/.ai-image-studio-backup/<marca-de-tiempo>/`.

1. Borra las carpetas de skills recién instaladas.
2. Copia de vuelta las carpetas desde el directorio de copia de seguridad.
3. Comprueba con el listado anterior que el estado es el esperado.

Si nunca usaste `--force`, no se sobrescribió nada y basta con borrar lo instalado.

Para probar sin tocar tu configuración real, usa un destino de proyecto en un
directorio temporal:

```bash
bash adapters/install-skills.sh project-claude /tmp/proyecto-de-prueba
```

## Limitaciones

- Este paquete **no** contiene `src/`, `schemas/`, `presets/`, `tests/`, `evals/`,
  `docs/`, `scripts/`, los manifiestos de plugin ni el servidor MCP. Las
  instrucciones que mencionen esas rutas pertenecen a otros artefactos.
- No incluye el comando `ai-image-studio` ni ninguna dependencia de Python.
- Los tres scripts de Python incluidos en las skills
  (`skills/image-quality-gates/scripts/compare_masks.py`,
  `skills/image-quality-gates/scripts/validate_background.py`,
  `skills/image-export-packager/scripts/export_webp.py`) importan el paquete
  `ai_image_studio`. Para ejecutarlos necesitas instalar además el paquete `full`.
  El resto del contenido de las skills funciona sin Python.
- Los instaladores no registran las skills en ningún marketplace: solo copian
  carpetas.
