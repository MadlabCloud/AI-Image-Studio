# ChatGPT y Codex

Revisión: 2026-08-05.

## Codex local

- Skills personales: `~/.agents/skills/<skill>/SKILL.md`.
- Skills de repositorio: `.agents/skills/<skill>/SKILL.md`.
- Codex detecta skills instaladas; si no aparecen, reinicia la sesión.

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File adapters\install-skills.ps1 -Target codex
```

## Plugins

Los plugins están disponibles en ChatGPT Work y Codex en superficies compatibles. En Codex CLI, abre el navegador con `/plugins` y comienza una sesión nueva después de instalar. El paquete de este repositorio es un artefacto de desarrollo; para instalación gráfica debe publicarse o distribuirse mediante un marketplace compatible.

Los plugins no están disponibles en ChatGPT Chat estándar, la extensión IDE ni móvil. El MCP personalizado en ChatGPT depende del plan, permisos y configuración del espacio de trabajo.
