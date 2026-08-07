---
name: image-quality-gates
description: Compara un resultado editado con su original y aplica puertas independientes de fondo, geometría, piezas, color, bordes, dimensiones, formato y privacidad. Úsala antes de aprobar o publicar cualquier imagen editada, especialmente productos de ecommerce. No permite que una métrica global compense un fallo crítico.
license: Apache-2.0
compatibility: Usa herramientas MCP de AI Image Studio o los scripts incluidos. Requiere original, resultado y, para máxima precisión, máscara de producto.
metadata:
  version: "0.2.0"
---

# Principio fail-closed

- Todos los gates críticos en PASS → `APPROVED`.
- Algún gate en REVIEW → `HUMAN_QC`.
- Algún gate en FAIL → `REJECTED`.
- No exportes desde REVIEW o FAIL.

# Gates obligatorios

1. **source-integrity**: hash del original preservado.
2. **background**: color y uniformidad del fondo fuera de producto/sombra.
3. **mask-agreement**: acuerdo entre máscaras independientes cuando proceda.
4. **geometry**: silueta, caja, área y componentes.
5. **expected-parts**: piezas esperadas según producto y perspectiva.
6. **color**: cambio dentro del producto bajo límite calibrado.
7. **edges**: halos, dientes, transparencias y huecos.
8. **dimensions-format**: dimensiones exactas, formato y alpha.
9. **privacy**: metadatos no autorizados eliminados.

# Procedimiento

1. Carga `references/gate-policy.md`.
2. Ejecuta `image_validate_background` con máscara cuando exista. Sin MCP, usa
   `scripts/validate_background.py`.
3. Ejecuta `image_compare_masks` si hay dos máscaras. Sin MCP, usa
   `scripts/compare_masks.py`.
4. Ejecuta `image_compare_pixels` solo sobre imágenes alineadas. **Las medias globales
   no son una puerta**: un defecto pequeño en área pero destructivo se diluye en ellas.
   Lee `max_absolute_error`, `changed_pixel_ratio` y el bloque `local`:
   - pocos bloques con error muy alto → daño localizado: pieza amputada, hueco, halo;
   - casi todos los bloques con error moderado → daño global: recoloreado o cambio de tono;
   - `max_absolute_error` alto con `mae` casi cero → mira dónde antes de aprobar nada.
5. Ejecuta `image_validate_output`.
6. Realiza una revisión visual adversarial: busca motivos para rechazar.
7. Genera un informe conforme al esquema `qc-report.schema.json`.
8. No uses una puntuación media; conserva estado por gate.

# Revisión adversarial

Busca específicamente elementos añadidos, eliminados, deformados, recoloreados o reconstruidos. Para productos, revisa patas, barras, reposapiés, soportes, tornillos, costuras, cremalleras, huecos y reflejos.

# Salida

```json
{
  "overall": "PASS|REVIEW|FAIL",
  "gates": {
    "background": {"status": "PASS", "details": {}},
    "geometry": {"status": "REVIEW", "details": {}}
  },
  "warnings": []
}
```
