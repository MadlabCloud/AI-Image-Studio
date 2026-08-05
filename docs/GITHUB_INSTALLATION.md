# Installation and distribution through GitHub

Canonical repository: `MadlabCloud/AI-Image-Studio`.

## Choose an installation path

### Development installation

Use this when contributing code or running the complete test suite.

```bash
git clone https://github.com/MadlabCloud/AI-Image-Studio.git
cd AI-Image-Studio
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev,mcp]"
pytest
ai-image-studio doctor
```

### Stable user installation from a GitHub Release

1. Open the Releases page.
2. Download the full package for the required version and `SHA256SUMS.txt`.
3. Verify the archive checksum.
4. Extract it.
5. Run `install.ps1` on Windows or `install.sh` on macOS/Linux.

Never install production systems directly from an untagged `main` snapshot.

## Installation targets

- `claude`: personal Claude Code skills.
- `codex`: personal Codex skills.
- `project-claude`: `.claude/skills` in one project.
- `project-codex`: `.agents/skills` in one project.
- `cli`: local Python virtual environment and command-line tools.
- `all`: CLI plus personal Claude and Codex skills.

## Windows

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install.ps1 -Target all
```

Project-scoped installation:

```powershell
.\install.ps1 -Target project-claude -ProjectRoot "C:\Projects\MyProject"
```

## macOS and Linux

```bash
chmod +x install.sh
./install.sh all
```

Project-scoped installation:

```bash
./install.sh project-codex /path/to/project
```

## Releases

Tags matching `v*` trigger the release workflow. The workflow runs tests, validates the bundle, builds packages, generates SHA-256 checksums and attaches the artifacts to a GitHub Release. A failure blocks publication.

## Updating

- Read `CHANGELOG.md`.
- Download a tagged stable release.
- Verify its checksum.
- Back up user configuration and private profiles.
- Run the installer and then `ai-image-studio doctor`.
- Keep the previous release until real-image validation passes.

## Rollback

Reinstall the previous tagged release. User configuration and private client profiles must live outside the repository and release directory so a rollback does not overwrite them.
