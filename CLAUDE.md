# CLAUDE.md

Cómo trabajar en este repositorio. **No duplica el planteamiento**: eso está en `README.md` (problema, estado del arte, método, datos, entregable) y en `articulo_divulgacion.md` (la narrativa completa). El estado exacto del trabajo está en `HANDOFF.md`.

**Al entrar en una sesión nueva: lee `HANDOFF.md` primero.** Dice en qué fase está el proyecto y qué sigue.

## El marco, y es vinculante

**Demostración de oficio nivel senior, no un descubrimiento.** Se decidió explícitamente tras revisar la literatura: perseguir novedad lleva al proyecto inflado de investigación, y la vara para eso es publicar.

- **No se deriva ningún estimador.** Métodos publicados y citados.
- **El proyecto no tiene tesis.** Todo hallazgo entra como un paso, no como titular — es el modo de falla propio de este trabajo y ya ocurrió tres veces en el planteamiento. Ver `rules/evidencia.md` §3.
- Lo que se demuestra es juicio: detectar el defecto del dato antes de estimar, elegir el método con criterio, cerrar en una decisión y **reportar dónde falla**.

## La pregunta, en una línea

> ¿Cuál de las correcciones disponibles lleva a mejores decisiones de despliegue, cuánto mejora, y en qué condiciones conviene no usar ninguna?

Y el criterio, que gobierna todo lo demás: **los métodos se juzgan por las decisiones que producen, no por si cumplen sus propios supuestos.** El orden es **medir → explicar → descartar**.

## Arquitectura

```
src/wcab/                    el paquete; nada lee data/raw directamente
├── io.py                    descarga desde OSF + carga
├── exclusion.py             ← LA regla de exclusión, un solo lugar
├── panel.py                 ← LA puerta a los datos: panel canónico
├── diagnostics/
│   ├── srm.py               paso 0 · desbalance de asignación
│   ├── noise.py             paso 1 · calibración contra los A/A
│   └── precision.py         paso 6 · dependencia parámetro-precisión
├── shrinkage/
│   ├── base.py              interfaz común: fit(panel) → θ̃
│   ├── dispersion.py        τ² en conjunto (Paule-Mandel, DerSimonian-Laird)
│   ├── standard.py          el método de referencia
│   ├── alternative.py       la alternativa elegida
│   └── neighborhood.py      global vs local (núcleo sobre semana / similitud)
├── thinning.py              paso 4 · partición hipergeométrica  ← el módulo crítico
├── decision.py              paso 5 · reglas y métricas
└── inference.py             bootstrap por experimento

scripts/NN_*.py              cada uno escribe su JSON en reports/results/
tests/                       test_thinning.py es el crítico
reports/results/*.json       una cifra, un script, una clave
reports/figures/*.png
data/raw/  data/derived/     ignorados por git
```

**El panel canónico es la única puerta a los datos.** Se construye una vez con la exclusión aplicada y se guarda en `data/derived/`. Un script que lea `data/raw/` directamente está mal.

**La interfaz común de `shrinkage/base.py` es lo que hace justa la comparación**: el arnés de decisión no sabe qué método está evaluando, así que «dos métodos × global/local» es un bucle, no código copiado cuatro veces.

## Fases de construcción

Cada una entrega algo comprobable antes de pasar a la siguiente.

| Fase | Se construye | Entrega |
|---|---|---|
| **A** | `io` · `exclusion` · `panel` + tests | La tabla mes a mes del SRM, reproducida por el repo |
| **B** | `diagnostics/noise` | El veredicto sobre `v`, **sea cual sea** |
| **C** | `thinning` + su test | La maquinaria de medición, verificada |
| **D** | `shrinkage/standard` global + `decision` | **La primera cifra de punta a punta** |
| **E** | `neighborhood` local + `alternative` | Las seis configuraciones |
| **F** | `05_donde_falla` · `06_explicar` | La parte no opcional |
| **G** | Congelar → confirmatorio → escribir | El entregable |

**Vigilar la fase D:** produce un número real antes de construir todo. Si ahí nada mejora la decisión, eso es el resultado y el proyecto se acorta.

## Las cuatro reglas, vinculantes

Se cargan solas desde `.claude/rules/`; no hace falta leerlas a mano, pero no se negocian sobre la marcha.

| Regla | De qué trata |
|---|---|
| `metodo.md` | El criterio, el orden medir→explicar→descartar, dos métodos, **la congelación** |
| `datos.md` | La exclusión jun-2013 a ene-2014 y el panel como única puerta |
| `evidencia.md` | Cifras desde scripts, referencias verificadas, **el guardarraíl contra las tesis** |
| `alcance.md` | Qué queda fuera y el entregable que le pone final |

## Dos hooks que te van a frenar, y están bien

| Hook | Qué bloquea |
|---|---|
| `venv_guard.py` | Invocar el Python o pip **globales**. Esta máquina tiene un Python 3.11.9 en el PATH; un `python script.py` por descuido usaría el intérprete equivocado. Excepciones: `-m venv` y `--version` |
| `freeze_guard.py` | Tocar la **muestra confirmatoria** mientras no exista `reports/results/METODO_CONGELADO.json`. **Falla cerrado**: si no ubica la raíz del proyecto, bloquea |

Si uno te rechaza, **reescribe el comando; no busques cómo rodearlo.** Y hay un tercero, `test_critico.py`, que corre `tests/test_thinning.py` al editar la partición: si falla, todas las cifras del proyecto quedan mal y nada más lo delata.

Los hooks se crearon en esta carpeta, así que **abre `/hooks` una vez al entrar** (o reinicia la sesión) para que el watcher los tome.

## Dos skills

| Skill | Cuándo |
|---|---|
| `auditar-cifras` | Antes de cerrar una sección o publicar. Rastrea cada cifra hasta `script → JSON → clave` |
| `revisar-estado-del-arte` | Antes de congelar, antes de publicar, o si pasaron dos meses. **Y siempre que se vaya a afirmar que algo no está hecho** — esa clase de afirmación ya falló tres veces aquí |

## Entorno

```bash
./.venv/Scripts/python.exe -m pip install -r requirements.txt
./.venv/Scripts/python.exe -m pytest -q
```

**Todo se desarrolla dentro del venv del proyecto.** Ya está creado y poblado (Python 3.11.9). `.venv/` ignorado por git.

## Idioma

Español, con ortografía y acentuación completas. Identificadores de código y términos técnicos en su forma original.

## Contexto histórico

Las decisiones de fondo —por qué existe el proyecto, qué se descartó y por qué, y los hallazgos técnicos que no conviene volver a descubrir— están en `../_bitacora-portafolio/`. **Empieza por su `README.md`**: es un índice con referencias a la intervención exacta donde se tomó cada decisión.

## Proyecto hermano

`../dose-selection-phase2` — mismo marco, brazos **ordenados por dosis**. Independiente en código y datos.

**Orden vinculante: este proyecto terminado y publicado antes de abrir el otro.** La razón: el historial de trabajo son proyectos que se desbordan y no se terminan.
