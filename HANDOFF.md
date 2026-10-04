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

## Qué sigue — fase B

1. `src/wcab/diagnostics/noise.py` — la calibración contra los A/A, como módulo.
2. `scripts/03_calibracion.py` — **el veredicto sobre `v`**, con el factor de diseño.
3. Decidir, con ese número, si el paso 2 usa `v` ingenuo, corregido, o ambos en comparación.

La auditoría previa ya anticipó el resultado (Q/gl = 1.927), pero hay que producirlo con el código y sobre el panel con exclusión aplicada, que es un universo distinto del que usé en la auditoría.

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
