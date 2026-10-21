"""Carga y validación de la configuración de Modo Democracia.

Estas funciones son puras (salvo la lectura del archivo) para poder probar las
decisiones de arranque sin abrir la interfaz, el micrófono ni el escritorio.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

DEFAULT_MODEL_PATH = "models/vosk-model-small-es-0.42"
DEFAULT_ACTIVATION_PHRASE = "modo democracia"


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
            "No se encontró el recurso obligatorio del logo.\n"
            f"Ruta comprobada: {logo}"
        )

    warnings: list[str] = []

    if wallpaper is None or not wallpaper.is_file():
        warnings.append(
            "Advertencia: imagen de fondo no disponible: "
            f"{wallpaper}. La aplicación continuará sin cambiar el fondo."
        )
        wallpaper = None

    optional = (
        ("audio", audio),
        ("icono de aplicación", app_icon),
        ("sello del Ministerio", ministry_icon),
    )

    for name, path in optional:
        if path is not None and not path.is_file():
            warnings.append(
                f"Advertencia: no se encontró {name}: {path}"
            )
            if name == "audio":
                audio = None
            elif name == "icono de aplicación":
                app_icon = None
            else:
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
        warning = (
            "Advertencia: cambio de fondo desactivado. "
            f"{unsupported_reason}"
        )
    elif requested and wallpaper is None:
        warning = (
            "Advertencia: cambio de fondo desactivado "
            "porque falta la imagen."
        )

    return WallpaperPlan(
        enabled=enabled,
        restore_on_exit=restore_on_exit,
        warning=warning,
    )


def voice_model_path(voice_config: dict, project_dir: Path) -> Path:
    """Resuelve el modelo de voz respecto a la carpeta del proyecto."""
    value = voice_config.get("model_path", DEFAULT_MODEL_PATH)

    if not value:
        value = DEFAULT_MODEL_PATH

    path = Path(str(value)).expanduser()

    if not path.is_absolute():
        path = Path(project_dir) / path

    return path


def voice_engine(voice_config: dict) -> str:
    return str(
        voice_config.get("recognition_engine", "vosk")
    ).lower()


def activation_phrase(general_config: dict) -> str:
    value = general_config.get(
        "activation_phrase", DEFAULT_ACTIVATION_PHRASE
    )
    return value if isinstance(value, str) else DEFAULT_ACTIVATION_PHRASE


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
