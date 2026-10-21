"""Escucha local y continua de la frase de activación mediante Vosk.

La voz es una función opcional: si faltan las dependencias, el modelo o el
micrófono, la aplicación debe poder iniciarse y seguir funcionando sin ella.
Las comprobaciones previas viven en funciones independientes para poder
probarlas sin abrir el micrófono ni cargar el modelo acústico.
"""
from __future__ import annotations

import importlib
import json
import queue
import re
import time
import unicodedata
from pathlib import Path

from PySide6.QtCore import QThread, Signal

SAMPLE_RATE = 16000
BLOCK_SIZE = 8000

# Archivos mínimos que debe contener un modelo de Vosk utilizable.
MODEL_REQUIRED_PATHS = (
    "am/final.mdl",
    "conf/mfcc.conf",
    "graph/HCLr.fst",
    "graph/Gr.fst",
)

# Frecuencia mínima con la que se repite un aviso del micrófono.
MIC_STATUS_INTERVAL_SECONDS = 3.0


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.lower())
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def check_dependencies() -> tuple[bool, str | None]:
    """Comprueba que Vosk y sounddevice pueden importarse.

    No instala nada: solo informa de lo que falta.
    """
    missing: list[str] = []

    for module in ("vosk", "sounddevice"):
        try:
            importlib.import_module(module)
        except Exception as exc:  # ImportError, OSError de PortAudio, etc.
            missing.append(f"{module} ({type(exc).__name__}: {exc})")

    if missing:
        return False, (
            "Faltan dependencias de voz: "
            + ", ".join(missing)
            + ". Instala requirements-voice.txt en el entorno virtual."
        )

    return True, None


def check_model(model_path: Path | str | None) -> tuple[bool, str | None]:
    """Comprueba que el modelo existe y contiene los archivos necesarios."""
    if model_path is None:
        return False, "No hay una ruta de modelo de voz configurada."

    path = Path(model_path).expanduser()

    if not path.is_dir():
        return False, (
            "No se encontró el modelo local de Vosk:\n"
            f"{path}\n"
            "Descárgalo con scripts/instalar_modelo_voz.sh."
        )

    missing = [
        relative
        for relative in MODEL_REQUIRED_PATHS
        if not (path / relative).is_file()
    ]

    if missing:
        return False, (
            "El modelo de Vosk está incompleto:\n"
            f"{path}\n"
            "Faltan: "
            + ", ".join(missing)
            + ". Vuelve a descargarlo con scripts/instalar_modelo_voz.sh."
        )

    return True, None


def check_input_device() -> tuple[bool, str | None]:
    """Comprueba que existe un micrófono de entrada predeterminado."""
    try:
        sounddevice = importlib.import_module("sounddevice")
    except Exception as exc:
        return False, (
            "No se pudo cargar sounddevice: "
            f"{type(exc).__name__}: {exc}"
        )

    try:
        device = sounddevice.query_devices(kind="input")
        channels = int(device.get("max_input_channels", 0) or 0)
    except Exception as exc:
        return False, (
            "No hay un micrófono de entrada disponible. "
            "Conecta uno y vuelve a iniciar la aplicación. "
            f"Detalle: {type(exc).__name__}: {exc}"
        )

    if channels < 1:
        return False, (
            "El dispositivo de entrada predeterminado no admite captura "
            "de audio. Selecciona otro micrófono en el sistema."
        )

    return True, None


def check_voice_availability(
    phrase: str,
    model_path: Path | str | None,
) -> tuple[bool, str | None]:
    """Comprobación previa completa, sin cargar el modelo ni abrir el micro."""
    if not normalize_text(phrase):
        return False, "La frase de activación está vacía en config.toml."

    for check in (
        check_dependencies,
        lambda: check_model(model_path),
        check_input_device,
    ):
        ok, error = check()
        if not ok:
            return False, error

    return True, None


class VoiceListener(QThread):
    """Worker de micrófono; nunca bloquea el hilo de la interfaz gráfica."""

    activation_detected = Signal()
    status_changed = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, phrase: str, model_path: Path, parent=None):
        super().__init__(parent)
        self.phrase = normalize_text(phrase)
        self.model_path = Path(model_path).expanduser().resolve()
        self._stop_requested = False
        self._failed = False
        self._audio_queue: queue.Queue[bytes] = queue.Queue(maxsize=32)
        self._last_mic_status: str | None = None
        self._last_mic_status_time = 0.0

    def start(self) -> bool:
        """Inicia la escucha una sola vez; devuelve False si ya estaba activa."""
        if self.isRunning():
            return False

        self._stop_requested = False
        self._failed = False
        self._last_mic_status = None
        self._last_mic_status_time = 0.0
        super().start()
        return True

    def stop(self, timeout_ms: int = 5000) -> bool:
        """Solicita la parada y espera a que el hilo libere el micrófono."""
        self._stop_requested = True

        # Desbloquea el bucle si está esperando audio.
        try:
            self._audio_queue.put_nowait(b"")
        except queue.Full:
            try:
                self._audio_queue.get_nowait()
                self._audio_queue.put_nowait(b"")
            except (queue.Empty, queue.Full):
                pass

        if not self.isRunning():
            return True

        return self.wait(timeout_ms)

    def _report_failure(self, message: str) -> None:
        """Registra un fallo controlado; la aplicación continúa sin voz."""
        self._failed = True
        self.error_occurred.emit(message)

    def _report_mic_status(self, status) -> None:
        """Evita que un problema de audio genere una secuencia ilimitada."""
        message = f"MICRÓFONO: {status}"
        now = time.monotonic()

        if (
            message != self._last_mic_status
            or now - self._last_mic_status_time
            >= MIC_STATUS_INTERVAL_SECONDS
        ):
            self._last_mic_status = message
            self._last_mic_status_time = now
            self.status_changed.emit(message)

    def run(self):
        if not self.phrase:
            self._report_failure(
                "La frase de activación está vacía en config.toml."
            )
            return

        model_ok, model_error = check_model(self.model_path)
        if not model_ok:
            self._report_failure(model_error or "Modelo de voz no válido.")
            return

        try:
            vosk = importlib.import_module("vosk")
            sounddevice = importlib.import_module("sounddevice")
            KaldiRecognizer = vosk.KaldiRecognizer
            Model = vosk.Model
            SetLogLevel = vosk.SetLogLevel
        except Exception as exc:
            self._report_failure(
                "Faltan dependencias de voz. Instala requirements-voice.txt "
                f"en el entorno virtual. Detalle: {type(exc).__name__}: {exc}"
            )
            return

        if self._stop_requested:
            self.status_changed.emit("ESCUCHA DETENIDA")
            return

        try:
            SetLogLevel(-1)
            self.status_changed.emit("CARGANDO RECONOCIMIENTO DE VOZ LOCAL…")
            model = Model(str(self.model_path))
            recognizer = KaldiRecognizer(model, SAMPLE_RATE)
            recognizer.SetWords(False)
        except Exception as exc:
            if not self._stop_requested:
                self._report_failure(
                    "No se pudo cargar el modelo de voz local. "
                    "Comprueba que el modelo esté completo y sea compatible "
                    f"con la versión de Vosk instalada. Detalle: "
                    f"{type(exc).__name__}: {exc}"
                )
            return

        if self._stop_requested:
            self.status_changed.emit("ESCUCHA DETENIDA")
            return

        device_ok, device_error = check_input_device()
        if not device_ok:
            self._report_failure(device_error or "Micrófono no disponible.")
            return

        def audio_callback(indata, frames, time_info, status):
            if status:
                self._report_mic_status(status)
            if self._stop_requested:
                return
            try:
                self._audio_queue.put_nowait(bytes(indata))
            except queue.Full:
                # Si el consumidor se retrasa, descartamos el bloque más viejo.
                try:
                    self._audio_queue.get_nowait()
                    self._audio_queue.put_nowait(bytes(indata))
                except (queue.Empty, queue.Full):
                    pass

        try:
            # El contexto garantiza que el dispositivo se libere al salir,
            # tanto por parada normal como por error.
            with sounddevice.RawInputStream(
                samplerate=SAMPLE_RATE,
                blocksize=BLOCK_SIZE,
                dtype="int16",
                channels=1,
                callback=audio_callback,
            ):
                self.status_changed.emit(
                    "ESCUCHA ACTIVA · DI «MODO DEMOCRACIA»"
                )
                armed = True

                while not self._stop_requested:
                    try:
                        data = self._audio_queue.get(timeout=0.25)
                    except queue.Empty:
                        continue

                    if not data:
                        continue

                    if recognizer.AcceptWaveform(data):
                        result = json.loads(recognizer.Result())
                        text = normalize_text(result.get("text", ""))

                        if self.phrase in text:
                            if armed:
                                armed = False
                                self.activation_detected.emit()
                        else:
                            # Se rearma cuando el reconocedor cierra una frase
                            # sin la palabra clave.
                            armed = True

        except Exception as exc:
            if not self._stop_requested:
                self._report_failure(
                    "No se pudo iniciar o mantener la escucha del micrófono. "
                    "Comprueba el dispositivo de entrada y los permisos de "
                    f"audio. Detalle: {type(exc).__name__}: {exc}"
                )
        finally:
            # Si falló, el mensaje de error ya explica el estado; no lo
            # sobrescribimos con «ESCUCHA DETENIDA».
            if not self._failed:
                self.status_changed.emit("ESCUCHA DETENIDA")
