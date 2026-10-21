# Inicio automático

Modo Democracia puede iniciarse oculto en la bandeja al iniciar sesión. La
instalación y la retirada son operaciones separadas y solo afectan a los
archivos o entradas creados por la aplicación.

## Órdenes comunes

Con el entorno virtual activado:

```sh
cd ~/Documentos/SuperEarthCommand
source .venv/bin/activate.fish
python -m core.autostart install
python -m core.autostart status
python -m core.autostart uninstall
```

También se conservan los envoltorios de Linux:

```sh
bash scripts/instalar_inicio_automatico.sh
bash scripts/quitar_inicio_automatico.sh
```

El inicio automático usa la opción `--hidden`, de modo que la ventana comience
en la bandeja del sistema. El intérprete y las rutas se guardan de forma
absoluta; no dependen del directorio desde el que se ejecutó el instalador.

## Linux (XDG autostart)

Archivos creados:

- `$XDG_CONFIG_HOME/autostart/modo-democracia.desktop`, o
  `~/.config/autostart/modo-democracia.desktop`.
- `~/.local/bin/modo-democracia`, un lanzador con el intérprete del `.venv`.

La entrada `.desktop` apunta al lanzador, define `Path` al proyecto y no abre
una terminal. La retirada elimina únicamente esos dos archivos si fueron
creados por la aplicación. Si `~/.local/bin/modo-democracia` ya existía y no
tiene la firma de Modo Democracia, la instalación se niega a sobrescribirlo y
la retirada lo conserva.

**Estado:** instalación, retirada y ejecución del lanzador probadas en CachyOS
con KDE Plasma 6 usando un HOME temporal. Falta comprobar el arranque real al
cerrar y volver a iniciar sesión.

## Windows

Se usa la clave del usuario:

```text
HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run
Valor: ModoDemocracia
```

El comando apunta a `pythonw.exe` del entorno virtual, a `app.py` y a
`--hidden`; las rutas se escriben entre comillas para admitir espacios. No se
crea ningún archivo en la carpeta de inicio ni se abre una consola.

La retirada elimina únicamente ese valor del registro. Para comprobarlo, inicia
sesión de nuevo y consulta el estado; para retirarlo:

```powershell
.\.venv\Scripts\python.exe -m core.autostart uninstall
```

**Estado:** implementado y revisado, pero **no probado en un equipo Windows
real**.

## macOS

Se crea un LaunchAgent:

```text
~/Library/LaunchAgents/com.superearth.mododemocracia.plist
```

La instalación escribe el archivo y lo carga con `launchctl bootstrap`; si esa
orden no está disponible, intenta el mecanismo antiguo `launchctl load -w`.
Como el agente tiene `RunAtLoad`, `launchctl` puede iniciar la aplicación
inmediatamente al instalar, además de hacerlo en cada inicio de sesión.

La retirada descarga el agente y elimina el archivo. Si macOS solicita permiso
de automatización o acceso a la carpeta, debe concederse para que la aplicación
pueda arrancar y usar sus funciones.

```sh
python -m core.autostart install
python -m core.autostart uninstall
```

**Estado:** implementado y revisado, pero **no probado en un equipo macOS
real**.

## Comprobar que funciona

1. Ejecuta `python -m core.autostart status`.
2. Cierra sesión y vuelve a entrar.
3. Comprueba que aparece el icono de Modo Democracia en la bandeja.
4. Abre el menú del icono y elige «Mostrar Modo Democracia».

## Resolución de problemas

- **No encuentra el Python del entorno virtual:** crea `.venv` e instala las
  dependencias antes de configurar el inicio automático.
- **Archivo ajeno en `~/.local/bin/modo-democracia`:** muévelo o elimínalo y
  vuelve a instalar.
- **El escritorio Linux no respeta XDG autostart:** comprueba que la sesión es
  KDE Plasma y que el archivo `.desktop` está en la ruta indicada por
  `XDG_CONFIG_HOME`.
- **Windows no inicia la aplicación:** revisa el valor `ModoDemocracia` en el
  registro y que `pythonw.exe` exista dentro de `.venv\Scripts`.
- **macOS no carga el agente:** ejecuta `launchctl print gui/$(id -u)` y revisa
  `~/Library/LaunchAgents/com.superearth.mododemocracia.plist`.
- **El inicio automático no debe confundirse con la activación por voz ni con
  el lanzamiento de Helldivers 2.** Son funciones independientes.

## Pruebas

`tests/test_autostart.py` comprueba la creación y retirada en Linux en un HOME
temporal, la protección de archivos ajenos, la compatibilidad con el lanzador
antiguo, la selección de gestor por plataforma y la generación del LaunchAgent
sin ejecutar `launchctl` real.
