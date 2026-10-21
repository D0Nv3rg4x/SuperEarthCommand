# Plataformas y compatibilidad

La lógica común está en `core/wallpaper.py`. Cada sistema operativo implementa
la interfaz de `platforms/base.py`; `platforms/__init__.py` selecciona el
adaptador y comprueba sus capacidades reales antes de usarlo.

## Estado de los adaptadores

| Plataforma | Implementación | Verificación real | Limitaciones conocidas |
|---|---|---|---|
| Linux + KDE Plasma 6 | `platforms/kde.py` | Sí, en CachyOS con KDE Plasma 6 y `plasma-apply-wallpaperimage` | Solo KDE Plasma 6. No se asume compatibilidad con GNOME ni otros escritorios. |
| Linux + otros escritorios | Sin adaptador | No aplica | El cambio de fondo se desactiva y se informa del escritorio detectado. |
| Windows | `platforms/windows.py` | **No verificada en un equipo Windows** | Usa `SystemParametersInfoW`. No se ha probado con varios monitores ni con fondos de presentación. |
| macOS | `platforms/macos.py` | **No verificada en un equipo macOS** | Usa `osascript` y System Events. Requiere permiso de automatización. La lectura del fondo actual usa el primer escritorio. |
| Otros sistemas | `UnsupportedWallpaperBackend` | No aplica | La aplicación continúa sin cambiar el fondo. |

## Comportamiento común

- `wallpaper_enabled = false` desactiva cualquier cambio de fondo.
- `restore_wallpaper_on_exit = false` conserva el fondo aplicado y descarta el
  estado pendiente para no restaurarlo en un inicio posterior.
- Si no se puede identificar el fondo actual, no se modifica el escritorio.
- Si falla la aplicación del nuevo fondo, se intenta restaurar el anterior.
- Los errores se informan y no bloquean el audio, la voz ni el lanzamiento del
  juego.

## Ubicación del estado

| Plataforma | Archivo |
|---|---|
| Linux | `$XDG_STATE_HOME/modo-democracia/wallpaper-state.json` o `~/.local/state/modo-democracia/wallpaper-state.json` |
| Windows | `%LOCALAPPDATA%\modo-democracia\wallpaper-state.json` |
| macOS | `~/Library/Application Support/modo-democracia/wallpaper-state.json` |

El archivo solo contiene la ruta del fondo original que debe restaurarse si la
aplicación no pudo hacerlo durante su ejecución normal.

## Pruebas

```sh
cd ~/Documentos/SuperEarthCommand
source .venv/bin/activate.fish
python -m unittest discover -s tests -v
```

`tests/test_platforms.py` comprueba la selección de adaptadores, la detección de
KDE Plasma 6, el rechazo de escritorios no implementados, la lectura del fondo
en Plasma y el controlador común con un adaptador simulado. No sustituye las
pruebas manuales en Windows o macOS.
