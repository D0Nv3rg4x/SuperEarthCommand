"""Pruebas de la Fase 5: inicio automático por plataforma."""

from __future__ import annotations

import os
import plistlib
import shlex
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from core.autostart import default_python_executable
from platforms import get_autostart_manager
from platforms import macos as macos_module
from platforms.base import AutostartManager
from platforms.linux import LinuxAutostartManager
from platforms.macos import MacOSAutostartManager
from platforms.windows import WindowsAutostartManager


@unittest.skipUnless(
    sys.platform.startswith("linux"), "Pruebas de autostart Linux"
)
class LinuxAutostartTests(unittest.TestCase):
    def setUp(self):
        self._temporary = tempfile.TemporaryDirectory()
        self.root = Path(self._temporary.name)
        self.home = self.root / "home"
        self.home.mkdir()
        self.project = self.root / "project"
        self.project.mkdir()
        (self.project / "app.py").write_text(
            "print('app')\n", encoding="utf-8"
        )
        self.python = self.project / ".venv" / "bin" / "python"
        self.python.parent.mkdir(parents=True)
        self.python.write_text("#!/bin/sh\n", encoding="utf-8")

        self._home_patch = mock.patch.object(
            Path, "home", return_value=self.home
        )
        self._home_patch.start()
        self._env_patch = mock.patch.dict(
            os.environ,
            {"XDG_CONFIG_HOME": str(self.home / ".config")},
        )
        self._env_patch.start()

        self.manager = LinuxAutostartManager(
            self.project, self.python
        )

    def tearDown(self):
        self._env_patch.stop()
        self._home_patch.stop()
        self._temporary.cleanup()

    def test_install_creates_launcher_and_desktop_entry(self):
        ok, error = self.manager.install()

        self.assertTrue(ok, error)
        self.assertTrue(self.manager.desktop_file.is_file())
        self.assertTrue(self.manager.launcher.is_file())
        self.assertTrue(self.manager.is_installed())

        launcher = self.manager.launcher.read_text(encoding="utf-8")
        desktop = self.manager.desktop_file.read_text(encoding="utf-8")

        self.assertIn("--hidden", launcher)
        self.assertIn(str(self.project), launcher)
        self.assertIn(str(self.python), launcher)
        self.assertIn("[Desktop Entry]", desktop)
        self.assertIn("Terminal=false", desktop)
        self.assertIn(f"Path={self.project}", desktop)
        self.assertIn(str(self.manager.launcher), desktop)

        mode = self.manager.launcher.stat().st_mode
        self.assertTrue(mode & stat.S_IXUSR)

    def test_reinstall_is_idempotent(self):
        self.assertTrue(self.manager.install()[0])
        self.assertTrue(self.manager.install()[0])
        self.assertTrue(self.manager.is_installed())

    def test_uninstall_removes_only_created_files(self):
        self.assertTrue(self.manager.install()[0])

        ok, error = self.manager.uninstall()

        self.assertTrue(ok, error)
        self.assertFalse(self.manager.desktop_file.exists())
        self.assertFalse(self.manager.launcher.exists())
        self.assertFalse(self.manager.is_installed())

    def test_uninstall_when_not_installed_reports_note(self):
        ok, error = self.manager.uninstall()

        self.assertTrue(ok, error)
        self.assertIn("no estaba instalado", self.manager.last_note)

    def test_install_refuses_to_overwrite_foreign_launcher(self):
        self.manager.launcher.parent.mkdir(parents=True)
        self.manager.launcher.write_text(
            "#!/bin/sh\necho ajeno\n", encoding="utf-8"
        )

        ok, error = self.manager.install()

        self.assertFalse(ok)
        self.assertIn("ajeno", error)
        self.assertIn("echo ajeno", self.manager.launcher.read_text())
        self.assertFalse(self.manager.desktop_file.exists())

    def test_uninstall_preserves_foreign_launcher(self):
        self.manager.desktop_file.parent.mkdir(parents=True)
        self.manager.desktop_file.write_text(
            "# Generado por Modo Democracia\n[Desktop Entry]\n",
            encoding="utf-8",
        )
        self.manager.launcher.parent.mkdir(parents=True)
        self.manager.launcher.write_text(
            "#!/bin/sh\necho ajeno\n", encoding="utf-8"
        )

        ok, error = self.manager.uninstall()

        self.assertTrue(ok, error)
        self.assertFalse(self.manager.desktop_file.exists())
        self.assertTrue(self.manager.launcher.exists())
        self.assertIn("conservó", self.manager.last_note)

    def test_install_refuses_to_overwrite_foreign_desktop_entry(self):
        self.manager.desktop_file.parent.mkdir(parents=True)
        self.manager.desktop_file.write_text(
            "[Desktop Entry]\nName=Otra aplicación\n",
            encoding="utf-8",
        )

        ok, error = self.manager.install()

        self.assertFalse(ok)
        self.assertIn("ajena", error)
        self.assertFalse(self.manager.launcher.exists())
        self.assertIn(
            "Otra aplicación",
            self.manager.desktop_file.read_text(encoding="utf-8"),
        )

    def test_uninstall_preserves_foreign_desktop_entry(self):
        self.manager.desktop_file.parent.mkdir(parents=True)
        self.manager.desktop_file.write_text(
            "[Desktop Entry]\nName=Otra aplicación\n",
            encoding="utf-8",
        )

        ok, error = self.manager.uninstall()

        self.assertTrue(ok, error)
        self.assertTrue(self.manager.desktop_file.exists())
        self.assertIn("conservó", self.manager.last_note)

    def test_legacy_launcher_is_recognized_and_replaced(self):
        self.manager.launcher.parent.mkdir(parents=True)
        self.manager.launcher.write_text(
            "#!/usr/bin/env bash\n"
            f'cd "{self.project}"\n'
            f'exec "{self.python}" "{self.project}/app.py" --hidden\n',
            encoding="utf-8",
        )

        ok, error = self.manager.install()

        self.assertTrue(ok, error)
        self.assertIn(
            "Generado por Modo Democracia",
            self.manager.launcher.read_text(encoding="utf-8"),
        )

    def test_paths_with_spaces_are_quoted(self):
        spaced_project = self.root / "proyecto con espacios"
        spaced_project.mkdir()
        (spaced_project / "app.py").write_text("", encoding="utf-8")
        manager = LinuxAutostartManager(
            spaced_project, self.python
        )

        ok, error = manager.install()

        self.assertTrue(ok, error)
        desktop = manager.desktop_file.read_text(encoding="utf-8")
        launcher = manager.launcher.read_text(encoding="utf-8")
        self.assertIn(f"Path={spaced_project}", desktop)
        self.assertIn(shlex.quote(str(spaced_project)), launcher)


class FactoryAndPlatformTests(unittest.TestCase):
    def setUp(self):
        self._temporary = tempfile.TemporaryDirectory()
        self.project = Path(self._temporary.name)
        self.python = self.project / "python"

    def tearDown(self):
        self._temporary.cleanup()

    def test_factory_selects_each_platform(self):
        self.assertIsInstance(
            get_autostart_manager(self.project, self.python, "linux"),
            LinuxAutostartManager,
        )
        self.assertIsInstance(
            get_autostart_manager(self.project, self.python, "win32"),
            WindowsAutostartManager,
        )
        self.assertIsInstance(
            get_autostart_manager(self.project, self.python, "darwin"),
            MacOSAutostartManager,
        )

    def test_unknown_platform_is_unsupported(self):
        manager = get_autostart_manager(
            self.project, self.python, "freebsd14"
        )
        self.assertIsInstance(manager, AutostartManager)
        self.assertFalse(manager.is_supported())
        self.assertFalse(manager.install()[0])

    @unittest.skipUnless(
        sys.platform.startswith("linux"), "Solo aplica en Linux"
    )
    def test_windows_is_not_supported_on_linux(self):
        manager = WindowsAutostartManager(self.project, self.python)
        self.assertFalse(manager.is_supported())
        ok, error = manager.install()
        self.assertFalse(ok)
        self.assertIn("Windows", error)

    @unittest.skipUnless(
        sys.platform.startswith("linux"), "Solo aplica en Linux"
    )
    def test_macos_is_not_supported_on_linux(self):
        manager = MacOSAutostartManager(self.project, self.python)
        self.assertFalse(manager.is_supported())
        ok, error = manager.install()
        self.assertFalse(ok)
        self.assertIn("macOS", error)

    def test_windows_command_quotes_paths_and_uses_hidden(self):
        manager = WindowsAutostartManager(
            self.project / "con espacios",
            self.python / "con espacios" / "pythonw.exe",
        )
        command = manager._command()
        self.assertIn('--hidden', command)
        self.assertEqual(command.count('"'), 4)


class PythonExecutableTests(unittest.TestCase):
    def test_prefers_project_virtualenv(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            python = project / ".venv" / "bin" / "python"
            python.parent.mkdir(parents=True)
            python.write_text("", encoding="utf-8")

            result = default_python_executable(project)

        self.assertEqual(result, python.absolute())

    def test_windows_prefers_pythonw(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            scripts = project / ".venv" / "Scripts"
            scripts.mkdir(parents=True)
            pythonw = scripts / "pythonw.exe"
            pythonw.write_text("", encoding="utf-8")

            with mock.patch(
                "core.autostart.sys.platform", "win32"
            ):
                result = default_python_executable(project)

        self.assertEqual(result, pythonw.absolute())


class MacOSInstallTests(unittest.TestCase):
    """Comprueba la lógica del LaunchAgent sin ejecutar launchctl real."""

    def test_install_and_uninstall_plist(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            home = root / "home"
            home.mkdir()
            project = root / "project"
            project.mkdir()
            (project / "app.py").write_text("", encoding="utf-8")
            python = project / "python"
            python.write_text("", encoding="utf-8")

            completed = SimpleNamespace(
                returncode=0, stdout="", stderr=""
            )

            with (
                mock.patch.object(Path, "home", return_value=home),
                mock.patch.object(
                    macos_module.sys, "platform", "darwin"
                ),
                mock.patch.object(
                    macos_module.shutil,
                    "which",
                    return_value="/bin/launchctl",
                ),
                mock.patch.object(
                    macos_module.subprocess,
                    "run",
                    return_value=completed,
                ) as run,
            ):
                manager = MacOSAutostartManager(project, python)
                ok, error = manager.install()

                self.assertTrue(ok, error)
                self.assertTrue(manager.plist_file.is_file())

                with manager.plist_file.open("rb") as file:
                    data = plistlib.load(file)

                self.assertEqual(
                    data["Label"], "com.superearth.mododemocracia"
                )
                self.assertIn("--hidden", data["ProgramArguments"])
                self.assertTrue(data["RunAtLoad"])

                commands = [
                    call.args[0] for call in run.call_args_list
                ]
                self.assertTrue(
                    any("bootstrap" in command for command in commands)
                )

                ok, error = manager.uninstall()
                self.assertTrue(ok, error)
                self.assertFalse(manager.plist_file.exists())


if __name__ == "__main__":
    unittest.main()
