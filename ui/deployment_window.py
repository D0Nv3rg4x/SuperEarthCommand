"""Interfaz cinematográfica de Modo Democracia."""

import math
import random
import shutil
import subprocess
import sys
import time
from pathlib import Path

from PySide6.QtCore import (
    QDateTime,
    QElapsedTimer,
    QEasingCurve,
    QPointF,
    QPropertyAnimation,
    QRectF,
    Qt,
    QTimer,
    QUrl,
)
from PySide6.QtGui import (
    QColor,
    QDesktopServices,
    QFont,
    QFontMetricsF,
    QIcon,
    QImage,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QPolygonF,
    QRadialGradient,
    QTransform,
)
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QStackedLayout,
    QVBoxLayout,
    QWidget,
)

from core.audio import AudioController


ARROWS = {
    Qt.Key.Key_Up: "↑",
    Qt.Key.Key_Down: "↓",
    Qt.Key.Key_Left: "←",
    Qt.Key.Key_Right: "→",
}

# Secuencias inspiradas en las estratagemas mostradas en la referencia.
STRATAGEMS = [
    {"name": "ANDANADA GATLING ORBITAL", "sequence": ["→", "→", "←", "↑", "↑"], "success": "ANDANADA GATLING AUTORIZADA", "message": "Super destructor listo"},
    {"name": "ATAQUE AÉREO DE GAS DEL ÁGUILA", "sequence": ["↑", "→", "←", "→"], "success": "ATAQUE DE GAS AUTORIZADO", "message": "Águila lista para el ataque"},
    {"name": "ATAQUE AÉREO EAGLE", "sequence": ["↑", "→", "↓", "→"], "success": "ATAQUE AÉREO AUTORIZADO", "message": "Águila lista para el ataque"},
    {"name": "ATAQUE ORBITAL DE GAS", "sequence": ["→", "→", "↓", "→"], "success": "ATAQUE ORBITAL AUTORIZADO", "message": "Super destructor listo"},
    {"name": "ATAQUE ORBITAL DE PRECISIÓN", "sequence": ["→", "→", "↑"], "success": "ATAQUE DE PRECISIÓN AUTORIZADO", "message": "Super destructor listo"},
    {"name": "ATAQUE ORBITAL EMS", "sequence": ["→", "→", "←", "↓"], "success": "ATAQUE EMS AUTORIZADO", "message": "Super destructor listo"},
    {"name": "CAÑÓN DE RIELES ORBITAL", "sequence": ["↓", "↑", "↓", "→", "←"], "success": "CAÑÓN DE RIELES AUTORIZADO", "message": "Super destructor listo"},
    {"name": "BOMBA DE RACIMO EAGLE", "sequence": ["↑", "→", "↓", "↓", "→"], "success": "BOMBA DE RACIMO AUTORIZADA", "message": "Águila lista para el ataque"},
    {"name": "BOMBA EAGLE DE 500 KG", "sequence": ["↑", "→", "↓", "↓", "↓"], "success": "BOMBA DE 500 KG AUTORIZADA", "message": "Águila lista para el ataque"},
    {"name": "BOMBARDEO ORBITAL DE 120 MM HE", "sequence": ["→", "→", "↓", "←", "→", "↓"], "success": "BOMBARDEO AUTORIZADO", "message": "Super destructor listo"},
    {"name": "BOMBARDEO ORBITAL DE 380 MM HE", "sequence": ["→", "↓", "↑", "↑", "←", "↓", "↓"], "success": "BOMBARDEO PESADO AUTORIZADO", "message": "Super destructor listo"},
    {"name": "BOMBARDEO ORBITAL DE HUMO", "sequence": ["→", "→", "↓", "↑"], "success": "COBERTURA DE HUMO AUTORIZADA", "message": "Super destructor listo"},
    {"name": "BOMBARDEO ORBITAL DE NAPALM", "sequence": ["→", "→", "↓", "←", "→", "↑"], "success": "BOMBARDEO DE NAPALM AUTORIZADO", "message": "Super destructor listo"},
    {"name": "BOMBARDEO ORBITAL PROGRESIVO", "sequence": ["→", "→", "→", "↓", "→", "↓"], "success": "BOMBARDEO PROGRESIVO AUTORIZADO", "message": "Super destructor listo"},
    {"name": "LÁSER ORBITAL", "sequence": ["→", "↓", "↑", "→", "↓"], "success": "LÁSER ORBITAL AUTORIZADO", "message": "Super destructor listo"},
    {"name": "PASADA DE AMETRALLAMIENTO EAGLE", "sequence": ["↑", "→", "→"], "success": "PASADA DE AMETRALLAMIENTO AUTORIZADA", "message": "Águila lista para el ataque"},
    {"name": "PODS DE COHETES EAGLE DE 110 MM", "sequence": ["↑", "↑", "→", "←"], "success": "PODS DE COHETES AUTORIZADOS", "message": "Águila lista para el ataque"},
]

WAKE_TEXT = "DESPERTANDO DE CRIOSUEÑO"
BATTLE_TEXT = "EN BATALLA"
WAKE_GREEN = "#3dff7c"


class BackgroundPanel(QWidget):
    """Fondo temático escalado al tamaño de la ventana (con caché)."""

    def __init__(self, image_path: Path | None):
        super().__init__()
        # La imagen es opcional: si falta, el panel conserva su fondo oscuro.
        self.image = QPixmap(str(image_path)) if image_path is not None else QPixmap()
        self._cache = QPixmap()

    def _rebuild_cache(self):
        # El escalado es costoso: se hace solo cuando cambia el tamaño,
        # no en cada fotograma de las animaciones.
        size = self.size()
        cache = QPixmap(size)
        cache.fill(QColor("#10100e"))
        painter = QPainter(cache)
        if not self.image.isNull():
            image = self.image.scaled(
                size,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            painter.drawPixmap(
                (size.width() - image.width()) // 2,
                (size.height() - image.height()) // 2,
                image,
            )
        painter.fillRect(cache.rect(), QColor(5, 8, 10, 165))
        painter.end()
        self._cache = cache

    def paintEvent(self, event):
        if self._cache.size() != self.size():
            self._rebuild_cache()
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self._cache)


class HeaderBar(QWidget):
    """Cabecera tipo terminal: panel biselado, indicador de enlace y reloj."""

    TITLE = "SUPER EARTH  //  COMANDO DE DESPLIEGUE"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(32)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._blink_on = True
        self._acc = 0.0

    def advance(self, dt: float):
        self._acc += dt
        if self._acc >= 0.5:
            self._acc = 0.0
            self._blink_on = not self._blink_on
            self.update()

    @staticmethod
    def _ticks(painter: QPainter, x: float, cy: float, direction: int):
        """Tres marcas inclinadas «///» en el extremo del panel."""
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#e7b65b"))
        for i in range(3):
            bx = x + direction * i * 7
            painter.drawPolygon(QPolygonF([
                QPointF(bx, cy + 5),
                QPointF(bx + 3, cy + 5),
                QPointF(bx + 3 + 4 * direction, cy - 5),
                QPointF(bx + 4 * direction, cy - 5),
            ]))

    def paintEvent(self, event):
        w, h = self.width(), self.height()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        cut = 9.0
        body = QRectF(0.5, 3.5, w - 1.0, h - 7.0)
        panel = QPolygonF([
            QPointF(body.left() + cut, body.top()),
            QPointF(body.right() - cut, body.top()),
            QPointF(body.right(), body.top() + cut),
            QPointF(body.right(), body.bottom() - cut),
            QPointF(body.right() - cut, body.bottom()),
            QPointF(body.left() + cut, body.bottom()),
            QPointF(body.left(), body.bottom() - cut),
            QPointF(body.left(), body.top() + cut),
        ])
        gradient = QLinearGradient(0, body.top(), 0, body.bottom())
        gradient.setColorAt(0.0, QColor(34, 28, 16, 215))
        gradient.setColorAt(1.0, QColor(10, 10, 9, 215))
        painter.setBrush(gradient)
        painter.setPen(QPen(QColor(184, 146, 58, 230), 1))
        painter.drawPolygon(panel)

        # Línea de acento interior en la parte inferior del panel.
        painter.setPen(QPen(QColor(231, 182, 91, 70), 1))
        painter.drawLine(QPointF(body.left() + cut + 4, body.bottom() - 3),
                         QPointF(body.right() - cut - 4, body.bottom() - 3))

        cy = h / 2.0
        self._ticks(painter, 16, cy, 1)
        self._ticks(painter, w - 16, cy, -1)

        title_spacing = 2.0
        title_font = QFont("Sans Serif", 8, QFont.Weight.Bold)
        title_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, title_spacing)
        painter.setFont(title_font)
        painter.setPen(QColor("#f0c46a"))
        painter.drawText(QRectF(0, 0, w, h), Qt.AlignmentFlag.AlignCenter, self.TITLE)

        # Los textos laterales solo se dibujan si caben junto al título.
        title_w = QFontMetricsF(title_font).horizontalAdvance(self.TITLE)
        side_spacing = 1.5
        side_font = QFont("Sans Serif", 7, QFont.Weight.Bold)
        side_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, side_spacing)
        painter.setFont(side_font)
        metrics = QFontMetricsF(side_font)
        available = (w - title_w) / 2.0 - 56

        left_text = "EN LÍNEA"
        if metrics.horizontalAdvance(left_text) + 14 <= available:
            x = 52.0
            if self._blink_on:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor("#4cff82"))
                painter.drawEllipse(QPointF(x + 3, cy), 3.0, 3.0)
            painter.setPen(QColor("#b9b19a"))
            painter.drawText(QRectF(x + 12, 0, available, h),
                             Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                             left_text)

        clock = QDateTime.currentDateTime().toString("HH:mm:ss")
        if metrics.horizontalAdvance(clock) <= available:
            painter.setPen(QColor("#b9b19a"))
            painter.drawText(QRectF(w - 52 - available, 0, available, h),
                             Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
                             clock)


class SpinningLogo(QWidget):
    """Logo que gira sobre su eje vertical como un holograma de terminal."""

    SPIN_DEG_PER_SEC = 42.0

    def __init__(self, logo_path: Path, width: int = 130, height: int = 92, parent=None):
        super().__init__(parent)
        self.setFixedSize(width, height)
        self._angle = 0.0
        self._time = 0.0
        self._pixmap = QPixmap()
        self._target = QRectF()
        source = QPixmap(str(logo_path))
        if not source.isNull():
            # Se prepara al doble de resolución para que el giro se vea nítido.
            self._pixmap = source.scaled(
                (width - 10) * 2,
                (height - 6) * 2,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            tw = self._pixmap.width() / 2.0
            th = self._pixmap.height() / 2.0
            self._target = QRectF((width - tw) / 2.0, (height - th) / 2.0, tw, th)

    def advance(self, dt: float):
        self._angle = (self._angle + dt * self.SPIN_DEG_PER_SEC) % 360.0
        self._time += dt
        self.update()

    def paintEvent(self, event):
        w, h = self.width(), self.height()
        dpr = self.devicePixelRatioF()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Halo dorado que pulsa suavemente detrás del logo.
        pulse = 0.5 + 0.5 * math.sin(self._time * 2.0)
        halo = QRadialGradient(QPointF(w / 2.0, h / 2.0), h * 0.5)
        halo.setColorAt(0.0, QColor(231, 182, 91, int(46 + 30 * pulse)))
        halo.setColorAt(1.0, QColor(231, 182, 91, 0))
        painter.fillRect(QRectF(0, 0, w, h), halo)

        # El logo se dibuja en una imagen aparte para que las líneas de
        # escaneo solo afecten a los píxeles del logo y no a su entorno.
        frame = QImage(int(w * dpr), int(h * dpr), QImage.Format.Format_ARGB32_Premultiplied)
        frame.setDevicePixelRatio(dpr)
        frame.fill(Qt.GlobalColor.transparent)
        fp = QPainter(frame)
        fp.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        fp.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        transform = QTransform()
        transform.translate(w / 2.0, h / 2.0)
        transform.rotate(self._angle, Qt.Axis.YAxis)
        transform.translate(-w / 2.0, -h / 2.0)
        fp.setTransform(transform)
        if self._pixmap.isNull():
            fp.setPen(QColor("#f4d18b"))
            fp.setFont(QFont("Sans Serif", 14, QFont.Weight.Bold))
            fp.drawText(QRectF(0, 0, w, h), Qt.AlignmentFlag.AlignCenter, "SUPER EARTH")
        else:
            fp.drawPixmap(self._target, self._pixmap, QRectF(self._pixmap.rect()))
        fp.resetTransform()

        fp.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceAtop)
        fp.setPen(QPen(QColor(0, 0, 0, 70), 1))
        for y in range(0, h, 3):
            fp.drawLine(0, y, w, y)
        band_y = (self._time * 38.0) % (h + 30.0) - 15.0
        band = QLinearGradient(0, band_y - 10, 0, band_y + 10)
        band.setColorAt(0.0, QColor(255, 240, 170, 0))
        band.setColorAt(0.5, QColor(255, 240, 170, 95))
        band.setColorAt(1.0, QColor(255, 240, 170, 0))
        fp.fillRect(QRectF(0, band_y - 10, w, 20), band)
        fp.end()

        painter.drawImage(0, 0, frame)


class ArrowKey(QWidget):
    """Tecla con flecha gruesa y corta, al estilo de las estratagemas del juego."""

    ANGLES = {"↑": 0, "→": 90, "↓": 180, "←": 270}
    # estado: (fondo, borde, flecha)
    STATES = {
        "normal": (QColor(27, 27, 29, 235), QColor("#353538"), QColor("#dedede")),
        "active": (QColor("#24231b"), QColor("#b9a91d"), QColor("#f5e33b")),
        "done": (QColor("#e7d72d"), QColor("#f4e747"), QColor("#18180f")),
        "error": (QColor("#b51f27"), QColor("#ff5c62"), QColor("#fff0f0")),
    }
    # Contorno de la flecha apuntando hacia arriba: cabeza ancha y asta
    # corta y gruesa, centrada en el origen.
    SHAPE = [
        (0.0, -12.0), (12.0, 0.0), (6.0, 0.0), (6.0, 12.0),
        (-6.0, 12.0), (-6.0, 0.0), (-12.0, 0.0),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(38, 38)
        self._arrow = ""
        self._state = "normal"

    def set_arrow(self, arrow: str, state: str):
        self._arrow = arrow
        self._state = state
        self.update()

    def paintEvent(self, event):
        background, border, foreground = self.STATES[self._state]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        painter.setPen(QPen(border, 1))
        painter.setBrush(background)
        painter.drawRoundedRect(rect, 5, 5)
        angle = self.ANGLES.get(self._arrow)
        if angle is None:
            return
        painter.translate(rect.center())
        painter.rotate(angle)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(foreground)
        painter.drawPolygon(QPolygonF([QPointF(x, y) for x, y in self.SHAPE]))


class StratagemKeys(QWidget):
    """Fila de teclas con flechas; confirmación amarilla o roja."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(38)
        self.key_labels: list[ArrowKey] = []
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(4)
        for _ in range(7):
            key = ArrowKey()
            self.key_labels.append(key)
            row.addWidget(key, 0, Qt.AlignmentFlag.AlignVCenter)
        self.set_sequence([])

    def set_sequence(self, sequence: list[str], completed_count: int = 0, error=False):
        for i, key in enumerate(self.key_labels):
            if i < len(sequence):
                state = "error" if error else ("done" if i < completed_count else ("active" if i == completed_count else "normal"))
                key.set_arrow(sequence[i], state)
                key.show()
            else:
                key.hide()
        self.adjustSize()


class StripedProgressBar(QWidget):
    """Barra fluida: progreso decimal, franjas continuas y porcentaje legible."""

    STRIPE_WIDTH = 12.0
    STRIPE_STEP = 18.0
    STRIPE_SPEED = 28.0  # píxeles por segundo

    def __init__(self, parent=None):
        super().__init__(parent)
        self._progress = 0.0
        self._stripe_offset = 0.0
        self.setFixedHeight(22)
        self.setMinimumWidth(260)

    def set_progress(self, ratio: float):
        self._progress = max(0.0, min(1.0, ratio))
        self.update()

    def percent(self) -> int:
        return int(self._progress * 100)

    def advance_stripes(self, dt: float):
        self._stripe_offset = (self._stripe_offset + dt * self.STRIPE_SPEED) % self.STRIPE_STEP
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        radius = rect.height() / 2.0

        track = QPainterPath()
        track.addRoundedRect(rect, radius, radius)
        painter.fillPath(track, QColor("#151515"))

        fill_width = (rect.width() - 3.0) * self._progress
        if fill_width > 1.0:
            chunk_rect = QRectF(rect.left() + 1.5, rect.top() + 1.5, fill_width, rect.height() - 3.0)
            chunk_radius = min(chunk_rect.height() / 2.0, chunk_rect.width() / 2.0)
            chunk = QPainterPath()
            chunk.addRoundedRect(chunk_rect, chunk_radius, chunk_radius)
            painter.save()
            painter.setClipPath(chunk)
            painter.fillRect(chunk_rect, QColor("#f2d51f"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#171717"))
            height = chunk_rect.height()
            x = chunk_rect.left() - height - self.STRIPE_STEP + self._stripe_offset
            while x < chunk_rect.right() + height:
                painter.drawPolygon(QPolygonF([
                    QPointF(x, chunk_rect.bottom()),
                    QPointF(x + self.STRIPE_WIDTH, chunk_rect.bottom()),
                    QPointF(x + self.STRIPE_WIDTH + height, chunk_rect.top()),
                    QPointF(x + height, chunk_rect.top()),
                ]))
                x += self.STRIPE_STEP
            painter.restore()

        painter.setPen(QPen(QColor("#b8a126"), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(track)

        # Porcentaje sobre una pastilla oscura para que se lea sobre las franjas.
        font = QFont("Sans Serif", 8, QFont.Weight.Bold)
        painter.setFont(font)
        pill_w = QFontMetricsF(font).horizontalAdvance("100%") + 16.0
        pill_h = rect.height() - 6.0
        pill = QRectF(
            rect.center().x() - pill_w / 2.0,
            rect.center().y() - pill_h / 2.0,
            pill_w,
            pill_h,
        )
        painter.setPen(QPen(QColor(184, 161, 38, 210), 1))
        painter.setBrush(QColor(8, 8, 8, 235))
        painter.drawRoundedRect(pill, pill_h / 2.0, pill_h / 2.0)
        painter.setPen(QColor("#ffe86b"))
        painter.drawText(pill, Qt.AlignmentFlag.AlignCenter, f"{self.percent()}%")


class DeploymentWindow(QMainWindow):
    """Pantalla de despliegue con minijuegos de estratagemas."""

    # Duración del desvanecimiento de la música al abrir el juego.
    AUDIO_FADE_MS = 3000

    def __init__(
        self,
        wallpaper_path: Path | None,
        logo_path: Path,
        audio_path: Path | None,
        duration_seconds: float = 13.2,
        app_icon_path: Path | None = None,
        ministry_icon_path: Path | None = None,
        wallpaper_controller=None,
        launch_game: bool = False,
        steam_app_id: str = "553850",
        launch_delay_seconds: float = 2.0,
        battle_delay_seconds: float = 300.0,
    ):
        super().__init__()
        self.wallpaper_path = wallpaper_path
        self.logo_path = logo_path
        self.audio_path = audio_path
        self.app_icon_path = app_icon_path
        self.ministry_icon_path = ministry_icon_path
        self.wallpaper_controller = wallpaper_controller
        self.wallpaper_changed = False
        self.voice_listener = None
        self._allow_exit = False

        self.launch_game_enabled = launch_game
        self.steam_app_id = str(steam_app_id)
        self.launch_delay_ms = int(max(0.0, launch_delay_seconds) * 1000)
        self.battle_delay_ms = int(max(0.0, battle_delay_seconds) * 1000)

        self.between_duration_ms = 800
        self.stage = "idle"
        self.input_index = 0
        self.current_stratagem: dict | None = None
        self.previous_stratagem_name: str | None = None
        self.main_elapsed_ms = 0
        self.main_duration_ms = int(max(1.0, duration_seconds) * 1000)
        self.minigame_active = False
        self.between_elapsed_ms = 0
        self.session_warnings: list[str] = []
        self.error_flash_timer = QTimer(self)
        self.error_flash_timer.setSingleShot(True)
        self.error_flash_timer.timeout.connect(self.clear_error_flash)
        self.audio = AudioController()

        self.setWindowTitle("Modo Democracia")
        # Ventana compacta para no cubrir innecesariamente el fondo de escritorio.
        self.setMinimumSize(500, 450)
        self.resize(650, 530)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        if app_icon_path and app_icon_path.is_file():
            self.setWindowIcon(QIcon(str(app_icon_path)))

        # Progreso: ~60 fps y tiempo real medido con un reloj monotónico, de modo
        # que la barra avanza de forma continua y no a saltos de 1 %.
        self._clock = QElapsedTimer()
        self._last_tick_ms = 0
        self.timer = QTimer(self)
        self.timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self.update_phase)

        # Animaciones decorativas (logo, cabecera, franjas): solo corren con
        # la ventana visible para no gastar CPU mientras está en la bandeja.
        self._last_anim = time.monotonic()
        self.anim_timer = QTimer(self)
        self.anim_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.anim_timer.setInterval(16)
        self.anim_timer.timeout.connect(self.animate_frame)

        # Fase final: la barra se desvanece, aparece el texto verde parpadeante
        # y, tras un breve instante, se lanza el juego.
        self.wake_timer = QTimer(self)
        self.wake_timer.setSingleShot(True)
        self.wake_timer.timeout.connect(self.show_wake_text)
        self.wake_blink_timer = QTimer(self)
        self.wake_blink_timer.setInterval(500)
        self.wake_blink_timer.timeout.connect(self.toggle_wake_blink)
        self.launch_timer = QTimer(self)
        self.launch_timer.setSingleShot(True)
        self.launch_timer.timeout.connect(self.launch_game)
        # Pasado un tiempo, «DESPERTANDO DE CRIOSUEÑO» cambia a «EN BATALLA».
        self.battle_timer = QTimer(self)
        self.battle_timer.setSingleShot(True)
        self.battle_timer.timeout.connect(self.show_battle_text)

        self.build_interface()

    def build_interface(self):
        background = BackgroundPanel(self.wallpaper_path)
        self.setCentralWidget(background)
        layout = QVBoxLayout(background)
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(6)

        self.header = HeaderBar()
        layout.addWidget(self.header)
        layout.addSpacing(2)

        self.logo = SpinningLogo(self.logo_path)
        layout.addWidget(self.logo, 0, Qt.AlignmentFlag.AlignHCenter)

        title = QLabel("MODO DEMOCRACIA")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Sans Serif", 22, QFont.Weight.Bold))
        title.setStyleSheet("color:#f5f0df;")
        layout.addWidget(title)

        subtitle = QLabel("LA LIBERTAD NO SE ENTREGA. SE DESPLIEGA.")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color:#e7b65b; font-size:12px; letter-spacing:2px;")
        layout.addWidget(subtitle)
        layout.addSpacing(1)

        self.status_label = QLabel("EN ESPERA DE AUTORIZACIÓN DEL OPERADOR")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color:white; font-size:11px; font-weight:bold;")
        layout.addWidget(self.status_label)

        # Zona de progreso: la barra y el texto de despertar comparten el mismo
        # espacio (apilados), así que el cambio no mueve el resto de la interfaz.
        self.progress_area = QWidget()
        self.progress_area.setFixedHeight(40)
        stack = QStackedLayout(self.progress_area)
        stack.setContentsMargins(0, 0, 0, 0)
        stack.setStackingMode(QStackedLayout.StackingMode.StackAll)

        self.bar_page = QWidget()
        bar_layout = QVBoxLayout(self.bar_page)
        bar_layout.setContentsMargins(0, 0, 0, 0)
        bar_layout.addStretch(1)
        self.progress = StripedProgressBar()
        bar_layout.addWidget(self.progress)
        bar_layout.addStretch(1)
        self.bar_opacity = QGraphicsOpacityEffect(self.bar_page)
        self.bar_opacity.setOpacity(1.0)
        self.bar_page.setGraphicsEffect(self.bar_opacity)
        self.bar_fade = QPropertyAnimation(self.bar_opacity, b"opacity", self)
        self.bar_fade.setDuration(380)
        self.bar_fade.setEasingCurve(QEasingCurve.Type.OutCubic)
        stack.addWidget(self.bar_page)

        wake_page = QWidget()
        wake_layout = QVBoxLayout(wake_page)
        wake_layout.setContentsMargins(0, 0, 0, 0)
        self.wake_label = QLabel(WAKE_TEXT)
        self.wake_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        wake_font = QFont("Sans Serif", 20, QFont.Weight.Bold)
        wake_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2.0)
        self.wake_label.setFont(wake_font)
        self.wake_label.setStyleSheet(f"color:{WAKE_GREEN};")
        self.wake_opacity = QGraphicsOpacityEffect(self.wake_label)
        self.wake_opacity.setOpacity(1.0)
        self.wake_label.setGraphicsEffect(self.wake_opacity)
        self.wake_label.hide()
        wake_layout.addWidget(self.wake_label, 0, Qt.AlignmentFlag.AlignCenter)
        stack.addWidget(wake_page)
        layout.addWidget(self.progress_area)

        # El bloque del minijuego anima su altura y opacidad; así el contenido
        # inferior se desplaza suavemente en lugar de saltar al ocultarlo.
        self.game_panel = QWidget()
        self.game_panel.setMaximumHeight(0)
        self.game_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.game_opacity = QGraphicsOpacityEffect(self.game_panel)
        self.game_opacity.setOpacity(0.0)
        self.game_panel.setGraphicsEffect(self.game_opacity)
        game_layout = QVBoxLayout(self.game_panel)
        game_layout.setContentsMargins(0, 0, 0, 0)
        game_layout.setSpacing(5)

        self.stratagem_title = QLabel("")
        self.stratagem_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stratagem_title.setWordWrap(True)
        self.stratagem_title.setStyleSheet("color:#e7b65b; font-size:11px; font-weight:bold;")
        game_layout.addWidget(self.stratagem_title)

        # El panel se ajusta al número de flechas y queda centrado.
        self.keys_panel = QFrame()
        self.keys_panel.setObjectName("keysPanel")
        self.keys_panel.setStyleSheet(self.normal_panel_style())
        panel_layout = QHBoxLayout(self.keys_panel)
        panel_layout.setContentsMargins(8, 6, 8, 6)
        panel_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sequence_keys = StratagemKeys()
        panel_layout.addWidget(self.sequence_keys)
        self.keys_panel.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        game_layout.addWidget(self.keys_panel, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.game_panel)

        self.game_height_animation = QPropertyAnimation(self.game_panel, b"maximumHeight", self)
        self.game_height_animation.setDuration(240)
        self.game_height_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.game_opacity_animation = QPropertyAnimation(self.game_opacity, b"opacity", self)
        self.game_opacity_animation.setDuration(200)
        self.game_opacity_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.game_hide_timer = QTimer(self)
        self.game_hide_timer.setSingleShot(True)
        self.game_hide_timer.timeout.connect(lambda: self.animate_game_panel(False))

        self.hint_label = QLabel("")
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint_label.setWordWrap(True)
        self.hint_label.setStyleSheet("color:#d0c9b6; font-size:10px;")
        layout.addWidget(self.hint_label)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self.cancel_button = QPushButton("✕  CANCELAR DESPLIEGUE")
        self.cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_button.setMinimumHeight(34)
        self.cancel_button.setMinimumWidth(190)
        self.cancel_button.setStyleSheet("""
            QPushButton { background:rgba(19,19,17,225); color:#f2e8d0;
                border:1px solid #b48a38; border-radius:5px; padding:7px 16px;
                font-size:10px; font-weight:bold; letter-spacing:1px; }
            QPushButton:hover { background:#54231d; color:#ffffff; border-color:#efb64e; }
            QPushButton:pressed { background:#8a3325; }
        """)
        self.cancel_button.clicked.connect(self.cancel_sequence)
        buttons.addWidget(self.cancel_button, 1)
        buttons.addStretch(1)
        layout.addLayout(buttons)

        footer = QHBoxLayout()
        footer.addStretch(1)
        ministry_text = QLabel("APROBADO POR EL MINISTERIO DE GUERRA")
        ministry_text.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        ministry_text.setStyleSheet("color:#d0c9b6; font-size:9px; letter-spacing:1px;")
        footer.addWidget(ministry_text)

        if self.ministry_icon_path and self.ministry_icon_path.is_file():
            ministry_icon = QLabel()
            ministry_pixmap = QPixmap(str(self.ministry_icon_path))
            if not ministry_pixmap.isNull():
                ministry_icon.setPixmap(ministry_pixmap.scaled(
                    30, 30,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                ))
            footer.addWidget(ministry_icon)
        layout.addLayout(footer)

    # ------------------------------------------------------------------
    # Animaciones decorativas
    # ------------------------------------------------------------------
    def showEvent(self, event):
        super().showEvent(event)
        self._last_anim = time.monotonic()
        self.anim_timer.start()

    def hideEvent(self, event):
        super().hideEvent(event)
        self.anim_timer.stop()

    def animate_frame(self):
        now = time.monotonic()
        dt = min(0.1, now - self._last_anim)
        self._last_anim = now
        self.logo.advance(dt)
        self.header.advance(dt)
        if self.bar_page.isVisible():
            self.progress.advance_stripes(dt)

    # ------------------------------------------------------------------
    # Voz
    # ------------------------------------------------------------------
    def on_voice_status(self, message: str):
        """Muestra el estado del reconocedor solo cuando no hay despliegue activo."""
        if self.stage == "idle":
            self.status_label.setText(message)

    def on_voice_error(self, message: str):
        print(f"Error de reconocimiento de voz: {message}", file=sys.stderr)
        if self.stage == "idle":
            self.status_label.setText("ESCUCHA POR VOZ NO DISPONIBLE")
            self.hint_label.setText(message)
            self.hint_label.setStyleSheet("color:#ffb0a8; font-size:11px;")

    def on_voice_disabled(self, message: str):
        """Muestra por qué la voz no está activa sin tratarlo como un fallo."""
        if self.stage == "idle":
            self.status_label.setText("ESCUCHA POR VOZ DESACTIVADA")
            self.hint_label.setText(message)
            self.hint_label.setStyleSheet("color:#d0c9b6; font-size:11px;")

    def activate_from_voice(self):
        """Al detectar la frase, muestra la ventana y solicita el despliegue."""
        if self.stage in ("idle", "complete"):
            self.show_from_tray()
            self.start_sequence()

    # ------------------------------------------------------------------
    # Secuencia
    # ------------------------------------------------------------------
    def reset_progress_area(self):
        """Devuelve la zona de progreso a su estado inicial (barra visible)."""
        self.wake_timer.stop()
        self.wake_blink_timer.stop()
        self.launch_timer.stop()
        self.battle_timer.stop()
        self.bar_fade.stop()
        self.bar_opacity.setOpacity(1.0)
        self.bar_page.show()
        self.wake_label.setText(WAKE_TEXT)
        self.wake_label.hide()
        self.wake_opacity.setOpacity(1.0)

    def start_sequence(self):
        # Permite repetir el protocolo por voz después de una ejecución completada.
        if self.stage == "complete":
            self.stage = "idle"
        if self.stage != "idle":
            return
        self.reset_progress_area()
        self.previous_stratagem_name = None
        self.current_stratagem = None
        self.stage = "running"
        self.main_elapsed_ms = 0
        self.session_warnings = []
        self.progress.set_progress(0.0)
        self.cancel_button.setText("✕  CANCELAR DESPLIEGUE")
        self.status_label.setText("INICIANDO PROTOCOLO DE DESPLIEGUE...")
        self.status_label.setStyleSheet("color:white; font-size:13px; font-weight:bold;")
        self.stratagem_title.setText("")
        self.game_hide_timer.stop()
        self.animate_game_panel(False)
        self.sequence_keys.set_sequence([])
        self.hint_label.setText("")
        self.hint_label.setStyleSheet("color:#d0c9b6; font-size:11px;")

        if self.wallpaper_controller is not None:
            changed, wallpaper_error = self.wallpaper_controller.activate()
            if changed:
                self.wallpaper_changed = True
            elif wallpaper_error:
                self.session_warnings.append(
                    "Aviso: no se pudo cambiar el fondo. El protocolo continuará sin modificarlo."
                )
                print(f"No se pudo cambiar el fondo: {wallpaper_error}", file=sys.stderr)

        if self.audio_path is None or not self.audio.play(self.audio_path):
            self.session_warnings.append("Aviso: no se encontró el audio. El protocolo continuará.")

        # El progreso principal corre por su cuenta: los aciertos del minijuego
        # nunca lo incrementan, lo pausan ni lo adelantan.
        self.minigame_active = True
        self._clock.start()
        self._last_tick_ms = 0
        self.timer.start()
        self.start_stratagem()

    def update_phase(self):
        if self.stage in ("idle", "complete"):
            self.timer.stop()
            return

        # Tiempo real transcurrido (limitado por si la interfaz se congela un
        # instante, por ejemplo al cambiar el fondo del escritorio).
        now = self._clock.elapsed()
        delta = min(now - self._last_tick_ms, 120)
        self._last_tick_ms = now

        self.main_elapsed_ms += delta
        ratio = min(1.0, self.main_elapsed_ms / self.main_duration_ms)
        self.progress.set_progress(ratio)

        if self.stage == "between":
            self.between_elapsed_ms += delta
            if self.between_elapsed_ms >= self.between_duration_ms and self.minigame_active:
                self.start_stratagem()

        if ratio >= 1.0:
            self.finish_sequence()

    def finish_sequence(self):
        self.stage = "complete"
        self.timer.stop()
        self.minigame_active = False
        self.error_flash_timer.stop()
        self.game_hide_timer.stop()
        self.keys_panel.setStyleSheet(self.normal_panel_style())
        self.stratagem_title.setText("")
        self.animate_game_panel(False)
        self.progress.set_progress(1.0)
        self.status_label.setText("¡DESPLIEGUE AUTORIZADO! POR LA SUPER TIERRA.")
        self.status_label.setStyleSheet("color:#f0df36; font-size:15px; font-weight:bold;")
        self.hint_label.setStyleSheet("color:#e9dc39; font-size:13px; font-weight:bold;")
        self.hint_label.setText("Todos los sistemas locales están preparados.")
        self.cancel_button.setText("✕  CERRAR")
        # El fondo de Super Tierra permanece activo tras completar la barra.
        # Se restaura únicamente cuando el usuario cierra/cancela la ventana.

        # La barra se desvanece y deja su lugar al texto de despertar.
        self.bar_fade.stop()
        self.bar_fade.setStartValue(self.bar_opacity.opacity())
        self.bar_fade.setEndValue(0.0)
        self.bar_fade.start()
        self.wake_timer.start(self.bar_fade.duration() + 40)

    def show_wake_text(self):
        if self.stage != "complete":
            return
        self.bar_page.hide()
        self.wake_opacity.setOpacity(1.0)
        self.wake_label.show()
        self.wake_blink_timer.start()
        self.launch_timer.start(self.launch_delay_ms)
        if self.launch_game_enabled and self.battle_delay_ms > 0:
            self.battle_timer.start(self.battle_delay_ms)

    def show_battle_text(self):
        if self.stage == "complete":
            self.wake_label.setText(BATTLE_TEXT)

    def toggle_wake_blink(self):
        on = self.wake_opacity.opacity() < 0.5
        self.wake_opacity.setOpacity(1.0 if on else 0.1)

    def launch_game(self):
        """Abre Helldivers 2 mediante Steam una vez mostrado el texto final."""
        if self.stage != "complete" or not self.launch_game_enabled:
            return
        url = f"steam://rungameid/{self.steam_app_id}"
        steam = shutil.which("steam")
        self.hint_label.setStyleSheet("color:#7dffa0; font-size:12px; font-weight:bold;")
        try:
            if steam:
                # Sesión propia: el juego no se cierra si se sale de la aplicación.
                subprocess.Popen(
                    [steam, url],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
            elif not QDesktopServices.openUrl(QUrl(url)):
                raise OSError("No se encontró Steam ni un manejador para steam://")
            self.hint_label.setText("Abriendo Helldivers 2 mediante Steam…")
            # La música baja de a poco para no mezclarse con el audio del juego.
            self.audio.fade_out(self.AUDIO_FADE_MS)
        except OSError as exc:
            print(f"No se pudo abrir Helldivers 2: {exc}", file=sys.stderr)
            self.hint_label.setStyleSheet("color:#ffb0a8; font-size:12px; font-weight:bold;")
            self.hint_label.setText("No se pudo abrir Helldivers 2. Comprueba que Steam esté instalado.")

    def animate_game_panel(self, visible: bool):
        """Expande/contrae el bloque del minijuego sin saltos de layout."""
        self.game_height_animation.stop()
        self.game_opacity_animation.stop()
        current_height = self.game_panel.maximumHeight()
        target_height = max(1, self.game_panel.sizeHint().height()) if visible else 0
        self.game_height_animation.setStartValue(current_height)
        self.game_height_animation.setEndValue(target_height)
        self.game_opacity_animation.setStartValue(self.game_opacity.opacity())
        self.game_opacity_animation.setEndValue(1.0 if visible else 0.0)
        if visible:
            self.game_panel.setMinimumHeight(0)
            self.game_panel.show()
        self.game_height_animation.start()
        self.game_opacity_animation.start()

    @staticmethod
    def normal_panel_style():
        return """
            QFrame#keysPanel { background:rgba(9,9,10,175);
                border:1px solid rgba(180,180,180,55); border-radius:12px; }
        """

    def start_stratagem(self):
        if not self.minigame_active or self.progress.percent() >= 100:
            return
        # Elegir una nueva estratagema aleatoria y evitar repetir la anterior
        # de inmediato siempre que haya otras disponibles.
        choices = [item for item in STRATAGEMS if item["name"] != self.previous_stratagem_name]
        self.current_stratagem = random.choice(choices or STRATAGEMS)
        self.previous_stratagem_name = self.current_stratagem["name"]
        self.input_index = 0
        self.stage = "stratagem"
        self.between_elapsed_ms = 0
        self.status_label.setStyleSheet("color:white; font-size:13px; font-weight:bold;")
        self.hint_label.setStyleSheet("color:#d0c9b6; font-size:11px;")
        self.status_label.setText(f"SISTEMA EN ESPERA: {self.current_stratagem['name']}")
        self.stratagem_title.setText(self.current_stratagem["name"])
        self.sequence_keys.set_sequence(self.current_stratagem["sequence"])
        self.keys_panel.setStyleSheet(self.normal_panel_style())
        self.keys_panel.show()
        self.animate_game_panel(True)
        # Los avisos de la sesión (fondo, audio) permanecen visibles.
        self.hint_label.setText(" ".join(self.session_warnings))
        self.setFocus()

    def clear_error_flash(self):
        if self.minigame_active and self.stage == "stratagem" and self.current_stratagem:
            self.keys_panel.setStyleSheet(self.normal_panel_style())
            self.sequence_keys.set_sequence(self.current_stratagem["sequence"], 0)
            self.status_label.setStyleSheet("color:white; font-size:13px; font-weight:bold;")
            self.status_label.setText(f"SISTEMA EN ESPERA: {self.current_stratagem['name']}")

    def keyPressEvent(self, event):
        if self.stage == "stratagem":
            arrow = ARROWS.get(event.key())
            if arrow:
                self.handle_arrow(arrow)
                event.accept()
                return
        if event.key() == Qt.Key.Key_Escape and self.stage != "idle":
            self.cancel_sequence()
            event.accept()
            return
        super().keyPressEvent(event)

    def handle_arrow(self, arrow: str):
        if not self.minigame_active or self.stage != "stratagem" or not self.current_stratagem:
            return
        sequence = self.current_stratagem["sequence"]
        expected = sequence[self.input_index]

        if arrow != expected:
            # El error solo afecta visualmente al minijuego. La barra principal
            # continúa avanzando con su temporizador habitual.
            self.input_index = 0
            self.sequence_keys.set_sequence(sequence, 0, error=True)
            self.keys_panel.setStyleSheet("""
                QFrame#keysPanel { background:rgba(140,10,18,230);
                    border:1px solid #ff424a; border-radius:12px; }
            """)
            self.status_label.setText("ERROR DE SECUENCIA")
            self.status_label.setStyleSheet("color:#ff555d; font-size:13px; font-weight:bold;")
            self.error_flash_timer.start(300)
            return

        self.input_index += 1
        self.sequence_keys.set_sequence(sequence, self.input_index)

        if self.input_index == len(sequence):
            self.status_label.setText(self.current_stratagem["success"])
            self.status_label.setStyleSheet("color:#f0df36; font-size:15px; font-weight:bold;")
            self.hint_label.setStyleSheet("color:#e9dc39; font-size:13px; font-weight:bold;")
            self.hint_label.setText(self.current_stratagem["message"])
            self.animate_game_panel(False)
            self.stage = "between"
            self.between_elapsed_ms = 0
            self.keys_panel.setStyleSheet(self.normal_panel_style())

    def restore_wallpaper(self):
        """Restaura el fondo original si el protocolo lo había cambiado."""
        if self.wallpaper_controller is None or not self.wallpaper_changed:
            return
        restored, error = self.wallpaper_controller.restore()
        if restored:
            self.wallpaper_changed = False
        elif error:
            print(f"No se pudo restaurar el fondo original: {error}", file=sys.stderr)

    def cancel_sequence(self):
        """Cancela/restaura la secuencia y oculta la ventana; la escucha continúa."""
        self.timer.stop()
        self.error_flash_timer.stop()
        self.audio.stop()
        self.reset_progress_area()
        self.minigame_active = False
        self.stage = "idle"
        self.progress.set_progress(0.0)
        self.status_label.setText("EN ESPERA DE AUTORIZACIÓN DEL OPERADOR")
        self.status_label.setStyleSheet("color:white; font-size:11px; font-weight:bold;")
        self.stratagem_title.setText("")
        self.hint_label.setText("")
        self.hint_label.setStyleSheet("color:#d0c9b6; font-size:10px;")
        self.game_hide_timer.stop()
        self.animate_game_panel(False)
        self.cancel_button.setText("✕  CANCELAR DESPLIEGUE")
        self.restore_wallpaper()
        self.hide()

    def show_from_tray(self):
        """Vuelve a mostrar la interfaz desde el icono de la bandeja."""
        self.show()
        self.raise_()
        self.activateWindow()

    def stop_voice_listener(self):
        """Detiene la escucha y libera el micrófono de forma controlada."""
        if self.voice_listener is not None and self.voice_listener.isRunning():
            if not self.voice_listener.stop():
                print(
                    "Advertencia: el hilo de voz no terminó a tiempo.",
                    file=sys.stderr,
                )

    def exit_application(self):
        """Salida explícita desde el menú de bandeja: detener todo y restaurar."""
        self._allow_exit = True
        self.stop_voice_listener()
        self.timer.stop()
        self.anim_timer.stop()
        self.error_flash_timer.stop()
        self.reset_progress_area()
        self.audio.stop()
        self.restore_wallpaper()
        self.close()
        QApplication.quit()

    def closeEvent(self, event):
        # Cerrar con X solo oculta la ventana; el worker de voz sigue activo.
        if not self._allow_exit:
            event.ignore()
            self.hide()
            return
        self.stop_voice_listener()
        self.timer.stop()
        self.anim_timer.stop()
        self.error_flash_timer.stop()
        self.reset_progress_area()
        self.audio.stop()
        self.restore_wallpaper()
        event.accept()