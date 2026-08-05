# Solución de problemas

## La skill no aparece

- Confirma que existe `SKILL.md` dentro de una carpeta propia.
- Claude Code: verifica `~/.claude/skills` o `.claude/skills`.
- Codex: verifica `~/.agents/skills` o `.agents/skills`.
- Reinicia cuando el directorio raíz de skills no existía al abrir la sesión.
- En Cowork, habilita la skill o el plugin en la cuenta; no depende de `~/.claude/skills`.

## El comando no existe

- Activa el entorno virtual.
- Ejecuta `pip install -e ".[dev,mcp]"`.
- Comprueba con `python -m ai_image_studio.cli doctor` si el entry point no está en PATH.

## La configuración no valida

- No guardes claves directamente.
- Usa nombres de variables como `PHOTOROOM_API_KEY`.
- No habilites proveedores externos con `allow_external_uploads=false`.
- No desactives preservación de originales ni fail-closed.

## El MCP no inicia

- Instala el extra `mcp`.
- Comprueba permisos y `AI_IMAGE_STUDIO_ALLOWED_ROOT`.
- Para sesiones remotas, un MCP STDIO local puede no estar disponible; se necesita un despliegue compatible y autenticado.

## Diagnóstico

```bash
ai-image-studio doctor --workspace ./workspace
```

Cambia una sola variable cada vez y vuelve a ejecutar la prueba que falló.
