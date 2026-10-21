# Arquitectura de Modo Democracia

La aplicación separa el arranque y la interfaz de las funciones que dependen
del sistema operativo o de recursos opcionales. El objetivo es que la falta de
voz, audio, fondo o inicio automático no impida usar el resto.

## Módulos

| Ruta | Responsabilidad |
|---|---|
| `app.py` | Punto de entrada: lee la configuración, prepara recursos, crea la ventana y la bandeja, conecta la voz y controla la salida. |
| `core/config.py` | Funciones puras para cargar TOML, resolver recursos, decidir el fondo, resolver la voz, comprobar el lanzamiento y convertir duraciones. |
| `core/voice.py` | Comprobaciones previas de Vosk/modelo/micrófono y `VoiceListener`, un `QThread` que escucha y emite señales. |
| `core/wallpaper.py` | Controlador común: activa, restaura, recupera estado pendiente y guarda la imagen original. |
| `core/audio.py` | Reproducción local y desvanecimiento del volumen con Qt Multimedia. |
| `core/autostart.py` | CLI `install`, `status` y `uninstall`; elige el gestor de la plataforma. |
| `platforms/` | Adaptadores de fondo y de inicio automático por sistema operativo. |
| `ui/deployment_window.py` | Interfaz, barra de progreso, estratagemas, estados de voz y lanzamiento de Steam. |
| `tests/` | Pruebas automatizadas con `unittest`. |

## Flujo de arranque

1. `app.py` comprueba que Python es 3.11 o superior.
2. Carga `config.toml` y clasifica los recursos:
   - el logo es obligatorio;
   - fondo, audio e iconos son opcionales y generan advertencias si faltan.
3. Pregunta al adaptador de plataforma si el fondo es compatible.
4. Recupera un estado de fondo pendiente de una ejecución anterior, solo si el
   cambio de fondo está habilitado.
5. Crea `DeploymentWindow`, la bandeja y el menú.
6. Comprueba la voz si `[voice].enabled` es verdadero. Si no está disponible,
   muestra el motivo y continúa.
7. Muestra la ventana o la mantiene oculta con `--hidden`; si no hay bandeja,
   la muestra para evitar una aplicación invisible.
8. Inicia `VoiceListener` y entra en el bucle de Qt.

Cualquier salida de `QApplication` pasa por `app.aboutToQuit`, que detiene el
hilo de voz. La salida explícita desde la bandeja también detiene el audio,
restaura el fondo y cierra la ventana.

## Flujo de la secuencia

- La frase detectada o el botón de inicio llaman a `start_sequence()`.
- Se activa el fondo mediante `WallpaperController.activate()` y se reproduce
  el audio local.
- La barra principal avanza con un reloj monotónico y un `QTimer` de 16 ms.
- Las estratagemas se eligen al azar; un error solo reinicia la estratagema
  actual y no altera la barra principal.
- Al llegar al 100 %, la barra se desvanece, aparece
  «DESPERTANDO DE CRIOSUEÑO» y, si corresponde, se programa el lanzamiento de
  Steam y el cambio posterior a «EN BATALLA».
- Cancelar con Esc o con el botón detiene la secuencia, detiene el audio,
  restaura el fondo y oculta la ventana.
- Cerrar con la X solo oculta la ventana. La escucha continúa hasta que se elige
  «Salir de Modo Democracia» en la bandeja.

## Voz opcional

`check_voice_availability()` comprueba, en este orden:

1. que la frase no esté vacía;
2. que `vosk` y `sounddevice` puedan importarse;
3. que el modelo exista y contenga los archivos mínimos;
4. que haya un dispositivo de entrada predeterminado.

`VoiceListener` vuelve a comprobar el modelo y las dependencias dentro del hilo,
abre `RawInputStream` con un contexto que libera el dispositivo y usa una cola
limitada para no acumular audio. `stop()` desbloquea la cola, espera al hilo y
permite cerrar sin dejar el micrófono abierto.

La voz y la interfaz están desacopladas: un fallo de voz se comunica mediante
señales y no cierra la aplicación.

## Fondo y estado persistente

`platforms/__init__.py` selecciona el adaptador:

- Linux: `LinuxWallpaperBackend`, que solo delega en `KDEWallpaperBackend` si
  detecta KDE Plasma 6 y `plasma-apply-wallpaperimage`.
- Windows: `WindowsWallpaperBackend`, con `SystemParametersInfoW`.
- macOS: `MacOSWallpaperBackend`, con `osascript` y System Events.
- Otros: `UnsupportedWallpaperBackend`.

Antes de aplicar un fondo, el controlador guarda la ruta del fondo original en
un archivo de estado por plataforma. Si no puede identificar el fondo actual,
no lo modifica. Al restaurar, elimina el archivo de estado; si falla, conserva
el estado para intentarlo en una ejecución posterior.

Rutas de estado:

| Plataforma | Archivo |
|---|---|
| Linux | `$XDG_STATE_HOME/modo-democracia/wallpaper-state.json` o `~/.local/state/modo-democracia/wallpaper-state.json` |
| Windows | `%LOCALAPPDATA%\modo-democracia\wallpaper-state.json` |
| macOS | `~/Library/Application Support/modo-democracia/wallpaper-state.json` |

## Inicio automático

`core/autostart.py` elige un `AutostartManager` según la plataforma:

- Linux: entrada XDG y lanzador en `~/.local/bin/modo-democracia`.
- Windows: valor `ModoDemocracia` en la clave `Run` del usuario.
- macOS: LaunchAgent en `~/Library/LaunchAgents/`.

Los gestores comprueban que `app.py` y el intérprete existan, usan `--hidden` y
protegen archivos ajenos. La instalación no se ejecuta automáticamente al
arrancar la aplicación.

## Pruebas

La suite usa `unittest` y no necesita dependencias adicionales:

```sh
cd ~/Documentos/SuperEarthCommand
bash scripts/ejecutar_pruebas.sh
```

`tests/test_config.py` prueba las decisiones puras sin abrir la interfaz.
`tests/test_voice.py` simula dependencias y micrófono. `tests/test_platforms.py`
y `tests/test_autostart.py` usan adaptadores simulados o un HOME temporal.
`tests/test_ui_flow.py` usa `QT_QPA_PLATFORM=offscreen` para probar la secuencia
sin una sesión gráfica.

Las pruebas automatizadas no demuestran el funcionamiento del micrófono, el
audio, el escritorio ni Steam en hardware real. Esas comprobaciones están en
[`docs/TESTING.md`](TESTING.md).
