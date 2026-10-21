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

from platforms import get_autostart_manager

PROJECT_DIR = Path(__file__).resolve().parents[1]


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
        description=(
            "Instala, retira o consulta el inicio automático de "
            "Modo Democracia."
        )
    )
    parser.add_argument(
        "action",
        choices=("install", "uninstall", "status"),
        help="Acción que se desea realizar.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    python_executable = default_python_executable(PROJECT_DIR)
    manager = get_autostart_manager(PROJECT_DIR, python_executable)

    if not manager.is_supported():
        print(
            "El inicio automático no está disponible en esta plataforma: "
            f"{manager.unsupported_reason()}",
            file=sys.stderr,
        )
        return 1

    if args.action == "status":
        installed = manager.is_installed()
        print(f"Gestor: {manager.name}")
        print(f"Estado: {'instalado' if installed else 'no instalado'}")
        print(f"Ubicación: {manager.location()}")
        print(f"Intérprete: {python_executable}")
        return 0

    if args.action == "install":
        ok, error = manager.install()
        if not ok:
            print(
                f"No se pudo instalar el inicio automático: {error}",
                file=sys.stderr,
            )
            return 1

        print(f"Inicio automático instalado ({manager.name}).")
        print(f"Ubicación: {manager.location()}")
        print(f"Intérprete: {python_executable}")
        print(
            "La aplicación se iniciará oculta en la bandeja al iniciar "
            "sesión."
        )
        if manager.last_note:
            print(manager.last_note)
        return 0

    ok, error = manager.uninstall()
    if not ok:
        print(
            f"No se pudo retirar el inicio automático: {error}",
            file=sys.stderr,
        )
        return 1

    print(f"Inicio automático retirado ({manager.name}).")
    if manager.last_note:
        print(manager.last_note)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
