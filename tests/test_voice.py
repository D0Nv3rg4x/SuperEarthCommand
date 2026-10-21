"""Pruebas de la Fase 3: reconocimiento de voz opcional."""

from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from PySide6.QtCore import QCoreApplication

from core import voice

PROJECT_DIR = Path(__file__).resolve().parents[1]
MODEL_DIR = PROJECT_DIR / "models/vosk-model-small-es-0.42"


class NormalizeTextTests(unittest.TestCase):
    def test_removes_accents_and_punctuation(self):
        self.assertEqual(
            voice.normalize_text("  ¡MODO DEMOCRACIA!  "),
            "modo democracia",
        )

    def test_collapses_repeated_separators(self):
        self.assertEqual(
            voice.normalize_text("Modo---Democracia"),
            "modo democracia",
        )


class ModelCheckTests(unittest.TestCase):
    def test_real_model_is_complete(self):
        ok, error = voice.check_model(MODEL_DIR)
        self.assertTrue(ok, error)
        self.assertIsNone(error)

    def test_missing_model_reports_path(self):
        missing = PROJECT_DIR / "models/no-existe"
        ok, error = voice.check_model(missing)
        self.assertFalse(ok)
        self.assertIn(str(missing), error)

    def test_incomplete_model_lists_missing_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "am").mkdir()
            (root / "am/final.mdl").write_bytes(b"x")

            ok, error = voice.check_model(root)

        self.assertFalse(ok)
        self.assertIn("incompleto", error)
        self.assertIn("conf/mfcc.conf", error)
        self.assertIn("graph/Gr.fst", error)

    def test_no_model_path_is_reported(self):
        ok, error = voice.check_model(None)
        self.assertFalse(ok)
        self.assertIn("ruta", error)


class DependencyCheckTests(unittest.TestCase):
    def test_missing_dependency_is_reported(self):
        def fake_import(module):
            if module == "vosk":
                raise ImportError("Vosk no instalado")
            return object()

        with mock.patch.object(voice, "importlib") as fake:
            fake.import_module.side_effect = fake_import
            ok, error = voice.check_dependencies()

        self.assertFalse(ok)
        self.assertIn("vosk", error)
        self.assertIn("requirements-voice.txt", error)

    def test_present_dependencies_are_accepted(self):
        with mock.patch.object(voice, "importlib") as fake:
            fake.import_module.return_value = object()
            ok, error = voice.check_dependencies()

        self.assertTrue(ok)
        self.assertIsNone(error)


class InputDeviceCheckTests(unittest.TestCase):
    def test_missing_microphone_is_reported(self):
        with mock.patch.object(voice, "importlib") as fake:
            fake.import_module.return_value.query_devices.side_effect = (
                ValueError("No default input device")
            )
            ok, error = voice.check_input_device()

        self.assertFalse(ok)
        self.assertIn("micrófono", error)

    def test_device_without_input_channels_is_rejected(self):
        with mock.patch.object(voice, "importlib") as fake:
            fake.import_module.return_value.query_devices.return_value = {
                "name": "salida",
                "max_input_channels": 0,
            }
            ok, error = voice.check_input_device()

        self.assertFalse(ok)
        self.assertIn("no admite", error)

    def test_default_input_device_is_accepted(self):
        with mock.patch.object(voice, "importlib") as fake:
            fake.import_module.return_value.query_devices.return_value = {
                "name": "Micrófono",
                "max_input_channels": 2,
            }
            ok, error = voice.check_input_device()

        self.assertTrue(ok)
        self.assertIsNone(error)


class AvailabilityTests(unittest.TestCase):
    def test_available_when_all_checks_pass(self):
        with (
            mock.patch.object(
                voice, "check_dependencies", return_value=(True, None)
            ),
            mock.patch.object(
                voice, "check_model", return_value=(True, None)
            ),
            mock.patch.object(
                voice, "check_input_device", return_value=(True, None)
            ),
        ):
            ok, error = voice.check_voice_availability(
                "modo democracia", MODEL_DIR
            )

        self.assertTrue(ok)
        self.assertIsNone(error)

    def test_unavailable_check_stops_later_checks(self):
        with (
            mock.patch.object(
                voice,
                "check_dependencies",
                return_value=(False, "sin dependencias"),
            ),
            mock.patch.object(voice, "check_model") as model_check,
            mock.patch.object(voice, "check_input_device") as device_check,
        ):
            ok, error = voice.check_voice_availability(
                "modo democracia", MODEL_DIR
            )

        self.assertFalse(ok)
        self.assertEqual(error, "sin dependencias")
        model_check.assert_not_called()
        device_check.assert_not_called()

    def test_empty_phrase_is_reported(self):
        ok, error = voice.check_voice_availability("  ", MODEL_DIR)
        self.assertFalse(ok)
        self.assertIn("frase", error)


class VoiceListenerLifecycleTests(unittest.TestCase):
    def test_start_does_not_duplicate_running_listener(self):
        listener = voice.VoiceListener("modo democracia", MODEL_DIR)

        with mock.patch.object(listener, "isRunning", return_value=True):
            started = listener.start()

        self.assertFalse(started)

    def test_stop_without_running_returns_true(self):
        listener = voice.VoiceListener("modo democracia", MODEL_DIR)

        with mock.patch.object(listener, "isRunning", return_value=False):
            stopped = listener.stop()

        self.assertTrue(stopped)

    def test_activation_signal_when_phrase_recognized(self):
        events = []

        class FakeStream:
            def __init__(self, **kwargs):
                self.callback = kwargs.get("callback")
                self.closed = False

            def __enter__(self):
                if self.callback:
                    self.callback(b"\x00\x00", 0, None, None)
                return self

            def __exit__(self, *args):
                self.closed = True

        class FakeVosk:
            @staticmethod
            def SetLogLevel(level):
                pass

            class Model:
                def __init__(self, path):
                    self.path = path

            class KaldiRecognizer:
                def __init__(self, model, rate):
                    pass

                def SetWords(self, value):
                    pass

                def AcceptWaveform(self, data):
                    return True

                def Result(self):
                    return '{"text": "modo democracia"}'

        class FakeSoundDevice:
            @staticmethod
            def query_devices(kind="input"):
                return {"name": "Fake mic", "max_input_channels": 1}

            @staticmethod
            def RawInputStream(**kwargs):
                return FakeStream(**kwargs)

        def fake_import(module):
            return {"vosk": FakeVosk, "sounddevice": FakeSoundDevice}[module]

        listener = voice.VoiceListener("modo democracia", MODEL_DIR)
        listener.activation_detected.connect(lambda: events.append(True))

        app = QCoreApplication.instance() or QCoreApplication([])

        with mock.patch.object(voice, "importlib") as fake:
            fake.import_module.side_effect = fake_import
            self.assertTrue(listener.start())

            deadline = time.monotonic() + 3.0
            while not events and time.monotonic() < deadline:
                app.processEvents()
                time.sleep(0.02)

            listener.stop(timeout_ms=3000)

        self.assertTrue(events, "No se emitió la activación por voz")

    def test_stop_releases_stream_and_ends_thread(self):
        class FakeStream:
            def __init__(self, **kwargs):
                self.closed = False

            def __enter__(self):
                return self

            def __exit__(self, *args):
                self.closed = True

        stream = FakeStream()

        class FakeVosk:
            @staticmethod
            def SetLogLevel(level):
                pass

            class Model:
                def __init__(self, path):
                    self.path = path

            class KaldiRecognizer:
                def __init__(self, model, rate):
                    pass

                def SetWords(self, value):
                    pass

                def AcceptWaveform(self, data):
                    return False

        class FakeSoundDevice:
            @staticmethod
            def query_devices(kind="input"):
                return {"name": "Fake mic", "max_input_channels": 1}

            @staticmethod
            def RawInputStream(**kwargs):
                return stream

        def fake_import(module):
            return {"vosk": FakeVosk, "sounddevice": FakeSoundDevice}[module]

        listener = voice.VoiceListener("modo democracia", MODEL_DIR)

        with mock.patch.object(voice, "importlib") as fake:
            fake.import_module.side_effect = fake_import
            self.assertTrue(listener.start())
            time.sleep(0.2)
            stopped = listener.stop(timeout_ms=3000)

        self.assertTrue(stopped, "El hilo de voz no terminó tras stop()")
        self.assertTrue(stream.closed, "El micrófono no se liberó al parar")
        self.assertFalse(listener.isRunning())


if __name__ == "__main__":
    unittest.main()
