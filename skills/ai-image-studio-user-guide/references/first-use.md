# Primer uso

## 1. Crear el espacio de trabajo

```bash
ai-image-studio init-config ./ai-image-studio.config.json --workspace-root ./workspace
ai-image-studio validate-config ./ai-image-studio.config.json
ai-image-studio doctor --workspace ./workspace
```

## 2. Probar sin editar

Empieza con una imagen no sensible y solicita:

```text
Analiza esta imagen con AI Image Studio. No la edites todavía. Clasifica el encargo, indica datos comprobados, preguntas pendientes, flujo recomendado y limitaciones actuales.
```

## 3. Confirmar la especificación

Revisa categoría, destino, fidelidad, política de fondo y salidas. El fondo blanco no es universal: solo se aplica cuando el perfil de producto o la plataforma lo exige.

## 4. Captura, si procede

Cuando todavía no existen las fotos, activa `photographer-capture-guide`. La exposición recomendada es un punto de partida y debe validarse mediante una toma de prueba.

## 5. Edición

En la versión actual, las skills y controles están disponibles, pero los motores RAW, segmentación doble y edición generativa externa deben instalarse o conectarse por separado. No presentes una recomendación como una edición ejecutada.

## 6. Validar y exportar

```bash
ai-image-studio validate-output resultado.png --width 1000 --height 1000 --format PNG
ai-image-studio export-webp resultado.png resultado.webp --width 1000 --height 1000
ai-image-studio package ./salidas ./entrega.zip --job-id prueba-001
```
