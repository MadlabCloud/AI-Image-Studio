---
name: image-export-packager
description: Exporta imágenes ya aprobadas a PNG, JPEG o WebP, preserva proporciones, aplica dimensiones exactas, elimina metadatos no autorizados, normaliza nombres y crea ZIP con manifiesto y hashes. Úsala solo después de que el control de calidad haya dado PASS.
license: Apache-2.0
compatibility: Usa herramientas MCP de AI Image Studio o scripts deterministas incluidos. No realiza retoque creativo.
metadata:
  version: "0.2.0"
---

# Precondición

No exportes si el informe QC no tiene `overall: PASS` o no existe una aprobación humana equivalente documentada.

# Flujo

1. Verifica estado `APPROVED`.
2. Normaliza el nombre: minúsculas, guiones, sin espacios ni tildes.
3. Usa el perfil de salida indicado en `decision.destination.profile_id` y `ImageJob.output`.
   - No impongas fondo blanco salvo que el perfil lo exija.
   - Usa `contain`, nunca `stretch`, salvo instrucción validada.
   - Elimina metadatos privados en derivados web.
4. Usa `image_export_webp` o `image_export_png`. Sin MCP, usa `scripts/export_webp.py`.
5. Usa `image_validate_output` sobre cada derivado.
6. Calcula SHA-256.
7. Crea ZIP mediante `image_package`.
8. Incluye `artifact-manifest.json`.

# Prohibiciones

- No deformes para rellenar el lienzo.
- No sobrescribas originales.
- No cambies la imagen durante la exportación salvo escala, composición sobre fondo y compresión especificadas.
- No empaquetes archivos que no hayan pasado validación.
