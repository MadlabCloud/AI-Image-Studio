---
name: image-intake-router
description: Analiza una imagen o tanda antes de editarla, clasifica el encargo, inspecciona archivos, hace solo las preguntas necesarias y bloquea una especificación de trabajo. Úsala para solicitudes de edición, retoque, limpieza, conversión o preparación de imágenes cuando el objetivo, la fidelidad o la salida todavía no estén definidos. No la uses para una simple conversión ya totalmente especificada.
license: Apache-2.0
compatibility: Requiere capacidad para leer imágenes. Aprovecha herramientas MCP de AI Image Studio cuando estén disponibles; puede funcionar como flujo de instrucciones sin MCP.
metadata:
  version: "0.2.0"
---

# Objetivo

Convertir una petición ambigua en un `ImageJob` explícito antes de editar.

# Reglas críticas

1. Inspecciona primero los archivos; pregunta después.
2. No repitas información que el usuario ya dio.
3. Formula como máximo cinco preguntas por bloque.
4. Incluye opciones `No lo sé`, `Analízalo tú` o `Elige la opción profesional`.
5. Separa `comprobado`, `probable` y `necesita confirmación`.
6. No inventes EXIF, cámara, ajustes, formato RAW ni herramientas.
7. No edites antes de bloquear la especificación, salvo modo rápido explícito.
8. Ante incertidumbre crítica, marca `NEEDS_REVIEW`; no asumas.

# Flujo

1. Usa `image_inspect` para cada archivo, si está disponible.
2. Completa las siete variables de `references/universal-decision-model.md`, partiendo de `references/universal-decision-template.json`.
3. Usa `references/decision-matrix.md` y `references/question-policy.md` para preguntar solo lo necesario.
4. Valida la decisión con `image_validate_decision`, si está disponible.
5. Usa `image_route_decision` para seleccionar la ruta sin asumir cámara ni fondo.
6. Define operaciones permitidas y prohibidas.
7. Presenta un resumen breve de configuración.
8. Solicita confirmación, salvo modo rápido.
9. Genera un `ImageJob` a partir de `references/image-job-template.json`, incluyendo el objeto `decision`.
10. Usa `image_prepare_job` para validar y preservar el original.

# Respuesta previa a la edición

```text
DIAGNÓSTICO
Categoría:
Uso final:
Comprobado:
Probable:
Falta confirmar:
Riesgos:

CONFIGURACIÓN PROPUESTA
Fidelidad:
Cambios permitidos:
Cambios prohibidos:
Fondo y política aplicable:
Captura y guía solicitada:
Salidas, incluida imagen de ambiente:
```

# Derivación

- Producto/ecommerce → `product-image-pipeline`.
- Validación del resultado → `image-quality-gates`.
- Conversión, nombres o ZIP → `image-export-packager`.
- Otros tipos → consulta `references/category-router.md` y aplica el prompt universal conservador.
