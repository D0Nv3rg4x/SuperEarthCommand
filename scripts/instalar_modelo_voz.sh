#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

LANG_CODE="${1:-es}"

case "$LANG_CODE" in
  es)
    MODEL_NAME="vosk-model-small-es-0.42"
    MODEL_LABEL="español"
    ;;
  en)
    MODEL_NAME="vosk-model-small-en-us-0.15"
    MODEL_LABEL="inglés"
    ;;
  *)
    echo "Idioma no soportado: $LANG_CODE. Usa 'es' o 'en'." >&2
    exit 2
    ;;
esac

MODEL_DIR="$PROJECT_DIR/models/$MODEL_NAME"
MODEL_URL="https://alphacephei.com/vosk/models/$MODEL_NAME.zip"

mkdir -p "$PROJECT_DIR/models"
if [[ -d "$MODEL_DIR" ]]; then
  echo "El modelo ya existe: $MODEL_DIR"
  exit 0
fi

for cmd in curl unzip; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Falta el comando '$cmd'. Instálalo con el gestor de paquetes de CachyOS y vuelve a ejecutar este script." >&2
    exit 1
  fi
done

TMP_ZIP="$(mktemp --suffix=.zip)"
TMP_DIR="$(mktemp -d)"
cleanup() { rm -f "$TMP_ZIP"; rm -rf "$TMP_DIR"; }
trap cleanup EXIT

echo "Descargando modelo de voz en $MODEL_LABEL (puede ocupar decenas de MB)..."
curl -fL --retry 2 "$MODEL_URL" -o "$TMP_ZIP"
unzip -q "$TMP_ZIP" -d "$TMP_DIR"
FOUND_MODEL="$TMP_DIR/$MODEL_NAME"
if [[ ! -d "$FOUND_MODEL" ]]; then
  echo "El ZIP descargado no contiene la carpeta esperada del modelo." >&2
  exit 1
fi
mv "$FOUND_MODEL" "$MODEL_DIR"
echo "Modelo instalado en: $MODEL_DIR"
