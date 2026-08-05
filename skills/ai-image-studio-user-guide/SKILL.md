---
name: ai-image-studio-user-guide
description: Instala, configura, verifica, actualiza, usa o desinstala AI Image Studio en Claude Code, Claude/Cowork, Codex y superficies compatibles de ChatGPT. Úsala cuando el usuario necesite primeros pasos, diagnóstico, privacidad, solución de problemas o conocer qué funciones están realmente disponibles en su plataforma.
license: Apache-2.0
compatibility: La guía funciona sin MCP. Cuando la CLI o el MCP local están instalados, puede usar image_system_doctor e image_validate_user_config.
metadata:
  version: "0.4.0"
---

# Objetivo

Guiar al usuario de forma segura y verificable desde la instalación hasta el primer trabajo, sin confundir una skill con un motor de edición ni prometer funciones que la plataforma no ofrece.

# Reglas

1. Pregunta sistema operativo, plataforma principal y modalidad: desarrollo, skills-only o plugin.
2. No des instrucciones de una plataforma distinta a la elegida.
3. Antes de instalar, consulta `references/platform-support.md`.
4. Usa `references/installation.md` para instalar y `references/first-use.md` para la primera ejecución.
5. No pidas ni guardes claves en archivos JSON; utiliza variables de entorno.
6. Ejecuta `ai-image-studio doctor` cuando la CLI esté disponible.
7. Valida la configuración antes de usarla.
8. Explica claramente qué es funcional, opcional, experimental o todavía no implementado.
9. No asumas que un ZIP de desarrollo es instalable con un clic en todas las plataformas.
10. En problemas, sigue `references/troubleshooting.md` y cambia una sola variable cada vez.
11. Para actualizar o desinstalar, conserva siempre originales, perfiles y configuraciones del usuario.
12. Cita la fecha de revisión de instrucciones de plataforma cuando sea relevante.

# Flujo

1. Identifica plataforma y sistema operativo.
2. Selecciona ruta compatible en `references/platform-support.md`.
3. Instala según `references/installation.md`.
4. Crea configuración local mediante `ai-image-studio init-config`.
5. Ejecuta `ai-image-studio validate-config` y `ai-image-studio doctor`.
6. Completa el primer flujo de `references/first-use.md`.
7. Enseña los flujos cotidianos desde `references/workflows.md`.
8. Aplica privacidad y permisos según `references/privacy-and-security.md`.
9. Para mantenimiento consulta `references/updates-and-uninstall.md`.

# Salida esperada

```text
PLATAFORMA Y MODO
Requisitos:
Instalación:
Configuración:
Diagnóstico:
Primera prueba:
Funciones disponibles:
Limitaciones actuales:
Siguiente acción:
```
