#!/usr/bin/env bash
#
# Instala las skills de AI Image Studio en el directorio de skills de un agente.
#
# Por defecto NO sustituye skills existentes: si detecta alguna con el mismo nombre
# se detiene sin escribir nada. Con --force sustituye, pero antes guarda una copia
# de seguridad de lo reemplazado.
#
# Codigos de salida:
#   0  correcto (o nada que hacer)
#   2  argumentos invalidos
#   3  conflicto: ya existen skills y no se indico --force
#   4  error de entrada/salida al copiar o al respaldar
set -euo pipefail

EXIT_BAD_ARGS=2
EXIT_CONFLICT=3
EXIT_IO=4

usage() {
  cat >&2 <<'USAGE'
Uso: install-skills.sh <destino> [raiz_proyecto] [opciones]

Destinos:
  claude          ~/.claude/skills
  codex           ~/.agents/skills
  project-claude  <raiz_proyecto>/.claude/skills
  project-codex   <raiz_proyecto>/.agents/skills

Opciones:
  -f, --force        Sustituye las skills existentes (crea copia de seguridad).
  -n, --dry-run      Muestra lo que haria sin escribir nada.
      --no-backup    Omite la copia de seguridad al sustituir. Requiere --force.
      --backup-root DIR
                     Directorio de copias. Por defecto
                     <destino>/.ai-image-studio-backup
  -h, --help         Muestra esta ayuda.

Ejemplos:
  install-skills.sh claude
  install-skills.sh claude --dry-run
  install-skills.sh claude --force
  install-skills.sh project-claude /ruta/al/proyecto --force
USAGE
}

TARGET=""
PROJECT_ROOT="$PWD"
FORCE=0
DRY_RUN=0
NO_BACKUP=0
BACKUP_ROOT=""
POSITIONAL=()

while [ $# -gt 0 ]; do
  case "$1" in
    -f|--force) FORCE=1; shift ;;
    -n|--dry-run) DRY_RUN=1; shift ;;
    --no-backup) NO_BACKUP=1; shift ;;
    --backup-root)
      [ $# -ge 2 ] || { echo "error: --backup-root necesita un valor" >&2; exit $EXIT_BAD_ARGS; }
      BACKUP_ROOT="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    -*) echo "error: opcion desconocida '$1'" >&2; usage; exit $EXIT_BAD_ARGS ;;
    *) POSITIONAL+=("$1"); shift ;;
  esac
done

if [ "${#POSITIONAL[@]}" -ge 1 ]; then TARGET="${POSITIONAL[0]}"; fi
if [ "${#POSITIONAL[@]}" -ge 2 ]; then PROJECT_ROOT="${POSITIONAL[1]}"; fi
if [ "${#POSITIONAL[@]}" -gt 2 ]; then
  echo "error: demasiados argumentos" >&2; usage; exit $EXIT_BAD_ARGS
fi

case "$TARGET" in
  claude) DEST="$HOME/.claude/skills" ;;
  codex) DEST="$HOME/.agents/skills" ;;
  project-claude) DEST="$PROJECT_ROOT/.claude/skills" ;;
  project-codex) DEST="$PROJECT_ROOT/.agents/skills" ;;
  "") echo "error: falta el destino" >&2; usage; exit $EXIT_BAD_ARGS ;;
  *) echo "error: destino desconocido '$TARGET'" >&2; usage; exit $EXIT_BAD_ARGS ;;
esac

if [ "$NO_BACKUP" -eq 1 ] && [ "$FORCE" -eq 0 ]; then
  echo "error: --no-backup solo tiene sentido junto con --force" >&2
  exit $EXIT_BAD_ARGS
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SOURCE="$ROOT/skills"
if [ ! -d "$SOURCE" ]; then
  echo "error: no se encuentra el directorio de skills: $SOURCE" >&2
  exit $EXIT_BAD_ARGS
fi

# ------------------------------------------------------------------ analisis previo
SKILLS=()
while IFS= read -r d; do SKILLS+=("$d"); done < <(find "$SOURCE" -mindepth 1 -maxdepth 1 -type d | sort)
if [ "${#SKILLS[@]}" -eq 0 ]; then
  echo "error: no hay skills que instalar en $SOURCE" >&2
  exit $EXIT_BAD_ARGS
fi

NEW=()
EXISTING=()
for d in "${SKILLS[@]}"; do
  name="$(basename "$d")"
  if [ -e "$DEST/$name" ]; then EXISTING+=("$name"); else NEW+=("$name"); fi
done

echo "Origen  : $SOURCE"
echo "Destino : $DEST"
echo "Skills  : ${#SKILLS[@]} detectadas -> ${#NEW[@]} nuevas, ${#EXISTING[@]} ya existentes"
for n in ${NEW+"${NEW[@]}"}; do echo "  [nueva]     $n"; done
for n in ${EXISTING+"${EXISTING[@]}"}; do echo "  [existente] $n"; done

# ------------------------------------------------------------------ puerta de seguridad
if [ "${#EXISTING[@]}" -gt 0 ] && [ "$FORCE" -eq 0 ] && [ "$DRY_RUN" -eq 0 ]; then
  echo ""
  echo "aviso: ya hay ${#EXISTING[@]} skills instaladas. No se ha modificado nada." >&2
  echo "Para sustituirlas, vuelve a ejecutar con --force:" >&2
  echo "  $0 $TARGET --force" >&2
  echo "Se guardara una copia de seguridad antes de sustituir (usa --no-backup para omitirla)." >&2
  exit $EXIT_CONFLICT
fi

if [ "$DRY_RUN" -eq 1 ]; then
  echo ""
  if [ "${#EXISTING[@]}" -gt 0 ] && [ "$FORCE" -eq 0 ]; then
    echo "Simulacion: se detendria con codigo $EXIT_CONFLICT por ${#EXISTING[@]} skills existentes."
  else
    for n in ${NEW+"${NEW[@]}"}; do echo "  instalaria  $DEST/$n"; done
    for n in ${EXISTING+"${EXISTING[@]}"}; do echo "  sustituiria $DEST/$n"; done
  fi
  echo "Simulacion (--dry-run): no se ha escrito nada."
  exit 0
fi

# ------------------------------------------------------------------ copia de seguridad
BACKUP_DIR=""
if [ "${#EXISTING[@]}" -gt 0 ] && [ "$NO_BACKUP" -eq 0 ]; then
  root="${BACKUP_ROOT:-$DEST/.ai-image-studio-backup}"
  BACKUP_DIR="$root/$(date +%Y%m%d-%H%M%S)"
  if ! mkdir -p "$BACKUP_DIR"; then
    echo "error: no se pudo crear el directorio de copia de seguridad" >&2; exit $EXIT_IO
  fi
  for n in "${EXISTING[@]}"; do
    if ! cp -R "$DEST/$n" "$BACKUP_DIR/$n"; then
      echo "error: fallo al respaldar $n" >&2; exit $EXIT_IO
    fi
  done
  echo "Copia de seguridad creada en: $BACKUP_DIR"
fi

# ------------------------------------------------------------------ instalacion
if ! mkdir -p "$DEST"; then
  echo "error: no se pudo crear el destino $DEST" >&2; exit $EXIT_IO
fi

installed=0
for d in "${SKILLS[@]}"; do
  name="$(basename "$d")"
  if ! { rm -rf "$DEST/$name" && cp -R "$d" "$DEST/$name"; }; then
    echo "error: fallo al instalar $name" >&2
    [ -n "$BACKUP_DIR" ] && echo "Puedes restaurar el estado anterior desde: $BACKUP_DIR" >&2
    exit $EXIT_IO
  fi
  installed=$((installed + 1))
done

echo ""
echo "$installed skills instaladas en: $DEST"
if [ -n "$BACKUP_DIR" ]; then
  echo "Rollback: borra las skills instaladas y copia de vuelta el contenido de $BACKUP_DIR"
fi
exit 0
