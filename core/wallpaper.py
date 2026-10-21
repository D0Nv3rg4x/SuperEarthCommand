"""Controlador genérico del fondo de pantalla.

La lógica de estado, activación y restauración es común. Los comandos y API
concretos viven en `platforms/`; este módulo no contiene detalles de KDE,
Windows ni macOS.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from platforms import get_wallpaper_backend
from platforms.base import WallpaperBackend


def state_directory() -> Path:
    """Devuelve la carpeta de estado propia de cada plataforma."""
    if sys.platform.startswith("win"):
        base = Path(
            os.environ.get(
                "LOCALAPPDATA",
                Path.home() / "AppData" / "Local",
            )
        )
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(
            os.environ.get(
                "XDG_STATE_HOME",
                Path.home() / ".local/state",
            )
        )

    return base / "modo-democracia"


def _state_paths() -> tuple[Path, Path]:
    directory = state_directory()
    return directory, directory / "wallpaper-state.json"


class WallpaperController:
    """Gestiona el fondo sin modificarlo hasta que se inicia el protocolo."""

    def __init__(
        self,
        target_image: Path | None,
        enabled: bool = True,
        restore_on_exit: bool = True,
        backend: WallpaperBackend | None = None,
    ):
        self.target_image = (
            Path(target_image).expanduser().resolve()
            if target_image is not None
            else None
        )
        self.enabled = enabled
        self.restore_on_exit = restore_on_exit
        self.backend = backend or get_wallpaper_backend()

        self.state_dir, self.state_file = _state_paths()

        self.active = False
        self.original_image: Path | None = None
        self.last_error: str | None = None

    @classmethod
    def is_supported(cls) -> bool:
        """Comprueba si la plataforma actual puede cambiar el fondo."""
        return get_wallpaper_backend().is_supported()

    @classmethod
    def support_status(cls) -> tuple[bool, str]:
        """Devuelve disponibilidad y el motivo cuando no está disponible."""
        backend = get_wallpaper_backend()
        supported = backend.is_supported()
        return supported, "" if supported else backend.unsupported_reason()

    @classmethod
    def recover_stale_state(cls) -> tuple[bool, str | None]:
        """Intenta restaurar un fondo guardado por una ejecución anterior."""
        _, state_file = _state_paths()

        if not state_file.is_file():
            return True, None

        backend = get_wallpaper_backend()

        if not backend.is_supported():
            return False, backend.unsupported_reason()

        try:
            data = json.loads(
                state_file.read_text(encoding="utf-8")
            )
            original = Path(data["original_image"]).expanduser()

            if not original.is_file():
                return False, (
                    "El fondo original guardado ya no existe: "
                    f"{original}"
                )

            ok, error = backend.apply(original)

            if ok:
                state_file.unlink(missing_ok=True)
                return True, None

            return False, error

        except (OSError, ValueError, KeyError, TypeError) as exc:
            return False, (
                f"No se pudo recuperar el fondo anterior: {exc}"
            )

    def activate(self) -> tuple[bool, str | None]:
        """Guarda el fondo actual y aplica la bandera de Super Tierra."""
        if not self.enabled:
            return True, None

        if self.active:
            return True, None

        if self.target_image is None or not self.target_image.is_file():
            self.last_error = (
                "No se encontró la imagen de Super Tierra: "
                f"{self.target_image}"
            )
            return False, self.last_error

        if not self.backend.is_supported():
            self.last_error = self.backend.unsupported_reason()
            return False, self.last_error

        original = self.backend.current_image()

        if original is None:
            self.last_error = (
                "No pude identificar una imagen de fondo local mediante "
                f"{self.backend.name}. Por seguridad, no se cambiará el fondo."
            )
            return False, self.last_error

        if original == self.target_image:
            self.original_image = original
            self.active = True
            return True, None

        try:
            self.state_dir.mkdir(
                parents=True,
                exist_ok=True,
            )
            self.state_file.write_text(
                json.dumps(
                    {"original_image": str(original)},
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
        except OSError as exc:
            self.last_error = (
                "No se pudo guardar una copia del fondo original: "
                f"{exc}"
            )
            return False, self.last_error

        ok, error = self.backend.apply(self.target_image)

        if not ok:
            # Si el comando falla tras modificar parcialmente el fondo,
            # intentamos restaurarlo y conservamos el estado si falla.
            restored, restore_error = self.backend.apply(original)

            if restored:
                try:
                    self.state_file.unlink(missing_ok=True)
                except OSError:
                    pass

            self.last_error = error or restore_error
            return False, self.last_error

        self.original_image = original
        self.active = True
        self.last_error = None
        return True, None

    def restore(self) -> tuple[bool, str | None]:
        """Restaura el fondo según la política configurada.

        Si la función está deshabilitada, no toca el escritorio ni el estado
        persistente. Si se pidió no restaurar al salir, deja el fondo actual
        como está y elimina el estado pendiente para que un inicio posterior
        no lo restaure de forma inesperada.
        """
        if not self.enabled:
            return True, None

        if not self.restore_on_exit:
            try:
                self.state_file.unlink(missing_ok=True)
            except OSError as exc:
                self.last_error = (
                    "No se pudo eliminar el estado pendiente del fondo: "
                    f"{exc}"
                )
                return False, self.last_error

            self.active = False
            self.original_image = None
            self.last_error = None
            return True, None

        if not self.active and not self.state_file.is_file():
            return True, None

        original = self.original_image

        if original is None and self.state_file.is_file():
            try:
                data = json.loads(
                    self.state_file.read_text(encoding="utf-8")
                )
                original = Path(data["original_image"]).expanduser()
            except (OSError, ValueError, KeyError, TypeError) as exc:
                self.last_error = (
                    "No se pudo leer la copia del fondo original: "
                    f"{exc}"
                )
                return False, self.last_error

        if original is None or not original.is_file():
            self.last_error = (
                "El archivo del fondo original no está disponible: "
                f"{original}"
            )
            return False, self.last_error

        ok, error = self.backend.apply(original)

        if ok:
            self.active = False
            self.original_image = None
            self.last_error = None

            try:
                self.state_file.unlink(missing_ok=True)
            except OSError:
                # Conservamos el estado para intentar recuperarlo más tarde.
                pass

            return True, None

        self.last_error = error
        return False, error
