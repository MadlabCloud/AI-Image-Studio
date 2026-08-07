# Changelog

## 0.6.0 - 2026-08-06

Primera versión que amplía una capacidad del núcleo, no solo la distribución.

### Añadido

- **`compare_pixels` mide también en local.** Devuelve ahora `max_absolute_error`,
  `changed_pixel_ratio` y un bloque `local` con el peor cuadrante y cuántos superan el
  umbral. Las claves anteriores no cambian.

  Encontrado probando el flujo con una fotografía de cámara real: se borró una franja de
  producto —el equivalente a una pata perdida por el matting— y las métricas globales la
  dieron por buena, con `mae` 0,81 y `p95_absolute_error` **0,0**. Cualquier umbral basado
  en ellas habría aprobado un producto amputado, porque el daño afectaba al 1,2 % de los
  píxeles y la media lo diluía. Sobre esa misma imagen, las métricas locales dan un peor
  bloque de 121,5 y 24 bloques por encima de 10.

  Además distinguen el tipo de daño: pocos bloques con error altísimo indican una
  amputación o un hueco; casi todos los bloques con error moderado, un recoloreado.

  Con máscara, la medición local se limita al producto, de modo que una diferencia
  legítima de fondo no contamina el peor bloque.

- La skill `image-quality-gates` y la herramienta MCP explican cómo leer estas métricas.
  El principio de la skill no cambia: ninguna métrica por sí sola es una puerta.

## 0.5.2 - 2026-08-06

Corrige el último punto que impedía reproducir desde el código los artefactos publicados.
No hay cambios funcionales.

### Corregido

- **Reproducibilidad entre plataformas**: los ZIP declaraban en la cabecera de cada entrada
  el sistema que los había construido — `0` (MS-DOS) en Windows y `3` (Unix) en Linux y
  macOS. Con el contenido de las entradas idéntico byte a byte, ese único campo bastaba
  para que el mismo commit produjera SHA-256 distintos según quién empaquetase, así que los
  hashes publicados por CI no se podían reproducir desde Windows. Se fija a Unix.

  El defecto sobrevivió a la corrección de finales de línea de 0.5.1 porque se verificaba
  convirtiendo el árbol a LF y reconstruyendo **en la misma máquina**, lo que deja fuera
  precisamente los metadatos que dependen de la plataforma. Se añade una prueba que fija
  `create_system`, las marcas de tiempo y los permisos de todas las entradas.

  Los artefactos de la Release v0.5.1 no están afectados: son válidos y su
  `SHA256SUMS.txt` se corresponde con ellos. Lo que no era posible es reconstruirlos desde
  el código en un sistema distinto y obtener el mismo hash.

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
  `ai-image-studio-codex-marketplace-<version>.zip`. Su directorio raíz pasa a llamarse
  `ai-image-studio-codex/`: es el artefacto que más anida y su entrada más larga medía 132
  caracteres, demasiado cerca del límite `MAX_PATH` de Windows; ahora mide 120. El nombre
  del ZIP no cambia.
- **README por artefacto**: cada ZIP incluye documentación propia. Los tres paquetes de
  skills ya no describen rutas (`src/`, `schemas/`, `tests/`, `adapters/`…) que no contienen.
- **Documentación**: se elimina la referencia a una carpeta `mcp/` inexistente; el servidor
  está en `src/ai_image_studio/mcp_server.py`.
- **Rendimiento del conteo de componentes**: `masks._components()` indexaba el array de
  numpy píxel a píxel y barría también el fondo desde Python. Ahora recorre índices planos
  sobre secuencias nativas y solo visita el primer plano. Sobre una máscara de producto de
  1000×1000 baja de 0,36 s a 0,08 s, y en el caso patológico de fondo completo de 1,68 s a
  0,58 s. Resultado idéntico, verificado contra la implementación anterior en 1214 casos.
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
  lectura que `rmtree` no puede borrar. Al conceder permiso de escritura se conserva el
  resto del modo: asignarlo a secas dejaba un directorio POSIX en `0o200`, sin permiso de
  búsqueda, y `rmtree` fallaba justo en el caso que se intentaba resolver.

- **CLI**: cualquier error salía como traza de Python y todos compartían el código 1. Ahora
  muestra un mensaje legible en stderr y distingue: **2** entrada inválida, **3** puerta
  fail-closed, **4** entrada/salida, **1** fallo interno.
- **JSON con BOM**: el CLI y la lectura de configuración aceptan UTF-8 con BOM. El Bloc de
  notas y PowerShell lo escriben por defecto en Windows, y `json.loads` lo rechazaba, así que
  guardar un `ImageJob` con el editor más común del sistema producía un error incomprensible.

### Skills

- Los tres scripts incluidos (`compare_masks.py`, `validate_background.py`, `export_webp.py`)
  se enlazan ya desde su `SKILL.md` como alternativa sin MCP. Antes ninguna skill los
  mencionaba, aunque su campo `compatibility` los prometía.
- Esos scripts explican qué falta cuando el paquete `ai_image_studio` no está instalado, en
  lugar de terminar con un `ModuleNotFoundError` pelado. Fuera del paquete Full la inserción
  en `sys.path` no resuelve.
- Se enlazan seis archivos de `references/` que existían, viajaban en los cuatro artefactos y
  ninguna `SKILL.md` citaba.
- `photographer-capture-guide` incorpora `agents/openai.yaml`, que era la única de las seis
  sin declarar su interfaz para Codex y ChatGPT.

### Añadido

- `docs/MCP_SETUP.md` con la estrategia de configuración portable por sistema operativo y
  una tabla de compatibilidad de versiones de MCP.
- `ruff` como analizador estático, con un conjunto de reglas acotado en `pyproject.toml`,
  target `lint` en el `Makefile` y job propio en CI. El `Makefile` declaraba `lint` en
  `.PHONY` pero el target no existía.
- Pruebas nuevas para las zonas que nunca tuvieron ninguna: estructura de las seis skills,
  casos de activación de `evals/`, contrato de códigos de salida del CLI, comparación de
  máscaras, reglas de privacidad de la configuración y resolución de modelos móviles.
- Prueba que impide que `schemas/` y `src/ai_image_studio/schemas/` diverjan. Son copias
  idénticas y el código solo carga la segunda; hasta ahora nada evitaba que la primera
  quedase como documentación falsa.
- `scripts/validate_artifacts.py`, que valida los ZIP como productos independientes:
  estructura, manifiestos, JSON UTF-8, README correspondiente, ausencia de material privado,
  igualdad byte a byte de las seis skills y coincidencia de SHA-256.
- Suite de pruebas ampliada de 29 a 214 casos.
- CI en Windows, Linux y macOS, con validación de artefactos, de los manifiestos de Claude
  Code y del comportamiento real del instalador en PowerShell, incluidos los destinos
  globales `claude` y `codex` sobre un perfil aislado cuyo aislamiento se comprueba antes de
  escribir nada.

### Sin cambios

- El comportamiento de las seis skills no cambia: solo se enlaza documentación y scripts que
  ya viajaban dentro de ellas. Los esquemas, los presets y los ejemplos no se modifican.
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
