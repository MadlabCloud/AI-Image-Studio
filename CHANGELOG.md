# Changelog

## 0.5.1 - 2026-08-05

Versión correctiva centrada en distribución. El núcleo funcional de 0.5.0 no cambia:
las seis skills, los esquemas, los presets y los ejemplos son idénticos.

### Corregido

- **MCP**: el extra opcional se limita a `mcp>=1.14,<2`. La restricción anterior `mcp>=1.0`
  permitía instalar mcp 2.x, que no expone `mcp.server.fastmcp` y dejaba el servidor
  inservible. El límite inferior excluye además las versiones 1.7 a 1.13, en las que
  construir el servidor falla con `TypeError` al resolver anotaciones diferidas.
- **doctor**: ya no basta con que el paquete `mcp` esté instalado; ahora se comprueba que
  `FastMCP` se importa y que el servidor se construye. Se distinguen los estados `absent`,
  `incompatible`, `import_error`, `build_error` y `ok`, y `ready` pasa a `false` cuando una
  capacidad declarada como instalada no puede funcionar.
- **Servidor MCP**: el ejecutable `ai-image-studio-mcp` traduce también el fallo de
  construcción a un mensaje accionable con el intervalo soportado, en lugar de mostrar el
  `TypeError` en crudo. Además, el handshake `initialize` anuncia ahora la versión de
  AI Image Studio; antes devolvía la del paquete `mcp` porque `FastMCP` no acepta `version`
  y el servidor de bajo nivel quedaba en `None`.
- **Configuración MCP**: `.mcp.json.example` usa el ejecutable `ai-image-studio-mcp` en lugar
  del `python` global, que fallaba fuera del directorio del proyecto con
  `No module named ai_image_studio`.
- **Marketplace de Claude Code**: `source` pasa de `"."` a `"./"` y se añade la descripción
  del marketplace que faltaba. `claude plugin validate --strict` ya pasa.
- **Distribución para Codex**: el artefacto es ahora un marketplace instalable, con
  `.agents/plugins/marketplace.json` y `plugins/ai-image-studio/`. Se renombra a
  `ai-image-studio-codex-marketplace-<version>.zip`.
- **README por artefacto**: cada ZIP incluye documentación propia. Los tres paquetes de
  skills ya no describen rutas (`src/`, `schemas/`, `tests/`, `adapters/`…) que no contienen.
- **Documentación**: se elimina la referencia a una carpeta `mcp/` inexistente; el servidor
  está en `src/ai_image_studio/mcp_server.py`.
- **Finales de línea**: todo el texto de los artefactos se normaliza a LF al empaquetar, y
  `SHA256SUMS.txt` se escribe siempre con LF. Antes solo se normalizaban los `.sh`, así que un
  árbol de trabajo Windows producía ZIP con hashes distintos a los de un árbol Linux: los
  SHA-256 publicados por CI no se podían reproducir en otra plataforma, y `sha256sum -c`
  rechazaba un `SHA256SUMS.txt` generado en Windows. Los ZIP son ahora idénticos byte a byte
  los construya Windows, Linux o macOS.

### Seguridad

- **Instalador de skills**: deja de sustituir skills existentes en silencio. Sin
  `-Force` / `--force` se detiene con código 3 y no escribe nada; con `-Force` crea una copia
  de seguridad con marca de tiempo antes de sustituir. Se añaden `-WhatIf` / `--dry-run`,
  `--no-backup`, `--backup-root` y códigos de salida documentados.
- **Códigos de salida del instalador PowerShell**: los códigos 2 y 4 eran inalcanzables.
  `Write-Error` es terminante con `$ErrorActionPreference = "Stop"` y mataba el script antes
  de su `exit`, devolviendo siempre 1; y `[ValidateSet]` rechazaba un `-Target` inválido desde
  el enlazador de parámetros, también con 1. Ahora `install-skills.ps1` valida el destino en
  el cuerpo y escribe a stderr sin lanzar, de modo que devuelve los mismos códigos que
  `install-skills.sh`: 0, 2, 3 y 4.
- **`.gitignore`**: las reglas de imágenes y RAW pasan a clases de caracteres
  (`*.[jJ][pP][gG]`). Las cámaras escriben la extensión en mayúsculas y, en sistemas de
  archivos sensibles a mayúsculas, `*.jpg` no casaba con `IMG_1347.JPG`; Windows lo disimulaba.
- **Empaquetado**: la selección de archivos respeta `.gitignore` y un escaneo de privacidad
  aborta la construcción si detecta fotografías personales, archivos `.env`, RAW, claves o
  rutas locales.
- **Empaquetado (fail-closed)**: si el directorio de preparación conserva restos de una
  construcción anterior, la construcción **aborta**. Antes solo avisaba, y un archivo ajeno
  al repositorio podía viajar dentro del ZIP; reproducido en Windows sobre un árbol
  sincronizado con la nube, donde las carpetas se vuelven marcadores de posición de solo
  lectura que `rmtree` no puede borrar.

### Añadido

- `docs/MCP_SETUP.md` con la estrategia de configuración portable por sistema operativo y
  una tabla de compatibilidad de versiones de MCP.
- `scripts/validate_artifacts.py`, que valida los ZIP como productos independientes:
  estructura, manifiestos, JSON UTF-8, README correspondiente, ausencia de material privado,
  igualdad byte a byte de las seis skills y coincidencia de SHA-256.
- Suite de pruebas ampliada de 29 a 121 casos.
- CI en Windows, Linux y macOS, con validación de artefactos, de los manifiestos de Claude
  Code y del comportamiento real del instalador en PowerShell, incluidos los destinos
  globales `claude` y `codex` sobre un perfil aislado cuyo aislamiento se comprueba antes de
  escribir nada.

### Sin cambios

- Las seis skills, los esquemas, los presets y los ejemplos no se modifican.
- La etiqueta y los artefactos de v0.5.0 permanecen intactos.

## 0.5.0 - 2026-08-05

- Prepara el repositorio canónico `MadlabCloud/AI-Image-Studio` para distribución mediante GitHub.
- Añade instalación desde clon o GitHub Release para Windows, macOS y Linux.
- Añade workflows de CI, seguridad y publicación de Releases con verificación de versión.
- Añade checksums SHA-256, instaladores, documentación de rollback y paquetes 0.5.0.
- Añade plantillas de issues y pull requests, Dependabot, CONTRIBUTING, CODE_OF_CONDUCT y NOTICE.
- Refuerza `.gitignore` para impedir RAW, imágenes, secretos, perfiles privados y artefactos locales.

## 0.4.0 - 2026-08-05

- Añade la skill `ai-image-studio-user-guide` y el manual consolidado.
- Añade compatibilidad documentada por plataforma y corrige afirmaciones sobre plugins.
- Añade `doctor`, `init-config` y `validate-config`.
- Añade configuración local validada que no admite secretos en texto plano.
- Añade herramientas MCP de diagnóstico y validación de configuración.
- Añade pruebas de configuración y diagnóstico.

## 0.3.0 - 2026-08-05

- Añade la skill `photographer-capture-guide`.
- Añade esquemas `CaptureGuideRequest` y `CapturePlan`.
- Añade perfiles iniciales para mobiliario, calzado, perfume/cristal, CV, bodas de día/noche, viaje e inmobiliaria.
- Añade CLI/MCP para validar solicitudes y recomendar captura.
- Añade registro versionado de las dos generaciones móviles mantenidas.
- La ruta universal activa la skill fotográfica cuando `guidance_requested=true`.
- Las recomendaciones de exposición son puntos de partida y requieren toma de prueba.

## 0.2.0 - 2026-08-05

- Añade el Modelo de Decisión Universal.
- Elimina la suposición global de fondo blanco y de cámara concreta.
- Añade políticas de fondo por categoría y salida de ambiente separada para productos.
- Añade validación y enrutamiento de decisiones mediante CLI y MCP.

## 0.1.0 - 2026-08-05

- Primera versión del núcleo portable.
- Cuatro skills enfocadas: admisión, producto estricto, control de calidad y exportación.
- Contratos JSON Schema y máquina de estados fail-closed.
- CLI determinista para inspección, hashes, máscaras, fondo, exportación y ZIP.
- Servidor MCP local opcional.
- Adaptadores de instalación para Claude Code y Codex/ChatGPT.
- Pruebas y evals iniciales.
