# Changelog

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
