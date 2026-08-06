# Configuración del servidor MCP

El servidor MCP es **opcional**. El CLI `ai-image-studio` funciona sin él.

Código fuente del servidor: `src/ai_image_studio/mcp_server.py`
(no existe una carpeta `mcp/` en el proyecto).

## Requisito de dependencia

El extra `mcp` está limitado a un intervalo verificado:

```
mcp>=1.14,<2
```

Motivo, comprobado versión a versión:

| Rango | Comportamiento |
|---|---|
| `mcp < 1.2` | No incluye `mcp.server.fastmcp`. |
| `mcp 1.7` – `mcp 1.13` | `FastMCP` importa, pero construir el servidor falla con `TypeError: issubclass() arg 1 must be a class` (esas versiones no resuelven las anotaciones diferidas `str \| None`). |
| `mcp 1.14` – `mcp 1.29` | Correcto. Intervalo soportado. |
| `mcp >= 2.0` | Eliminó `mcp.server.fastmcp`. El servidor no arranca. |

Instalación:

```bash
pip install "ai-image-studio[mcp]"
```

Comprobación real (no basta con que el paquete esté instalado):

```bash
ai-image-studio doctor
```

El campo `mcp.state` del informe indica exactamente qué ocurre:

| `state` | Significado | `ready` |
|---|---|---|
| `absent` | El extra no está instalado. No es un fallo. | sin cambios |
| `incompatible` | `mcp` instalado pero sin `mcp.server.fastmcp` (típicamente 2.x). | `false` |
| `import_error` | `mcp.server.fastmcp` existe pero falla al importarse. | `false` |
| `build_error` | `FastMCP` importa pero el servidor no se construye. | `false` |
| `ok` | El servidor se construye correctamente. | sin cambios |

## Estrategia de configuración portable

`.mcp.json.example` usa el ejecutable `ai-image-studio-mcp`, que el propio paquete
instala como *console script*. Es la opción recomendada porque no contiene rutas
absolutas y funciona igual en los tres sistemas operativos.

```json
{
  "mcpServers": {
    "ai-image-studio": {
      "command": "ai-image-studio-mcp",
      "args": [],
      "env": {
        "AI_IMAGE_STUDIO_MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

**Condición necesaria:** el cliente MCP debe poder encontrar `ai-image-studio-mcp`
en el `PATH` del proceso que lo lanza. Un cliente arrancado desde fuera del entorno
virtual no hereda el `PATH` de ese entorno.

### Comprobar que el ejecutable es visible

Linux / macOS:

```bash
command -v ai-image-studio-mcp
```

Windows (PowerShell):

```powershell
Get-Command ai-image-studio-mcp | Select-Object -ExpandProperty Source
```

Si el comando responde con una ruta, la configuración anterior sirve tal cual.

### Alternativa: ruta explícita al entorno virtual

Si el cliente MCP no ve el ejecutable, indica la ruta absoluta del entorno virtual.
Sustituye `RUTA/DEL/PROYECTO` por la ruta real de tu equipo. **No publiques esta
variante en repositorios ni en artefactos: contiene rutas locales.**

Windows (PowerShell):

```json
{
  "mcpServers": {
    "ai-image-studio": {
      "command": "C:\\RUTA\\DEL\\PROYECTO\\.venv\\Scripts\\ai-image-studio-mcp.exe",
      "args": [],
      "env": { "AI_IMAGE_STUDIO_MCP_TRANSPORT": "stdio" }
    }
  }
}
```

Linux / macOS:

```json
{
  "mcpServers": {
    "ai-image-studio": {
      "command": "/RUTA/DEL/PROYECTO/.venv/bin/ai-image-studio-mcp",
      "args": [],
      "env": { "AI_IMAGE_STUDIO_MCP_TRANSPORT": "stdio" }
    }
  }
}
```

### Alternativa: intérprete del entorno virtual

Equivalente a la anterior, invocando el módulo. Es la única forma válida de usar
`python -m`: **nunca** el `python` global, porque fuera del entorno del proyecto
falla con `No module named ai_image_studio`.

Windows:

```json
"command": "C:\\RUTA\\DEL\\PROYECTO\\.venv\\Scripts\\python.exe",
"args": ["-m", "ai_image_studio.mcp_server"]
```

Linux / macOS:

```json
"command": "/RUTA/DEL/PROYECTO/.venv/bin/python",
"args": ["-m", "ai_image_studio.mcp_server"]
```

## Restricción de acceso al sistema de archivos

Define `AI_IMAGE_STUDIO_ALLOWED_ROOT` para que las herramientas MCP solo puedan
leer y escribir dentro de un directorio concreto:

```json
"env": {
  "AI_IMAGE_STUDIO_MCP_TRANSPORT": "stdio",
  "AI_IMAGE_STUDIO_ALLOWED_ROOT": "/RUTA/DEL/WORKSPACE"
}
```

## Diagnóstico de problemas

| Síntoma | Causa habitual | Solución |
|---|---|---|
| `No module named ai_image_studio` | Se usó el `python` global. | Usa `ai-image-studio-mcp` o el intérprete del entorno virtual. |
| `No module named 'mcp.server.fastmcp'` | `mcp` 2.x instalado. | `pip install "mcp>=1.14,<2"` |
| `TypeError: issubclass() arg 1 must be a class` | `mcp` entre 1.7 y 1.13. | `pip install "mcp>=1.14,<2"` |
| El cliente no encuentra el comando | El ejecutable no está en el `PATH` del cliente. | Usa la ruta absoluta del entorno virtual. |
