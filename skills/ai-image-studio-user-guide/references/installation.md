# Instalación

## Elegir modalidad

### Desarrollo completo

Incluye CLI, tests y MCP opcional.

```bash
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev,mcp]"
pytest
ai-image-studio doctor
```

### Skills-only

No instala motores de edición. Añade instrucciones especializadas al agente.

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File adapters\install-skills.ps1 -Target claude
powershell -ExecutionPolicy Bypass -File adapters\install-skills.ps1 -Target codex
```

macOS/Linux:

```bash
bash adapters/install-skills.sh claude
bash adapters/install-skills.sh codex
```

### Proyecto concreto

- Claude Code: copia `skills/*` a `.claude/skills/`.
- Codex: copia `skills/*` a `.agents/skills/`.

## Claude Desktop y Cowork

1. Abre Claude; en Cowork entra primero en la pestaña Cowork.
2. Abre `Customize` y la pestaña `Plugins`.
3. Instala desde el directorio o carga un plugin personalizado compatible.
4. Inicia una tarea nueva y comprueba las skills con `/` o el botón `+`.

Las sesiones Cowork no leen automáticamente las skills personales de `~/.claude/skills`.

## ChatGPT Work y Codex

- Para desarrollo local de Codex, instala en `~/.agents/skills` o `.agents/skills`.
- En Codex CLI, los plugins se gestionan desde `/plugins` cuando el marketplace está configurado.
- En ChatGPT Work o Codex de escritorio, usa el directorio de Plugins de la superficie compatible.
- ChatGPT Chat estándar, móvil y la extensión IDE no ofrecen el mismo sistema de plugins.

## Comprobación

```bash
ai-image-studio doctor
ai-image-studio init-config ./ai-image-studio.config.json
ai-image-studio validate-config ./ai-image-studio.config.json
```
