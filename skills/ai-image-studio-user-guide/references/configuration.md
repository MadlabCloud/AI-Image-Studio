# Configuración

El archivo de configuración es local, versionable sin secretos y validado por JSON Schema.

## Principios

- `preserve_originals` siempre es `true`.
- `fail_closed` y `human_review_on_uncertainty` siempre son `true`.
- Los servicios externos están desactivados por defecto.
- Las claves se pasan mediante variables de entorno; nunca se escriben en el JSON.
- Habilitar un proveedor externo exige autorización de subida y aceptación de su política de datos.

## Comandos

```bash
ai-image-studio init-config ./ai-image-studio.config.json
ai-image-studio validate-config ./ai-image-studio.config.json
```

## Perfiles del cliente

Los perfiles de ecommerce, marca o marketplace deben guardarse separados de la configuración general. Pueden definir fondo, tamaño, escala visual, sombra, nomenclatura y formatos sin afectar a bodas, retratos, viajes u otras categorías.
