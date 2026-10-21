"""Adaptador de Windows.

Usa la API nativa SystemParametersInfoW, de modo que no depende de comandos de
KDE ni de una terminal. El soporte está implementado pero no se ha validado en
un equipo Windows real.
"""

from __future__ import annotations

import ctypes
import sys
from pathlib import Path

from .base import AutostartManager, WallpaperBackend

SPI_GETDESKWALLPAPER = 0x0073
SPI_SETDESKWALLPAPER = 0x0014
SPIF_UPDATEINIFILE = 0x01
SPIF_SENDCHANGE = 0x02
MAX_PATH_CHARS = 32768


class WindowsWallpaperBackend(WallpaperBackend):
    """Cambia el fondo mediante la API de usuario de Windows."""

    name = "Windows"

    def is_supported(self) -> bool:
        return sys.platform.startswith("win") and hasattr(ctypes, "windll")

    def unsupported_reason(self) -> str:
        if not sys.platform.startswith("win"):
            return "El adaptador de Windows solo funciona en Windows."
        return "No se pudo acceder a la API de configuración de Windows."

    def current_image(self) -> Path | None:
        """Lee la ruta del fondo actual mediante SPI_GETDESKWALLPAPER."""
        if not self.is_supported():
            return None

        try:
            buffer = ctypes.create_unicode_buffer(MAX_PATH_CHARS)
            ok = ctypes.windll.user32.SystemParametersInfoW(
                SPI_GETDESKWALLPAPER,
                len(buffer),
                buffer,
                0,
            )
        except (AttributeError, OSError):
            return None

        if not ok or not buffer.value:
            return None

        path = Path(buffer.value)
        return path.resolve() if path.is_file() else None

    def apply(self, image: Path) -> tuple[bool, str | None]:
        """Aplica la imagen con SystemParametersInfoW (admite rutas con espacios)."""
        if not self.is_supported():
            return False, self.unsupported_reason()

        path = Path(image).expanduser()

        if not path.is_file():
            return False, f"No se encontró la imagen de fondo: {path}"

        try:
            ok = ctypes.windll.user32.SystemParametersInfoW(
                SPI_SETDESKWALLPAPER,
                0,
                str(path.resolve()),
                SPIF_UPDATEINIFILE | SPIF_SENDCHANGE,
            )
        except (AttributeError, OSError) as exc:
            return False, (
                "No se pudo llamar a la API de Windows para cambiar el fondo: "
                f"{type(exc).__name__}: {exc}"
            )

        if not ok:
            try:
                code = ctypes.windll.kernel32.GetLastError()
            except (AttributeError, OSError):
                code = 0
            return False, (
                "Windows rechazó el cambio de fondo "
                f"(código de error {code}). Comprueba la ruta y los permisos."
            )

        return True, None


class WindowsAutostartManager(AutostartManager):
    """Inicio automático mediante la clave Run del usuario en el registro."""

    name = "Windows (HKCU Run)"
    RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
    VALUE_NAME = "ModoDemocracia"

    def is_supported(self) -> bool:
        return sys.platform.startswith("win")

    def unsupported_reason(self) -> str:
        return "El inicio automático del registro solo está disponible en Windows."

    def location(self) -> str:
        return f"HKEY_CURRENT_USER\\{self.RUN_KEY}\\{self.VALUE_NAME}"

    def _command(self) -> str:
        return (
            f'"{self.python_executable}" '
            f'"{self.app_script}" --hidden'
        )

    def is_installed(self) -> bool:
        if not self.is_supported():
            return False

        import winreg

        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.RUN_KEY,
                0,
                winreg.KEY_READ,
            ) as key:
                value, _ = winreg.QueryValueEx(key, self.VALUE_NAME)
        except (FileNotFoundError, OSError):
            return False

        return bool(value)

    def install(self) -> tuple[bool, str | None]:
        self.last_note = None

        if not self.is_supported():
            return False, self.unsupported_reason()

        if not self.app_script.is_file():
            return False, (
                "No se encontró app.py en el proyecto: "
                f"{self.app_script}"
            )

        if not self.python_executable.is_file():
            return False, (
                "No se encontró el intérprete de Python indicado: "
                f"{self.python_executable}"
            )

        import winreg

        try:
            with winreg.CreateKeyEx(
                winreg.HKEY_CURRENT_USER,
                self.RUN_KEY,
                0,
                winreg.KEY_SET_VALUE,
            ) as key:
                winreg.SetValueEx(
                    key,
                    self.VALUE_NAME,
                    0,
                    winreg.REG_SZ,
                    self._command(),
                )
        except OSError as exc:
            return False, (
                "No se pudo crear la entrada de inicio automático: "
                f"{exc}"
            )

        return True, None

    def uninstall(self) -> tuple[bool, str | None]:
        self.last_note = None

        if not self.is_supported():
            return False, self.unsupported_reason()

        import winreg

        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.RUN_KEY,
                0,
                winreg.KEY_SET_VALUE,
            ) as key:
                winreg.DeleteValue(key, self.VALUE_NAME)
        except FileNotFoundError:
            self.last_note = "El inicio automático no estaba instalado."
            return True, None
        except OSError as exc:
            return False, (
                "No se pudo eliminar la entrada de inicio automático: "
                f"{exc}"
            )

        return True, None
