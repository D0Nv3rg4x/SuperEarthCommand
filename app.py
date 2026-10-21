
"""Punto de entrada de Modo Democracia."""

import sys

if sys.version_info < (3, 11):
    print(
        "Error: Modo Democracia requiere Python 3.11 o superior.",
        file=sys.stderr,
    )
    raise SystemExit(1)

import traceback
from pathlib import Path

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

from core.config import (
    activation_phrase,
    load_config as load_config_file,
    plan_wallpaper,
    prepare_assets,
    resolve_asset as resolve_project_asset,
    sequence_timing,
    should_launch_game,
    voice_engine,
    voice_model_path,
)
from core.wallpaper import WallpaperController
from core.voice import VoiceListener, check_voice_availability
from ui.deployment_window import DeploymentWindow

PROJECT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = PROJECT_DIR / "config.toml"


def load_config():
    """Carga la configuración de la aplicación."""
    return load_config_file(CONFIG_FILE)


def resolve_asset(assets: dict, key: str) -> Path | None:
    """Resuelve una ruta de recurso relativa al proyecto."""
    return resolve_project_asset(assets, key, PROJECT_DIR)


def main() -> int:
    start_hidden = "--hidden" in sys.argv
    qt_args = [arg for arg in sys.argv if arg != "--hidden"]

    app = QApplication(qt_args)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("Modo Democracia")
    app.setOrganizationName("Super Earth")

    try:
        config = load_config()
        assets = config.get("assets", {})
        sequence = config.get("sequence", {})
        voice_config = config.get("voice", {})
        general_config = config.get("general", {})
        steam_config = config.get("steam", {})

        selection = prepare_assets(assets, PROJECT_DIR)
        for warning in selection.warnings:
            print(warning, file=sys.stderr)

        wallpaper = selection.wallpaper
        logo = selection.logo
        audio = selection.audio
        app_icon = selection.app_icon
        ministry_icon = selection.ministry_icon

        wallpaper_plan = plan_wallpaper(
            sequence,
            WallpaperController.support_status(),
            wallpaper,
        )
        restore_wallpaper = wallpaper_plan.restore_on_exit
        wallpaper_enabled = wallpaper_plan.enabled

        if wallpaper_plan.warning:
            print(wallpaper_plan.warning, file=sys.stderr)

        wallpaper_controller = WallpaperController(
            wallpaper,
            enabled=wallpaper_enabled,
            restore_on_exit=restore_wallpaper,
        )

        # Solo intentar recuperar el fondo de una ejecución anterior
        # cuando la función esté habilitada y el entorno sea compatible.
        if wallpaper_enabled:
            recovered, recovery_error = (
                WallpaperController.recover_stale_state()
            )
            if not recovered:
                print(
                    "Advertencia: recuperación del fondo pendiente: "
                    f"{recovery_error}",
                    file=sys.stderr,
                )

        # Helldivers 2 solo se abre si ambos interruptores están activados.
        launch_game = should_launch_game(sequence, steam_config)
        timing = sequence_timing(sequence)

        window = DeploymentWindow(
            wallpaper_path=wallpaper,
            logo_path=logo,
            audio_path=audio,
            duration_seconds=timing.duration_seconds,
            app_icon_path=app_icon,
            ministry_icon_path=ministry_icon,
            wallpaper_controller=wallpaper_controller,
            launch_game=launch_game,
            steam_app_id=str(
                steam_config.get("app_id", "553850")
            ),
            launch_delay_seconds=timing.launch_delay_seconds,
            battle_delay_seconds=timing.battle_text_delay_seconds,
        )

        # Icono persistente de la bandeja.
        # Se conserva una referencia durante app.exec().
        tray_icon_path = (
            app_icon if app_icon and app_icon.is_file() else logo
        )
        tray_icon = QSystemTrayIcon(
            QIcon(str(tray_icon_path)) if tray_icon_path else QIcon(),
            app,
        )
        tray_icon.setToolTip(
            "Modo Democracia · preparando reconocimiento de voz"
        )

        tray_menu = QMenu()

        status_action = QAction(
            "Reconocimiento de voz: iniciando…",
            tray_menu,
        )
        status_action.setEnabled(False)
        tray_menu.addAction(status_action)
        tray_menu.addSeparator()

        show_action = QAction(
            "Mostrar Modo Democracia",
            tray_menu,
        )
        show_action.triggered.connect(window.show_from_tray)
        tray_menu.addAction(show_action)

        exit_action = QAction(
            "Salir de Modo Democracia",
            tray_menu,
        )
        exit_action.triggered.connect(window.exit_application)
        tray_menu.addAction(exit_action)

        tray_icon.setContextMenu(tray_menu)
        tray_icon.activated.connect(
            lambda reason: window.show_from_tray()
            if reason in (
                QSystemTrayIcon.ActivationReason.Trigger,
                QSystemTrayIcon.ActivationReason.DoubleClick,
            )
            else None
        )

        tray_available = QSystemTrayIcon.isSystemTrayAvailable()

        if tray_available:
            tray_icon.show()
        else:
            print(
                "Advertencia: KDE no informa una bandeja del sistema disponible.",
                file=sys.stderr,
            )

        voice_listener = None

        if voice_config.get("enabled", False):
            voice_ready = False
            engine = voice_engine(voice_config)
            phrase = activation_phrase(general_config)

            if engine != "vosk":
                voice_problem = (
                    "Motor de voz no compatible; se esperaba 'vosk'."
                )
            else:
                model_path = voice_model_path(
                    voice_config, PROJECT_DIR
                )

                try:
                    voice_ready, voice_problem = check_voice_availability(
                        phrase,
                        model_path,
                    )
                except Exception as exc:
                    # Una configuración inesperada no debe impedir el inicio.
                    voice_ready = False
                    voice_problem = (
                        "No se pudo comprobar el reconocimiento de voz: "
                        f"{type(exc).__name__}: {exc}"
                    )

            if not voice_ready:
                # La voz es opcional: se informa y la aplicación continúa
                # con la interfaz, el audio, el fondo y el lanzamiento.
                voice_problem = voice_problem or "Voz no disponible."
                print(
                    "Advertencia: reconocimiento de voz desactivado. "
                    f"{voice_problem}",
                    file=sys.stderr,
                )
                window.on_voice_disabled(voice_problem)
                status_action.setText(
                    "Reconocimiento de voz: desactivado"
                )
                tray_icon.setToolTip(
                    "Modo Democracia · reconocimiento de voz desactivado"
                )
            else:
                voice_listener = VoiceListener(
                    phrase=phrase,
                    model_path=model_path,
                    parent=window,
                )

                voice_listener.activation_detected.connect(
                    window.activate_from_voice
                )
                voice_listener.status_changed.connect(
                    window.on_voice_status
                )
                voice_listener.status_changed.connect(
                    lambda message: status_action.setText(
                        message.replace("…", "...")
                    )
                )
                voice_listener.status_changed.connect(
                    lambda message: tray_icon.setToolTip(
                        f"Modo Democracia · {message}"
                    )
                )
                voice_listener.error_occurred.connect(
                    window.on_voice_error
                )
                voice_listener.error_occurred.connect(
                    lambda message: status_action.setText(
                        "Reconocimiento de voz: error"
                    )
                )
                voice_listener.error_occurred.connect(
                    lambda message: tray_icon.setToolTip(
                        "Modo Democracia · "
                        "reconocimiento de voz no disponible"
                    )
                )

                window.voice_listener = voice_listener
        else:
            window.on_voice_disabled(
                "El reconocimiento de voz está desactivado en config.toml."
            )
            status_action.setText("Reconocimiento de voz: desactivado")
            tray_icon.setToolTip(
                "Modo Democracia · reconocimiento de voz desactivado"
            )

        def stop_voice_listener() -> None:
            """Detiene la escucha una sola vez y libera el micrófono."""
            if voice_listener is None:
                return
            if not voice_listener.stop():
                print(
                    "Advertencia: el hilo de voz no terminó a tiempo.",
                    file=sys.stderr,
                )

        # Cualquier salida de la aplicación (menú, cierre del sistema o
        # QApplication.quit) debe detener la escucha.
        app.aboutToQuit.connect(stop_voice_listener)

        if not tray_available:
            # Sin bandeja no debe quedar una aplicación invisible.
            window.show()
        elif not start_hidden:
            window.show()
            window.raise_()
            window.activateWindow()

        if voice_listener is not None:
            voice_listener.start()

        print("Modo Democracia se ha iniciado correctamente.")
        return app.exec()

    except Exception as exc:
        traceback.print_exc()
        QMessageBox.critical(
            None,
            "Error al iniciar Modo Democracia",
            "No se pudo iniciar la aplicación.\n\n"
            f"{type(exc).__name__}: {exc}\n\n"
            "Consulta la terminal para ver el detalle del error.",
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
