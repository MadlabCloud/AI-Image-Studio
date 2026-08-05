# Claude Desktop y Cowork

Revisión: 2026-08-05.

## Claude Code local

- Skills personales: `~/.claude/skills/<skill>/SKILL.md`.
- Skills de proyecto: `.claude/skills/<skill>/SKILL.md`.
- MCP local: STDIO cuando el proceso se ejecuta en el mismo equipo.

## Claude Desktop y Cowork

1. Abre Claude. En Cowork, entra primero en la pestaña Cowork.
2. Abre `Customize` en la barra lateral.
3. En `Plugins`, instala desde el directorio o carga un plugin personalizado compatible.
4. Las skills del plugin aparecen mediante `/` o el botón `+`.

Cowork y las sesiones cloud no leen automáticamente `~/.claude/skills/`. Cargan las skills habilitadas en la cuenta al iniciar la sesión; las sesiones cloud también pueden cargar skills del repositorio en `.claude/skills/`.

Los plugins personalizados añadidos desde Claude Desktop/Cowork se guardan localmente. Instala solo paquetes de confianza: un plugin puede incluir código o servidores MCP con permisos del usuario.
