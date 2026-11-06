"""Carga y validación de la configuración de Modo Democracia.

Estas funciones son puras (salvo la lectura del archivo) para poder probar las
decisiones de arranque sin abrir la interfaz, el micrófono ni el escritorio.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from core import i18n

DEFAULT_MODEL_PATHS = {
    "es": "models/vosk-model-small-es-0.42",
    "en": "models/vosk-model-small-en-us-0.15",
}
DEFAULT_MODEL_PATH = DEFAULT_MODEL_PATHS["es"]


def load_config(path: Path) -> dict:
    """Carga un archivo TOML de configuración."""
    with Path(path).open("rb") as file:
        return tomllib.load(file)


def resolve_asset(
    assets: dict,
    key: str,
    project_dir: Path,
) -> Path | None:
    """Resuelve una ruta de recurso relativa al proyecto."""
    value = assets.get(key)

    if not value:
        return None

    path = Path(value).expanduser()

    if not path.is_absolute():
        path = Path(project_dir) / path

    return path.resolve()


def path_is_missing(path: Path | None) -> bool:
    """Indica si un recurso opcional fue configurado pero no existe."""
    return path is not None and not path.is_file()


@dataclass(frozen=True)
class AssetSelection:
    wallpaper: Path | None
    logo: Path
    audio: Path | None
    app_icon: Path | None
    ministry_icon: Path | None
    warnings: tuple[str, ...]


def prepare_assets(assets: dict, project_dir: Path) -> AssetSelection:
    """Clasifica recursos obligatorios y opcionales.

    El logo es obligatorio. La ausencia de los demás se informa y no impide
    iniciar la aplicación.
    """
    wallpaper = resolve_asset(assets, "wallpaper", project_dir)
    logo = resolve_asset(assets, "logo", project_dir)
    audio = resolve_asset(assets, "audio", project_dir)
    app_icon = resolve_asset(assets, "app_icon", project_dir)
    ministry_icon = resolve_asset(
        assets, "ministry_icon", project_dir
    )

    if logo is None or not logo.is_file():
        raise FileNotFoundError(
            i18n.t("config.error.logo_required", path=logo)
        )

    warnings: list[str] = []

    if wallpaper is None or not wallpaper.is_file():
        warnings.append(
            i18n.t("config.warning.wallpaper_missing", path=wallpaper)
        )
        wallpaper = None

    if path_is_missing(audio):
        warnings.append(
            i18n.t("config.warning.audio_missing", path=audio)
        )
        audio = None

    if path_is_missing(app_icon):
        warnings.append(
            i18n.t("config.warning.app_icon_missing", path=app_icon)
        )
        app_icon = None

    if path_is_missing(ministry_icon):
        warnings.append(
            i18n.t("config.warning.ministry_icon_missing", path=ministry_icon)
        )
        ministry_icon = None

    return AssetSelection(
        wallpaper=wallpaper,
        logo=logo,
        audio=audio,
        app_icon=app_icon,
        ministry_icon=ministry_icon,
        warnings=tuple(warnings),
    )


@dataclass(frozen=True)
class WallpaperPlan:
    enabled: bool
    restore_on_exit: bool
    warning: str | None


def plan_wallpaper(
    sequence: dict,
    support_status: tuple[bool, str],
    wallpaper: Path | None,
) -> WallpaperPlan:
    """Decide si el fondo se cambia y si debe restaurarse al salir."""
    requested = bool(sequence.get("wallpaper_enabled", True))
    restore_on_exit = bool(
        sequence.get("restore_wallpaper_on_exit", True)
    )
    supported, unsupported_reason = support_status
    enabled = requested and supported and wallpaper is not None

    warning = None

    if requested and not supported:
        warning = i18n.t(
            "config.warning.wallpaper_unsupported",
            reason=unsupported_reason,
        )
    elif requested and wallpaper is None:
        warning = i18n.t("config.warning.wallpaper_no_image")

    return WallpaperPlan(
        enabled=enabled,
        restore_on_exit=restore_on_exit,
        warning=warning,
    )


def voice_model_path(
    voice_config: dict,
    project_dir: Path,
    language: str | None = None,
) -> Path:
    """Resuelve el modelo de voz respecto a la carpeta del proyecto.

    Si `model_path` está vacío, se usa el modelo predeterminado del idioma
    activo (o del indicado explícitamente).
    """
    value = voice_config.get("model_path")

    if not value:
        code = language or i18n.get_language()
        value = DEFAULT_MODEL_PATHS.get(code, DEFAULT_MODEL_PATH)

    path = Path(str(value)).expanduser()

    if not path.is_absolute():
        path = Path(project_dir) / path

    return path


def voice_engine(voice_config: dict) -> str:
    return str(
        voice_config.get("recognition_engine", "vosk")
    ).lower()


def activation_phrase(
    general_config: dict,
    language: str | None = None,
) -> str:
    """Frase de activación configurada o la predeterminada del idioma.

    Una clave ausente usa la frase del idioma. Una clave presente y vacía
    desactiva la voz, como se documenta en la configuración.
    """
    code = language or i18n.get_language()

    if "activation_phrase" not in general_config:
        return i18n.t_for(code, "voice.phrase")

    value = general_config["activation_phrase"]

    if isinstance(value, str):
        return value

    return i18n.t_for(code, "voice.phrase")


def should_launch_game(sequence: dict, steam: dict) -> bool:
    """Helldivers 2 solo se abre si ambos interruptores están activados."""
    return bool(
        sequence.get("launch_game_after_sequence", False)
    ) and bool(steam.get("launch_enabled", False))


@dataclass(frozen=True)
class SequenceTiming:
    duration_seconds: float
    launch_delay_seconds: float
    battle_text_delay_seconds: float


def sequence_timing(sequence: dict) -> SequenceTiming:
    """Convierte las duraciones y usa el valor predeterminado si son inválidas."""
    def number(key: str, default: float) -> float:
        try:
            return float(sequence.get(key, default))
        except (TypeError, ValueError):
            return default

    return SequenceTiming(
        duration_seconds=number("duration_seconds", 13.2),
        launch_delay_seconds=number("launch_delay_seconds", 2.0),
        battle_text_delay_seconds=number(
            "battle_text_delay_seconds", 300.0
        ),
    )
