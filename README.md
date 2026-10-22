# 🕰️ Reloj en Python

Reloj analógico y digital hecho **solo con Python puro**: sin `import`, sin librerías
(ni siquiera la librería estándar), sin HTML y sin CSS.

![Captura del reloj](docs/captura.png)

## ¿Cómo funciona?

El programa calcula todo con Python y genera un archivo **`reloj.svg`**. SVG es un formato
de imagen vectorial, y sus animaciones nativas (SMIL) mueven las agujas en vivo en
cualquier navegador sin JavaScript, HTML ni CSS.

| Necesidad | Cómo se resuelve sin librerías |
|---|---|
| Hora actual | Se lee `/proc/stat` (momento del arranque) + `/proc/uptime` con `open()` |
| Zona horaria | Lector propio del formato binario TZif de `/etc/localtime` |
| Horario de verano | Intérprete propio de reglas POSIX (`CET-1CEST,M3.5.0,M10.5.0/3`) |
| Fecha | Algoritmo de días ↔ calendario civil y nombres en español |
| Seno y coseno | Series de Taylor escritas a mano |
| Animación | `<animateTransform>` con inicio negativo para arrancar en la hora exacta |
| Botones | Eventos `click` de SMIL (`begin="boton.click"`) |

## Requisitos

- Python 3.9 o superior
- Linux (usa `/proc` y `/usr/share/zoneinfo`)
- Un navegador moderno (Firefox, Chrome, Edge…)

## Uso

```bash
python3 reloj.py
```

El programa pregunta:

1. **Tema inicial**: Clásico, Neón, Matrix o Atardecer.
2. **Hora de la alarma** (`HH:MM`), o Enter para no poner ninguna.
3. **Fecha para la cuenta regresiva** (`DD/MM`), o Enter para Navidad.

Después abre el archivo generado en el navegador:

```bash
xdg-open reloj.svg
```

> ⚠️ El reloj se sincroniza al momento de generarse. Ábrelo enseguida; si lo abres más
> tarde, vuelve a ejecutar `python3 reloj.py`.

## Funcionalidades

- 🕰️ **Reloj analógico** con agujas animadas (el segundero avanza a saltos, como uno real).
- 🔢 **Reloj digital tipo odómetro** con los dos puntos parpadeando.
- 📅 **Fecha en español** y un **saludo** que cambia según la hora del día.
- 🎨 **4 temas de color** que se cambian con un clic.
- 🌎 **Relojes del mundo**: Bogotá, Madrid, Tokio y Nueva York, con su diferencia horaria
  y horario de verano.
- ⏰ **Alarma**: un marcador en la esfera y un aviso a pantalla completa que se apaga con
  un clic.
- ⏱️ **Cronómetro** con décimas de segundo.
- 🍅 **Pomodoro** de 25 minutos con un anillo de progreso.
- 🎉 **Modo divertido**:
  - la hora en palabras ("Son las tres y cuarto"),
  - un reloj al revés que gira en sentido contrario,
  - un botón para hacer girar el reloj (o un clic en la esfera),
  - una cuenta regresiva hasta una fecha especial.

## Limitaciones

- Sin JavaScript no se puede pausar el cronómetro: solo iniciar y reiniciar.
- La alarma no suena, porque SVG no reproduce audio. El aviso es visual.
- Si `/proc` no está disponible se usa el reloj de hardware, que en algunos equipos guarda
  la hora local en vez de UTC.

## Estructura

Todo está en un único archivo, `reloj.py`, porque usar varios módulos exigiría `import`.
Está organizado en secciones:

1. Hora del sistema
2. Calendario
3. Zonas horarias (TZif + reglas POSIX)
4. Trigonometría
5. Generación de SVG (esfera, agujas, odómetros)
6. Paneles: mundo, cronómetro, pomodoro y modo divertido
7. Preguntas al usuario y `main()`
