# AI Image Studio — Paquete Full

Este archivo describe **exclusivamente** el contenido del artefacto
`ai-image-studio-full-<versión>.zip`.

Repositorio canónico: <https://github.com/MadlabCloud/AI-Image-Studio>

## Propósito

Distribución completa del proyecto: interfaz de línea de comandos, servidor MCP
opcional, las seis skills, esquemas, ejemplos, instaladores y la suite de pruebas.
Es el paquete adecuado para instalar la herramienta, ejecutar las pruebas o
contribuir al proyecto.

Si solo quieres las skills para un agente, usa el paquete
`standalone-skills`, `claude-plugin` o `codex-marketplace` en su lugar.

## Contenido real

Al extraer el ZIP obtienes un directorio `ai-image-studio/` con:

| Ruta | Contenido |
|---|---|
| `src/ai_image_studio/` | Código de la aplicación. El servidor MCP es `src/ai_image_studio/mcp_server.py`. |
| `skills/` | Las seis skills (`SKILL.md`, referencias y scripts). |
| `schemas/` | Esquemas JSON públicos. |
| `presets/` | Perfiles de captura y registro de dispositivos. |
| `examples/` | Trabajos, decisiones y configuraciones de ejemplo. |
| `tests/` | Suite de pruebas. |
| `evals/` | Casos de activación de skills. |
| `adapters/` | Instaladores de skills y notas por plataforma. |
| `docs/` | `GITHUB_INSTALLATION.md` y `MCP_SETUP.md`. |
| `scripts/` | Construcción de artefactos, checksums y validación del bundle. |
| `packaging/` | Los README específicos de cada artefacto. |
| `.claude-plugin/` | `plugin.json` y `marketplace.json` de Claude Code. |
| `.codex-plugin/` | `plugin.json` de Codex. |
| `.github/` | Flujos de CI, Release y seguridad. |
| `.mcp.json.example` | Ejemplo portable de configuración MCP. |
| `pyproject.toml`, `requirements.txt`, `requirements-dev.txt` | Empaquetado y dependencias. |
| `install.sh`, `install.ps1`, `Makefile`, `Dockerfile` | Utilidades de instalación. |
| `README.md`, `USER_MANUAL.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `LICENSE`, `NOTICE` | Documentación y licencias. |

Este `README.md` sustituye al README general del repositorio dentro del artefacto.

## Requisitos

- Python 3.10 o superior.
- Dependencias obligatorias: `Pillow`, `numpy`, `jsonschema` (se instalan solas).
- Opcional: extra `mcp`, limitado a `mcp>=1.14,<2`.
- Opcional: ExifTool, darktable-cli, RawTherapee CLI, ImageMagick.

## Verificación SHA-256

Compara el hash antes de extraer, usando el `SHA256SUMS.txt` publicado junto a los
artefactos.

Windows (PowerShell):

```powershell
Get-FileHash .\ai-image-studio-full-<versión>.zip -Algorithm SHA256
```

Linux / macOS:

```bash
shasum -a 256 ai-image-studio-full-<versión>.zip
```

## Instalación

```bash
unzip ai-image-studio-full-<versión>.zip
cd ai-image-studio
python -m venv .venv
```

Activa el entorno virtual — Windows: `.venv\Scripts\activate`;
Linux/macOS: `source .venv/bin/activate` — y después:

```bash
pip install -e ".[dev,mcp]"
```

Omite `mcp` si no vas a usar el servidor MCP: `pip install -e ".[dev]"`.

## Validación

```bash
pytest
python scripts/validate_bundle.py
ai-image-studio doctor
```

`doctor` devuelve JSON. Revisa dos campos:

- `ready` debe ser `true`.
- `mcp.state` debe ser `ok` si instalaste el extra `mcp`, o `absent` si no lo hiciste.
  Cualquier otro valor (`incompatible`, `import_error`, `build_error`) indica un
  problema real y explica la causa en `mcp.detail`.

Servidor MCP: consulta `docs/MCP_SETUP.md` y usa `.mcp.json.example` como base.

Instalación de las skills en un agente:

```bash
bash adapters/install-skills.sh claude
```

```powershell
powershell -ExecutionPolicy Bypass -File adapters\install-skills.ps1 -Target claude
```

Destinos admitidos: `claude`, `codex`, `project-claude`, `project-codex`.
Sin `-Force` (o `--force`) el instalador **no** sobrescribe skills existentes.

## Actualización

Descarga el nuevo ZIP, verifica su SHA-256 y extráelo en un directorio distinto.
Después, dentro del entorno virtual:

```bash
pip install -e ".[dev,mcp]" --upgrade
```

Vuelve a ejecutar `pytest` y `ai-image-studio doctor`.

## Desinstalación

```bash
pip uninstall ai-image-studio
```

Elimina después el directorio extraído y, si lo creaste, el entorno virtual `.venv`.
Las skills instaladas en un agente se retiran borrando sus carpetas en
`~/.claude/skills/` o `~/.agents/skills/`, o restaurando la copia de seguridad que
el instalador creó en `<destino>/.ai-image-studio-backup/`.

## Rollback

1. `pip uninstall ai-image-studio`.
2. Borra el directorio extraído de esta versión.
3. Restaura las skills desde `<destino>/.ai-image-studio-backup/<marca-de-tiempo>/`
   si necesitas volver al estado anterior.
4. Extrae de nuevo la versión anterior y repite la instalación.

No se modifica ningún archivo fuera del directorio extraído, del entorno virtual y
de los destinos de skills que indiques explícitamente.

## Limitaciones

- El servidor MCP **no** funciona con `mcp` 2.x ni con las versiones 1.7 a 1.13.
  El intervalo verificado es `mcp>=1.14,<2`.
- Los motores RAW y ExifTool son opcionales: su ausencia no impide usar el CLI ni
  las skills, pero limita el trabajo con formatos RAW.
- Este paquete **no** es un marketplace de Claude Code ni de Codex. Para eso están
  los artefactos `claude-plugin` y `codex-marketplace`.
- `doctor` no realiza conexiones de red.
