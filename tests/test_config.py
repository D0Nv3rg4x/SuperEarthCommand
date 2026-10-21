"""Pruebas de configuración y clasificación de recursos."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core.config import (
    DEFAULT_MODEL_PATH,
    activation_phrase,
    load_config,
    plan_wallpaper,
    prepare_assets,
    resolve_asset,
    sequence_timing,
    should_launch_game,
    voice_engine,
    voice_model_path,
)

PROJECT_DIR = Path(__file__).resolve().parents[1]


class ConfigFileTests(unittest.TestCase):
    def test_loads_toml(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.toml"
            path.write_text(
                '[general]\nactivation_phrase = "Prueba"\n',
                encoding="utf-8",
            )
            config = load_config(path)

        self.assertEqual(
            config["general"]["activation_phrase"], "Prueba"
        )

    def test_real_project_config_can_be_loaded(self):
        config = load_config(PROJECT_DIR / "config.toml")
        self.assertIn("general", config)
        self.assertIn("sequence", config)
        self.assertIn("voice", config)
        self.assertIn("steam", config)


class AssetResolutionTests(unittest.TestCase):
    def test_relative_asset_is_resolved_against_project(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "Assets").mkdir()
            image = project / "Assets" / "logo.png"
            image.write_bytes(b"x")

            result = resolve_asset(
                {"logo": "Assets/logo.png"},
                "logo",
                project,
            )

        self.assertEqual(result, image.resolve())

    def test_absolute_asset_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "logo.png"
            image.write_bytes(b"x")

            result = resolve_asset(
                {"logo": str(image)}, "logo", Path(directory)
            )

        self.assertEqual(result, image.resolve())

    def test_missing_key_returns_none(self):
        self.assertIsNone(
            resolve_asset({}, "logo", PROJECT_DIR)
        )


class AssetSelectionTests(unittest.TestCase):
    def make_assets(self, root: Path, *, wallpaper=True):
        (root / "Assets").mkdir()
        logo = root / "Assets" / "logo.png"
        logo.write_bytes(b"logo")

        assets = {"logo": "Assets/logo.png"}

        if wallpaper:
            image = root / "Assets" / "wall.png"
            image.write_bytes(b"wall")
            assets["wallpaper"] = "Assets/wall.png"

        return root, assets

    def test_valid_assets_have_no_warnings(self):
        with tempfile.TemporaryDirectory() as directory:
            root, assets = self.make_assets(Path(directory))
            selection = prepare_assets(assets, root)

        self.assertIsNotNone(selection.wallpaper)
        self.assertEqual(selection.logo.name, "logo.png")
        self.assertEqual(selection.warnings, ())

    def test_logo_is_required(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(FileNotFoundError) as context:
                prepare_assets(
                    {"logo": "Assets/no-existe.png"}, root
                )

        self.assertIn("recurso obligatorio", str(context.exception))
        self.assertIn("no-existe.png", str(context.exception))

    def test_missing_wallpaper_is_optional_and_warned(self):
        with tempfile.TemporaryDirectory() as directory:
            root, assets = self.make_assets(
                Path(directory), wallpaper=False
            )
            selection = prepare_assets(assets, root)

        self.assertIsNone(selection.wallpaper)
        self.assertIn(
            "imagen de fondo no disponible",
            " ".join(selection.warnings),
        )

    def test_missing_optional_resources_are_disabled(self):
        with tempfile.TemporaryDirectory() as directory:
            root, assets = self.make_assets(Path(directory))
            assets["audio"] = "Assets/sin-audio.mp3"
            assets["app_icon"] = "Assets/sin-icono.svg"
            assets["ministry_icon"] = "Assets/sin-sello.png"

            selection = prepare_assets(assets, root)

        self.assertIsNone(selection.audio)
        self.assertIsNone(selection.app_icon)
        self.assertIsNone(selection.ministry_icon)
        warnings = " ".join(selection.warnings)
        self.assertIn("audio", warnings)
        self.assertIn("icono de aplicación", warnings)
        self.assertIn("sello del Ministerio", warnings)

    def test_real_config_assets_are_complete(self):
        config = load_config(PROJECT_DIR / "config.toml")
        selection = prepare_assets(config["assets"], PROJECT_DIR)

        self.assertTrue(selection.logo.is_file())
        self.assertTrue(selection.wallpaper.is_file())
        self.assertTrue(selection.audio.is_file())


class WallpaperPlanTests(unittest.TestCase):
    def test_enabled_when_requested_supported_and_image_present(self):
        plan = plan_wallpaper(
            {},
            (True, ""),
            Path("/tmp/wall.png"),
        )
        self.assertTrue(plan.enabled)
        self.assertTrue(plan.restore_on_exit)
        self.assertIsNone(plan.warning)

    def test_disabled_by_configuration(self):
        plan = plan_wallpaper(
            {"wallpaper_enabled": False},
            (True, ""),
            Path("/tmp/wall.png"),
        )
        self.assertFalse(plan.enabled)
        self.assertIsNone(plan.warning)

    def test_unsupported_environment_is_warned(self):
        plan = plan_wallpaper(
            {},
            (False, "No hay adaptador."),
            Path("/tmp/wall.png"),
        )
        self.assertFalse(plan.enabled)
        self.assertIn("No hay adaptador", plan.warning)

    def test_missing_image_is_warned(self):
        plan = plan_wallpaper({}, (True, ""), None)
        self.assertFalse(plan.enabled)
        self.assertIn("falta la imagen", plan.warning)

    def test_restore_is_independent_from_change(self):
        plan = plan_wallpaper(
            {
                "wallpaper_enabled": False,
                "restore_wallpaper_on_exit": False,
            },
            (False, "sin soporte"),
            None,
        )
        self.assertFalse(plan.enabled)
        self.assertFalse(plan.restore_on_exit)


class VoiceConfigTests(unittest.TestCase):
    def test_default_model_path(self):
        path = voice_model_path({}, PROJECT_DIR)
        self.assertEqual(
            path, PROJECT_DIR / DEFAULT_MODEL_PATH
        )

    def test_absolute_model_path(self):
        path = voice_model_path(
            {"model_path": "/opt/modelo"}, Path("/proyecto")
        )
        self.assertEqual(path, Path("/opt/modelo"))

    def test_relative_model_path_uses_project(self):
        path = voice_model_path(
            {"model_path": "models/modelo"}, Path("/proyecto")
        )
        self.assertEqual(path, Path("/proyecto/models/modelo"))

    def test_empty_model_path_uses_default(self):
        path = voice_model_path(
            {"model_path": ""}, Path("/proyecto")
        )
        self.assertEqual(
            path, Path("/proyecto") / DEFAULT_MODEL_PATH
        )

    def test_engine_is_lowercase(self):
        self.assertEqual(
            voice_engine({"recognition_engine": "VOSK"}), "vosk"
        )
        self.assertEqual(voice_engine({}), "vosk")

    def test_activation_phrase_has_default_and_type_guard(self):
        self.assertEqual(activation_phrase({}), "modo democracia")
        self.assertEqual(
            activation_phrase({"activation_phrase": "Hola"}),
            "Hola",
        )
        self.assertEqual(
            activation_phrase({"activation_phrase": 123}),
            "modo democracia",
        )


class LaunchAndTimingTests(unittest.TestCase):
    def test_game_requires_both_switches(self):
        self.assertTrue(
            should_launch_game(
                {"launch_game_after_sequence": True},
                {"launch_enabled": True},
            )
        )
        self.assertFalse(
            should_launch_game(
                {"launch_game_after_sequence": True},
                {"launch_enabled": False},
            )
        )
        self.assertFalse(
            should_launch_game(
                {"launch_game_after_sequence": False},
                {"launch_enabled": True},
            )
        )

    def test_default_timing(self):
        timing = sequence_timing({})
        self.assertEqual(timing.duration_seconds, 13.2)
        self.assertEqual(timing.launch_delay_seconds, 2.0)
        self.assertEqual(timing.battle_text_delay_seconds, 300.0)

    def test_valid_timing_is_converted(self):
        timing = sequence_timing(
            {
                "duration_seconds": "2.5",
                "launch_delay_seconds": 1,
                "battle_text_delay_seconds": 10.5,
            }
        )
        self.assertEqual(timing.duration_seconds, 2.5)
        self.assertEqual(timing.launch_delay_seconds, 1.0)
        self.assertEqual(timing.battle_text_delay_seconds, 10.5)

    def test_invalid_timing_falls_back(self):
        timing = sequence_timing(
            {
                "duration_seconds": "no es un número",
                "launch_delay_seconds": None,
                "battle_text_delay_seconds": [],
            }
        )
        self.assertEqual(timing.duration_seconds, 13.2)
        self.assertEqual(timing.launch_delay_seconds, 2.0)
        self.assertEqual(timing.battle_text_delay_seconds, 300.0)


if __name__ == "__main__":
    unittest.main()
