# La maldición del ganador en pruebas A/B [PRUEBAS A/B, EL PROBLEMA OCULTO]

Cuando un equipo elige la variante ganadora de un experimento, ¿cuánto de esa ventaja es real y cuánto es suerte? Y lo que importa de verdad: **¿corregirlo cambia lo que se lanza, y la decisión cambiada es mejor?**[LAS EMPRESAS COMO AMAZON, UBER, DIDI, LABORATORIOS CLINICOS, EMPRESAS AUTOMOTICES Y MUCHOS OTROS SECTORES TOMANA DECISICONES SOBRE COMO PROMOCIONAR UN PRODUCTO Y PARA ELLO REALIZAN EXPERIMENTOS ONLINE U OFFICELINE PERO YA SEA DE UNA U OTRA FORMA LA CAMPAÑA, EL PRODUCTO U OTRA COSA ELEGIDO POR EL DISEÑO PROPROIO DE LAS PRUEBAS A/B INDICAN CUAL DESPLEGAR, SIN EMBARGO, ¿CUANTA DE ESA VENTAJA ES REAL Y CUÁNTO ES SUERTE Y LO QUE IMPORTA DE VERDAD:  ¿CORREGIRLO CAMBIA LO QUE SE LANZA, Y LA DECISIÓN CAMBIADA ES MEJOR? ]

Medido en 27 616 experimentos aleatorizados reales, con datos públicos que cualquiera puede volver a correr.[EN ESTE ESTUDIO CONSIDERAREMOS LOS DATOS PROPORCIONADOS POR ESTA EMPRESA PARA REALIZAR UN ANALISIS DE LO PLANTEADO REFERENCIANDO LAS ÚLTIMAS INVESTIGACIONES SOBRE EL TEMA]

---

## 1. Qué pasa en la industria[ANTECEDENTES]

Las empresas de tecnología deciden con experimentos. No con uno: **con miles simultáneos**. Cada cambio de producto, cada ajuste de un recomendador, cada rediseño pasa por una prueba A/B antes de lanzarse.[DIFRENTES EMPRESAS AL LANZAR UN PRODUCTO O SERVICIO, ELEGIR UN MEDICAMENTO, UNA PUBLICIDAD REQUIEREN ELEGIR LA MEJOR ESTRATEGIA PARA POSICIONAR LO MEJOR QUE SE PUEDA SU PRODUCTO O LIBERAR EL MEDICAMENTO QUE MAYOR BENEFICIO TRAIGA AL ENFERMO Y LA FORMA DE LLEVAR A CABO ESTO ES ATRAVÉS DE EXPERIMENTACIÓN EXPERIMENTACIÓN QUE REQUIERE MILES DE REPLICAS SIMULTANEAS DEL MISMO. CADA AJUSTE DE UN RECOMENDADOR, CADA REDISEÑO PASA POR UNA PRUEBA A/B ANTES DE LANZARSE.]

Y la mayoría de esas pruebas no encuentra nada. Las cifras publicadas por quienes dirigieron esas plataformas:[ACTUALMENTE LA MAYORIA DE ESTAS PRUEBA NO ENCUENTRAN ALGO. GOOGLE, BING Y MICROSOF HAN MOSTRADO CIFRAS SOBRE SUS EXPERIMENTOS: ]

| Organización | Resultado |
|---|---|
| Google y Bing | **10%–20%** de los experimentos producen resultados positivos |
| Microsoft | **un tercio** funciona · **un tercio** es neutro · **un tercio empeora** la métrica que pretendía mejorar |

Fuente: Kohavi y coautores, [plataforma de experimentación de Microsoft](https://exp-platform.com/Documents/2015-08OnlineControlledExperimentsKDDKeynoteNR.pdf). ✓

Si solo una de cada cinco ideas funciona, encontrar la buena importa mucho. Y el método para encontrarla es casi siempre el mismo: **se elige la variante con el mejor resultado medido.**

## 2. Por qué eso falla, y no por falta de disciplina [EL FALLO NO DICIPLINARIO]

Ahí está el problema, y es aritmético.

Cuando una prueba[DE QUE PRUEBA ESTAMOS HABLANDO] tiene **poca potencia** —pocos usuarios para el tamaño del efecto que busca—, la estimación de cada variante trae mucho ruido. Entonces ocurre algo que no es intuitivo:

> La única forma de que un efecto real pero pequeño destaque en una muestra chica es que **el ruido lo empuje por encima de su valor verdadero**.

Dicho al revés: **el solo hecho de destacar en una prueba sub-potenciada garantiza que la estimación está inflada.** No es un sesgo del analista ni un error de cálculo. Es una consecuencia de elegir el máximo entre cantidades ruidosas.

Se le llama **maldición del ganador**[QUIEN LA LLAMA ASÍ], y su costo es concreto: la mejora prometida al negocio no aparece. El equipo reporta «+8%», se lanza, y la métrica no se mueve. Con el tiempo eso erosiona la confianza en todo el sistema de experimentación — justo el sistema que debería ser la fuente de verdad.

## 3. Qué se está haciendo hoy al respecto [ACTUALIDAD]

Esto no es una curiosidad académica: se está resolviendo ahora mismo, en producción.

En **marzo de 2026**, un equipo de **Meta Platforms** publicó [*Breaking the Winner's Curse with Bayesian Hybrid Shrinkage*](https://arxiv.org/pdf/2603.12867) ✓. Su diagnóstico, textual:

> *«La adopción generalizada de pruebas A/B ha introducido una "maldición del ganador" omnipresente: los experimentos seleccionados para lanzamiento exhiben con frecuencia estimaciones sesgadas al alza e intervalos de confianza inválidos. Este sesgo de selección lleva a proyecciones de impacto demasiado optimistas y socava la toma de decisiones, particularmente en regímenes de baja potencia.»*

Su solución es **Bayes empírico**: en lugar de creerle a cada estimación por sí sola, se las acerca a lo que dicen las demás. Y su aporte específico es un factor de contracción **local**, propio de cada experimento, en contraste con aplicar la misma corrección a todos.

Ese eje —**contraer hacia todos, o solo hacia los parecidos**— es el mismo que explora [Li (2025)](https://arxiv.org/abs/2511.21282) ✓ para experimentos a lo largo del tiempo.

## 4. Qué queda sin responder[EL PROBLEMA POCO TRATADO]

Dos cosas, y de ahí sale este proyecto.

**Primera: nadie comprueba si la decisión mejora.** El trabajo de Meta se evalúa con error cuadrático medio, sesgo y cobertura de los intervalos. Busqué la palabra *regret* en el paper: **no aparece ni una vez.** Son métricas de **estimación**, y estimar mejor no implica decidir mejor — son preguntas distintas y la segunda es la que paga la nómina.

**Segunda: está medido sobre datos que nadie más puede ver.** La validación de Meta usa sus experimentos internos. Nadie fuera de Meta puede reproducirla, cuestionarla ni extenderla.

## 5. El problema que este proyecto resuelve

> Con miles de experimentos sub-potenciados y la costumbre de elegir el máximo:
> **(a)** ¿cuánto se infla la variante ganadora?
> **(b)** ¿corregir esa inflación cambia qué variante lanzarías?
> **(c)** cuando la cambia, ¿la nueva elección rinde mejor — y dónde no?

Sobre datos **públicos**, con la decisión validada en información que **no participó en tomarla**.

**El dominio es un medio digital, pero el problema no es de medios.** Es de cualquier organización que corra muchas pruebas pequeñas y se quede con la mejor: comercio electrónico, buscadores, plataformas de contenido, bancos probando ofertas. Según las cifras del punto 1, eso es la industria tecnológica entera.

## 6. Los datos, y por qué estos

**Upworthy Research Archive** — Matias, Munger, Aubin Le Quere y Ebersole, *Scientific Data* (2021) ✓. Público en OSF: <https://osf.io/jd64p/>. Cuatro CSV, ~128 MB.

Upworthy fue un medio digital que entre 2013 y 2015 probaba titulares e imágenes **como operación diaria**: para cada historia escribía varias versiones y las mostraba al azar, midiendo impresiones y clics. No es un experimento académico: es trabajo real que quedó guardado.

**Por qué este y no otro:** es el corpus público más grande de experimentos aleatorizados reales. Y lo decisivo — la aleatorización significa que **el efecto está identificado por diseño**. No hay que defender supuestos de identificación, así que todo el esfuerzo va a lo que el proyecto quiere demostrar: estimación y decisión.

**Escala, medida abriendo los archivos y no copiada de la documentación:**

```
confirmatorio   22 743 experimentos | 105 551 brazos | 376.5M impresiones
exploratorio     4 873 experimentos |  22 666 brazos |  81.0M impresiones
reserva          conjunto disjunto, apartado para un estudio meta-científico con COS

2–14 brazos por experimento (media 4.65) | 121 semanas | ene-2013 a abr-2015
mediana 3 119 impresiones por brazo      | tasa de clic global 1.52%
```

**El régimen es exactamente el del problema.** Con esos números, el error estándar de un brazo ronda **0.23 puntos** sobre una base de 1.52%, mientras la dispersión observada entre brazos es 0.35. Es decir: **el 43% de la variación entre brazos es puro ruido.** Baja potencia, de fábrica, 27 616 veces.

**Qué varía entre brazos** (exploratorio):

| Varía | Experimentos |
|---|---|
| Solo el titular | 2 307 |
| Solo la imagen | 1 426 |
| Ambos | 300 |
| Ninguno de los dos registrado | **840** ← pruebas A/A de facto |

Esos 840 valen oro: sin variación real, la dispersión verdadera entre brazos es cero por construcción. Son una distribución nula gratis para comprobar el modelo de ruido.

---

## 7. Cómo se resuelve, paso a paso

Cada paso dice **qué se hace**, **con qué teoría** y **qué podría salir mal si no se hiciera**.

### Notación

Experimento $e$, brazos $t = 1 \dots K_e$.

| Símbolo | Qué es |
|---|---|
| $n_{et}$, $c_{et}$ | impresiones y clics del brazo |
| $\hat\theta_{et} = c_{et}/n_{et}$ | tasa observada |
| $v_{et} = \hat\theta_{et}(1-\hat\theta_{et})/n_{et}$ | su varianza binomial |
| $\tau^2$ | dispersión **real** entre brazos — lo que hay que estimar |

### Paso 0 — Comprobar que el sorteo fue un sorteo

**Qué se hace.** Una prueba χ² de impresiones por brazo contra asignación uniforme, experimento por experimento.

**Qué podría salir mal.** El equipo del archivo reportó en junio de 2024 ✓ que una mala configuración de la caché de Cloudflare, el 25 de junio de 2013, hizo que durante meses se mostrara **una sola variante** hasta que la caché expiraba. Afecta a ~22% de las pruebas. Analizarlas como si fueran aleatorias contamina todo lo que venga después.

**Qué encontré.** No me fié de la marca del archivo: lo reproduje. Coincide mes a mes.

```
feb–may 2013   2–5%     línea base
jun 2013      21.8%     arranca (el glitch fue el día 25)
jul–dic 2013  56–88%    ventana del fallo
ene 2014      15.1%     lo arreglan a mitad de mes
feb 2014+     0.0–0.5%  tasa nominal; el resto del archivo está limpio
```

Se excluye **jun-2013 a ene-2014**. La regla está en `.claude/rules/datos.md` y vive en una sola función del código.

### Paso 1 — Comprobar que el ruido está bien medido

**Qué se hace.** En los ~840 experimentos A/A, la dispersión real entre brazos es cero. Entonces la varianza observada debe igualar el promedio de $v_{et}$, y la $Q$ de Cochran debe valer en promedio $K_e - 1$.

**Por qué importa.** Toda la contracción del paso 2 depende de $v$. Si $v$ está mal medido, el método da una respuesta precisa y equivocada.

**Qué pasa si falla.** Se dice, antes de usarlo. No se sigue como si nada.

Es un chequeo barato que casi nadie hace, y es la diferencia entre aplicar una fórmula y saber si sus insumos valen.

### Paso 2 — Contraer cada brazo hacia su experimento

**Qué se hace.**

$$\tilde\theta_{et} = (1-\alpha_{et})\,\hat\theta_{et} + \alpha_{et}\,\bar\theta_e, \qquad \alpha_{et} = \frac{v_{et}}{v_{et} + \tau^2}$$

La idea en una línea: **si el ruido pesa más que las diferencias reales, hazle más caso al promedio que a cada medición.**

**Con qué teoría.** Bayes empírico paramétrico (Efron y Morris; Morris) — *pendiente de verificar antes de citarse*.

**El detalle que importa.** Con $K_e$ entre 2 y 14 brazos, estimar $\tau^2$ **dentro de cada experimento** es usar un dato ruidoso para decidir cuánto confiar en datos ruidosos. Por eso $\tau^2$ se estima **en conjunto**, con los métodos del meta-análisis (Paule-Mandel, DerSimonian-Laird) o por máxima verosimilitud jerárquica — *pendientes de verificar*.

### Paso 3 — Decidir hacia dónde se agrupa: todos, o los parecidos

**Qué se hace.** Dos variantes del paso 2:

- **Global:** un solo $\tau^2$ y un centro común a todos los experimentos.
- **Local:** $\tau^2$ y el centro se calculan sobre un **vecindario** — núcleo sobre `test_week` (121 semanas, mediana de 40 experimentos por semana) y, por separado, sobre similitud de titular.

**Con qué teoría.** Es el contraste que plantea Li (2025) ✓, y es el aporte específico del método de Meta ✓.

**La disciplina.** El ancho del vecindario se **declara de antemano** y se reporta la sensibilidad al moverlo. **Nunca se elige mirando la mitad de evaluación** — hacerlo convertiría la validación en un ajuste.

### Paso 4 — Medir la inflación sin hacer trampa

**Qué se hace.** De las $n$ impresiones de cada brazo se toman $m$ para una mitad A y el resto para una mitad B; los $c$ clics se reparten $\text{Hipergeométrica}(n, c, m)$.

**Con qué teoría, y aquí casi me equivoco de nombre.** Esto es **data thinning** para distribuciones cerradas bajo convolución —la binomial entre ellas— (Neufeld y coautores, JMLR 2024): produce dos partes **independientes** que suman la observación original. Es exacto, no una aproximación.

Iba a llamarlo *data fission* (Leiner, Duan, Tibshirani y Ramdas). Habría sido incorrecto: para distribuciones distintas de la gaussiana y la Poisson, *data fission* produce componentes **que no son independientes**, y la independencia es justo lo que necesitamos aquí.

**El estimando principal:**

$$\text{Inflación} = \mathbb{E}\big[\hat\theta^{A}_{e,t^*} - \hat\theta^{B}_{e,t^*}\big], \qquad t^* = \arg\max_t \hat\theta^{A}_{et}$$

El brazo se elige con A; se mide con B, que no participó en elegirlo.

**Por qué no sirve la muestra de reserva del archivo.** Parecería el lugar natural para validar. No lo es: la reserva son **experimentos distintos**, no más datos de los mismos. Lo comprobé en la documentación oficial antes de construir nada sobre esa suposición.

### Paso 5 — Comprobar si la decisión mejora, que es la pregunta real

**Qué se hace.** Cuatro reglas, todas eligiendo con A y evaluadas en B:

| | Regla |
|---|---|
| **R0** | brazo al azar — la referencia que hay que ganar |
| **R1** | $\arg\max \hat\theta$ — crudo |
| **R2** | $\arg\max \tilde\theta$ — contraído global |
| **R3** | $\arg\max \tilde\theta$ — contraído local |

Tres métricas: **valor** (lo que rindió el brazo elegido en B), **arrepentimiento** (contra el mejor brazo según B) y la **curva por presupuesto** (si solo se puede lanzar en $K$ de $N$ experimentos).

**Y la parte obligatoria: dónde falla.** En qué fracción de experimentos R2 y R3 quedan *peor* que R1, y qué los caracteriza. Contraer mejora el conjunto y perjudica a casos concretos; omitir cuáles sería deshonesto.

**Criterio de éxito, declarado antes de mirar.** Que la regla contraída gane **en valor fuera de muestra**. No que reduzca el error de estimación — eso es lo que ya mide Meta. Si no gana, se reporta que no gana.

### Paso 6 — Heterogeneidad (opcional, y solo al final)

En los 2 307 experimentos que varían solo el titular, el texto como covariable con DR-learner o DML. **Solo si los pasos 0 a 5 están cerrados.**

### Inferencia

- **El clúster es el experimento**, no el brazo. El bootstrap remuestrea experimentos.
- La variación entre las $S$ particiones se reporta **por separado** de la incertidumbre muestral: son dos fuentes distintas.
- **Desarrollo en el exploratorio (4 873); confirmación en el confirmatorio (22 743) sin haberlo tocado antes.** Esa disciplina viene en el diseño del archivo y se respeta.

---

## 8. Qué se entrega

**Un análisis escrito de 2 000 a 3 000 palabras**, con esta estructura, y el repositorio como respaldo reproducible.

La extensión es un límite, no una meta: es lo que impide que el trabajo se estire sin fin.

1. El problema de industria y su costo (secciones 1–2 de este README)
2. Qué se hace hoy y qué queda abierto (3–4)
3. Los datos y por qué estos (6)
4. El recorrido, paso por paso, con lo que podría haber salido mal en cada uno (7)
5. El resultado: las tres cifras de la sección 5
6. **Dónde falla**, con su caracterización
7. Límites

**Terminado significa:**

- [ ] Tubería reproducible de extremo a extremo, desde la descarga del OSF.
- [ ] Paso 0 con la tabla mes a mes reproducida por el código del repo.
- [ ] Paso 1 con el veredicto sobre $v$, sea cual sea.
- [ ] Las tres cifras: inflación, frecuencia de cambio de decisión, valor fuera de muestra.
- [ ] La sección de dónde falla, escrita.
- [ ] Método desarrollado en exploratorio y confirmado en confirmatorio.
- [ ] El escrito, dentro de la extensión.

## Límites declarados

- La asignación es por impresión, no por usuario: no hay efectos individuales ni segmentación por persona.
- Datos de 2013–2015. Es el archivo público más grande de experimentos reales; para una demostración metodológica la fecha no cambia las conclusiones, pero es visible y se declara.
- Solo se usa el ~78% del archivo que pasa el diagnóstico del paso 0.
- El dominio son titulares de medios. La transferencia se argumenta por **estructura** —muchas pruebas sub-potenciadas, decisión por selección del máximo— no por mecanismo.
- **No se deriva ningún método.** Todos son publicados y citados. Lo que aporta el proyecto es aplicarlos con cuidado a datos públicos y llevar la pregunta hasta la decisión.

## Dónde se ubica en la literatura

| Trabajo | Qué aporta | Estado |
|---|---|---|
| Kohavi y coautores, plataforma de Microsoft | Las cifras de cuántos experimentos funcionan | ✓ |
| Mudd, Zaidi, Friedberg, Gorbachev, Choubey y Nassif (**Meta, mar-2026**) | Bayes empírico con contracción local contra la maldición del ganador; evalúa MSE, sesgo y cobertura | ✓ |
| Li (2025), arXiv 2511.21282 | Bayes empírico **local**: agrupar hacia comparables cercanos | ✓ |
| Neufeld y coautores (JMLR 2024) | **Data thinning** para distribuciones cerradas bajo convolución | ✓ |
| Matias y coautores (2021) + actualización jun-2024 | El archivo y su fallo de aleatorización | ✓ |
| Robertson y coautores (2023), *Nature Human Behaviour* | Usan el archivo para la pregunta de **contenido**, no de decisión | ✓ |
| Efron y Morris; Morris; Andrews, Kitagawa y McCloskey; Paule-Mandel; DerSimonian-Laird | Bayes empírico clásico, inferencia en ganadores, estimación de $\tau^2$ | *pendientes de verificar* |

**La posición, sin inflarla:** el método está publicado y en producción en Meta. Este proyecto no lo inventa. Pregunta lo que ese trabajo no pregunta —si la decisión mejora— y lo hace sobre datos que cualquiera puede descargar y volver a correr.

## Alcance: qué queda fuera, explícitamente

- **DiD y control sintético.** Los datos son aleatorizados; no hay nada que identificar por tendencias paralelas.
- **Tratamiento continuo.** No hay dosis en estos datos y no se inventa una. Ese es el proyecto hermano `../dose-selection-phase2`.
- **Qué tipo de titular funciona mejor.** Ya lo contestó Robertson y coautores (2023).
- **Derivar estimadores.**
- **Documentos de gobierno.** Este README crece y nada más; el estado vive en `HANDOFF.md`, corto.

## Entorno

**Todo se desarrolla dentro del entorno virtual del proyecto.** Sin excepción: es lo que evita conflictos de versiones con otros proyectos y con el Python global de la máquina.

```bash
python -m venv .venv                                        # solo la primera vez
./.venv/Scripts/python.exe -m pip install -r requirements.txt
./.venv/Scripts/python.exe -m pytest -q                      # así se corre todo
```

El entorno **ya está creado y poblado** (Python 3.11.9). `requirements.txt` fija los rangos. `.venv/` está ignorado por git.

Hay un hook `PreToolUse` que **bloquea invocar el Python o pip globales** antes de que corran, porque esta máquina tiene un Python 3.11.9 en el PATH y un `python script.py` por descuido usaría el intérprete equivocado. Las únicas excepciones son `python -m venv` y `python --version`, necesarias para crear el entorno.
