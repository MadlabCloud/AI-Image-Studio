import json
import re
from pathlib import Path


def test_skill_manifests():
    root=Path(__file__).resolve().parents[1]
    for skill in (root/'skills').iterdir():
        if not skill.is_dir(): continue
        text=(skill/'SKILL.md').read_text(encoding='utf-8')
        assert text.startswith('---\n')
        assert re.search(r'^name:\s*'+re.escape(skill.name)+r'\s*$',text,re.M)
        assert re.search(r'^description:\s*.+$',text,re.M)
        assert len(text.splitlines()) <= 500

def test_packaged_schemas_match():
    root=Path(__file__).resolve().parents[1]
    for p in (root/'schemas').glob('*.json'):
        a=json.loads(p.read_text())
        b=json.loads((root/'src/ai_image_studio/schemas'/p.name).read_text())
        assert a==b
