"""Pruebas funcionales del flujo de la interfaz, sin ventana real."""

from __future__ import annotations

import os
import unittest
from pathlib import Path
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication

from core.audio import AudioController
from ui.deployment_window import ARROWS, DeploymentWindow

PROJECT_DIR = Path(__file__).resolve().parents[1]
LOGO = PROJECT_DIR / "Assets" / "Super_Earth_Logo.webp"


class FakeWallpaper:
    def __init__(self, activate_result=(True, None)):
        self.activate_result = activate_result
        self.activate_calls = 0
        self.restore_calls = 0

    def activate(self):
        self.activate_calls += 1
        return self.activate_result

    def restore(self):
        self.restore_calls += 1
        return True, None


class InterfaceFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        instance = QApplication.instance()

        if instance is None:
            cls.app = QApplication(["modo-democracia-tests"])
        elif isinstance(instance, QApplication):
            cls.app = instance
        else:
            raise unittest.SkipTest(
                "Ya existe una QCoreApplication incompatible."
            )

        cls.app.setQuitOnLastWindowClosed(False)

    def setUp(self):
        self.window = None

    def tearDown(self):
        if self.window is not None:
            self.window.timer.stop()
            self.window.anim_timer.stop()
            self.window.error_flash_timer.stop()
            self.window.game_hide_timer.stop()
            self.window._allow_exit = True
            self.window.close()
            self.window.deleteLater()
            self.app.processEvents()

    def make_window(
        self,
        duration_seconds: float = 0.4,
        wallpaper=None,
        launch_game: bool = False,
    ):
        self.window = DeploymentWindow(
            wallpaper_path=None,
            logo_path=LOGO,
            audio_path=None,
            duration_seconds=duration_seconds,
            app_icon_path=None,
            ministry_icon_path=None,
            wallpaper_controller=wallpaper,
            launch_game=launch_game,
            launch_delay_seconds=0.05,
            battle_delay_seconds=0.0,
        )
        return self.window

    def wait(self, milliseconds: int):
        loop = QEventLoop()
        QTimer.singleShot(milliseconds, loop.quit)
        loop.exec()

    def test_window_starts_idle(self):
        window = self.make_window()

        self.assertEqual(window.stage, "idle")
        self.assertFalse(window.timer.isActive())
        self.assertEqual(window.progress.percent(), 0)
        self.assertIn(
            "EN ESPERA", window.status_label.text()
        )

    def test_start_and_cancel_activate_and_restore_wallpaper(self):
        wallpaper = FakeWallpaper()
        window = self.make_window(wallpaper=wallpaper)

        window.start_sequence()

        self.assertEqual(wallpaper.activate_calls, 1)
        self.assertTrue(window.timer.isActive())
        self.assertIn(window.stage, ("stratagem", "running"))
        self.assertIsNotNone(window.current_stratagem)

        window.cancel_sequence()

        self.assertEqual(wallpaper.restore_calls, 1)
        self.assertEqual(window.stage, "idle")
        self.assertFalse(window.timer.isActive())
        self.assertEqual(window.progress.percent(), 0)

    def test_wallpaper_failure_does_not_stop_sequence(self):
        wallpaper = FakeWallpaper(
            activate_result=(False, "fallo simulado")
        )
        window = self.make_window(wallpaper=wallpaper)

        window.start_sequence()

        self.assertTrue(window.timer.isActive())
        self.assertIn(
            "no se pudo cambiar el fondo",
            " ".join(window.session_warnings),
        )

    def test_progress_reaches_completion(self):
        window = self.make_window(duration_seconds=1.0)

        window.start_sequence()
        self.wait(1400)

        self.assertEqual(window.stage, "complete")
        self.assertEqual(window.progress.percent(), 100)
        self.assertFalse(window.timer.isActive())

    def test_correct_arrow_sequence_is_accepted(self):
        window = self.make_window(duration_seconds=5.0)
        window.start_sequence()
        stratagem = window.current_stratagem

        for arrow in stratagem["sequence"]:
            window.handle_arrow(arrow)

        self.assertEqual(window.stage, "between")
        self.assertEqual(
            window.hint_label.text(), stratagem["message"]
        )

    def test_wrong_arrow_resets_sequence_and_recovers(self):
        window = self.make_window(duration_seconds=5.0)
        window.start_sequence()
        stratagem = window.current_stratagem
        wrong = next(
            arrow
            for arrow in ARROWS.values()
            if arrow != stratagem["sequence"][0]
        )

        window.handle_arrow(wrong)

        self.assertEqual(window.input_index, 0)
        self.assertEqual(window.status_label.text(), "ERROR DE SECUENCIA")

        self.wait(400)

        self.assertIn(
            "SISTEMA EN ESPERA", window.status_label.text()
        )

    def test_game_launch_uses_steam_when_enabled(self):
        window = self.make_window(launch_game=True)
        window.stage = "complete"

        with (
            mock.patch(
                "ui.deployment_window.shutil.which",
                return_value="/usr/bin/steam",
            ),
            mock.patch(
                "ui.deployment_window.subprocess.Popen"
            ) as popen,
        ):
            window.launch_game()

        self.assertEqual(popen.call_count, 1)
        self.assertIn("steam://rungameid/", popen.call_args.args[0][1])
        self.assertIn("Abriendo Helldivers 2", window.hint_label.text())

    def test_game_is_not_launched_when_disabled(self):
        window = self.make_window(launch_game=False)
        window.stage = "complete"

        with mock.patch(
            "ui.deployment_window.subprocess.Popen"
        ) as popen:
            window.launch_game()

        popen.assert_not_called()

    def test_audio_rejects_missing_file(self):
        controller = AudioController()
        try:
            self.assertFalse(
                controller.play(Path("/no/existe/audio.mp3"))
            )
            controller.stop()
        finally:
            controller.player.deleteLater()


if __name__ == "__main__":
    unittest.main()
