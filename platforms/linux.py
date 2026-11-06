"""Adaptador general de Linux.

Linux no es un escritorio único. Este adaptador solo delega en KDE Plasma 6,
que es el entorno implementado y validado; para el resto informa que la función
no está disponible en lugar de ejecutar comandos de otro escritorio.
"""

from __future__ import annotations

import os
import re
import shlex
import sys
from pathlib import Path

from core import i18n

from .base import AutostartManager, WallpaperBackend
from .kde import KDEWallpaperBackend


class LinuxWallpaperBackend(WallpaperBackend):
    """Selecciona el mecanismo disponible según el escritorio de Linux."""

    name = "Linux"

    def __init__(self, kde_backend: KDEWallpaperBackend | None = None):
        self._kde = kde_backend or KDEWallpaperBackend()
        if self._kde.is_supported():
            self.name = self._kde.name

    def is_supported(self) -> bool:
        return self._kde.is_supported()

    def unsupported_reason(self) -> str:
        if self._kde.is_supported():
            return ""

        desktops = sorted(KDEWallpaperBackend._desktops())
        current = (
            ", ".join(desktops)
            if desktops
            else i18n.t("platform.linux.unknown_desktop")
        )

        if any(
            "kde" in desktop or "plasma" in desktop
            for desktop in desktops
        ):
            return self._kde.unsupported_reason()

        return i18n.t("platform.linux.no_adapter", desktop=current)

    def current_image(self) -> Path | None:
        if not self.is_supported():
            return None
        return self._kde.current_image()

    def apply(self, image: Path) -> tuple[bool, str | None]:
        if not self.is_supported():
            return False, self.unsupported_reason()
        return self._kde.apply(image)


AUTOSTART_MARKER = "# Generado por Modo Democracia"
DESKTOP_MARKER = "# Generado por Modo Democracia"
LAUNCHER_NAME = "modo-democracia"
DESKTOP_NAME = "modo-democracia.desktop"


def _desktop_exec_quote(value: str) -> str:
    """Cita un argumento según el formato Exec de los archivos .desktop."""
    if not value:
        return '""'

    if re.search(r'[\s"\'\\><~|&;$*?#()`]', value):
        escaped = (
            value.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("`", "\\`")
            .replace("$", "\\$")
        )
        return f'"{escaped}"'

    return value


class LinuxAutostartManager(AutostartManager):
    """Inicio automático mediante XDG autostart y un lanzador estable."""

    name = "Linux (XDG autostart)"

    def __init__(self, project_dir: Path, python_executable: Path):
        super().__init__(project_dir, python_executable)

        config_home = Path(
            os.environ.get(
                "XDG_CONFIG_HOME",
                Path.home() / ".config",
            )
        )
        self.autostart_dir = config_home / "autostart"
        self.desktop_file = self.autostart_dir / DESKTOP_NAME
        self.launcher = Path.home() / ".local" / "bin" / LAUNCHER_NAME
        self.icon = (
            self.project_dir
            / "Assets"
            / "Helldivers_2_(Icon).svg"
        )

    def is_supported(self) -> bool:
        return sys.platform.startswith("linux")

    def unsupported_reason(self) -> str:
        return i18n.t("platform.linux.autostart_only_linux")

    def location(self) -> Path:
        return self.desktop_file

    def _is_our_launcher(self, text: str) -> bool:
        """Reconoce el lanzador nuevo y el generado por versiones anteriores."""
        return AUTOSTART_MARKER in text or (
            str(self.project_dir) in text
            and "app.py" in text
            and "--hidden" in text
        )

    def _is_our_desktop(self, text: str) -> bool:
        """Reconoce la entrada nueva y la generada por versiones anteriores."""
        return DESKTOP_MARKER in text or (
            "Name=Modo Democracia" in text
            and LAUNCHER_NAME in text
        )

    def is_installed(self) -> bool:
        if (
            not self.desktop_file.is_file()
            or not self.launcher.is_file()
        ):
            return False

        try:
            desktop = self.desktop_file.read_text(encoding="utf-8")
            launcher = self.launcher.read_text(encoding="utf-8")
        except OSError:
            return False

        return (
            self._is_our_desktop(desktop)
            and self._is_our_launcher(launcher)
        )

    def install(self) -> tuple[bool, str | None]:
        self.last_note = None

        if not self.is_supported():
            return False, self.unsupported_reason()

        if not self.app_script.is_file():
            return False, i18n.t(
                "autostart.error.app_missing", path=self.app_script
            )

        if not self.python_executable.is_file():
            return False, i18n.t(
                "autostart.error.python_missing",
                path=self.python_executable,
            )

        launcher_existed = self.launcher.exists()

        if launcher_existed:
            try:
                existing = self.launcher.read_text(encoding="utf-8")
            except OSError as exc:
                return False, i18n.t(
                    "autostart.error.launcher_read",
                    path=self.launcher,
                    error=exc,
                )

            if not self._is_our_launcher(existing):
                return False, i18n.t(
                    "autostart.error.foreign_launcher",
                    path=self.launcher,
                )

        desktop_existed = self.desktop_file.exists()

        if desktop_existed:
            try:
                existing_desktop = self.desktop_file.read_text(
                    encoding="utf-8"
                )
            except OSError as exc:
                return False, i18n.t(
                    "autostart.error.desktop_read",
                    path=self.desktop_file,
                    error=exc,
                )

            if not self._is_our_desktop(existing_desktop):
                return False, i18n.t(
                    "autostart.error.foreign_desktop",
                    path=self.desktop_file,
                )

        launcher_content = (
            "#!/usr/bin/env bash\n"
            f"{AUTOSTART_MARKER}. No editar a mano.\n"
            "set -euo pipefail\n"
            f"cd {shlex.quote(str(self.project_dir))}\n"
            f"exec {shlex.quote(str(self.python_executable))} "
            f"{shlex.quote(str(self.app_script))} --hidden\n"
        )

        desktop_exec = _desktop_exec_quote(str(self.launcher))
        icon_line = (
            f"Icon={self.icon}\n"
            if self.icon.is_file()
            else "Icon=applications-games\n"
        )
        desktop_content = (
            f"{DESKTOP_MARKER}\n"
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Modo Democracia\n"
            f"Comment={i18n.t('autostart.desktop.comment')}\n"
            f"Exec={desktop_exec}\n"
            f"TryExec={self.launcher}\n"
            f"Path={self.project_dir}\n"
            f"{icon_line}"
            "Terminal=false\n"
            "StartupNotify=false\n"
            "X-GNOME-Autostart-enabled=true\n"
            "X-KDE-autostart-after=panel\n"
        )

        try:
            self.launcher.parent.mkdir(parents=True, exist_ok=True)
            self.autostart_dir.mkdir(parents=True, exist_ok=True)

            self.launcher.write_text(
                launcher_content,
                encoding="utf-8",
            )
            os.chmod(self.launcher, 0o755)

            self.desktop_file.write_text(
                desktop_content,
                encoding="utf-8",
            )
            os.chmod(self.desktop_file, 0o644)
        except OSError as exc:
            if not launcher_existed:
                try:
                    self.launcher.unlink(missing_ok=True)
                except OSError:
                    pass
            if not desktop_existed:
                try:
                    self.desktop_file.unlink(missing_ok=True)
                except OSError:
                    pass
            return False, i18n.t("autostart.error.write", error=exc)

        return True, None

    def uninstall(self) -> tuple[bool, str | None]:
        self.last_note = None

        if not self.is_supported():
            return False, self.unsupported_reason()

        removed_something = False

        if self.desktop_file.exists():
            try:
                desktop = self.desktop_file.read_text(encoding="utf-8")
            except OSError as exc:
                return False, i18n.t(
                    "autostart.error.desktop_read",
                    path=self.desktop_file,
                    error=exc,
                )

            if self._is_our_desktop(desktop):
                try:
                    self.desktop_file.unlink()
                    removed_something = True
                except OSError as exc:
                    return False, i18n.t(
                        "autostart.error.remove_desktop",
                        path=self.desktop_file,
                        error=exc,
                    )
            else:
                self.last_note = i18n.t(
                    "autostart.note.kept_desktop",
                    path=self.desktop_file,
                )

        if self.launcher.exists():
            try:
                text = self.launcher.read_text(encoding="utf-8")
            except OSError as exc:
                return False, i18n.t(
                    "autostart.error.read_launcher_for_removal",
                    path=self.launcher,
                    error=exc,
                )

            if self._is_our_launcher(text):
                try:
                    self.launcher.unlink()
                    removed_something = True
                except OSError as exc:
                    return False, i18n.t(
                        "autostart.error.remove_launcher",
                        path=self.launcher,
                        error=exc,
                    )
            else:
                self.last_note = i18n.t(
                    "autostart.note.kept_launcher",
                    path=self.launcher,
                )

        if not removed_something:
            message = i18n.t("autostart.note.not_installed")
            self.last_note = (
                f"{self.last_note} {message}"
                if self.last_note
                else message
            )

        return True, None
