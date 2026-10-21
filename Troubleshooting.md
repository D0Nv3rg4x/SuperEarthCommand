# Troubleshooting y guía detallada

Esta guía recoge la instalación por sistema, la configuración completa y la
resolución de problemas que no caben en el README. El README queda como
presentación operativa del proyecto.

## Requisitos detallados

### Comunes

- Python **3.11 o superior**. El proyecto se ha probado con Python 3.14.8.
- `pip` y el módulo `venv`.
- PySide6. El entorno de referencia usa PySide6 6.12.0; `requirements.txt` no
  fija una versión concreta.
- Los recursos incluidos en `Assets/`. El logo es obligatorio; el audio, el
  fondo y los iconos son opcionales.

### Linux / KDE Plasma 6

Para el cambio de fondo:

- KDE Plasma 6.
- `plasma-apply-wallpaperimage`, normalmente incluido con Plasma Workspace.
- No se asume compatibilidad con GNOME, XFCE ni otros escritorios.

El inicio automático de Linux usa XDG autostart y no necesita systemd.

### Voz opcional

- `vosk` y `sounddevice`, incluidos en `requirements-voice.txt`.
- PortAudio disponible para `sounddevice`. En CachyOS se instala con el gestor
  de paquetes del sistema si aún no está presente.
- Modelo local `vosk-model-small-es-0.42` en `models/`.
- Micrófono de entrada configurado en el sistema.

Vosk puede no tener una distribución compatible con todas las versiones de
Python. Si `pip` no encuentra una versión válida, crea un entorno virtual con un
Python compatible y ejecuta el proyecto desde ese entorno; no es necesario
cambiar el Python del sistema.

### Steam opcional

- Steam instalado y disponible como `steam`, o un manejador del esquema
  `steam://` registrado en el sistema.
- Helldivers 2 instalado en la cuenta de Steam. El identificador configurado
  por defecto es `553850`.

### Windows y macOS

El código de fondo y de inicio automático existe para ambas plataformas, pero
no se ha probado en hardware real. No actives esas funciones como si estuvieran
validadas.

## Instalación detallada

1. Copia o clona el proyecto en una carpeta estable. Evita moverlo después de
   instalar el inicio automático, porque las rutas se guardan de forma absoluta.

2. Crea el entorno virtual desde la carpeta del proyecto.

   Bash/Zsh:

   ```sh
   cd ~/Documentos/SuperEarthCommand
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

   Fish (entorno de referencia en CachyOS):

   ```fish
   cd ~/Documentos/SuperEarthCommand
   python3 -m venv .venv
   source .venv/bin/activate.fish
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

   Windows PowerShell:

   ```powershell
   cd $HOME\Documentos\SuperEarthCommand
   py -3 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   ```

   macOS:

   ```sh
   cd ~/Documentos/SuperEarthCommand
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install -r requirements.txt
   ```

3. Instala la voz solo si la quieres usar:

   ```sh
   python -m pip install -r requirements-voice.txt
   ```

4. Descarga el modelo de voz. En Linux, el script incluido comprueba si ya
   existe y usa `curl` y `unzip`:

   ```sh
   bash scripts/instalar_modelo_voz.sh
   ```

   En Windows o macOS, descarga el ZIP del modelo desde el enlace indicado en
   `scripts/instalar_modelo_voz.sh` y extrae la carpeta
   `vosk-model-small-es-0.42` dentro de `models/`.

5. Comprueba que la instalación funciona:

   ```sh
   python -u app.py
   ```

Si no quieres usar voz, pon `enabled = false` en `[voice]`. La aplicación
arranca y la bandeja funciona, pero la secuencia no se inicia porque
actualmente no hay un botón alternativo de inicio.

## Configuración completa

La configuración se lee de `config.toml`, en la carpeta del proyecto. Las rutas
de recursos pueden ser relativas al proyecto, absolutas o comenzar por `~`.

### `[general]`

| Clave | Valor actual | Efecto |
|---|---|---|
| `activation_phrase` | `"modo democracia"` | Frase que activa la secuencia. Se normaliza (mayúsculas, tildes y signos no importan). Si está vacía, la voz se desactiva. |

### `[assets]`

| Clave | Valor actual | Efecto |
|---|---|---|
| `wallpaper` | `Assets/flagSuperEarth_upscalemedia-transformed (1).png` | Imagen que se aplica al iniciar la secuencia. Si falta, se avisa y se continúa sin cambiar el fondo. |
| `logo` | `Assets/Super_Earth_Logo.webp` | **Obligatorio.** Se usa en la interfaz y como alternativa para la bandeja. Si falta, la aplicación no inicia. |
| `app_icon` | `Assets/Helldivers_2_(Icon).svg` | Icono de ventana y bandeja. Si falta, se usa el logo. |
| `ministry_icon` | `Assets/Ministry_of_Defense_Icon.png` | Sello decorativo del pie. Si falta, simplemente no se muestra. |
| `audio` | `Assets/Helldivers 2 Main Theme - A Cup Of Liber-Tea.mp3` | Música local. Si falta, la secuencia continúa sin audio. |

### `[sequence]`

| Clave | Valor actual | Efecto |
|---|---|---|
| `duration_seconds` | `13.2` | Duración de la barra principal. La interfaz aplica un mínimo de 1 segundo. Un valor no numérico usa `13.2`. |
| `launch_delay_seconds` | `2.0` | Espera después de mostrar «DESPERTANDO DE CRIOSUEÑO» antes de intentar abrir Steam. |
| `battle_text_delay_seconds` | `300` | Tiempo tras el despertar para cambiar el texto a «EN BATALLA». Solo se programa si el lanzamiento está activado. |
| `launch_game_after_sequence` | `true` | Primer interruptor del lanzamiento. Debe ser `true` junto con `steam.launch_enabled`. |
| `wallpaper_enabled` | `true` | Permite cambiar el fondo. También requiere un entorno compatible y una imagen válida. |
| `restore_wallpaper_on_exit` | `true` | Restaura el fondo original al cancelar o salir. Si es `false`, deja el fondo aplicado y elimina el estado pendiente para no restaurarlo en un inicio posterior. |

### `[voice]`

| Clave | Valor actual | Efecto |
|---|---|---|
| `enabled` | `true` | Activa la escucha. Si es `false`, no se abre el micrófono y la interfaz sigue funcionando. |
| `recognition_engine` | `"vosk"` | Solo se admite `vosk`; cualquier otro valor desactiva la voz con un aviso. |
| `model_path` | `models/vosk-model-small-es-0.42` | Ruta del modelo, relativa al proyecto o absoluta. Si está vacía, se usa la ruta predeterminada. |

### `[steam]`

| Clave | Valor actual | Efecto |
|---|---|---|
| `app_id` | `"553850"` | Identificador usado en `steam://rungameid/<app_id>`. |
| `launch_enabled` | `true` | Segundo interruptor del lanzamiento. Debe ser `true` junto con `launch_game_after_sequence`. |

### Combinaciones útiles

Desactivar solo la voz:

```toml
[voice]
enabled = false
```

Desactivar solo el cambio de fondo:

```toml
[sequence]
wallpaper_enabled = false
```

Mantener el fondo aplicado al salir:

```toml
[sequence]
restore_wallpaper_on_exit = false
```

No abrir Steam:

```toml
[sequence]
launch_game_after_sequence = false
```

La aplicación no instala dependencias, no descarga el modelo y no modifica el
escritorio ni el inicio automático sin una orden explícita.

## Inicio automático

La instalación es opcional y no se activa sola. Usa `--hidden`, así que la
aplicación comienza en la bandeja. Consulta
[`docs/AUTOSTART.md`](docs/AUTOSTART.md) para los comandos de Linux, Windows y
macOS, las rutas que crea y cómo retirarlo.

En Linux, con el entorno virtual activado:

```sh
python -m core.autostart install
python -m core.autostart status
```

Para retirarlo:

```sh
python -m core.autostart uninstall
```

## Resolución de problemas

### La aplicación no arranca

- Comprueba la versión de Python: debe ser 3.11 o superior.
- Usa el intérprete del entorno virtual (`python` tras activar `.venv`, o
  `.venv/bin/python`), no el Python del sistema.
- Comprueba que PySide6 está instalado con
  `python -m pip show PySide6`.
- Si falta el logo, revisa la ruta en `[assets]`. El logo es el único recurso
  obligatorio.
- Ejecuta desde una terminal para ver el mensaje completo de error. La
  aplicación muestra un cuadro de diálogo y también escribe el detalle en
  `stderr`.

### La voz no se activa

- Comprueba las dependencias:

  ```sh
  python -c "import vosk, sounddevice; print('dependencias OK')"
  ```

- Verifica que existe el modelo y que contiene, al menos,
  `am/final.mdl`, `conf/mfcc.conf`, `graph/HCLr.fst` y `graph/Gr.fst`.
- Comprueba que el micrófono predeterminado aparece en el sistema y que Qt/KDE
  puede capturarlo.
- Si Vosk no se instala con la versión actual de Python, usa un entorno virtual
  con otra versión compatible. No cambies el Python del sistema solo para este
  proyecto.
- La aplicación escribe en la terminal el motivo exacto por el que desactiva la
  voz.

### El fondo no cambia

- En Linux solo está implementado KDE Plasma 6. Comprueba:

  ```sh
  echo "$XDG_CURRENT_DESKTOP $KDE_SESSION_VERSION"
  command -v plasma-apply-wallpaperimage
  ```

- Si no aparece el comando, instala Plasma Workspace con el gestor de paquetes
  de tu distribución.
- Si el adaptador no está disponible, la aplicación avisa y continúa; puedes
  desactivar la función con `wallpaper_enabled = false`.

### No se oye la música

- Comprueba que el archivo indicado en `[assets].audio` existe.
- Revisa la salida de audio del sistema y el volumen de Qt/KDE.
- Si falta el audio, la secuencia sigue funcionando y muestra un aviso.

### Steam no se abre

- Comprueba que `steam` está en el `PATH` o que el sistema tiene registrado el
  esquema `steam://`.
- Verifica que `app_id = "553850"` corresponde a Helldivers 2 en tu cuenta.
- Recuerda que deben ser `true` tanto `launch_game_after_sequence` como
  `launch_enabled`.

### El inicio automático no funciona

- Ejecuta `python -m core.autostart status`.
- En Linux, comprueba que existe la entrada en `~/.config/autostart/` o en la
  ruta de `XDG_CONFIG_HOME`.
- Si hay un archivo ajeno en `~/.local/bin/modo-democracia` o en la entrada
  `.desktop`, muévelo o elimínalo antes de instalar.
- En Windows, revisa el valor `ModoDemocracia` en el registro.
- En macOS, revisa `launchctl print gui/$(id -u)` y el archivo plist.
- Si no se ha probado en tu plataforma, no lo actives como si estuviera
  validado.

## Comprobaciones manuales

Las pruebas automatizadas cubren configuración, recursos, voz simulada,
adaptadores de fondo, inicio automático y flujo de interfaz. Siguen pendientes
las comprobaciones con hardware real: frase con micrófono, reproducción de
audio, cambio y restauración del fondo visible, apertura de Steam, bandeja y
autostart tras cerrar sesión. Consulta [`docs/TESTING.md`](docs/TESTING.md).

## Archivos locales y privacidad

- `.venv/`: entorno virtual local. Contiene rutas absolutas del equipo, está
  excluido por `.gitignore` y se regenera siguiendo la instalación.
- `models/`: modelo de Vosk de gran tamaño, también excluido por `.gitignore`.

El código, `config.toml` y la documentación no contienen credenciales ni rutas
personales. Si compartes el proyecto, excluye `.venv/` y `models/`.
