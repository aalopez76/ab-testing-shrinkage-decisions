# HANDOFF

> Estado actual, corto. **No es un historial** — se reescribe, no se acumula. El contexto histórico está en `../_bitacora-portafolio/`.

**Última actualización:** 3 de octubre de 2026
**Fase:** antes de **A**. Planteamiento y harness cerrados; **cero código de análisis**.

## Qué está hecho

- **Planteamiento completo** en `README.md` y `articulo_divulgacion.md`: problema, estado del arte (9 referencias, 7 de los últimos 14 meses), criterio, método, datos y entregable.
- **Datos descargados y verificados** en `data/`:
  - `upworthy-exploratory.csv` — 22 666 brazos, 4 873 experimentos
  - `upworthy-confirmatory.csv` — 105 551 brazos, 22 743 experimentos
- **Arquitectura decidida** y documentada en `CLAUDE.md`: paquete `src/wcab/`, scripts numerados, fases A–G.
- **Entorno virtual** creado y poblado (Python 3.11.9). Ver `requirements.txt`.
- **Harness completo y probado**: permisos, tres hooks, cuatro reglas, dos skills.
- **Diagnóstico de aleatorización** corrido una vez en sesión (aún no como script del repo): reproduce el fallo documentado mes a mes.
- **Diagnóstico de dependencia parámetro-precisión** corrido una vez: Spearman −0.15 entre experimentos, gradiente monótono Q5/Q1 = 0.75. **Pendiente comprobarlo controlando por periodo y tipo de experimento** antes de afirmar nada.

## Hallazgo que cambia el plan (auditoría del 3-oct)

**El modelo de ruido binomial subestima la dispersión ~1.9×.** Medido sobre 1 579 experimentos sin variación en ningún campo público: Q/gl = 1.927, y 25.6% con p < 0.05 contra el 5% nominal.

No se distingue si es agrupamiento (impresiones no independientes) o variación no registrada. **Ambas se declaran.**

Consecuencia para el método: el paso 2 debe comparar **`v` ingenuo contra `v` corregido por factor de diseño**, porque con `v` subestimado el método contrae de menos. Está escrito en el README antes del paso 2.

## Fase A: TERMINADA (3-oct-2026)

Reproducible de cero. `rm -rf data/derived && ./.venv/Scripts/python.exe scripts/01_panel.py`

- `src/wcab/exclusion.py` — la regla, con 6 pruebas incluidos los bordes y las fechas inválidas.
- `src/wcab/panel.py` — panel canónico, única puerta a los datos, con 8 pruebas de contrato.
- `src/wcab/diagnostics/srm.py` + `scripts/02_diagnostico_srm.py` — **la tabla mes a mes, producida por el repo.**
- `src/wcab/io.py` — descarga desde el OSF.
- `pyproject.toml` — paquete instalable (`pip install -e .`), así `import wcab` funciona en tests y scripts.
- **14 pruebas, todas pasan.**

La tabla del paso 0, por el código:

```
2013-06   22.3%     2013-10   75.7%     2014-01   11.0%
2013-07   59.1%     2013-11   84.5%     2014-02    0.6%
2013-08   60.1%     2013-12   86.4%     feb-2014 en adelante: 0.0%-0.9%
2013-09   66.3%
```

**Lo que la fase A encontró, y es el motivo de que exista la regla de evidencia:** varias cifras de los documentos estaban mal. Citaban los totales *antes* de la exclusión y una definición laxa de A/A. Ya están corregidas desde `reports/results/01_panel.json`:

| Decía | Es |
|---|---|
| exploratorio 4 873 exp. | **3 380** tras exclusión (se va el 30.6%) |
| tasa global 1.52% | **1.28%** |
| 2–14 brazos | hasta **20** en el confirmatorio |
| 121 semanas | **68** tras exclusión |
| 840 A/A | **295** (definición estricta: ningún campo público varía) |
| 2 307 solo titular | **1 589** |

## Fases B, C y D: TERMINADAS (3-oct-2026)

**B — el modelo de ruido está mal, medido.** `Q/gl = 1.940` sobre los 295 A/A del panel (confirma el 1.927 de la auditoría). Factor de diseño 1.940. Las dos explicaciones —agrupamiento de impresiones o variación no publicada— **no son distinguibles** y las dos quedan declaradas.

**C — la partición, verificada.** `thinning.py` con 14 pruebas. La crítica: **correlación entre las dos mitades = +0.0013** contra un tope de 0.023, y ambas insesgadas. Hay una prueba de contraste que documenta por qué no se usa *data fission*.

**D — la primera cifra, y cambia el proyecto.**

```
regla                  valor    arrepent.  inflación
azar                 0.01331     0.00456    0.00002
crudo                0.01551     0.00237    0.00237
contraído global     0.01551     0.00237    0.00237
```

Tres cosas:

1. **La maldición del ganador es real y está cuantificada.** El ganador promete 1.551% y entrega 1.314%: **sobreestima un 15.3% relativo**.
2. **Es un efecto de selección**, confirmado internamente: elegir al azar da inflación 0.00002, cien veces menor.
3. **La contracción global NO cambia la decisión** — 99.8% de los experimentos eligen lo mismo.

**Y el por qué es una propiedad matemática, no un accidente.** `v` se calcula con la tasa agrupada del experimento, así que dentro de un experimento depende solo de `n`; y como los brazos reciben impresiones parecidas por diseño, **α es casi uniforme** (rango mediano 0.009 sobre α≈0.47). Con α uniforme, θ̃ = (1−α)θ̂ + α·centro es monótona creciente en θ̂ y **conserva el orden**.

Está fijado en `tests/test_decision.py::test_la_contraccion_uniforme_NO_puede_cambiar_el_maximo`.

**Consecuencia para la fase E, que deja de ser opcional:** solo puede mejorar la decisión un método cuyo **objetivo difiera entre brazos** —contraer hacia un vecindario de experimentos parecidos, no hacia el centro del propio experimento— o cuya **α difiera materialmente** entre brazos. Eso es exactamente el eje global contra local.

## Fase E: TERMINADA (3-oct-2026) — resultado negativo, y limpio

El dilema de la fase D se resolvió en la literatura: la condición que hace real un problema de selección es la **precisión heterogénea** (Gu y Koenker, *Invidious Comparisons*, 2020-21). Medida en el panel:

```
dentro de un experimento   razón n_max/n_min: mediana 1.040, p99 1.094  → HOMOGÉNEA
entre experimentos         impresiones p99/p01 = 7.1, error estándar p90/p10 = 2.63  → heterogénea
```

Así que el nivel correcto es **entre** experimentos — y resulta ser el que la industria plantea: Meta habla de «los experimentos seleccionados para lanzamiento», Netflix de *cuándo* lanzar.

### La decisión y el resultado

Con presupuesto limitado, qué experimentos desplegar. Ganancia realizada media, en puntos porcentuales:

```
regla         5%      10%     25%     50%    100%
azar        0.236   0.242   0.246   0.249   0.254
cruda       1.073   0.864   0.605   0.425   0.254
contraída   0.800   0.690   0.544   0.411   0.254
cola        0.723   0.642   0.519   0.406   0.254
oráculo     1.765   1.429   1.001   0.672   0.254
```

**La regla cruda gana en todos los presupuestos.** Contraer empeora la decisión (−0.27 pp al 5%), y la regla de probabilidad de cola empeora más (−0.35 pp).

**Y no es artefacto del factor de diseño**, comprobado: la dirección se mantiene incluso con factor 1.0 (α=0.41, −0.078 pp). Lo que sí depende del factor es la magnitud —de −0.08 a −0.80 según α— y hay que declararlo.

### El mecanismo

Contraer comprime todo hacia el centro. Eso baja el error cuadrático, pero **comprime también las diferencias de las que depende el orden**. Y solo paga si la heterogeneidad de precisión es grande, porque lo que aporta es despreciar a los imprecisos. Con 2.6× de dispersión en el error estándar y una ventaja real chica frente al ruido, la compresión cuesta más de lo que el descuento diferencial aporta.

**Es la advertencia documentada:** los métodos que dependen de la independencia previa pueden dar peores medias posteriores, y **las decisiones de cribado basadas en ellas pueden ser peores que las tomadas con las estimaciones sin contraer.**

### Dos arreglos que salieron construyendo

1. **τ² salía cero con dos mitades.** Porque δ̂ = θ̂(máximo) − media **ya es un estadístico seleccionado**, y Bayes empírico supone una estimación no seleccionada. Se resolvió con `thinning.partir_tres`: un tercio elige, otro estima, otro evalúa. Así δ̂ es la ventaja de un brazo **ya fijado** y la contracción se le puede aplicar.
2. **Escribí la interpretación de la sensibilidad antes de ver los números**, y la contradecían. Queda anotado: es el fallo que la regla de evidencia §3 existe para evitar.

## Qué sigue — fase F

1. Dónde falla, en los dos niveles: qué experimentos pierde la contracción y qué los caracteriza.
2. Explicar: el régimen de la proporción (Chen y Lei), la dependencia parámetro-precisión (Chen), la calibración del paso 1.
3. Con esto, el enunciado del proyecto ya está casi completo y **es negativo en las dos decisiones**. Hay que escribirlo tal cual.

## Decisiones tomadas que no hay que volver a discutir

- **Marco:** oficio senior, no descubrimiento. El proyecto **no tiene tesis**; los hallazgos entran como pasos.
- **Criterio:** los métodos se juzgan por las decisiones que producen. Orden **medir → explicar → descartar**.
- **Dos métodos**, más el eje global/local. Un tercero exige decidirlo.
- **Exclusión jun-2013 a ene-2014**, verificada.
- **La validación va por partición hipergeométrica dentro del brazo** (*data thinning*, Neufeld y coautores JMLR 2024), **no** por la muestra de reserva del archivo: son experimentos distintos. Y **no** es *data fission*, que para la binomial no da partes independientes.
- **Spotify no es un competidor**: su posición es la referencia a batir (la regla «sin corregir») y su advertencia, la hipótesis que el resultado confirma o descarta.
- **Lo que se podrá concluir está acotado** a estos datos. No «Meta se equivoca».
- **El proyecto hermano no se abre** hasta que este esté terminado y publicado.

## Pendiente de verificar antes de citarse

Kohavi y coautores · Gelman y Carlin (2014) · Capen, Clapp y Campbell (1971) · Efron y Morris (1977) · DerSimonian-Laird · Paule-Mandel.

**No escribirlas en ningún entregable hasta comprobarlas.**

## Última revisión del estado del arte

**3 de octubre de 2026.** Nueve referencias en la tabla del README, todas con enlace verificado salvo las de la lista anterior. Siguiente revisión: antes de congelar el método, o si pasan dos meses.

## Entorno

```
./.venv/Scripts/python.exe   # creado y poblado; reconstruir con requirements.txt
```
