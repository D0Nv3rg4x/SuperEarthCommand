
"""Reproducción de audio para Modo Democracia."""

import sys
from pathlib import Path

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QUrl
from PySide6.QtMultimedia import (
    QAudioOutput,
    QMediaDevices,
    QMediaPlayer,
)


class AudioController:
    """Controla la reproducción de la banda sonora local."""

    DEFAULT_VOLUME = 0.65

    def __init__(self):
        self.player = QMediaPlayer()
        self.output = QAudioOutput()
        self._volume = self.DEFAULT_VOLUME

        # Seleccionar explícitamente la salida predeterminada de Qt.
        device = QMediaDevices.defaultAudioOutput()
        if not device.isNull():
            self.output.setDevice(device)

        self.output.setVolume(self._volume)
        self.player.setAudioOutput(self.output)
        self.player.errorOccurred.connect(self._on_error)

        # Animación del volumen para el desvanecimiento final.
        self._fade = QPropertyAnimation(self.output, b"volume")
        self._fade.setEasingCurve(QEasingCurve.Type.Linear)
        self._fade.finished.connect(self._on_fade_finished)

    def _on_error(self, error, message) -> None:
        print(f"Error de audio: {error} {message}", file=sys.stderr)

    def _on_fade_finished(self) -> None:
        # Solo se detiene si el volumen llegó realmente a cero; así una
        # interrupción manual del desvanecimiento no corta la música.
        if self.output.volume() <= 0.001:
            self.player.stop()
            self.output.setVolume(self._volume)

    def play(self, audio_path: str | Path) -> bool:
        """Reproduce el archivo indicado si existe."""
        path = Path(audio_path).expanduser().resolve()

        if not path.is_file():
            return False

        self._fade.stop()
        self.output.setVolume(self._volume)
        self.player.setSource(QUrl.fromLocalFile(str(path)))
        self.player.play()
        return True

    def fade_out(self, duration_ms: int = 4000) -> None:
        """Baja el volumen de forma gradual y detiene la música al llegar a cero."""
        if self.player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
            return

        self._fade.stop()
        self._fade.setDuration(max(1, int(duration_ms)))
        self._fade.setStartValue(self.output.volume())
        self._fade.setEndValue(0.0)
        self._fade.start()

    def stop(self) -> None:
        """Detiene la reproducción de inmediato y restaura el volumen."""
        self._fade.stop()
        self.player.stop()
        self.output.setVolume(self._volume)

    def set_volume(self, volume: float) -> None:
        """Ajusta el volumen entre 0.0 y 1.0."""
        self._volume = max(0.0, min(1.0, volume))
        self.output.setVolume(self._volume)
