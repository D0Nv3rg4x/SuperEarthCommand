"""Adaptadores de plataforma.

La aplicación pide un adaptador y comprueba sus capacidades reales; no asume
que un sistema operativo concreto soporte todas las funciones.
"""

from __future__ import annotations

import sys

from pathlib import Path

from .base import (
    AutostartManager,
    UnsupportedWallpaperBackend,
    WallpaperBackend,
)
from .linux import LinuxAutostartManager, LinuxWallpaperBackend
from .macos import MacOSAutostartManager, MacOSWallpaperBackend
from .windows import WindowsAutostartManager, WindowsWallpaperBackend


def get_wallpaper_backend(platform_name: str | None = None) -> WallpaperBackend:
    """Selecciona el adaptador según el sistema operativo real."""
    platform_name = platform_name or sys.platform

    if platform_name.startswith("win"):
        return WindowsWallpaperBackend()

    if platform_name == "darwin":
        return MacOSWallpaperBackend()

    if platform_name.startswith("linux"):
        return LinuxWallpaperBackend()

    return UnsupportedWallpaperBackend(
        f"Sistema no soportado para cambiar el fondo: {platform_name}."
    )


def get_autostart_manager(
    project_dir: Path,
    python_executable: Path,
    platform_name: str | None = None,
) -> AutostartManager:
    """Selecciona el gestor de inicio automático del sistema actual."""
    platform_name = platform_name or sys.platform

    if platform_name.startswith("win"):
        return WindowsAutostartManager(project_dir, python_executable)

    if platform_name == "darwin":
        return MacOSAutostartManager(project_dir, python_executable)

    if platform_name.startswith("linux"):
        return LinuxAutostartManager(project_dir, python_executable)

    return AutostartManager(project_dir, python_executable)


__all__ = [
    "AutostartManager",
    "UnsupportedWallpaperBackend",
    "WallpaperBackend",
    "get_autostart_manager",
    "get_wallpaper_backend",
]
