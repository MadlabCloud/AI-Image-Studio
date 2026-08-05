# AI Image Studio

Sistema portable de **Agent Skills + herramientas deterministas + MCP opcional** para clasificar, preparar, editar, validar y exportar imágenes mediante un modelo de decisión universal y flujos especializados.

## Objetivo

Reducir errores no detectados mediante un flujo cerrado:

```text
RECEIVED → INSPECTED → CLASSIFIED → SPEC_LOCKED → SOURCE_PRESERVED
→ PROCESSED → AUTOMATIC_QC → HUMAN_QC (si procede) → APPROVED
→ EXPORTED → PACKAGED
```

La regla principal es **fail closed**: si una puerta crítica falla o no hay evidencia suficiente, el trabajo no pasa a exportación.

## Contenido

- `skills/`: skills compatibles con el estándar Agent Skills.
- `src/ai_image_studio/`: CLI y lógica determinista.
- `schemas/`: contratos JSON Schema 2020-12.
- `presets/`: configuraciones versionadas.
- `mcp/`: servidor MCP local opcional.
- `tests/`: pruebas unitarias y de integración.
- `evals/`: casos de activación y comportamiento.
- `adapters/`: instalación para Claude Code y Codex/ChatGPT.

## Modelo de Decisión Universal

Antes de editar se bloquean siete variables: categoría, destino, captura, escenario, fidelidad, política de fondo y salidas. El sistema no asume una cámara concreta ni fondo blanco. Para productos web puede solicitar una imagen de ambiente separada; si falta el contexto, exige una referencia o recomendaciones.

Consulta `skills/image-intake-router/references/universal-decision-model.md`.

## Instalación desde GitHub

Repositorio canónico: `MadlabCloud/AI-Image-Studio`.

```bash
git clone https://github.com/MadlabCloud/AI-Image-Studio.git
cd AI-Image-Studio
```

Para producción, usa una GitHub Release etiquetada y verifica `SHA256SUMS.txt`. Consulta `docs/GITHUB_INSTALLATION.md`.

## Instalación de desarrollo

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -e ".[dev,mcp]"
pytest
```

## Uso de la CLI

```bash
ai-image-studio inspect foto.jpg
ai-image-studio validate-decision decision.json
ai-image-studio route-decision decision.json
ai-image-studio prepare-job job.json --workspace ./workspace
ai-image-studio compare-masks mask-a.png mask-b.png
ai-image-studio validate-background resultado.png --mask product-mask.png
ai-image-studio export-webp resultado.png salida.webp --width 1000 --height 1000
ai-image-studio package ./salidas paquete.zip
```

## Instalación de skills

### Claude Code local

```powershell
powershell -ExecutionPolicy Bypass -File adapters\install-skills.ps1 -Target claude
```

### Codex / ChatGPT Desktop

```powershell
powershell -ExecutionPolicy Bypass -File adapters\install-skills.ps1 -Target codex
```

Para Cowork, las skills deben habilitarse en la cuenta de Claude o distribuirse como plugin. Consulta `adapters/CLAUDE_COWORK.md`.

## Garantías y límites

Este proyecto no promete que un modelo generativo cometa cero errores. Su diseño busca **cero defectos críticos no detectados**, mediante validación, bloqueo de transiciones, trazabilidad y revisión humana en casos dudosos.

## Estado

Versión `0.5.0`: añade distribución oficial desde GitHub, CI, seguridad, instaladores y Releases verificadas.
