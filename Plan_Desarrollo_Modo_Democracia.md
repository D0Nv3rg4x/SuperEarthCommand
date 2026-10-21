# Modo Democracia — Plan de desarrollo y fases del proyecto

## 1. Propósito del documento

Este documento establece el plan de trabajo de **Modo Democracia**, una aplicación que permite activar mediante voz una secuencia inspirada en *Helldivers 2*, con interfaz visual, audio, gestión opcional del fondo de pantalla y lanzamiento del juego según la configuración.

El objetivo es mejorar la robustez, la portabilidad, la facilidad de mantenimiento y la documentación del proyecto, conservando las funciones que ya están operativas.

Este documento describe las siete fases acordadas, sus objetivos, tareas, resultados esperados, criterios de aceptación y dependencias. No implica que todas las funciones descritas estén implementadas o verificadas en todas las plataformas.

## 2. Estado general

| Fase | Área de trabajo | Estado |
|---:|---|---|
| 1 | Detección de Python y gestión de recursos obligatorios/opcionales | Completada según las pruebas del usuario |
| 2 | Aislamiento y detección del soporte para fondos de pantalla | Completada según las pruebas del usuario |
| 3 | Reconocimiento de voz opcional | Implementada; pendiente validación manual de la frase |
| 4 | Adaptadores para Linux, Windows y macOS | Implementada en código; Windows y macOS sin validar en hardware real |
| 5 | Inicio automático por sistema operativo | Implementado; Linux probado con HOME temporal; Windows y macOS sin probar en hardware real |
| 6 | Pruebas funcionales y de regresión | Batería automatizada completada; Windows y macOS pendientes de prueba real |
| 7 | Actualización del README y documentación | Completada; documentación alineada con el código y las limitaciones verificadas |

**Estado confirmado por el usuario:** la aplicación funciona en su totalidad en el entorno actual. Las fases 1 y 2 se consideran completadas. La compilación de sintaxis de algunos archivos no sustituye las pruebas de funcionamiento en otros sistemas operativos.

## 3. Principios de trabajo

1. **Conservar el comportamiento existente.** Los cambios deben ser incrementales y no deben eliminar funciones que ya funcionan.
2. **Fallar de forma controlada.** La ausencia de una función opcional no debe impedir el inicio completo de la aplicación cuando sea razonable continuar sin ella.
3. **Separar responsabilidades.** La lógica principal no debe contener detalles específicos de cada sistema operativo cuando puedan encapsularse en adaptadores.
4. **Detectar capacidades reales.** No se debe asumir que una función está disponible únicamente por el nombre del sistema operativo; hay que comprobar las herramientas y condiciones necesarias.
5. **No modificar el entorno automáticamente.** La aplicación no debe instalar dependencias ni alterar el sistema sin una acción explícita.
6. **Documentar lo que realmente existe.** Diferenciar las funciones implementadas, las verificadas y las pendientes.
7. **Validar después de los cambios.** Cada fase debe comprobar que las funciones anteriores continúan operativas.

---

# Fase 1 — Corregir la detección de Python y la gestión de recursos

**Estado:** completada según las pruebas del usuario.

## Objetivo

Mejorar el diagnóstico durante el arranque y distinguir entre los componentes indispensables para iniciar la aplicación y los recursos cuya ausencia puede tolerarse.

## Trabajo contemplado

- Comprobar la versión de Python y comunicar incompatibilidades de forma comprensible.
- Identificar dependencias esenciales y explicar cuáles faltan.
- Resolver las rutas de los recursos de forma coherente con la ubicación del proyecto.
- Distinguir los recursos obligatorios de los opcionales.
- Evitar que la ausencia de un recurso opcional provoque un cierre innecesario.
- Proporcionar mensajes útiles cuando falte un componente esencial.

## Clasificación orientativa de recursos

La clasificación definitiva depende de cómo los use el código real.

| Recurso o componente | Comportamiento esperado |
|---|---|
| Logotipo necesario para construir la interfaz | Si es indispensable, informar del problema claramente. |
| Archivo de audio de la secuencia | Permitir continuar sin audio si su ausencia está contemplada. |
| Imagen del fondo de pantalla | Permitir iniciar sin cambiar el fondo. |
| Iconos secundarios | Usar una alternativa o prescindir de ellos cuando sea posible. |
| Dependencias esenciales | Identificar las dependencias ausentes y explicar cómo preparar el entorno correcto. |

## Resultado esperado

El inicio debe producir mensajes claros y accionables, en lugar de errores poco explicativos derivados de archivos ausentes o de un intérprete de Python incorrecto.

## Criterios de aceptación

- [x] El usuario confirma que la aplicación funciona en su entorno.
- [x] La documentación de instalación explica el uso del entorno virtual.
- [x] Los errores de dependencias y recursos se verifican mediante pruebas repetibles en la fase 6.

> La instalación desde cero y los errores de recursos están documentados en
> `README.md` y cubiertos por `tests/test_config.py`.

---

# Fase 2 — Aislar y detectar el soporte de fondos de pantalla

**Estado:** completada según las pruebas del usuario.

## Objetivo

Separar la gestión del fondo de pantalla del resto de la aplicación y habilitarla únicamente cuando la configuración y el entorno lo permitan.

## Trabajo contemplado

- Detectar si el entorno dispone de un mecanismo compatible para cambiar el fondo.
- Comprobar que la herramienta necesaria está disponible antes de usarla.
- Permitir desactivar la función mediante configuración.
- Evitar cambios en el escritorio si la función está desactivada o no es compatible.
- Guardar el estado necesario para restaurar el fondo original cuando corresponda.
- Gestionar los errores al aplicar o restaurar el fondo.
- Evitar restauraciones inesperadas en una sesión posterior.
- Permitir que el resto de la secuencia funcione si el cambio de fondo no está disponible.

## Configuración

Las siguientes opciones representan decisiones diferentes:

- `wallpaper_enabled`: determina si la función de cambio de fondo está habilitada.
- `restore_wallpaper_on_exit`: determina si debe restaurarse el fondo original al cerrar normalmente la aplicación.

Desactivar el cambio de fondo no debe confundirse con elegir dejar aplicado el fondo de la aplicación al salir.

## Consideraciones para el entorno actual

El entorno actual del usuario es CachyOS con KDE Plasma 6. El mecanismo implementado para este entorno utiliza `plasma-apply-wallpaperimage`. Esto no demuestra por sí solo compatibilidad con todos los escritorios Linux.

## Resultado esperado

El cambio de fondo debe ser una función opcional, aislada y controlada, sin bloquear el resto de la aplicación cuando no esté disponible.

## Criterios de aceptación

- [x] El usuario confirma que el programa funciona en su entorno.
- [x] Las distintas combinaciones de configuración y errores se cubren con pruebas de regresión.
- [x] La documentación describe las limitaciones de compatibilidad que hayan sido verificadas.

Las combinaciones de `wallpaper_enabled`, `restore_wallpaper_on_exit`, soporte
del entorno y ausencia de imagen están en `tests/test_config.py`. Las
limitaciones por escritorio y plataforma están en `docs/PLATFORMS.md`.

---

# Fase 3 — Mejorar el reconocimiento de voz opcional

**Estado:** implementada; pendiente de validación manual de la activación por voz.

## Objetivo

Permitir que la aplicación funcione sin Vosk, sin el modelo de reconocimiento de voz o sin un micrófono disponible, sin que esas condiciones impidan el inicio normal.

Cuando todos los recursos estén disponibles, la activación mediante la frase **«Modo Democracia»** debe seguir funcionando como hasta ahora.

## 3.1. Separar el arranque del reconocimiento de voz

- Evitar que la inicialización del motor de voz sea un requisito absoluto para crear la interfaz.
- Gestionar los errores de inicialización sin cerrar toda la aplicación cuando sea posible continuar sin voz.
- Revisar tanto `core/voice.py` como `app.py`, porque un error puede propagarse aunque el módulo de voz controle sus propias excepciones.
- Mantener separadas la disponibilidad de la interfaz y la disponibilidad del reconocimiento de voz.

## 3.2. Gestionar la ausencia o el fallo de Vosk

Contemplar estos escenarios:

- Vosk está instalado y se inicializa correctamente.
- Vosk no está instalado.
- Vosk está instalado, pero no puede importarse.
- La inicialización del motor de reconocimiento falla.

En los escenarios de fallo, la aplicación debe informar del problema, desactivar la activación por voz y continuar con las demás funciones cuando sea posible. No debe instalar dependencias automáticamente ni modificar el entorno Python del usuario.

## 3.3. Gestionar el modelo de reconocimiento

La configuración actual utiliza la ruta:

`models/vosk-model-small-es-0.42`

El programa debe comprobar que el modelo existe y que contiene los elementos necesarios para su uso. Si falta o está incompleto:

- Informar de la ruta que intentó utilizar.
- Desactivar la función de voz de forma controlada.
- Permitir que la aplicación continúe sin reconocimiento.
- Resolver la ruta de manera coherente con la ubicación del proyecto, sin depender accidentalmente del directorio desde el que se ejecuta el comando.

## 3.4. Gestionar el micrófono y la captura de audio

Contemplar al menos:

- No hay un micrófono disponible.
- El micrófono está desconectado o no puede abrirse.
- El servidor de audio no está disponible.
- La captura no puede iniciarse.
- La captura o el reconocimiento fallan durante la ejecución.

Cuando se produzca un error, la aplicación debe detener o desactivar la escucha de forma controlada. No debe dejar hilos bloqueados, impedir el cierre de la ventana ni generar una secuencia ilimitada de mensajes de error.

## 3.5. Ciclo de vida y recursos

- Evitar inicializar dos veces el mismo proceso de reconocimiento.
- Liberar el dispositivo de captura al detener la escucha.
- Detener la escucha al cerrar la aplicación.
- Mantener sincronizados el estado de la interfaz y el estado real del reconocimiento.
- Evitar que un error de voz interrumpa el audio de la secuencia, la interfaz, la gestión del fondo o el lanzamiento del juego.

## 3.6. Conservar el comportamiento normal

Cuando Vosk, el modelo y el micrófono estén disponibles, la frase «Modo Democracia» debe seguir activando la secuencia. La opción de voz en `config.toml` debe seguir teniendo efecto.

## Archivos previsiblemente relacionados

- `core/voice.py`
- `app.py`
- `config.toml`, únicamente si se necesita ajustar o documentar la configuración.

La lista es orientativa: se deben modificar solo los archivos que realmente lo requieran tras revisar su contenido actual.

## Resultado esperado

La aplicación puede funcionar sin reconocimiento de voz y explica por qué esa función no está disponible, sin perder el comportamiento de voz en una configuración válida.

## Criterios de aceptación

- [x] La aplicación inicia sin Vosk (comprobado con un entorno aislado y un módulo que falla al importar).
- [x] La aplicación inicia sin el modelo (comprobado con una ruta inexistente).
- [x] La aplicación inicia sin un micrófono disponible (comprobado con `query_devices` fallando).
- [x] Los fallos al abrir o usar el micrófono se controlan correctamente.
- [x] La escucha se detiene y libera sus recursos al cerrar.
- [ ] La activación por voz funciona cuando todos los recursos están disponibles. **Requiere prueba manual con micrófono real.**
- [x] Los fallos de voz no interrumpen las demás funciones.
- [x] Los escenarios se cubren con pruebas repetibles en `tests/test_voice.py`.

## Comprobaciones automatizadas de la fase

Las comprobaciones se pueden repetir con:

```sh
cd ~/Documentos/SuperEarthCommand
source .venv/bin/activate.fish
python -m unittest discover -s tests -v
```

Las pruebas cubren dependencias ausentes, modelo ausente o incompleto, micrófono
no disponible, reutilización del hilo de escucha y liberación del dispositivo al
detener. No sustituyen la prueba manual de decir «Modo Democracia» con un
micrófono real, que queda pendiente.

---

# Fase 4 — Implementar adaptadores para Linux, Windows y macOS

**Estado:** implementada en código. Linux/KDE Plasma 6 conserva el mecanismo validado; los adaptadores de Windows y macOS no se han probado en hardware real.

## Objetivo

Encapsular los mecanismos específicos de cada sistema operativo para que la lógica principal no dependa de comandos exclusivos de una plataforma.

La existencia de adaptadores no demuestra automáticamente que la aplicación se haya probado completamente en los tres sistemas.

## 4.1. Definir una interfaz común

Los adaptadores deben ofrecer operaciones coherentes para las capacidades que comparten, por ejemplo:

- Comprobar si una función está disponible.
- Aplicar un fondo de pantalla.
- Restaurar el estado anterior cuando corresponda.
- Comunicar si una operación no está soportada.
- Devolver errores comprensibles para la lógica principal.

La interfaz exacta debe adaptarse al código existente. No es necesario crear abstracciones que no aporten utilidad real.

## 4.2. Adaptador de Linux

- Detectar el entorno de escritorio y las herramientas necesarias.
- Conservar el comportamiento validado en KDE Plasma 6.
- No asumir que todos los escritorios Linux comparten comandos o formatos de configuración.
- Permitir desactivar una función concreta si el escritorio no es compatible.
- Evitar cambios en el escritorio cuando la capacidad no esté disponible.

El soporte para GNOME u otros escritorios debe añadirse y probarse explícitamente si forma parte del alcance final; no debe inferirse del soporte de Linux en general.

## 4.3. Adaptador de Windows

- Utilizar mecanismos propios de Windows para las operaciones soportadas.
- Evitar ejecutar comandos de KDE.
- Manejar rutas y nombres que incluyan espacios.
- Gestionar errores y permisos de manera controlada.
- Probar la aplicación en un entorno Windows real antes de declarar el soporte como verificado.

## 4.4. Adaptador de macOS

- Utilizar mecanismos propios de macOS para las operaciones soportadas.
- Considerar rutas, permisos y diferencias entre versiones.
- Evitar ejecutar herramientas exclusivas de Linux o Windows.
- Desactivar las funciones no disponibles sin impedir el resto de la aplicación.
- Probar el comportamiento en macOS antes de declarar el soporte como verificado.

## 4.5. Selección del adaptador

- Identificar el sistema operativo.
- Seleccionar el adaptador correspondiente.
- Comprobar las capacidades concretas disponibles.
- Gestionar sistemas no soportados de forma controlada.
- Mantener los detalles de cada plataforma fuera de la lógica principal siempre que sea razonable.

## Resultado esperado

Cada sistema utiliza sus propios mecanismos y la aplicación mantiene un comportamiento predecible ante funciones no soportadas.

## Criterios de aceptación

- [x] El adaptador de Linux conserva el funcionamiento existente (mismo comando y misma lectura de Plasma, cubiertos por pruebas).
- [x] El adaptador de Windows utiliza mecanismos apropiados para Windows (`SystemParametersInfoW`).
- [x] El adaptador de macOS utiliza mecanismos apropiados para macOS (`osascript` y System Events).
- [x] La lógica principal no depende de comandos específicos dispersos por el proyecto.
- [x] Las funciones no soportadas se gestionan de forma controlada.
- [x] Se documenta qué plataformas y versiones se han probado realmente en `docs/PLATFORMS.md`.

## Comprobaciones automatizadas de la fase

```sh
cd ~/Documentos/SuperEarthCommand
source .venv/bin/activate.fish
python -m unittest discover -s tests -v
```

`tests/test_platforms.py` cubre la selección de adaptadores, la detección de
KDE Plasma 6, el rechazo de escritorios no implementados, la lectura del fondo
en Plasma, las rutas de estado por plataforma y el controlador común con un
adaptador simulado. Windows y macOS solo están implementados y revisados: no se
declaran verificados hasta probarlos en un equipo real.

---

# Fase 5 — Separar el inicio automático por sistema operativo

**Estado:** implementada. Linux (XDG autostart) está probado con un HOME temporal; falta comprobar el inicio real al cerrar y abrir sesión. Windows y macOS están implementados y documentados, pero no probados en hardware real.

## Objetivo

Permitir que el usuario configure el inicio automático de la aplicación mediante el mecanismo apropiado de cada sistema operativo, con procedimientos documentados para instalar y retirar esa configuración.

Esta fase trata del inicio de la aplicación al iniciar sesión. No debe confundirse con la activación por voz ni con el lanzamiento de Helldivers 2.

## 5.1. Linux

Para el entorno actual de KDE Plasma se puede utilizar el mecanismo de autostart del usuario.

La implementación debe:

- Crear la configuración necesaria en la ubicación apropiada.
- Utilizar una ruta estable a la aplicación.
- Ejecutar el intérprete o entorno virtual correcto.
- Evitar depender del directorio de trabajo accidental de la sesión.
- Informar si no se puede crear o retirar la configuración.
- Permitir desactivar el inicio automático sin desinstalar el proyecto.

La compatibilidad con otros escritorios debe verificarse por separado.

## 5.2. Windows

- Utilizar un mecanismo apropiado para iniciar la aplicación durante la sesión del usuario.
- Resolver correctamente rutas con espacios.
- Utilizar el intérprete o empaquetado correcto.
- Evitar depender de una terminal abierta.
- Proporcionar un procedimiento claro para desactivar el inicio automático.

## 5.3. macOS

- Utilizar un mecanismo compatible con el inicio de sesión de macOS y con la forma de distribución de la aplicación.
- Gestionar las rutas y permisos necesarios.
- Proporcionar un método claro para activar y desactivar la función.
- Verificar el comportamiento en un entorno macOS real.

## 5.4. Instalación y retirada

Cada plataforma debe tener operaciones de instalación y retirada claramente separadas.

La retirada debe eliminar únicamente los archivos o entradas creados por la aplicación. No debe borrar los recursos del proyecto ni modificar configuraciones ajenas.

## Resultado esperado

La instalación y retirada del inicio automático están documentadas para cada plataforma compatible.

## Criterios de aceptación

- [x] Se puede activar el inicio automático (Linux probado con HOME temporal; Windows y macOS implementados).
- [x] La aplicación se inicia con el intérprete y las rutas correctas (lanzador de Linux ejecutado en una prueba aislada).
- [x] Se puede retirar el inicio automático sin desinstalar la aplicación.
- [x] La retirada no elimina datos ajenos al programa.
- [x] Los errores de instalación o retirada se comunican claramente.
- [x] Los procedimientos están documentados por plataforma en `docs/AUTOSTART.md`.

## Comprobaciones automatizadas de la fase

```sh
cd ~/Documentos/SuperEarthCommand
source .venv/bin/activate.fish
python -m unittest discover -s tests -v
```

`tests/test_autostart.py` cubre la instalación y retirada en un HOME temporal,
la protección de archivos ajenos, la migración del lanzador anterior, las rutas
con espacios, la selección de gestor por plataforma y la generación del
LaunchAgent de macOS. Windows y macOS siguen pendientes de validación real.

---

# Fase 6 — Crear pruebas funcionales y de regresión

**Estado:** completada como fase formal. La batería automatizada se ejecuta con `unittest`; Windows y macOS siguen pendientes de prueba real.

## Objetivo

Reducir el riesgo de que una modificación rompa una función existente y hacer repetible la verificación del comportamiento.

La comprobación sintáctica con `py_compile` es útil, pero no demuestra por sí sola que la aplicación funcione correctamente.

## 6.1. Pruebas unitarias

Probar módulos individuales sin depender innecesariamente del escritorio, del micrófono o de dispositivos reales.

Áreas posibles:

- Resolución de rutas.
- Lectura y validación de configuración.
- Clasificación de recursos obligatorios y opcionales.
- Detección de capacidades de los adaptadores.
- Manejo de errores de Vosk y del modelo.
- Decisiones de activación y restauración del fondo.
- Creación y retirada de la configuración de inicio automático.

Cuando sea adecuado, deben utilizarse dobles de prueba o dependencias simuladas para evitar modificar el escritorio real.

## 6.2. Pruebas funcionales

Comprobar el flujo general de la aplicación:

- Inicio de la interfaz.
- Activación de la secuencia.
- Reproducción de audio.
- Avance y finalización de la barra de progreso.
- Gestión del fondo de pantalla.
- Detención de la escucha.
- Cierre de la aplicación.
- Lanzamiento del juego cuando la opción correspondiente está activada.

Las pruebas deben respetar la configuración actual y no asumir que todas las funciones están habilitadas en todos los entornos.

## 6.3. Pruebas de escenarios de fallo

Incluir escenarios como:

- Falta Vosk.
- Falta el modelo de voz.
- No hay micrófono disponible.
- El dispositivo de audio no puede abrirse.
- Falta la imagen de fondo.
- No existe la herramienta necesaria para cambiar el fondo.
- La configuración contiene rutas incorrectas.
- Falla la restauración del fondo.
- Falla la creación o retirada del inicio automático.
- Se ejecuta en una plataforma no soportada.

Para cada escenario debe definirse el resultado esperado: continuar sin una función, mostrar un mensaje o detener el inicio cuando un componente esencial impida funcionar.

## 6.4. Pruebas de regresión

Después de cambios relevantes, verificar que continúan funcionando las características existentes. Por ejemplo, una modificación del reconocimiento de voz no debe cambiar la duración de la secuencia ni interrumpir la interfaz, el audio o el lanzamiento del juego.

## 6.5. Herramientas y ejecución

- Utilizar herramientas disponibles en el entorno virtual del proyecto.
- Aprovechar `unittest` cuando sea suficiente, evitando dependencias adicionales innecesarias.
- Documentar los comandos para ejecutar las pruebas.
- Separar las pruebas automatizadas de las comprobaciones manuales que requieren hardware o un sistema operativo concreto.
- Registrar los resultados y los escenarios no probados.

## Resultado esperado

Un conjunto de pruebas repetible que reduzca el riesgo de regresiones y permita identificar qué comportamientos han sido comprobados.

## Criterios de aceptación

- [x] Existe una batería de pruebas ejecutable (97 pruebas con `unittest`).
- [x] Se prueban comportamientos normales y escenarios de error.
- [x] Los resultados se pueden interpretar con claridad.
- [x] Se vuelven a ejecutar las pruebas de regresión tras cambios relevantes.
- [x] Se documentan las pruebas manuales y las dependientes de plataforma en `docs/TESTING.md`.
- [x] No se afirma que una plataforma está validada si solo se ha compilado o revisado el código.

## Comprobaciones automatizadas de la fase

```sh
cd ~/Documentos/SuperEarthCommand
bash scripts/ejecutar_pruebas.sh
```

La batería incluye configuración y recursos, voz opcional, adaptadores de
fondo, inicio automático y flujo de interfaz en modo `offscreen`. Las pruebas
manuales de micrófono, audio, cambio de fondo real, Steam, bandeja y sistemas
Windows/macOS están registradas en `docs/TESTING.md`.

---

# Fase 7 — Actualizar README y documentación

**Estado:** completada. `README.md` describe la instalación, ejecución, configuración, inicio automático, resolución de problemas y limitaciones reales; el resto de documentos están enlazados desde él.

## Objetivo

Alinear la documentación con la versión real del programa para que otra persona pueda preparar el entorno, ejecutar la aplicación, configurar sus funciones y resolver los problemas habituales.

## 7.1. Requisitos e instalación

Documentar:

- Versiones de Python compatibles, una vez verificadas en el proyecto.
- Dependencias necesarias.
- Estructura de directorios.
- Creación del entorno virtual.
- Activación del entorno virtual según la shell.
- Instalación de dependencias.
- Preparación del modelo de Vosk si se desea usar la activación por voz.
- Ubicación de los recursos requeridos.

Para el entorno actual de CachyOS con Fish, el procedimiento de ejecución conocido es:

```fish
cd ~/Documentos/SuperEarthCommand
source .venv/bin/activate.fish
python app.py
```

El entorno virtual debe activarse porque las dependencias del proyecto pueden estar instaladas en `.venv` y no en el Python del sistema.

## 7.2. Ejecución y configuración

- Explicar el comando de inicio.
- Describir las opciones de `config.toml`.
- Indicar los valores predeterminados comprobados.
- Explicar la activación y desactivación del reconocimiento de voz.
- Documentar la gestión del fondo de pantalla y su restauración.
- Explicar las opciones relacionadas con la duración de la secuencia y el lanzamiento del juego.
- No documentar opciones que no existan en el código final.

## 7.3. Compatibilidad

Distinguir claramente entre:

- Funciones verificadas en CachyOS y KDE Plasma 6.
- Funciones implementadas pero aún no verificadas en otros sistemas.
- Funciones que no están disponibles en un entorno determinado.

No debe anunciarse soporte completo para Windows o macOS solo porque existan adaptadores en el código.

## 7.4. Inicio automático

Incluir instrucciones separadas para Linux, Windows y macOS cuando sus implementaciones estén listas y verificadas.

Cada sección debe explicar:

- Cómo activar el inicio automático.
- Cómo comprobar que funciona.
- Cómo desactivarlo.
- Qué archivos o configuraciones crea.
- Cómo resolver errores habituales.

## 7.5. Resolución de problemas

Incluir, según los casos que se hayan comprobado:

- Dependencias ausentes.
- Uso de un intérprete Python incorrecto.
- Modelo de Vosk ausente o inválido.
- Micrófono no disponible.
- Fallos del servidor de audio.
- Fondo de pantalla no compatible.
- Errores de permisos o rutas.
- Problemas con el inicio automático.

## Resultado esperado

La documentación debe describir la aplicación real, sus requisitos y sus limitaciones, sin depender de las conversaciones de desarrollo.

## Criterios de aceptación

- [x] El README permite preparar el entorno desde cero.
- [x] Los comandos corresponden a la estructura real del proyecto.
- [x] Las opciones de configuración están explicadas.
- [x] Las funciones opcionales y sus limitaciones están documentadas.
- [x] El inicio automático tiene instrucciones por plataforma.
- [x] Los requisitos y las plataformas probadas están descritos con precisión.
- [x] La documentación se revisa contra la versión final del código.

El README distingue expresamente lo verificado en CachyOS/KDE Plasma 6 de lo
implementado sin validación en Windows y macOS. También se han retirado de
`config.toml` las claves que no tenían efecto.

---

# 8. Orden de ejecución y dependencias

El orden previsto es:

1. Fase 1 — robustez del arranque.
2. Fase 2 — gestión del fondo de pantalla.
3. Fase 3 — reconocimiento de voz opcional.
4. Fase 4 — adaptadores para cada sistema operativo.
5. Fase 5 — inicio automático por sistema operativo.
6. Fase 6 — pruebas funcionales y de regresión.
7. Fase 7 — documentación final.

Las fases 1 y 2 se consideran completadas según la validación del usuario. No es necesario rehacerlas, aunque sus comportamientos deben incluirse en las pruebas de regresión.

La fase 6 puede prepararse progresivamente: cada fase nueva debería incluir sus propias comprobaciones, mientras que la fase 6 consolida una batería formal de pruebas.

La fase 7 debe reflejar el estado real alcanzado. Es preferible documentar una limitación con precisión que declarar una función terminada sin haberla probado.

---

# 9. Definición de terminado del proyecto

El plan se considerará completado cuando se cumplan los siguientes puntos:

- [x] La aplicación conserva el comportamiento existente en el entorno validado.
- [x] Puede iniciar sin reconocimiento de voz cuando Vosk, el modelo o el micrófono no están disponibles.
- [x] Los errores de funciones opcionales se gestionan de forma controlada.
- [x] La lógica específica de cada sistema operativo está aislada en adaptadores.
- [x] Las funciones no compatibles se desactivan sin afectar innecesariamente al resto de la aplicación.
- [x] El inicio automático puede instalarse y retirarse mediante procedimientos documentados (Linux probado con HOME temporal; Windows y macOS pendientes de prueba real).
- [x] Existe una batería de pruebas funcionales y de regresión.
- [x] Las pruebas y las plataformas realmente verificadas están registradas.
- [x] El README y la documentación corresponden al código final.
- [x] No se han introducido cambios ajenos al alcance acordado.

## 10. Próximo paso

Las siete fases del plan están completadas. La documentación final está en
`README.md` y en `docs/`; la batería automatizada tiene 97 pruebas. Quedan
pendientes las comprobaciones que requieren hardware o una sesión real:

- frase con micrófono real;
- reproducción de audio;
- cambio y restauración del fondo en un escritorio visible;
- apertura de Helldivers 2 mediante Steam;
- inicio automático tras cerrar y volver a iniciar sesión;
- validación de los adaptadores de Windows y macOS en sus sistemas reales.

No quedan fases de desarrollo planificadas. Cualquier cambio futuro debe
mantener las funciones opcionales aisladas, ejecutar
`bash scripts/ejecutar_pruebas.sh` y actualizar `docs/TESTING.md` con las
plataformas realmente verificadas.
