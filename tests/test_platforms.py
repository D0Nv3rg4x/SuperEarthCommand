"""Pruebas de la Fase 4: adaptadores de plataforma y controlador común."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from core import wallpaper
from platforms import get_wallpaper_backend
from platforms.base import UnsupportedWallpaperBackend, WallpaperBackend
from platforms.kde import KDEWallpaperBackend
from platforms.linux import LinuxWallpaperBackend
from platforms.macos import MacOSWallpaperBackend
from platforms.windows import WindowsWallpaperBackend


class FactoryTests(unittest.TestCase):
    def test_windows_backend_is_selected(self):
        self.assertIsInstance(
            get_wallpaper_backend("win32"), WindowsWallpaperBackend
        )

    def test_macos_backend_is_selected(self):
        self.assertIsInstance(
            get_wallpaper_backend("darwin"), MacOSWallpaperBackend
        )

    def test_linux_backend_is_selected(self):
        self.assertIsInstance(
            get_wallpaper_backend("linux"), LinuxWallpaperBackend
        )

    def test_unknown_platform_is_unsupported(self):
        backend = get_wallpaper_backend("freebsd14")
        self.assertIsInstance(backend, UnsupportedWallpaperBackend)
        self.assertFalse(backend.is_supported())
        self.assertIn("freebsd14", backend.unsupported_reason())


class KDEAdapterTests(unittest.TestCase):
    def test_kde_plasma_6_with_command_is_supported(self):
        environment = {
            "XDG_CURRENT_DESKTOP": "KDE",
            "XDG_SESSION_DESKTOP": "KDE",
            "KDE_SESSION_VERSION": "6",
        }
        with (
            mock.patch.dict(os.environ, environment),
            mock.patch(
                "platforms.kde.shutil.which",
                return_value="/usr/bin/plasma-apply-wallpaperimage",
            ),
        ):
            self.assertTrue(KDEWallpaperBackend.is_supported())

    def test_kde_without_command_is_not_supported(self):
        environment = {
            "XDG_CURRENT_DESKTOP": "KDE",
            "XDG_SESSION_DESKTOP": "KDE",
            "KDE_SESSION_VERSION": "6",
        }
        with (
            mock.patch.dict(os.environ, environment),
            mock.patch("platforms.kde.shutil.which", return_value=None),
        ):
            self.assertFalse(KDEWallpaperBackend.is_supported())
            self.assertIn(
                "plasma-apply-wallpaperimage",
                KDEWallpaperBackend.unsupported_reason(),
            )

    def test_kde_plasma_5_is_not_supported(self):
        environment = {
            "XDG_CURRENT_DESKTOP": "KDE",
            "XDG_SESSION_DESKTOP": "KDE",
            "KDE_SESSION_VERSION": "5",
        }
        with (
            mock.patch.dict(os.environ, environment),
            mock.patch(
                "platforms.kde.shutil.which",
                return_value="/usr/bin/plasma-apply-wallpaperimage",
            ),
        ):
            self.assertFalse(KDEWallpaperBackend.is_supported())
            self.assertIn(
                "Plasma 6", KDEWallpaperBackend.unsupported_reason()
            )

    def test_file_url_is_converted_to_local_path(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "wall paper.png"
            image.write_bytes(b"x")

            converted = KDEWallpaperBackend._to_local_path(
                image.as_uri()
            )

        self.assertEqual(converted, image.resolve())

    def test_current_image_is_read_from_plasma_config(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            image = home / "wallpaper.png"
            image.write_bytes(b"x")

            config = (
                home
                / ".config"
                / "plasma-org.kde.plasma.desktop-appletsrc"
            )
            config.parent.mkdir(parents=True)
            config.write_text(
                "[Containments][1][Wallpaper][org.kde.image][General]\n"
                f"Image={image.as_uri()}\n",
                encoding="utf-8",
            )

            with mock.patch.object(Path, "home", return_value=home):
                current = KDEWallpaperBackend._read_current_image()

        self.assertEqual(current, image.resolve())

    def test_apply_uses_plasma_command(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "wall.png"
            image.write_bytes(b"x")

            completed = SimpleNamespace(
                returncode=0, stdout="", stderr=""
            )

            with (
                mock.patch(
                    "platforms.kde.shutil.which",
                    return_value="/usr/bin/plasma-apply-wallpaperimage",
                ),
                mock.patch(
                    "platforms.kde.subprocess.run",
                    return_value=completed,
                ) as run,
            ):
                ok, error = KDEWallpaperBackend().apply(image)

        self.assertTrue(ok)
        self.assertIsNone(error)
        self.assertIn(str(image), run.call_args.args[0])

    def test_apply_reports_command_error(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "wall.png"
            image.write_bytes(b"x")

            completed = SimpleNamespace(
                returncode=1, stdout="", stderr="falló el comando"
            )

            with (
                mock.patch(
                    "platforms.kde.shutil.which",
                    return_value="/usr/bin/plasma-apply-wallpaperimage",
                ),
                mock.patch(
                    "platforms.kde.subprocess.run",
                    return_value=completed,
                ),
            ):
                ok, error = KDEWallpaperBackend().apply(image)

        self.assertFalse(ok)
        self.assertIn("falló el comando", error)


class LinuxAdapterTests(unittest.TestCase):
    def test_gnome_is_not_claimed_as_supported(self):
        environment = {
            "XDG_CURRENT_DESKTOP": "GNOME",
            "XDG_SESSION_DESKTOP": "gnome",
            "KDE_SESSION_VERSION": "",
        }
        with mock.patch.dict(os.environ, environment):
            backend = LinuxWallpaperBackend()
            self.assertFalse(backend.is_supported())
            self.assertIn("gnome", backend.unsupported_reason())

    def test_kde_is_delegated(self):
        environment = {
            "XDG_CURRENT_DESKTOP": "KDE",
            "XDG_SESSION_DESKTOP": "KDE",
            "KDE_SESSION_VERSION": "6",
        }
        with (
            mock.patch.dict(os.environ, environment),
            mock.patch(
                "platforms.kde.shutil.which",
                return_value="/usr/bin/plasma-apply-wallpaperimage",
            ),
        ):
            backend = LinuxWallpaperBackend()

        self.assertTrue(backend.is_supported())
        self.assertEqual(backend.name, "KDE Plasma 6")


@unittest.skipUnless(
    sys.platform.startswith("linux"), "Solo aplica en Linux"
)
class OtherPlatformsTests(unittest.TestCase):
    def test_windows_is_not_claimed_on_linux(self):
        backend = WindowsWallpaperBackend()
        self.assertFalse(backend.is_supported())
        self.assertIn("Windows", backend.unsupported_reason())

    def test_macos_is_not_claimed_on_linux(self):
        backend = MacOSWallpaperBackend()
        self.assertFalse(backend.is_supported())
        self.assertIn("macOS", backend.unsupported_reason())


class FakeBackend(WallpaperBackend):
    name = "Fake"

    def __init__(self, current=None, supported=True, fail_on=None):
        self.current = current
        self.supported = supported
        self.fail_on = {Path(path).resolve() for path in (fail_on or [])}
        self.applied: list[Path] = []

    def is_supported(self):
        return self.supported

    def unsupported_reason(self):
        return "Adaptador falso no disponible."

    def current_image(self):
        return self.current

    def apply(self, image):
        image = Path(image).resolve()
        self.applied.append(image)

        if image in self.fail_on:
            return False, f"Fallo simulado al aplicar {image}"

        return True, None


class WallpaperControllerTests(unittest.TestCase):
    def make_controller(
        self,
        directory: Path,
        backend: FakeBackend,
        *,
        enabled: bool = True,
        restore_on_exit: bool = True,
    ):
        target = directory / "target.png"
        target.write_bytes(b"target")

        with mock.patch.object(
            wallpaper,
            "state_directory",
            return_value=directory / "state",
        ):
            controller = wallpaper.WallpaperController(
                target,
                enabled=enabled,
                restore_on_exit=restore_on_exit,
                backend=backend,
            )

        return controller, target.resolve()

    def test_activate_and_restore(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = root / "original.png"
            original.write_bytes(b"original")

            backend = FakeBackend(current=original)
            controller, target = self.make_controller(root, backend)

            ok, error = controller.activate()

            self.assertTrue(ok, error)
            self.assertEqual(backend.applied, [target])
            self.assertTrue(controller.state_file.is_file())

            ok, error = controller.restore()

            self.assertTrue(ok, error)
            self.assertEqual(
                backend.applied, [target, original.resolve()]
            )
            self.assertFalse(controller.state_file.exists())

    def test_unsupported_backend_does_not_change_wallpaper(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            backend = FakeBackend(supported=False)
            controller, _ = self.make_controller(root, backend)

            ok, error = controller.activate()

            self.assertFalse(ok)
            self.assertIn("no disponible", error)
            self.assertEqual(backend.applied, [])
            self.assertFalse(controller.state_file.exists())

    def test_no_restore_on_exit_keeps_wallpaper_and_discards_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = root / "original.png"
            original.write_bytes(b"original")

            backend = FakeBackend(current=original)
            controller, target = self.make_controller(
                root, backend, restore_on_exit=False
            )

            self.assertTrue(controller.activate()[0])
            ok, error = controller.restore()

            self.assertTrue(ok, error)
            self.assertEqual(backend.applied, [target])
            self.assertFalse(controller.state_file.exists())

    def test_same_image_is_not_applied_again(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = root / "original.png"
            original.write_bytes(b"original")

            backend = FakeBackend(current=original)
            controller, _ = self.make_controller(root, backend)
            controller.target_image = original.resolve()

            ok, error = controller.activate()

            self.assertTrue(ok, error)
            self.assertEqual(backend.applied, [])
            self.assertTrue(controller.active)

    def test_apply_failure_attempts_restore(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = root / "original.png"
            original.write_bytes(b"original")

            backend = FakeBackend(current=original)
            controller, target = self.make_controller(root, backend)
            backend.fail_on = {target}

            ok, error = controller.activate()

            self.assertFalse(ok)
            self.assertIn("Fallo simulado", error)
            self.assertEqual(
                backend.applied, [target, original.resolve()]
            )
            self.assertFalse(controller.state_file.exists())

    def test_disabled_controller_does_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = root / "original.png"
            original.write_bytes(b"original")

            backend = FakeBackend(current=original)
            controller, _ = self.make_controller(
                root, backend, enabled=False
            )

            self.assertTrue(controller.activate()[0])
            self.assertTrue(controller.restore()[0])
            self.assertEqual(backend.applied, [])
            self.assertFalse(controller.state_file.exists())

    def test_recover_stale_state_restores_saved_image(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = root / "original.png"
            original.write_bytes(b"original")

            backend = FakeBackend()
            state_dir = root / "state"
            state_dir.mkdir()
            (state_dir / "wallpaper-state.json").write_text(
                f'{{"original_image": "{original}"}}',
                encoding="utf-8",
            )

            with (
                mock.patch.object(
                    wallpaper, "state_directory", return_value=state_dir
                ),
                mock.patch.object(
                    wallpaper,
                    "get_wallpaper_backend",
                    return_value=backend,
                ),
            ):
                ok, error = wallpaper.WallpaperController.recover_stale_state()

            self.assertTrue(ok, error)
            self.assertEqual(backend.applied, [original.resolve()])
            self.assertFalse(
                (state_dir / "wallpaper-state.json").exists()
            )


class StateDirectoryTests(unittest.TestCase):
    def test_linux_uses_xdg_state_home(self):
        with tempfile.TemporaryDirectory() as directory:
            with (
                mock.patch.object(wallpaper.sys, "platform", "linux"),
                mock.patch.dict(
                    os.environ, {"XDG_STATE_HOME": directory}
                ),
            ):
                result = wallpaper.state_directory()

        self.assertEqual(
            result, Path(directory) / "modo-democracia"
        )

    def test_windows_uses_local_app_data(self):
        with tempfile.TemporaryDirectory() as directory:
            with (
                mock.patch.object(wallpaper.sys, "platform", "win32"),
                mock.patch.dict(
                    os.environ, {"LOCALAPPDATA": directory}
                ),
            ):
                result = wallpaper.state_directory()

        self.assertEqual(
            result, Path(directory) / "modo-democracia"
        )

    def test_macos_uses_application_support(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            with (
                mock.patch.object(wallpaper.sys, "platform", "darwin"),
                mock.patch.object(Path, "home", return_value=home),
            ):
                result = wallpaper.state_directory()

        self.assertEqual(
            result,
            home / "Library" / "Application Support" / "modo-democracia",
        )


if __name__ == "__main__":
    unittest.main()
