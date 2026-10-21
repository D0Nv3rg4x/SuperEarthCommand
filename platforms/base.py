"""Interfaz común para los sistemas operativos.

La lógica principal solo usa esta interfaz; cada adaptador encapsula los
comandos y API propios de su plataforma. Un adaptador no debe asumir que una
función está disponible por el simple hecho de estar en un sistema conocido.
"""

from __future__ import annotations

from pathlib import Path


class WallpaperBackend:
    """Operaciones de fondo de pantalla que implementa cada plataforma."""

    name = "sistema no compatible"

    def is_supported(self) -> bool:
        """Indica si la plataforma y sus herramientas permiten cambiar el fondo."""
        return False

    def unsupported_reason(self) -> str:
        """Explica por qué la función no está disponible."""
        return f"El cambio de fondo no está disponible en {self.name}."

    def current_image(self) -> Path | None:
        """Devuelve la imagen de fondo actual, o None si no puede identificarla."""
        return None

    def apply(self, image: Path) -> tuple[bool, str | None]:
        """Aplica una imagen como fondo; devuelve éxito y un error legible."""
        return False, self.unsupported_reason()


class UnsupportedWallpaperBackend(WallpaperBackend):
    """Adaptador neutro para sistemas o escritorios sin soporte."""

    def __init__(self, reason: str):
        self._reason = reason
        self.name = "sistema no compatible"

    def unsupported_reason(self) -> str:
        return self._reason


class AutostartManager:
    """Instalación y retirada del inicio automático por plataforma.

    `last_note` permite devolver una advertencia no bloqueante al usuario
    (por ejemplo, un archivo ajeno que se conservó durante la retirada).
    """

    name = "sistema no compatible"

    def __init__(self, project_dir: Path, python_executable: Path):
        self.project_dir = Path(project_dir).expanduser().resolve()
        self.python_executable = (
            Path(python_executable).expanduser().absolute()
        )
        self.last_note: str | None = None

    @property
    def app_script(self) -> Path:
        return self.project_dir / "app.py"

    def is_supported(self) -> bool:
        return False

    def is_installed(self) -> bool:
        return False

    def location(self) -> Path | str | None:
        return None

    def install(self) -> tuple[bool, str | None]:
        return False, self.unsupported_reason()

    def uninstall(self) -> tuple[bool, str | None]:
        return False, self.unsupported_reason()

    def unsupported_reason(self) -> str:
        return f"El inicio automático no está disponible en {self.name}."
