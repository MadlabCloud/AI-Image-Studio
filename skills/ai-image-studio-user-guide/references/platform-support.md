# Compatibilidad por plataforma

Revisión: 2026-08-05.

| Plataforma | Skills locales | Plugin | MCP local | Estado recomendado |
|---|---:|---:|---:|---|
| Claude Code | Sí: `~/.claude/skills` o `.claude/skills` | Sí | Sí, STDIO | Soporte principal de desarrollo |
| Claude Desktop / chat | Mediante skills de cuenta o plugin | Sí, desde Customize | Depende del plugin y permisos | Uso interactivo |
| Claude Cowork | No lee `~/.claude/skills`; usa skills de cuenta, proyecto cloud o plugin | Sí | Un servidor local puede no estar disponible en sesiones remotas | Plugin/skill sincronizada |
| Codex CLI / app | Sí: `~/.agents/skills` o `.agents/skills` | Sí en superficies compatibles | Sí, según host | Soporte principal de desarrollo |
| ChatGPT Work | No usa las carpetas locales directamente | Sí desde el directorio compatible | Apps/MCP según plan y permisos | Plugin publicado o app autorizada |
| ChatGPT Chat estándar / móvil | No | No | No como plugin local | Utilizar instrucciones, archivos y capacidades nativas disponibles |

## Regla de honestidad

Los paquetes `dist/*plugin*.zip` de este repositorio son artefactos de desarrollo y distribución. Claude Desktop/Cowork permite cargar plugins personalizados. En ChatGPT/Codex, la instalación gráfica depende de una superficie compatible y de que el plugin esté disponible mediante un marketplace o mecanismo autorizado; para desarrollo local se usan las skills en `.agents/skills`.

## Fuentes oficiales revisadas

- Claude Code: ubicación y alcance de skills.
- Claude: Customize, plugins y uso en Cowork.
- OpenAI: skills locales de Codex y plugins de ChatGPT Work/Codex.
- ChatGPT: disponibilidad de apps MCP según plan y permisos del espacio de trabajo.
