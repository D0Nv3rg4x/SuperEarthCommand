"""Pruebas de los catálogos de idioma y de la selección de idioma."""

from __future__ import annotations

import os
import string
import tempfile
import unittest
from pathlib import Path
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from core import i18n
from core.autostart import configure_language
from core.config import activation_phrase, voice_model_path
from ui.deployment_window import STRATAGEM_DEFS, build_stratagems

PROJECT_DIR = Path(__file__).resolve().parents[1]


def placeholders(text: str) -> set[str]:
    return {
        field
        for _, field, _, _ in string.Formatter().parse(text)
        if field
    }


class CatalogTests(unittest.TestCase):
    def test_spanish_and_english_are_available(self):
        self.assertIn("es", i18n.available_languages())
        self.assertIn("en", i18n.available_languages())

    def test_all_catalogs_share_the_same_keys(self):
        languages = i18n.available_languages()
        reference = set(i18n.catalog("es"))

        for language in languages:
            with self.subTest(language=language):
                self.assertEqual(set(i18n.catalog(language)), reference)

    def test_no_translation_is_empty(self):
        for language in i18n.available_languages():
            for key, value in i18n.catalog(language).items():
                with self.subTest(language=language, key=key):
                    self.assertTrue(value.strip())

    def test_placeholders_match_between_languages(self):
        for key, source in i18n.catalog("es").items():
            expected = placeholders(source)
            for language in i18n.available_languages():
                with self.subTest(language=language, key=key):
                    self.assertEqual(
                        placeholders(i18n.catalog(language)[key]),
                        expected,
                    )

    def test_every_stratagem_has_text_in_every_language(self):
        required = {"name", "success", "message"}

        for language in i18n.available_languages():
            catalog = i18n.catalog(language)
            for definition in STRATAGEM_DEFS:
                identifier = definition["id"]
                for field in required:
                    key = (
                        f"stratagem.message.{definition['message']}"
                        if field == "message"
                        else f"stratagem.{identifier}.{field}"
                    )
                    with self.subTest(
                        language=language,
                        stratagem=identifier,
                        field=field,
                    ):
                        self.assertIn(key, catalog)


class LanguageResolutionTests(unittest.TestCase):
    def test_normalizes_locale_variants(self):
        self.assertEqual(
            i18n.normalize_language("es_CL.UTF-8"), "es"
        )
        self.assertEqual(i18n.normalize_language("en-US"), "en")
        self.assertEqual(i18n.normalize_language("EN"), "en")
        self.assertIsNone(i18n.normalize_language("fr"))
        self.assertIsNone(i18n.normalize_language(None))

    def test_default_is_spanish(self):
        self.assertEqual(i18n.resolve_language(None), "es")
        self.assertEqual(i18n.resolve_language(""), "es")
        self.assertEqual(i18n.resolve_language("fr"), "es")

    def test_auto_uses_system_language(self):
        with mock.patch.object(
            i18n, "system_language", return_value="en"
        ):
            self.assertEqual(i18n.resolve_language("auto"), "en")

    def test_auto_falls_back_to_english(self):
        with mock.patch.object(
            i18n, "system_language", return_value=None
        ):
            self.assertEqual(i18n.resolve_language("auto"), "en")

    def test_system_language_reads_language_environment(self):
        with mock.patch.dict(
            os.environ,
            {"LANGUAGE": "en_US.UTF-8", "LANG": "", "LC_ALL": ""},
            clear=False,
        ):
            self.assertEqual(i18n.system_language(), "en")


class TranslationTests(unittest.TestCase):
    def setUp(self):
        self.previous = i18n.get_language()

    def tearDown(self):
        i18n.set_language(self.previous)

    def test_switches_the_visible_text(self):
        i18n.set_language("en")
        self.assertEqual(i18n.t("app.name"), "Democracy Mode")
        self.assertEqual(
            i18n.t("ui.status.idle"),
            "AWAITING OPERATOR AUTHORIZATION",
        )

        i18n.set_language("es")
        self.assertEqual(i18n.t("app.name"), "Modo Democracia")

    def test_formats_parameters(self):
        i18n.set_language("en")
        self.assertEqual(
            i18n.t("ui.status.waiting", name="ORBITAL LASER"),
            "SYSTEM READY: ORBITAL LASER",
        )

    def test_unknown_key_is_returned_for_diagnostics(self):
        self.assertEqual(
            i18n.t("no.existe.esta.clave"), "no.existe.esta.clave"
        )

    def test_unknown_language_falls_back_to_spanish(self):
        self.assertEqual(
            i18n.t_for("fr", "app.name"), "Modo Democracia"
        )

    def test_missing_parameter_keeps_the_template(self):
        self.assertEqual(
            i18n.t_for("es", "ui.status.waiting"),
            "SISTEMA EN ESPERA: {name}",
        )

    def test_english_stratagems_are_translated(self):
        i18n.set_language("en")
        stratagems = build_stratagems()

        self.assertEqual(len(stratagems), len(STRATAGEM_DEFS))
        railcannon = next(
            item for item in stratagems if item["id"] == "railcannon"
        )
        self.assertEqual(
            railcannon["name"], "ORBITAL RAILCANNON STRIKE"
        )
        self.assertEqual(
            railcannon["success"], "RAILCANNON AUTHORIZED"
        )


class VoiceLanguageTests(unittest.TestCase):
    def test_activation_phrase_depends_on_language(self):
        self.assertEqual(
            activation_phrase({}, "es"), "modo democracia"
        )
        self.assertEqual(
            activation_phrase({}, "en"), "democracy mode"
        )

    def test_explicit_empty_phrase_disables_voice(self):
        self.assertEqual(
            activation_phrase({"activation_phrase": ""}, "en"), ""
        )

    def test_explicit_phrase_wins(self):
        self.assertEqual(
            activation_phrase(
                {"activation_phrase": "libertad"}, "en"
            ),
            "libertad",
        )

    def test_model_path_depends_on_language(self):
        spanish = voice_model_path({}, PROJECT_DIR, "es")
        english = voice_model_path({}, PROJECT_DIR, "en")

        self.assertEqual(
            spanish, PROJECT_DIR / "models/vosk-model-small-es-0.42"
        )
        self.assertEqual(
            english,
            PROJECT_DIR / "models/vosk-model-small-en-us-0.15",
        )

    def test_explicit_model_path_wins(self):
        path = voice_model_path(
            {"model_path": "models/custom"}, PROJECT_DIR, "en"
        )
        self.assertEqual(path, PROJECT_DIR / "models" / "custom")


class AutostartLanguageTests(unittest.TestCase):
    def setUp(self):
        self.previous = i18n.get_language()

    def tearDown(self):
        i18n.set_language(self.previous)

    def test_reads_language_from_project_config(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "config.toml").write_text(
                '[general]\nlanguage = "en"\n',
                encoding="utf-8",
            )
            self.assertEqual(configure_language(root), "en")

    def test_missing_config_keeps_spanish(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(
                configure_language(Path(directory)), "es"
            )


if __name__ == "__main__":
    unittest.main()
