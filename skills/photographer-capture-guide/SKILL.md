---
name: photographer-capture-guide
description: Prepara una guía de captura antes de fotografiar productos, personas, bodas, viajes, arquitectura o interiores. Úsala cuando el usuario pregunte cómo configurar una cámara o un móvil, cómo iluminar una escena, qué fotos hacer o cómo evitar errores de captura. No asumas una marca concreta; ofrece pasos específicos de iPhone o Samsung solo para las dos generaciones mantenidas y tras verificar el modelo exacto.
license: Apache-2.0
compatibility: Funciona como manual de instrucciones y aprovecha image_validate_capture_request e image_recommend_capture cuando las herramientas MCP de AI Image Studio están disponibles.
metadata:
  version: "0.3.0"
---

# Objetivo

Convertir una situación fotográfica en un plan de captura práctico, verificable y adaptado al sujeto, la luz, el movimiento, el dispositivo, los recursos y el destino final.

# Reglas críticas

1. No asumas cámara, objetivo, móvil, luz ni configuración.
2. Inspecciona metadatos cuando existan, pero no los inventes.
3. Trata los valores ISO, apertura y velocidad como puntos de partida, no como exposición garantizada.
4. Separa principios universales de pasos específicos del dispositivo.
5. Para móviles, usa instrucciones específicas solo si el modelo pertenece a las dos generaciones registradas y la función está verificada para ese modelo; el alcance exacto está en `references/smartphone-support-policy.md`.
6. Para otros móviles, ofrece guía genérica segura.
7. El fondo ecommerce solo pertenece a la rama de producto y depende del canal o perfil del cliente.
8. Para personas, bodas, viajes e interiores, el fondo y el ambiente se tratan según la categoría.
9. Haz una toma de prueba y exige revisar histograma, enfoque y altas luces.
10. No continúes con una recomendación precisa cuando falten datos críticos; formula como máximo cinco preguntas.

# Flujo

1. Completa `references/capture-request-template.json`.
2. Consulta `references/manual-architecture.md`, `references/capture-matrix.md` y `references/camera-universal-controls.md`.
3. Valida con `image_validate_capture_request` cuando esté disponible.
4. Genera el plan con `image_recommend_capture`.
5. Adapta el nivel de explicación a principiante, intermedio o avanzado.
6. Presenta: preparación, iluminación, ajustes iniciales, enfoque, composición, lista de tomas, comprobación y riesgos.
7. Tras la primera prueba, ajusta mediante evidencia real: histograma, zonas quemadas, trepidación, ruido y profundidad de campo.

# Salida

```text
PLAN DE CAPTURA
Escenario y objetivo:
Datos comprobados:
Suposiciones:
Preguntas pendientes:
Preparación:
Iluminación:
Ajustes iniciales de cámara:
Pasos para móvil, si procede:
Composición:
Lista de tomas:
Control antes de terminar:
Riesgos y correcciones:
```
