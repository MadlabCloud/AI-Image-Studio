# Modelo de Decisión Universal

Antes de editar, completa siete variables. Los valores `unknown` son válidos cuando el usuario no conoce el dato; no deben inventarse.

1. **Categoría**: tipo y subtipo de imagen.
2. **Destino**: canal, plataforma y perfil visual.
3. **Captura**: dispositivo, formato, escenario y si se solicita guía fotográfica.
4. **Fidelidad**: strict, commercial o creative.
5. **Fondo**: relevancia y política dependientes de la categoría.
6. **Salidas**: catálogo, ambiente, web, impresión u otros derivados.
7. **Confirmación**: el `ImageJob` no se bloquea hasta que la decisión esté confirmada.

## Principios

- No asumir una cámara concreta.
- No asumir fondo blanco.
- `product_catalog` y `product_environment` solo son válidos para productos.
- Una imagen de ambiente es un derivado separado de la imagen de catálogo.
- Si se solicita ambiente sin contexto, debe activarse `recommendations_requested=true`.
- Para personas, bodas, viajes y arquitectura, el fondo se conserva o trata según su propia política.
- La configuración de captura puede quedar desconocida; solo se pregunta cuando afecta al resultado o se solicita guía.
