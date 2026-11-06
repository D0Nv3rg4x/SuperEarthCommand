"""Adaptador experimental de macOS.

Usa osascript para pedir a System Events que cambie la imagen de los escritorios.
Requiere permiso de automatización sobre System Events. El soporte está
implementado pero no se ha validado en un equipo macOS real.
"""

from __future__ import annotations

import os
import plistlib
import shutil
import subprocess
import sys
from pathlib import Path

from core import i18n

from .base import AutostartManager, WallpaperBackend

READ_SCRIPT = (
    'tell application "System Events" to get POSIX path of '
    '(picture of desktop 1 as alias)'
)

APPLY_SCRIPT = """
on run argv
    set imagePath to item 1 of argv
    tell application "System Events"
        tell every desktop
            set picture to (POSIX file imagePath)
        end tell
    end tell
end run
"""


class MacOSWallpaperBackend(WallpaperBackend):
    """Cambia el fondo con System Events, sin comandos de Linux ni Windows."""

    name = "macOS"

    def is_supported(self) -> bool:
        return (
            sys.platform == "darwin"
            and shutil.which("osascript") is not None
        )

    def unsupported_reason(self) -> str:
        if sys.platform != "darwin":
            return i18n.t("platform.macos.only_macos")
        return i18n.t("platform.macos.osascript_missing")

    def current_image(self) -> Path | None:
        """Lee la imagen del primer escritorio; hay límites con varios monitores."""
        if not self.is_supported():
            return None

        try:
            result = subprocess.run(
                ["osascript", "-e", READ_SCRIPT],
                capture_output=True,
                text=True,
                timeout=12,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None

        if result.returncode != 0:
            return None

        value = result.stdout.strip()

        if not value or value == "missing value":
            return None

        path = Path(value).expanduser()
        return path.resolve() if path.is_file() else None

    def apply(self, image: Path) -> tuple[bool, str | None]:
        if not self.is_supported():
            return False, self.unsupported_reason()

        path = Path(image).expanduser()

        if not path.is_file():
            return False, i18n.t(
                "platform.macos.image_missing", path=path
            )

        try:
            result = subprocess.run(
                ["osascript", "-e", APPLY_SCRIPT, str(path.resolve())],
                capture_output=True,
                text=True,
                timeout=12,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return False, i18n.t(
                "platform.macos.apply_failed", error=exc
            )

        if result.returncode != 0:
            details = (result.stderr or result.stdout).strip()
            return False, (
                details
                or i18n.t(
                    "platform.macos.exit_code", code=result.returncode
                )
            )

        return True, None


LAUNCH_AGENT_LABEL = "com.superearth.mododemocracia"


class MacOSAutostartManager(AutostartManager):
    """Inicio automático mediante un LaunchAgent de macOS."""

    name = "macOS (LaunchAgent)"

    def __init__(self, project_dir: Path, python_executable: Path):
        super().__init__(project_dir, python_executable)
        self.plist_file = (
            Path.home()
            / "Library"
            / "LaunchAgents"
            / f"{LAUNCH_AGENT_LABEL}.plist"
        )

    def is_supported(self) -> bool:
        return (
            sys.platform == "darwin"
            and shutil.which("launchctl") is not None
        )

    def unsupported_reason(self) -> str:
        if sys.platform != "darwin":
            return i18n.t("platform.macos.autostart_only_macos")
        return i18n.t("platform.macos.launchctl_missing")

    def location(self) -> Path:
        return self.plist_file

    def is_installed(self) -> bool:
        return self.is_supported() and self.plist_file.is_file()

    def _run_launchctl(self, args: list[str]):
        return subprocess.run(
            ["launchctl", *args],
            capture_output=True,
            text=True,
            timeout=12,
            check=False,
        )

    def _bootout(self) -> None:
        """Descarga el agente; los errores se ignoran porque puede no estar cargado."""
        target = f"gui/{os.getuid()}/{LAUNCH_AGENT_LABEL}"
        try:
            self._run_launchctl(["bootout", target])
        except (OSError, subprocess.TimeoutExpired):
            pass

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

        data = {
            "Label": LAUNCH_AGENT_LABEL,
            "ProgramArguments": [
                str(self.python_executable),
                str(self.app_script),
                "--hidden",
            ],
            "WorkingDirectory": str(self.project_dir),
            "RunAtLoad": True,
            "KeepAlive": False,
            "LimitLoadToSessionType": "Aqua",
        }

        try:
            self.plist_file.parent.mkdir(parents=True, exist_ok=True)
            with self.plist_file.open("wb") as file:
                plistlib.dump(data, file)
            os.chmod(self.plist_file, 0o644)
        except OSError as exc:
            return False, i18n.t(
                "autostart.error.plist_write",
                path=self.plist_file,
                error=exc,
            )

        self._bootout()

        try:
            result = self._run_launchctl(
                [
                    "bootstrap",
                    f"gui/{os.getuid()}",
                    str(self.plist_file),
                ]
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            self.plist_file.unlink(missing_ok=True)
            return False, i18n.t(
                "autostart.error.launchctl_run", error=exc
            )

        if result.returncode != 0:
            # Compatibilidad con versiones anteriores de macOS.
            try:
                fallback = self._run_launchctl(
                    ["load", "-w", str(self.plist_file)]
                )
            except (OSError, subprocess.TimeoutExpired):
                fallback = None

            if fallback is None or fallback.returncode != 0:
                details = (
                    result.stderr or result.stdout or ""
                ).strip()
                self.plist_file.unlink(missing_ok=True)
                return False, i18n.t(
                    "platform.macos.launchctl_failed",
                    detail=(
                        details
                        or i18n.t(
                            "platform.macos.launchctl_detail"
                        )
                    ),
                )

            self.last_note = i18n.t(
                "autostart.note.legacy_launchctl"
            )

        return True, None

    def uninstall(self) -> tuple[bool, str | None]:
        self.last_note = None

        if not self.is_supported():
            return False, self.unsupported_reason()

        self._bootout()

        try:
            self._run_launchctl(
                ["unload", "-w", str(self.plist_file)]
            )
        except (OSError, subprocess.TimeoutExpired):
            pass

        if not self.plist_file.exists():
            self.last_note = i18n.t("autostart.note.not_installed")
            return True, None

        try:
            self.plist_file.unlink()
        except OSError as exc:
            return False, i18n.t(
                "autostart.error.plist_delete",
                path=self.plist_file,
                error=exc,
            )

        return True, None
