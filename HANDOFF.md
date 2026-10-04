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

## Qué sigue — fase E

1. `src/wcab/shrinkage/neighborhood.py` — τ² y centro sobre un vecindario: núcleo en `semana` y, por separado, similitud de titular.
2. Añadir la alternativa de método. Con el hallazgo de D, la candidata con sentido es la que rompe la uniformidad de α.
3. Volver a correr `04_decisiones.py` con las seis configuraciones.

**Decisión pendiente que D obliga a tomar:** si contraer hacia el centro del propio experimento no puede reordenar, el eje «global» del plan hay que redefinirlo como *hacia el promedio de todos los experimentos* (que sí difiere de la media interna) en lugar de *hacia la media del propio experimento*. Hay que escribirlo antes de implementar.

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
