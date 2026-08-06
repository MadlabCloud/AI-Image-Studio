# Manual de Usuario — AI Image Studio

Versión 0.5.2 · Revisión 2026-08-06

## 1. Qué es

AI Image Studio es una arquitectura portable de skills, contratos, controles y utilidades deterministas para planificar, procesar, validar y exportar imágenes. Una skill enseña el procedimiento; no sustituye por sí sola a Lightroom, darktable, Photoshop, PhotoRoom, un segmentador o un modelo generativo.

## 2. Principio de seguridad

El sistema trabaja en modo **fail closed**: un resultado con una puerta crítica fallida no se exporta. Los originales no se sobrescriben y los servicios externos permanecen desactivados hasta que el usuario los autorice.

## 3. Compatibilidad

### Claude Code

Instalación personal en `~/.claude/skills` o por proyecto en `.claude/skills`. Es la vía recomendada para desarrollo local y MCP STDIO.

### Claude Desktop y Cowork

Las skills se gestionan desde `Customize`. Cowork no lee automáticamente `~/.claude/skills`; utiliza skills habilitadas en la cuenta, skills del repositorio cloud o plugins instalados.

### Codex

Instalación local en `~/.agents/skills` o por repositorio en `.agents/skills`. Los plugins se gestionan en superficies compatibles y en Codex CLI mediante su navegador de plugins.

### ChatGPT

Los plugins pertenecen a ChatGPT Work y superficies compatibles de Codex. Chat estándar, móvil y la extensión IDE no ofrecen el mismo mecanismo. Las apps MCP personalizadas dependen del plan, permisos y despliegue del espacio de trabajo.

## 4. Instalación desde GitHub

Para desarrollo, clona `https://github.com/MadlabCloud/AI-Image-Studio.git`. Para uso estable, descarga una versión etiquetada desde GitHub Releases, verifica `SHA256SUMS.txt` y ejecuta `install.ps1` o `install.sh`. Consulta `docs/GITHUB_INSTALLATION.md`.

## 5. Instalación completa

```bash
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev,mcp]"
pytest
ai-image-studio doctor
```

## 6. Instalación de skills

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

## 7. Configuración inicial

```bash
ai-image-studio init-config ./ai-image-studio.config.json --workspace-root ./workspace
ai-image-studio validate-config ./ai-image-studio.config.json
ai-image-studio doctor --workspace ./workspace
```

La configuración no contiene secretos. Las credenciales futuras se suministran mediante variables de entorno.

## 8. Primera prueba

Entrega una imagen no sensible y solicita análisis sin edición. Confirma categoría, destino, fidelidad, fondo y salidas. Para productos puede haber catálogo y ambiente; el ambiente es un derivado creativo separado. Para personas, bodas y viajes no se aplica automáticamente un fondo ecommerce.

## 9. Comandos esenciales

```bash
ai-image-studio inspect foto.jpg
ai-image-studio validate-decision decision.json
ai-image-studio route-decision decision.json
ai-image-studio recommend-capture capture.json
ai-image-studio validate-background resultado.png --mask producto.png
ai-image-studio validate-output resultado.png --width 1000 --height 1000
ai-image-studio export-webp resultado.png salida.webp
ai-image-studio package ./salidas entrega.zip
```

## 10. Privacidad

- Conserva originales y hashes.
- No subas imágenes externamente sin permiso.
- No escribas claves en JSON o skills.
- Limita rutas del MCP.
- Elimina metadatos de archivos web cuando proceda.

## 11. Actualización

Respalda configuración y perfiles, revisa el changelog, ejecuta tests y valida imágenes reales antes de sustituir la versión de producción.

## 12. Desinstalación

Elimina solo las skills de AI Image Studio de las carpetas de Claude o Codex, o usa el gestor de Plugins. Para la CLI: `pip uninstall ai-image-studio` dentro del entorno virtual.

## 13. Límites de esta versión

La versión 0.4.0 ofrece modelo de decisión, manual fotográfico, guía de usuario, diagnósticos, contratos, validadores básicos y exportación. Los motores RAW, segmentación doble, matting avanzado, visión de piezas y generación de ambientes siguen siendo integraciones futuras.
