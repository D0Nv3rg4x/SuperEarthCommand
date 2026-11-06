"""Gestión del inicio automático por línea de comandos.

Uso:
    python -m core.autostart install
    python -m core.autostart uninstall
    python -m core.autostart status

No importa PySide6: puede ejecutarse con el Python del entorno virtual sin
abrir la interfaz.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from core import i18n
from core.config import load_config
from platforms import get_autostart_manager

PROJECT_DIR = Path(__file__).resolve().parents[1]
CONFIG_FILE = PROJECT_DIR / "config.toml"


def configure_language(project_dir: Path = PROJECT_DIR) -> str:
    """Aplica el idioma de `config.toml` a la salida de la herramienta."""
    try:
        general = load_config(project_dir / "config.toml").get(
            "general", {}
        )
    except (OSError, ValueError):
        general = {}

    return i18n.set_language(general.get("language"))


def default_python_executable(project_dir: Path) -> Path:
    """Prefiere el intérprete del entorno virtual del proyecto."""
    if sys.platform.startswith("win"):
        candidates = (
            project_dir / ".venv" / "Scripts" / "pythonw.exe",
            project_dir / ".venv" / "Scripts" / "python.exe",
        )
    else:
        candidates = (project_dir / ".venv" / "bin" / "python",)

    for candidate in candidates:
        if candidate.is_file():
            # No resolver enlaces simbólicos: .venv/bin/python suele apuntar
            # al Python del sistema y resolverlo perdería el entorno virtual.
            return candidate.absolute()

    return Path(sys.executable).absolute()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=i18n.t("autostart.cli.description")
    )
    parser.add_argument(
        "action",
        choices=("install", "uninstall", "status"),
        help=i18n.t("autostart.cli.action_help"),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    configure_language()
    args = build_parser().parse_args(argv)

    python_executable = default_python_executable(PROJECT_DIR)
    manager = get_autostart_manager(PROJECT_DIR, python_executable)

    if not manager.is_supported():
        print(
            i18n.t(
                "autostart.cli.unsupported",
                reason=manager.unsupported_reason(),
            ),
            file=sys.stderr,
        )
        return 1

    if args.action == "status":
        installed = manager.is_installed()
        state = i18n.t(
            "autostart.cli.state.installed"
            if installed
            else "autostart.cli.state.not_installed"
        )
        print(i18n.t("autostart.cli.manager", name=manager.name))
        print(i18n.t("autostart.cli.state", state=state))
        print(i18n.t("autostart.cli.location", path=manager.location()))
        print(
            i18n.t(
                "autostart.cli.interpreter", path=python_executable
            )
        )
        return 0

    if args.action == "install":
        ok, error = manager.install()
        if not ok:
            print(
                i18n.t(
                    "autostart.cli.install_failed", error=error
                ),
                file=sys.stderr,
            )
            return 1

        print(i18n.t("autostart.cli.installed", name=manager.name))
        print(i18n.t("autostart.cli.location", path=manager.location()))
        print(
            i18n.t(
                "autostart.cli.interpreter", path=python_executable
            )
        )
        print(i18n.t("autostart.cli.hidden"))
        if manager.last_note:
            print(manager.last_note)
        return 0

    ok, error = manager.uninstall()
    if not ok:
        print(
            i18n.t(
                "autostart.cli.uninstall_failed", error=error
            ),
            file=sys.stderr,
        )
        return 1

    print(i18n.t("autostart.cli.uninstalled", name=manager.name))
    if manager.last_note:
        print(manager.last_note)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
