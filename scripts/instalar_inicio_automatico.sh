#!/usr/bin/env bash
# Instala el inicio automático de Modo Democracia usando el gestor del sistema.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="$PROJECT_DIR/.venv/bin/python"

if [[ ! -x "$PYTHON" ]]; then
  echo "No encuentro el Python del entorno virtual: $PYTHON" >&2
  echo "Crea primero el entorno .venv del proyecto e instala las dependencias." >&2
  exit 1
fi

cd "$PROJECT_DIR"
exec "$PYTHON" -m core.autostart install
