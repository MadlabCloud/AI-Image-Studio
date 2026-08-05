---
name: product-image-pipeline
description: Prepara fotografías reales de productos para ecommerce con fidelidad estricta: preserva el original, corrige luz y color, elimina el fondo mediante máscara, compone sobre blanco y bloquea cualquier cambio de geometría, piezas, materiales o color. Úsala para sillas, taburetes, mobiliario y otros productos de catálogo. No la uses para escenas publicitarias creativas o rediseños del producto.
license: Apache-2.0
compatibility: Funciona como procedimiento portable. Para ejecución determinista usa las herramientas MCP de AI Image Studio y un motor de revelado/segmentación autorizado.
metadata:
  version: "0.2.0"
---

# Regla principal

En `strict`, los píxeles del producto deben proceder de la fotografía original revelada. Está prohibido regenerar la imagen completa del producto.

# Prerrequisitos

- `ImageJob` confirmado y bloqueado.
- Original preservado con SHA-256.
- Operaciones permitidas y prohibidas explícitas.

# Flujo estricto

1. Inspecciona el original y su pareja RAW/JPEG, si existe.
2. Si es RAW, usa un revelador real; no confundas la previsualización con revelado RAW.
3. Guarda el revelado intermedio sin pérdida o con mínima pérdida.
4. Obtén dos máscaras independientes cuando el producto tenga patas finas, huecos, metal, cristal o poco contraste.
5. Compara las máscaras con `image_compare_masks`.
6. Si la discrepancia supera los límites de `references/quality-thresholds.md`, detente en `NEEDS_REVIEW`.
7. Compón los píxeles originales sobre el fondo objetivo.
8. Limita la generación a zonas externas al producto mediante máscara protegida.
9. Conserva estructura, perspectiva, número de piezas, costuras, tornillos, materiales, textura y color.
10. Entrega el candidato a `image-quality-gates` antes de exportar.

# Edición permitida en strict

- Revelado RAW documentado.
- Exposición, balance de blancos, luces, sombras y lente.
- Reducción moderada de ruido y nitidez.
- Máscara y sustitución del fondo.
- Eliminación puntual de polvo o manchas, con registro.
- Sombra original recuperada o sombra de contacto controlada.

# Edición prohibida en strict

- Generación completa del producto.
- Relleno generativo sobre el producto sin máscara pequeña y revisión.
- Recoloración.
- Cambio de forma, proporciones o perspectiva.
- Añadir o eliminar patas, soportes, tornillos, barras, costuras o cremalleras.
- Simetrización artificial.
- Sustituir materiales o texturas.

# Política de fondo y salidas

- Usa `decision.background`; no asumas fondo blanco.
- El perfil puede venir de la web, marketplace, identidad visual o briefing del cliente.
- Si se exige `#FFFFFF`, valida uniformidad, ausencia de horizonte y sombra autorizada.
- La imagen de catálogo y la imagen de ambiente son derivados distintos.
- Para ambiente, exige contexto del usuario, imagen de referencia o `recommendations_requested=true`.
- La generación de ambiente no puede modificar el producto maestro ni sustituir la imagen de catálogo.

# Salida

No declares el resultado aprobado. Pásalo siempre a `image-quality-gates`.
