# Contributing to AI Image Studio

Thank you for helping improve AI Image Studio. The project is developed in small, auditable microphases.

## Development setup

```bash
git clone https://github.com/MadlabCloud/AI-Image-Studio.git
cd AI-Image-Studio
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev,mcp]"
pytest
python scripts/validate_bundle.py
```

## Branches and pull requests

- Create a focused branch from `main`.
- Keep each pull request limited to one microphase or defect.
- Add or update tests for every behavioral change.
- Update `CHANGELOG.md` when behavior, schemas, commands, packaging or installation changes.
- Never commit customer images, RAW files, secrets, API keys or private brand profiles.

## Required checks

Before opening a pull request:

```bash
pytest
python scripts/validate_bundle.py
python -m compileall -q src skills
python scripts/build_distributions.py
python scripts/generate_checksums.py dist
```

## Security and privacy

Follow `SECURITY.md`. Report vulnerabilities privately rather than through a public issue.

## Licensing

Unless explicitly stated otherwise, contributions are submitted under Apache-2.0.
