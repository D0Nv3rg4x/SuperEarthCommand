"""Catálogos de idioma y traducción de los textos visibles.

El idioma se decide una sola vez al arrancar (o al ejecutar la herramienta de
inicio automático) y afecta a toda la aplicación. No se traduce en caliente:
cambiar de idioma requiere reiniciar, igual que en la mayoría de aplicaciones
de escritorio.

Los catálogos viven en `locales/<código>.json` con claves planas. Añadir un
idioma consiste en copiar un catálogo, traducir sus valores y volver a iniciar.
Las claves ausentes caen al idioma predeterminado y, si tampoco existe, se
devuelve la propia clave para que el fallo sea visible y fácil de localizar.
"""

from __future__ import annotations

import json
import locale
import os
from functools import lru_cache
from pathlib import Path

LOCALES_DIR = Path(__file__).resolve().parents[1] / "locales"

DEFAULT_LANGUAGE = "es"
# Idioma internacional cuando `language = "auto"` no encuentra una traducción.
INTERNATIONAL_LANGUAGE = "en"

_current_language = DEFAULT_LANGUAGE


def available_languages() -> tuple[str, ...]:
    """Devuelve los códigos de idioma con catálogo instalado."""
    return tuple(
        sorted(path.stem for path in LOCALES_DIR.glob("*.json"))
    )


def normalize_language(value: object) -> str | None:
    """Convierte `es_CL.UTF-8`, `en-US` o `EN` en un código disponible."""
    if value is None:
        return None

    raw = str(value).strip().lower().replace("_", "-")
    raw = raw.split(".")[0].split("@")[0]

    if not raw:
        return None

    code = raw.split("-")[0]
    return code if code in available_languages() else None


def system_language() -> str | None:
    """Detecta el idioma del sistema sin depender de Qt."""
    candidates: list[str] = []

    for variable in ("LC_ALL", "LC_MESSAGES", "LANGUAGE"):
        value = os.environ.get(variable, "").strip()
        if value:
            candidates.extend(value.split(":"))

    candidates.append(os.environ.get("LANG", "").strip())

    try:
        candidates.append(locale.getlocale()[0] or "")
    except (ValueError, TypeError):
        pass

    for candidate in candidates:
        code = normalize_language(candidate)
        if code:
            return code
    return None


def resolve_language(value: object = None) -> str:
    """Decide el idioma final a partir del valor de `config.toml`.

    - Ausente o vacío: español, el comportamiento histórico del proyecto.
    - `auto`: idioma del sistema; si no hay catálogo, inglés.
    - Código desconocido: español.
    """
    if value is None:
        return DEFAULT_LANGUAGE

    text = str(value).strip().lower()

    if not text:
        return DEFAULT_LANGUAGE

    if text == "auto":
        return system_language() or INTERNATIONAL_LANGUAGE

    return normalize_language(text) or DEFAULT_LANGUAGE


def set_language(value: object = None) -> str:
    """Fija el idioma global y devuelve el código aplicado."""
    global _current_language
    _current_language = resolve_language(value)
    return _current_language


def get_language() -> str:
    return _current_language


@lru_cache(maxsize=None)
def catalog(language: str) -> dict[str, str]:
    """Carga (y memoriza) el catálogo de un idioma."""
    path = LOCALES_DIR / f"{language}.json"

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}

    if not isinstance(data, dict):
        return {}

    return {
        str(key): str(value)
        for key, value in data.items()
        if isinstance(value, str)
    }


def t_for(language: str, key: str, **params) -> str:
    """Traduce una clave para un idioma concreto."""
    text = catalog(language).get(key)

    if text is None and language != DEFAULT_LANGUAGE:
        text = catalog(DEFAULT_LANGUAGE).get(key)

    if text is None:
        return key

    if not params:
        return text

    try:
        return text.format(**params)
    except (KeyError, IndexError, ValueError):
        # Una plantilla mal formada nunca debe impedir que la app arranque.
        return text


def t(key: str, **params) -> str:
    """Traduce una clave en el idioma activo."""
    return t_for(_current_language, key, **params)
