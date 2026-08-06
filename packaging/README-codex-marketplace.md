# AI Image Studio — Marketplace de Codex

Este archivo describe **exclusivamente** el contenido del artefacto
`ai-image-studio-codex-marketplace-<versión>.zip`.

Repositorio canónico: <https://github.com/MadlabCloud/AI-Image-Studio>

## Propósito

Marketplace de Codex **ya instalable**, con el envoltorio completo que espera
`codex plugin marketplace add`. En la versión 0.5.0 se distribuía solo el plugin
suelto y el usuario tenía que construir a mano la estructura del marketplace; este
artefacto la incluye.

No contiene el CLI de Python ni el servidor MCP: es exclusivamente el paquete de
skills para Codex. Si necesitas los comandos `ai-image-studio ...`, usa el paquete
`full`.

## Contenido real

Al extraer el ZIP obtienes un directorio `ai-image-studio-codex-marketplace/` con:

| Ruta | Contenido |
|---|---|
| `.agents/plugins/marketplace.json` | Manifiesto del marketplace. Declara el plugin con `source.path = ./plugins/ai-image-studio`. |
| `plugins/ai-image-studio/.codex-plugin/plugin.json` | Manifiesto del plugin. |
| `plugins/ai-image-studio/skills/` | Las seis skills. |
| `plugins/ai-image-studio/LICENSE`, `plugins/ai-image-studio/NOTICE` | Licencia y avisos del plugin. |
| `README.md` | Este archivo. |
| `LICENSE`, `NOTICE` | Licencia Apache-2.0 y avisos. |

Las seis skills son: `ai-image-studio-user-guide`, `image-intake-router`,
`photographer-capture-guide`, `product-image-pipeline`, `image-quality-gates`,
`image-export-packager`.

No hay ninguna otra carpeta dentro de este artefacto.

## Requisitos

- Codex CLI instalado y disponible como comando `codex`.
- Nada más. Este paquete no requiere Python.

## Verificación SHA-256

Windows (PowerShell):

```powershell
Get-FileHash .\ai-image-studio-codex-marketplace-<versión>.zip -Algorithm SHA256
```

Linux / macOS:

```bash
shasum -a 256 ai-image-studio-codex-marketplace-<versión>.zip
```

Compara el resultado con la línea correspondiente de `SHA256SUMS.txt`.

## Instalación

```bash
unzip ai-image-studio-codex-marketplace-<versión>.zip
codex plugin marketplace add ./ai-image-studio-codex-marketplace
codex plugin add ai-image-studio@ai-image-studio-marketplace
```

En Windows (PowerShell), extrae con
`Expand-Archive .\ai-image-studio-codex-marketplace-<versión>.zip -DestinationPath .`
y usa la ruta `.\ai-image-studio-codex-marketplace`.

> Mantén el directorio extraído mientras el plugin esté instalado: el marketplace
> declara una fuente local que apunta a esa ruta.

> **Windows: extrae en una ruta corta.** La entrada más larga de este ZIP mide 132
> caracteres. Con el límite clásico `MAX_PATH` de 260 caracteres (activo salvo que
> `HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem\LongPathsEnabled` valga 1), la
> extracción falla con `[WinError 206]` si el directorio de destino ya es profundo.
> `C:\Users\<tu-usuario>\Downloads` o cualquier ruta similar deja margen de sobra.

## Validación

Tras añadir el marketplace y antes de instalar:

```bash
codex plugin marketplace list
codex plugin list
```

El plugin `ai-image-studio` debe aparecer como disponible. Después de instalarlo,
comprueba que su estado es instalado o habilitado y que expone las seis skills.

Validación sin depender del CLI, útil para automatización:

```bash
python -c "import json;d=json.load(open('ai-image-studio-codex-marketplace/.agents/plugins/marketplace.json'));print(d['plugins'][0]['source'])"
```

Debe imprimir `{'source': 'local', 'path': './plugins/ai-image-studio'}` y esa ruta
debe existir dentro del directorio extraído.

## Actualización

```bash
codex plugin remove ai-image-studio@ai-image-studio-marketplace
codex plugin marketplace remove ai-image-studio-marketplace
```

Extrae después la versión nueva y repite la instalación.

## Desinstalación

```bash
codex plugin remove ai-image-studio@ai-image-studio-marketplace
codex plugin marketplace remove ai-image-studio-marketplace
```

Borra por último el directorio extraído.

## Rollback

1. Ejecuta los dos comandos de desinstalación anteriores.
2. Comprueba con `codex plugin list` que el plugin ya no figura.
3. Borra el directorio extraído.
4. Extrae la versión anterior y vuelve a instalarla.

Para probar sin tocar tu configuración real, aísla el entorno con `CODEX_HOME`:

```bash
CODEX_HOME=/tmp/codex-prueba codex plugin marketplace add ./ai-image-studio-codex-marketplace
```

Al terminar basta con borrar `/tmp/codex-prueba`.

En Windows, define `CODEX_HOME` bajo `%LOCALAPPDATA%` y no bajo `%TEMP%`: el CLI se
niega a crear sus binarios auxiliares dentro de un directorio temporal y avisa en
cada comando.

## Limitaciones

- Este paquete **no** contiene `src/`, `schemas/`, `presets/`, `tests/`, `evals/`,
  `adapters/`, `docs/`, `scripts/` ni el servidor MCP. Las instrucciones que
  mencionen esas rutas pertenecen al paquete `full`.
- No incluye el comando `ai-image-studio` ni ninguna dependencia de Python.
- Los tres scripts de Python incluidos en las skills
  (`image-quality-gates/scripts/compare_masks.py`,
  `image-quality-gates/scripts/validate_background.py`,
  `image-export-packager/scripts/export_webp.py`) importan el paquete
  `ai_image_studio`. Para ejecutarlos necesitas instalar además el paquete `full`.
- El marketplace es local: apunta a la carpeta extraída, no a una URL remota.
- La estructura de este artefacto se valida automáticamente en CI. El ciclo completo
  de instalación y desinstalación se ha verificado a mano con Codex CLI 0.140.0 en
  Windows, sobre un `CODEX_HOME` aislado.
