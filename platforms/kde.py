"""Adaptador KDE Plasma 6.

Conserva el mecanismo ya validado en CachyOS: plasma-apply-wallpaperimage y la
lectura de la imagen actual desde la configuración de Plasma. No se asume que
otros escritorios de Linux compartan estos comandos o formatos.
"""

from __future__ import annotations

import configparser
import os
import re
import shutil
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlparse

from .base import WallpaperBackend

PLASMA_COMMAND = "plasma-apply-wallpaperimage"
PLASMA_CONFIG = "plasma-org.kde.plasma.desktop-appletsrc"


class KDEWallpaperBackend(WallpaperBackend):
    """Implementación específica de KDE Plasma 6."""

    name = "KDE Plasma 6"

    @staticmethod
    def _command() -> str | None:
        """Devuelve la ruta al comando de KDE si está instalado."""
        return shutil.which(PLASMA_COMMAND)

    @classmethod
    def _desktops(cls) -> set[str]:
        raw = (
            os.environ.get("XDG_CURRENT_DESKTOP", "")
            + ":"
            + os.environ.get("XDG_SESSION_DESKTOP", "")
        )
        return {
            value.strip().lower()
            for value in raw.replace(":", ";").split(";")
            if value.strip()
        }

    @classmethod
    def is_supported(cls) -> bool:
        """Comprueba que el escritorio es KDE Plasma 6 y el comando existe."""
        desktops = cls._desktops()

        return (
            any(
                "kde" in desktop or "plasma" in desktop
                for desktop in desktops
            )
            and os.environ.get("KDE_SESSION_VERSION", "").strip() == "6"
            and cls._command() is not None
        )

    @classmethod
    def unsupported_reason(cls) -> str:
        desktops = cls._desktops()

        if not any(
            "kde" in desktop or "plasma" in desktop
            for desktop in desktops
        ):
            return (
                "El escritorio actual no es KDE Plasma. "
                "No se asume compatibilidad con otros escritorios."
            )

        if os.environ.get("KDE_SESSION_VERSION", "").strip() != "6":
            return "El cambio de fondo implementado requiere KDE Plasma 6."

        if cls._command() is None:
            return (
                "No se encontró plasma-apply-wallpaperimage. "
                "Comprueba que Plasma Workspace esté instalado."
            )

        return ""

    @staticmethod
    def _to_local_path(value: str) -> Path | None:
        """Convierte una ruta o URL file:// en una ruta local existente."""
        value = value.strip().strip('"')

        if not value:
            return None

        if value.startswith("file:"):
            parsed = urlparse(value)
            if parsed.scheme != "file":
                return None
            value = unquote(parsed.path)
        elif "://" in value:
            return None

        path = Path(value).expanduser()

        if path.is_absolute() and path.is_file():
            return path.resolve()

        return None

    @classmethod
    def _read_current_image(cls) -> Path | None:
        """Busca la imagen de fondo local en la configuración de Plasma."""
        config_file = Path.home() / ".config" / PLASMA_CONFIG

        if not config_file.is_file():
            return None

        parser = configparser.ConfigParser(
            interpolation=None,
            strict=False,
        )
        parser.optionxform = str.lower

        try:
            parser.read(config_file, encoding="utf-8")
        except (OSError, configparser.Error):
            return None

        candidates: list[Path] = []

        for section in parser.sections():
            normalized = section.lower()

            if "wallpaper" not in normalized or "general" not in normalized:
                continue

            image = parser.get(section, "image", fallback="")
            path = cls._to_local_path(image)

            if path and path not in candidates:
                candidates.append(path)

        if candidates:
            return candidates[-1]

        # Fallback para variantes del formato de configuración de KDE.
        try:
            text = config_file.read_text(
                encoding="utf-8",
                errors="ignore",
            )
        except OSError:
            return None

        fallback_candidates: list[Path] = []

        for match in re.finditer(
            r"(?im)^Image\s*=\s*(.+?)\s*$",
            text,
        ):
            path = cls._to_local_path(match.group(1))

            if path and path not in fallback_candidates:
                fallback_candidates.append(path)

        if fallback_candidates:
            return fallback_candidates[-1]

        return None

    def current_image(self) -> Path | None:
        return self._read_current_image()

    @staticmethod
    def _run_command(image: Path) -> tuple[bool, str | None]:
        """Solicita a KDE que aplique una imagen como fondo."""
        command = shutil.which(PLASMA_COMMAND)

        if not command:
            return False, (
                "No se encontró plasma-apply-wallpaperimage. "
                "Comprueba que Plasma Workspace esté instalado."
            )

        try:
            result = subprocess.run(
                [command, str(image)],
                capture_output=True,
                text=True,
                timeout=12,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return False, f"No se pudo cambiar el fondo: {exc}"

        if result.returncode != 0:
            details = (result.stderr or result.stdout).strip()
            return False, (
                details
                or "plasma-apply-wallpaperimage terminó con "
                f"código {result.returncode}."
            )

        return True, None

    def apply(self, image: Path) -> tuple[bool, str | None]:
        return self._run_command(image)
