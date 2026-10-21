# Pruebas y verificación

La comprobación sintáctica con `py_compile` no demuestra que la aplicación
funcione. Este documento separa las pruebas automatizadas de las que requieren
un escritorio, audio, micrófono o un sistema operativo concreto.

## Ejecutar la batería automatizada

```sh
cd ~/Documentos/SuperEarthCommand
bash scripts/ejecutar_pruebas.sh
```

Equivale a:

```sh
source .venv/bin/activate.fish
QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -v
```

También se puede ejecutar un archivo concreto:

```sh
python -m unittest tests.test_voice -v
```

## Cobertura automatizada

| Archivo | Qué comprueba |
|---|---|
| `tests/test_config.py` | Carga TOML, rutas de recursos, logo obligatorio, recursos opcionales, decisiones de fondo, voz, lanzamiento y duraciones. |
| `tests/test_voice.py` | Dependencias y modelo de voz, micrófono ausente, activación simulada, parada del hilo y liberación del dispositivo. |
| `tests/test_platforms.py` | Selección de adaptador, detección de KDE Plasma 6, rechazo de otros escritorios, lectura del fondo y controlador común. |
| `tests/test_autostart.py` | Instalación y retirada en un HOME temporal, archivos ajenos, rutas con espacios, LaunchAgent y selección de gestor. |
| `tests/test_ui_flow.py` | Inicio de la secuencia, cancelación, barra de progreso, aciertos y errores de estratagemas, lanzamiento de Steam y audio ausente. |
| `tests/test_project.py` | Comprobaciones básicas de identidad del proyecto. |

Las pruebas de interfaz usan `QT_QPA_PLATFORM=offscreen`. No demuestran que la
ventana se vea correctamente en un escritorio real ni que el audio suene.

## Escenarios de error cubiertos

- Vosk no instalado o no importable.
- Modelo de voz ausente o incompleto.
- Micrófono no disponible o que falla al abrirse.
- Logo obligatorio ausente.
- Fondo, audio o iconos opcionales ausentes.
- Entorno de escritorio sin adaptador de fondo.
- Fondo actual no identificable y fallo al aplicar o restaurar.
- Rutas de recursos y de modelo relativas o absolutas.
- Duraciones inválidas en la configuración.
- Inicio automático no disponible, archivos ajenos y errores de creación.

## Comprobaciones manuales necesarias

Estas pruebas no se pueden sustituir por las automatizadas:

1. **Voz real:** iniciar `python -u app.py`, decir «Modo Democracia» y confirmar
   que la secuencia se activa una sola vez.
2. **Audio real:** comprobar que suena la música y que baja al abrir el juego.
3. **Fondo real:** confirmar que cambia al iniciar la secuencia y se restaura al
   cancelar o salir según `restore_wallpaper_on_exit`.
4. **Bandeja:** comprobar que la X oculta la ventana, que la escucha continúa y
   que el menú permite mostrar o salir.
5. **Steam:** confirmar que Helldivers 2 se abre cuando ambos interruptores
   están activados.
6. **Inicio automático Linux:** instalar, cerrar sesión, volver a entrar,
   comprobar la bandeja y retirar el inicio automático.
7. **Windows y macOS:** repetir el arranque, el fondo, la bandeja, el inicio
   automático y la retirada en hardware real.

## Registro de resultados

| Fecha | Entorno | Resultado |
|---|---|---|
| 2026-10-21 | CachyOS, KDE Plasma 6, Python 3.14.8 | 97 pruebas automatizadas correctas. Arranque, voz opcional simulada, fondo y autostart Linux con HOME temporal comprobados; la frase con micrófono real y el inicio de sesión real siguen pendientes de prueba manual. |
| Pendiente | Windows real | Sin ejecutar. |
| Pendiente | macOS real | Sin ejecutar. |

No debe afirmarse que Windows o macOS están validados solo porque su código
compile o porque sus pruebas unitarias pasen en Linux.

## Añadir pruebas

- Usar `unittest`; no se requieren dependencias adicionales.
- Evitar abrir el micrófono, cambiar el fondo o modificar el autostart real.
- Usar `unittest.mock` y directorios temporales para aislar el sistema.
- Para pruebas de interfaz, importar después de que `tests/__init__.py` defina
  `QT_QPA_PLATFORM=offscreen`.
- Una prueba nueva debe describir el comportamiento esperado, no solo que una
  función no lanza una excepción.
