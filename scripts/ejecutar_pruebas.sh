#!/usr/bin/env bash
# Ejecuta la batería automatizada del proyecto en el entorno virtual.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="$PROJECT_DIR/.venv/bin/python"

if [[ ! -x "$PYTHON" ]]; then
  echo "No encuentro el Python del entorno virtual: $PYTHON" >&2
  echo "Crea primero el entorno .venv del proyecto e instala las dependencias." >&2
  exit 1
fi

# Las pruebas de interfaz no deben necesitar un servidor gráfico.
export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-offscreen}"

cd "$PROJECT_DIR"
exec "$PYTHON" -m unittest discover -s tests -v
