# Portafolio · Macroeconomía y Empresa

Portafolio académico de **Michelle Griffiths Boada** (UCB, 2026). Una sola página con cuatro pestañas: Apuntes (infografías interactivas), Trabajos, Ejercicios y Datos macroeconómicos de Bolivia en vivo (INE · BCB).

## Estructura

```
index.html               página principal (pestañas)
assets/style.css         sistema visual compartido
infografias/             una infografía interactiva por parte del cuaderno
data/contenido.json      apuntes, trabajos y ejercicios (editar aquí para agregar)
data/macro.json          datos INE/BCB (lo actualiza el script)
scripts/actualizar_datos.py   descarga IPC, tipo de cambio y UFV del BCB
trabajos/                archivos entregados
.github/workflows/       actualización diaria automática
```

## Agregar un trabajo

1. Copiar el archivo a `trabajos/`.
2. Agregar una entrada en `data/contenido.json`, en la lista `trabajos`:

```json
{"fecha": "2026-09-25", "titulo": "Taller 2 · IPC", "tipo": "Taller", "estado": "entregado",
 "descripcion": "Canasta familiar simple y cálculo del IPC.", "archivo": "trabajos/taller-2-ipc.pdf"}
```

`estado` puede ser `pendiente`, `entregado` o `calificado`; opcionalmente `"nota": "95"`.

## Agregar un ejercicio

Misma idea, lista `ejercicios`: `n`, `titulo`, `sesion`, `enunciado`, `solucion`.

## Datos

`python scripts/actualizar_datos.py` regenera `data/macro.json`. En GitHub, el workflow lo corre cada día a las 08:30 (hora de Bolivia) y publica el cambio solo.

## Ver en local

```
python -m http.server 8080
```
y abrir http://localhost:8080 (hace falta servidor porque la página lee JSON).
