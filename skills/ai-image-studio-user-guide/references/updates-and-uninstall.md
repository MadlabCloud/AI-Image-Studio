# Actualización y desinstalación

## Antes de actualizar

1. Copia la configuración y perfiles del usuario.
2. Conserva originales y trabajos aprobados.
3. Lee `CHANGELOG.md`.
4. Ejecuta tests en una instalación de desarrollo.
5. No reemplaces una versión de producción sin probar un conjunto real de imágenes.

## Actualizar skills locales

Vuelve a ejecutar el instalador desde la nueva versión. El script reemplaza las carpetas de skills con el mismo nombre.

## Desinstalar skills

Elimina únicamente las carpetas de AI Image Studio de:

- Claude: `~/.claude/skills/`.
- Codex: `~/.agents/skills/`.

No elimines otras skills del usuario.

## Desinstalar plugin

Utiliza el gestor de Plugins de la plataforma. En Claude: `Customize > Plugins`. En Codex CLI: `/plugins`. Las opciones exactas pueden variar por versión.

## Desinstalar CLI

Dentro del entorno virtual:

```bash
pip uninstall ai-image-studio
```

Después elimina el entorno virtual solo cuando hayas respaldado configuración, perfiles y resultados.
