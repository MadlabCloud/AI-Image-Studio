from pathlib import Path
import re, sys, json
ROOT=Path(__file__).resolve().parents[1]
errors=[]
for skill in sorted((ROOT/'skills').iterdir()):
    if not skill.is_dir(): continue
    p=skill/'SKILL.md'
    if not p.is_file(): errors.append(f"{skill.name}: falta SKILL.md"); continue
    text=p.read_text(encoding='utf-8')
    m=re.match(r'^---\n(.*?)\n---\n',text,re.S)
    if not m: errors.append(f"{skill.name}: frontmatter inválido"); continue
    fm=m.group(1)
    name=re.search(r'^name:\s*(.+)$',fm,re.M)
    desc=re.search(r'^description:\s*(.+)$',fm,re.M)
    if not name or name.group(1).strip()!=skill.name: errors.append(f"{skill.name}: name no coincide")
    if not desc or not desc.group(1).strip(): errors.append(f"{skill.name}: description vacía")
    if desc and len(desc.group(1).strip())>1024: errors.append(f"{skill.name}: description >1024")
    if len(text.splitlines())>500: errors.append(f"{skill.name}: SKILL.md >500 líneas")
for schema in (ROOT/'schemas').glob('*.json'):
    try: json.loads(schema.read_text(encoding='utf-8'))
    except Exception as e: errors.append(f"{schema.name}: JSON inválido {e}")

# --- Todo JSON del repositorio debe ser UTF-8 válido y sin BOM -------------------
SKIP_JSON = {'.git', '.venv', 'node_modules', '__pycache__', 'dist', '.build-dist', '.pytest_cache'}
for path in sorted(ROOT.rglob('*.json')):
    rel = path.relative_to(ROOT)
    if any(part in SKIP_JSON for part in rel.parts):
        continue
    raw = path.read_bytes()
    if raw.startswith(b'\xef\xbb\xbf'):
        errors.append(f"{rel.as_posix()}: JSON con BOM UTF-8")
        continue
    try:
        json.loads(raw.decode('utf-8'))
    except Exception as e:
        errors.append(f"{rel.as_posix()}: JSON inválido o no UTF-8: {e}")

# --- Manifiestos de distribución --------------------------------------------------
try:
    try: import tomllib
    except ModuleNotFoundError: import tomli as tomllib
    version = tomllib.loads((ROOT/'pyproject.toml').read_text(encoding='utf-8'))['project']['version']
except Exception as e:  # pragma: no cover - pyproject ilegible
    version = None
    errors.append(f"pyproject.toml: no se pudo leer la versión: {e}")

def _load(rel):
    path = ROOT / rel
    if not path.is_file():
        errors.append(f"{rel}: falta el manifiesto"); return None
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception as e:
        errors.append(f"{rel}: JSON inválido: {e}"); return None

claude_plugin = _load('.claude-plugin/plugin.json')
claude_market = _load('.claude-plugin/marketplace.json')
codex_plugin = _load('.codex-plugin/plugin.json')

if claude_market is not None:
    if not claude_market.get('description'):
        errors.append(".claude-plugin/marketplace.json: falta 'description' (claude plugin validate --strict lo exige)")
    entries = claude_market.get('plugins') or []
    if len(entries) != 1:
        errors.append(".claude-plugin/marketplace.json: se espera exactamente un plugin")
    else:
        entry = entries[0]
        if entry.get('source') != './':
            errors.append(f".claude-plugin/marketplace.json: source debe ser './', es {entry.get('source')!r}")
        if not entry.get('description'):
            errors.append(".claude-plugin/marketplace.json: la entrada del plugin no tiene descripción")
        if version and entry.get('version') != version:
            errors.append(f".claude-plugin/marketplace.json: versión {entry.get('version')} != {version}")

for label, manifest in (('.claude-plugin/plugin.json', claude_plugin), ('.codex-plugin/plugin.json', codex_plugin)):
    if manifest is None:
        continue
    if manifest.get('name') != 'ai-image-studio':
        errors.append(f"{label}: 'name' debe ser 'ai-image-studio'")
    if version and manifest.get('version') != version:
        errors.append(f"{label}: versión {manifest.get('version')} != {version}")
    skills_ref = manifest.get('skills')
    if skills_ref and not (ROOT / skills_ref.lstrip('./')).is_dir():
        errors.append(f"{label}: 'skills' apunta a una ruta inexistente: {skills_ref}")

# --- README específico por artefacto ----------------------------------------------
for artifact in ('full', 'claude-plugin', 'codex-marketplace', 'standalone-skills'):
    readme = ROOT / 'packaging' / f'README-{artifact}.md'
    if not readme.is_file():
        errors.append(f"packaging/README-{artifact}.md: falta el README específico del artefacto")

# --- Ejemplo de configuración MCP portable ----------------------------------------
example = ROOT / '.mcp.json.example'
if not example.is_file():
    errors.append('.mcp.json.example: falta el ejemplo de configuración MCP')
else:
    try:
        servers = json.loads(example.read_text(encoding='utf-8'))['mcpServers']
        command = servers['ai-image-studio']['command']
        if command == 'python':
            errors.append(".mcp.json.example: 'python' global no es portable; usa 'ai-image-studio-mcp'")
        if re.search(r'^[A-Za-z]:[\\/]|^/home/|^/Users/', str(command)):
            errors.append(f".mcp.json.example: contiene una ruta local: {command}")
    except Exception as e:
        errors.append(f".mcp.json.example: estructura inesperada: {e}")

if errors:
    print('\n'.join(errors),file=sys.stderr); raise SystemExit(1)
print('Bundle válido')
