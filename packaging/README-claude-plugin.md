# AI Image Studio — Plugin de Claude Code

Este archivo describe **exclusivamente** el contenido del artefacto
`ai-image-studio-claude-plugin-<versión>.zip`.

Repositorio canónico: <https://github.com/MadlabCloud/AI-Image-Studio>

## Propósito

Marketplace y plugin de Claude Code que instala las seis skills de AI Image Studio.
No incluye el CLI de Python, el servidor MCP ni la suite de pruebas: es
exclusivamente el paquete de skills para Claude Code.

Si necesitas los comandos `ai-image-studio ...`, usa el paquete `full`.

## Contenido real

Al extraer el ZIP obtienes un directorio `ai-image-studio/` con:

| Ruta | Contenido |
|---|---|
| `.claude-plugin/plugin.json` | Manifiesto del plugin. |
| `.claude-plugin/marketplace.json` | Manifiesto del marketplace. |
| `skills/ai-image-studio-user-guide/` | Guía de uso. |
| `skills/image-intake-router/` | Admisión y enrutado de imágenes. |
| `skills/photographer-capture-guide/` | Guía de captura fotográfica. |
| `skills/product-image-pipeline/` | Flujo estricto de imagen de producto. |
| `skills/image-quality-gates/` | Puertas de calidad. |
| `skills/image-export-packager/` | Exportación y empaquetado. |
| `README.md` | Este archivo. |
| `LICENSE`, `NOTICE` | Licencia Apache-2.0 y avisos. |

No hay ninguna otra carpeta dentro de este artefacto.

## Requisitos

- Claude Code instalado y disponible como comando `claude`.
- Nada más. Este paquete no requiere Python.

## Verificación SHA-256

Windows (PowerShell):

```powershell
Get-FileHash .\ai-image-studio-claude-plugin-<versión>.zip -Algorithm SHA256
```

Linux / macOS:

```bash
shasum -a 256 ai-image-studio-claude-plugin-<versión>.zip
```

Compara el resultado con la línea correspondiente de `SHA256SUMS.txt`.

## Instalación

Extrae el ZIP y registra el directorio extraído como marketplace local.

```bash
unzip ai-image-studio-claude-plugin-<versión>.zip
claude plugin marketplace add ./ai-image-studio
claude plugin install ai-image-studio@ai-image-studio-marketplace
```

En Windows (PowerShell), sustituye la extracción por
`Expand-Archive .\ai-image-studio-claude-plugin-<versión>.zip -DestinationPath .`
y usa la misma ruta `.\ai-image-studio`.

> Mantén el directorio extraído mientras el plugin esté instalado: el marketplace
> apunta a esa ruta local.

## Validación

Antes de instalar, comprueba que los manifiestos son correctos:

```bash
claude plugin validate ./ai-image-studio --strict
```

Debe responder `Validation passed` y devolver código de salida 0.

Después de instalar, comprueba que aparecen las seis skills:

```bash
claude plugin list
claude plugin details ai-image-studio@ai-image-studio-marketplace
```

El inventario debe indicar `Skills (6)` con estos nombres:
`ai-image-studio-user-guide`, `image-export-packager`, `image-intake-router`,
`image-quality-gates`, `photographer-capture-guide`, `product-image-pipeline`.

## Actualización

```bash
claude plugin uninstall ai-image-studio@ai-image-studio-marketplace
claude plugin marketplace remove ai-image-studio-marketplace
```

Extrae después la versión nueva y repite la instalación. También puedes usar
`claude plugin update ai-image-studio@ai-image-studio-marketplace` si el directorio
del marketplace ya apunta a la versión nueva; requiere reiniciar Claude Code.

## Desinstalación

```bash
claude plugin uninstall ai-image-studio@ai-image-studio-marketplace
claude plugin marketplace remove ai-image-studio-marketplace
```

Borra por último el directorio extraído.

## Rollback

1. Ejecuta los dos comandos de desinstalación anteriores.
2. Comprueba con `claude plugin list` que no queda ningún plugin instalado.
3. Borra el directorio extraído.
4. Extrae la versión anterior y vuelve a instalarla.

Los ajustes de usuario quedan sin referencias a este plugin tras la desinstalación.
Claude Code puede conservar una copia en su caché interna marcada como huérfana;
no está activa y puede eliminarse manualmente si lo deseas.

Para probar sin tocar tu configuración real, usa un directorio aislado:

```bash
CLAUDE_CONFIG_DIR=/tmp/prueba-aislada claude plugin marketplace add ./ai-image-studio
```

## Limitaciones

- Este paquete **no** contiene `src/`, `schemas/`, `presets/`, `tests/`, `evals/`,
  `adapters/`, `docs/`, `scripts/` ni el servidor MCP. Las instrucciones que
  mencionen esas rutas pertenecen al paquete `full`.
- No incluye el comando `ai-image-studio` ni ninguna dependencia de Python.
- Las skills que ejecutan scripts de Python (por ejemplo, las de puertas de calidad
  y exportación) necesitan que instales además el paquete `full` para disponer de
  esos scripts y sus dependencias.
- El marketplace es local: apunta a la carpeta extraída, no a una URL remota.
