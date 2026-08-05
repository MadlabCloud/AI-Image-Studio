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
if errors:
    print('\n'.join(errors),file=sys.stderr); raise SystemExit(1)
print('Bundle válido')
