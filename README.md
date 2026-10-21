# Modo Democracia

Aplicación de escritorio inspirada en *Helldivers 2*. Escucha la frase
**«Modo Democracia»**, muestra una secuencia de despliegue con música y
estratagemas, puede cambiar temporalmente el fondo del escritorio y, si se
configura, abre Helldivers 2 mediante Steam.

La aplicación está pensada para ejecutarse sin instalar nada automáticamente:
todas las funciones opcionales se comprueban antes de usarse y, si falta algo,
la aplicación lo explica y continúa con el resto.

## Estado de verificación

| Plataforma / función | Estado |
|---|---|
| Linux + KDE Plasma 6 (CachyOS) | **Verificado** con Plasma 6 y `plasma-apply-wallpaperimage`. |
| Fondo en otros escritorios Linux | No implementado; la función se desactiva. |
| Reconocimiento de voz en Linux | Implementado y probado con dispositivos simulados; **la frase con micrófono real sigue pendiente de prueba manual**. |
| Inicio automático en Linux | Implementado; instalación, retirada y lanzador probados con un HOME temporal. **Falta comprobar el inicio real al cerrar y abrir sesión.** |
| Windows (fondo y autostart por registro) | Implementado, **no probado en un equipo Windows real**. |
| macOS (fondo y LaunchAgent) | Implementado, **no probado en un equipo macOS real**. |
| Secuencia, audio, bandeja y lanzamiento de Steam | Implementados; la interfaz se ha probado en modo offscreen y el arranque real en KDE. La reproducción de audio y la apertura de Steam requieren comprobación manual. |

No debe interpretarse que Windows o macOS están soportados y validados solo
porque su código exista o compile. Consulta [`docs/PLATFORMS.md`](docs/PLATFORMS.md)
y [`docs/TESTING.md`](docs/TESTING.md).

## Características

- Activación local por voz con Vosk; no se envía audio a servicios en la nube.
- Interfaz cinematográfica con barra de progreso, animaciones y minijuego de
  estratagemas.
- Música local con desvanecimiento al abrir el juego.
- Cambio opcional del fondo de pantalla y restauración controlada.
- Icono persistente en la bandeja del sistema.
- Inicio automático opcional, oculto en la bandeja.
- Lanzamiento opcional de Helldivers 2 mediante Steam.

## Requisitos

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

## Instalación desde cero

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

## Ejecución

Con el entorno virtual activado:

```sh
cd ~/Documentos/SuperEarthCommand
python -u app.py
```

Para iniciar directamente en la bandeja, sin mostrar la ventana:

```sh
python -u app.py --hidden
```

Al arrancar:

- si la voz está disponible, se muestra el estado de escucha en la interfaz y
  en la bandeja;
- si falta Vosk, el modelo o el micrófono, la aplicación continúa y explica el
  motivo;
- si la bandeja no está disponible, la ventana se muestra para que la
  aplicación no quede invisible.

## Uso

1. Di **«Modo Democracia»**. La interfaz no tiene un botón de inicio separado:
   si la voz no está disponible, la aplicación y la bandeja siguen
   funcionando, pero la secuencia no se activa hasta que la voz vuelva a estar
   disponible.
2. La aplicación cambia el fondo si está permitido, reproduce la música e
   inicia la barra de progreso.
3. Durante la secuencia aparecen estratagemas: pulsa las flechas indicadas. Un
   error reinicia la estratagema actual, pero no detiene la barra principal.
4. Al completar la barra aparece «DESPERTANDO DE CRIOSUEÑO». Si el lanzamiento
   está activado, Steam se abre después de `launch_delay_seconds` y la música
   se desvanece.
5. El fondo de Super Tierra permanece al completar la secuencia y se restaura
   al cancelar o salir, según `restore_wallpaper_on_exit`.

Controles:

- **Esc** o **CANCELAR DESPLIEGUE**: detiene la secuencia, restaura el fondo y
  oculta la ventana.
- **X**: oculta la ventana; la escucha por voz sigue activa.
- **Icono de la bandeja**: muestra la ventana o permite salir completamente.
- **Salir de Modo Democracia**: detiene la voz, detiene el audio, restaura el
  fondo y cierra la aplicación.

## Configuración

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

La instalación es opcional y no se activa sola. El inicio automático usa
`--hidden`, por lo que la aplicación comienza en la bandeja. Consulta
[`docs/AUTOSTART.md`](docs/AUTOSTART.md) para los detalles y la resolución de
problemas.

### Linux (probado con HOME temporal)

Con el entorno virtual activado:

```sh
cd ~/Documentos/SuperEarthCommand
source .venv/bin/activate.fish
python -m core.autostart install
python -m core.autostart status
```

También se puede usar:

```sh
bash scripts/instalar_inicio_automatico.sh
```

Crea:

- `$XDG_CONFIG_HOME/autostart/modo-democracia.desktop`, o
  `~/.config/autostart/modo-democracia.desktop`.
- `~/.local/bin/modo-democracia`, con el intérprete del `.venv`.

Para comprobarlo, cierra sesión, vuelve a entrar en KDE Plasma y busca el icono
en la bandeja. Para retirarlo:

```sh
python -m core.autostart uninstall
```

o:

```sh
bash scripts/quitar_inicio_automatico.sh
```

La retirada solo elimina los archivos creados por la aplicación. Si encuentra
un archivo ajeno en esas rutas, no lo sobrescribe ni lo borra.

### Windows (implementado, no verificado)

Con el entorno virtual activado en PowerShell:

```powershell
.\.venv\Scripts\python.exe -m core.autostart install
.\.venv\Scripts\python.exe -m core.autostart status
```

Crea el valor `ModoDemocracia` en:

```text
HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run
```

El comando apunta a `pythonw.exe`, a `app.py` y a `--hidden`. Para retirarlo:

```powershell
.\.venv\Scripts\python.exe -m core.autostart uninstall
```

No se ha probado en un equipo Windows real.

### macOS (implementado, no verificado)

Con el entorno virtual activado:

```sh
python -m core.autostart install
python -m core.autostart status
```

Crea y carga un LaunchAgent en:

```text
~/Library/LaunchAgents/com.superearth.mododemocracia.plist
```

macOS puede solicitar permiso de automatización o acceso a archivos. Para
retirarlo:

```sh
python -m core.autostart uninstall
```

No se ha probado en un equipo macOS real.

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
- En Linux, comprueba que existe la entrada en
  `~/.config/autostart/` o en la ruta de `XDG_CONFIG_HOME`.
- Si hay un archivo ajeno en `~/.local/bin/modo-democracia` o en la entrada
  `.desktop`, muévelo o elimínalo antes de instalar.
- En Windows, revisa el valor `ModoDemocracia` en el registro.
- En macOS, revisa `launchctl print gui/$(id -u)` y el archivo plist.
- Si no se ha probado en tu plataforma, no lo actives como si estuviera
  validado.

## Pruebas

La batería automatizada actual tiene **97 pruebas**:

```sh
cd ~/Documentos/SuperEarthCommand
bash scripts/ejecutar_pruebas.sh
```

Equivale a ejecutar `unittest` con el Python del `.venv` y
`QT_QPA_PLATFORM=offscreen`. Las pruebas cubren configuración, recursos, voz
opcional, adaptadores de fondo, inicio automático y flujo de interfaz.

Las comprobaciones que necesitan hardware real están separadas en
[`docs/TESTING.md`](docs/TESTING.md). En particular, siguen pendientes:

- la frase con micrófono real;
- la reproducción de audio real;
- el cambio y la restauración del fondo en un escritorio visible;
- la apertura de Helldivers 2 mediante Steam;
- el inicio automático tras cerrar y volver a iniciar sesión;
- las pruebas en Windows y macOS reales.

## Estructura del proyecto

```text
app.py                  Arranque, bandeja y conexión de módulos
config.toml             Configuración de la aplicación
core/
  config.py             Carga y decisiones puras de configuración
  voice.py              Voz opcional con Vosk y ciclo de vida del micrófono
  wallpaper.py          Estado, activación y restauración del fondo
  audio.py              Reproducción y desvanecimiento de la música
  autostart.py          Órdenes install/status/uninstall
platforms/
  base.py               Interfaces comunes
  linux.py              XDG autostart y selección de escritorio Linux
  kde.py                Fondo en KDE Plasma 6
  windows.py            Fondo y registro de Windows
  macos.py              Fondo y LaunchAgent de macOS
ui/
  deployment_window.py  Interfaz, secuencia y minijuego
tests/                  Pruebas automatizadas con unittest
scripts/                Instalación del modelo, autostart y pruebas
docs/                   Arquitectura, plataformas, autostart y pruebas
Assets/                 Imágenes, iconos y audio
models/                 Modelo de Vosk (descarga opcional; no se instala solo)
```

La lógica efectiva de la secuencia está en `ui/deployment_window.py` y el
lanzamiento de Steam se realiza desde esa ventana.

### Archivos locales que no deben compartirse

- `.venv/`: entorno virtual local. Contiene rutas absolutas del equipo y está
  excluido por `.gitignore`; se regenera siguiendo las instrucciones de
  instalación.
- `models/`: modelo de Vosk de gran tamaño. Es una descarga opcional y también
  está excluido por `.gitignore`.

El código, `config.toml` y la documentación no contienen credenciales ni rutas
personales. Si compartes el proyecto, excluye `.venv/` y `models/`.

## Documentación

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md): módulos y flujo de arranque.
- [`docs/PLATFORMS.md`](docs/PLATFORMS.md): compatibilidad y limitaciones.
- [`docs/AUTOSTART.md`](docs/AUTOSTART.md): inicio automático por plataforma.
- [`docs/TESTING.md`](docs/TESTING.md): pruebas, resultados y comprobaciones
  manuales.
- [`Plan_Desarrollo_Modo_Democracia.md`](Plan_Desarrollo_Modo_Democracia.md):
  plan de desarrollo y estado de las fases.
