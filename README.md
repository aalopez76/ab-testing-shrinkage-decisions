# La maldición del ganador en pruebas A/B

Cuando un equipo elige la variante ganadora de un experimento, ¿cuánto de esa ventaja es real y cuánto es suerte? Y lo que importa de verdad: **¿corregirlo cambia lo que se lanza, y la decisión cambiada es mejor?**

Medido en 3,380 experimentos de la muestra exploratoria aleatorizados reales, con datos públicos que cualquiera puede volver a correr.

---

## 1. Qué pasa en la industria

Las empresas de tecnología deciden con experimentos. No con uno: **con miles simultáneos**. Cada cambio de producto, cada ajuste de un recomendador, cada rediseño pasa por una prueba A/B antes de lanzarse.

Y la mayoría de esas pruebas no encuentra nada. Las cifras publicadas por quienes dirigieron esas plataformas:

| Organización | Resultado | Fuente |
|---|---|---|
| Google y Bing | **10%–20%** de los experimentos producen resultados positivos | Kohavi y Thomke, *Harvard Business Review*, sep–oct 2017 ✓ |
| Microsoft | **un tercio** positivo y significativo · **un tercio** plano · **un tercio** negativo y significativo | Kohavi, keynote KDD 2015 ✓ (texto literal) |

Del keynote de KDD conviene citar la frase exacta, porque es más fuerte que su paráfrasis: *«la mayoría de los experimentos muestran que las funcionalidades no logran mover las métricas que fueron diseñadas para mejorar»*. Y sobre Bing añade, sin dar número: *«la tasa de éxito es menor»*.

Si solo una de cada cinco ideas funciona, encontrar la buena importa mucho. Y el método para encontrarla es casi siempre el mismo: **se elige la variante con el mejor resultado medido.**

## 2. Por qué eso falla, y no por falta de disciplina

Ahí está el problema, y es aritmético.

Cuando una prueba tiene **poca potencia** —pocos usuarios para el tamaño del efecto que busca—, la estimación de cada variante trae mucho ruido. Entonces ocurre algo que no es intuitivo:

> La única forma de que un efecto real pero pequeño destaque en una muestra chica es que **el ruido lo empuje por encima de su valor verdadero**.

Dicho al revés: **el solo hecho de destacar en una prueba sub-potenciada garantiza que la estimación está inflada.** No es un sesgo del analista ni un error de cálculo. Es una consecuencia de elegir el máximo entre cantidades ruidosas.

Se le llama **maldición del ganador**, y su costo es concreto: la mejora prometida al negocio no aparece. El equipo reporta «+8%», se lanza, y la métrica no se mueve. Con el tiempo eso erosiona la confianza en todo el sistema de experimentación — justo el sistema que debería ser la fuente de verdad.

## 3. Qué se está haciendo hoy: hay herramientas, y son muy nuevas

La herramienta común es el **Bayes empírico**: cuando se estiman muchas cantidades parecidas y cada estimación trae ruido, conviene acercar cada una a lo que dicen las demás. Al acercamiento se le llama **contracción** (*shrinkage*).

| Cuándo | Quién | Qué aporta | Estado |
|---|---|---|---|
| abr 2019 | Dimmery, Bakshy y Sekhon (**Facebook**) | Contracción para experimentos de varios brazos, 17 experimentos internos | ✓ |
| 2024 | Neufeld y coautores (**JMLR**) | **Data thinning**: dos partes independientes que suman la observación | ✓ |
| dic 2024 | Sudijono, Ejdemyr, Lal y Tingley (**Netflix**) | La decisión de lanzamiento como objetivo de optimización | ✓ |
| nov 2025 | Li | Contracción **local**: vecindarios en lugar del promedio global | ✓ |
| nov 2025 | Mudd y coautores (**Meta**) | La maldición del ganador de frente; evalúa MSE, sesgo y cobertura | ✓ |
| **dic 2025** | **Chen y Lei** | Contracción **binomial directa**, sin aproximación gaussiana; para proporciones y muestras pequeñas | ✓ |
| **mar 2026** | **Chen**, *Econometrica* 94(2), 305–340 | `close`: relaja el supuesto de independencia entre el parámetro y la precisión | ✓ |
| **abr 2026** | **Neufeld, Perry y Witten** | Revisión de la inferencia condicionada a la selección; «inferencia sobre un ganador» como caso central | ✓ |
| sep 2026 | **Spotify** | **Dice que no**: una previa mal calibrada puede empeorar las cosas | ✓ |

**Siete de nueve son de los últimos catorce meses.** Y la última convierte esto en una decisión y no en una receta: Spotify reconoce que la previa reduce el sesgo, pero advierte que mantenerla bien calibrada es extremadamente exigente y que **mal calibrada empeora** el resultado. Falla, dicen, cuando el historial mezcla distribuciones de efecto distintas, cuando cambian con el tiempo, y cuando no hay suficiente historia.

## 4. Lo que un equipo no puede resolver hoy

Métodos publicados en el último año y medio, con supuestos distintos, y dos empresas de referencia diciendo cosas opuestas. Meta y Netflix invierten en la infraestructura; Spotify la rechaza por escrito. Ambas posiciones son razonadas y no pueden ser correctas para todos.

Y toda la evidencia está medida **sobre datos internos**: diecisiete experimentos de Facebook, el historial de Netflix, los experimentos de Meta. Nadie fuera puede reproducirla ni comprobar si aplica a su caso.

**Por qué importa resolverlo bien:**

- **El costo de elegir mal no es simétrico.** Si la corrección sirve y no se usa, se dejan mejoras sobre la mesa. Si se usa mal, **se decide peor que no corrigiendo**. No es una herramienta que se adopte por si acaso.
- **Quien decida hoy no tiene en qué apoyarse** más que una discusión de autoridad entre dos empresas.
- **La confianza en el sistema es lo que está en juego.** Una plataforma de experimentación existe para que las decisiones no dependan de quién argumenta mejor; si entrega mejoras que no se materializan, pierde esa función.

Este proyecto no cierra la discusión. Aporta **un dato público, reproducible y verificable** donde hoy solo hay evidencia privada.

## 5. El problema que este proyecto resuelve

> **¿Cuál de las correcciones disponibles lleva a mejores decisiones de despliegue, cuánto mejora, y en qué condiciones conviene no usar ninguna?**

Desglosado en tres preguntas medibles:

1. **¿Cuánto se infla la variante ganadora?**
2. **¿Corregirlo cambia qué variante se despliega?**
3. **Cuando la cambia, ¿la nueva elección rinde mejor — y dónde no?**

Sobre datos **públicos**, con el modelo de ruido verificado antes de usarlo, y con la decisión evaluada en información que **no participó en tomarla**.

### El criterio, declarado antes de mirar

> **Los métodos se juzgan por las decisiones que producen, no por si cumplen sus propios supuestos.**

La alternativa es tentadora y está mal. Un método con supuestos impecables puede ser la elección equivocada si optimiza lo que no se paga —el error de estimación cuando lo que cuesta es la decisión. Y un método con un supuesto violado puede decidir mejor de todos modos: la robustez se mide, no se deduce.

De ahí el orden de trabajo, que es **medir → explicar → descartar**:

| Paso | Qué hace |
|---|---|
| **Medir** | Qué método elige mejor, evaluado fuera de muestra |
| **Explicar** | Los diagnósticos vienen después, para entender el resultado — no filtran candidatos de entrada |
| **Descartar** | Con la razón nombrada, y **no todas son del dato** |

Razones de descarte posibles, cada una con su lectura distinta:

| Razón | Ejemplo en este proyecto |
|---|---|
| **No responde la pregunta** | Netflix optimiza a nivel de programa; aquí la pregunta es qué variante elegir **dentro** de un experimento. Fuera por **alcance** |
| **La naturaleza del dato** | La aproximación gaussiana con proporciones de 1.5% y ~3 000 ensayos es donde Chen y Lei recomiendan la binomial directa |
| **Costo operativo** | Una implementación de referencia en otro lenguaje es un costo real: se declara, no se omite |
| **No sobrevive la comparación** | Pierde fuera de muestra. El descarte más limpio |
| **No es un método** | La posición de Spotify es una restricción operativa, no un competidor a implementar |

**Se implementan dos métodos, no todos:** la contracción estándar —lo que usa la industria, la referencia a batir o confirmar— y **una** alternativa. El eje global contra local se cruza encima. Más de dos no se termina, y un proyecto sin terminar no demuestra nada.

**El dominio es un medio digital, pero el problema no es de medios.** Es de cualquier organización que corra muchas pruebas pequeñas y se quede con la mejor.

## 6. Los datos, y por qué estos

**Upworthy Research Archive** — Matias, Munger, Aubin Le Quere y Ebersole, *Scientific Data* (2021) ✓. Público en OSF: <https://osf.io/jd64p/>. Cuatro CSV, ~128 MB.

Upworthy fue un medio digital que entre 2013 y 2015 probaba titulares e imágenes **como operación diaria**: para cada historia escribía varias versiones y las mostraba al azar, midiendo impresiones y clics. No es un experimento académico: es trabajo real que quedó guardado.

**Por qué este y no otro:** es el corpus público más grande de experimentos aleatorizados reales. Y lo decisivo — la aleatorización significa que **el efecto está identificado por diseño**. No hay que defender supuestos de identificación, así que todo el esfuerzo va a lo que el proyecto quiere demostrar: estimación y decisión.

**Escala, medida abriendo los archivos y no copiada de la documentación:**

```
MUESTRA EXPLORATORIA, tras la exclusión (de reports/results/01_panel.json)
  3,380 experimentos | 16,629 brazos | 58.8M impresiones
  2 a 14 brazos por experimento (media 4.92)
  mediana de 3,136 impresiones por brazo | tasa de clic 1.28%
  68 semanas | 295 A/A | 1,589 varían solo el titular

La exclusión deja fuera 1,493 de 4,873 experimentos (30.6%).
El confirmatorio se cuantificará al correrlo, una sola vez, con el método congelado.
```

**El régimen es exactamente el del problema.** Con una tasa base de 1.28% y una mediana de 3,136 impresiones por brazo, el error estándar típico de una medición es de **0.20 puntos porcentuales** — del orden del 16% de la señal que se quiere detectar. Poca potencia, de fábrica, 3,380 veces solo en el exploratorio, justo donde Gelman y Carlin advierten que la exageración se dispara.

La descomposición entre ruido y diferencia real **no se declara aquí**: la produce el paso 1, y la auditoría previa ya mostró que el modelo binomial subestima el ruido ~1.9×.

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

**Qué se hace.** En los ~295 experimentos A/A, la dispersión real entre brazos es cero. Entonces la varianza observada debe igualar el promedio de $v_{et}$, y la $Q$ de Cochran debe valer en promedio $K_e - 1$.

**Por qué importa.** Toda la contracción del paso 2 depende de $v$. Si $v$ está mal medido, el método da una respuesta precisa y equivocada.

**Qué pasa si falla.** Se dice, antes de usarlo. No se sigue como si nada.

Es un chequeo barato que casi nadie hace, y es la diferencia entre aplicar una fórmula y saber si sus insumos valen.

## Hallazgo de la auditoría previa (3-oct-2026): el modelo de ruido falla

Se corrió el diagnóstico del paso 1 **antes** de construir, y el resultado cambia el plan:

```
sobre 1 579 experimentos donde NINGÚN campo público varía entre brazos
  Q observada / grados de libertad  = 1.927     (debería ser ~1.00)
  mediana por experimento           = 1.442
  fracción con p < 0.05             = 0.256     (debería ser ~0.05)
```

La dispersión real entre brazos es **casi el doble** de lo que predice la fórmula binomial, de forma sistemática y no por unos pocos casos extremos.

**Dos explicaciones, y no son distinguibles con estos datos:**

1. **El modelo binomial subestima el ruido.** Las impresiones dentro de un brazo no son independientes —un mismo usuario puede ver varias, hay efectos de hora y de fuente de tráfico—, lo que infla la varianza real. Es el problema de datos agrupados, habitual en experimentación en línea.
2. **Esos experimentos no son realmente A/A.** Algo varió que no está en los campos públicos. Ya se filtraron los 1 619 que varían en `excerpt` y los 287 que varían en `lede`, pero podría quedar variación no registrada.

**Qué cambia en el método:**

- La contracción usa α = v/(v+τ²). Si `v` está subestimado ~1.9×, **α queda subestimado y el método contrae de menos.**
- Así que el paso 2 debe usar un `v` **corregido por un factor de diseño**, y la comparación debe incluir **`v` ingenuo contra `v` corregido** — porque esa es, exactamente, la pregunta de calibración.
- Y es una instancia medida de la advertencia de Spotify: el insumo de la previa está mal por un factor de dos.

**Cómo se reporta:** como paso, no como tesis. La no identificación entre las dos explicaciones se declara; no se elige la que convenga.

### Paso 2 — Contraer: dos métodos, dos destinos

**Qué se hace.**

$$\tilde\theta_{et} = (1-\alpha_{et})\,\hat\theta_{et} + \alpha_{et}\,\bar\theta_e, \qquad \alpha_{et} = \frac{v_{et}}{v_{et} + \tau^2}$$

La idea en una línea: **si el ruido pesa más que las diferencias reales, hazle más caso al promedio que a cada medición.**

**Con qué teoría.** Bayes empírico paramétrico (Efron y Morris; Morris) — *pendiente de verificar antes de citarse*.

**El detalle que importa.** Con $K_e$ entre 2 y 14 brazos, estimar $\tau^2$ **dentro de cada experimento** es usar un dato ruidoso para decidir cuánto confiar en datos ruidosos. Por eso $\tau^2$ se estima **en conjunto**, con los métodos del meta-análisis (Paule-Mandel, DerSimonian-Laird) o por máxima verosimilitud jerárquica — *pendientes de verificar*.

### Paso 3 — Hacia dónde se agrupa: todos, o los parecidos

**Qué se hace.** Dos variantes del paso 2:

- **Global:** un solo $\tau^2$ y un centro común a todos los experimentos.
- **Local:** $\tau^2$ y el centro se calculan sobre un **vecindario** — núcleo sobre `test_week` (68 semanas, mediana de 40 experimentos por semana) y, por separado, sobre similitud de titular.

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

### Paso 5 — Comparar decisiones, no estimaciones

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

### Paso 6 — Explicar el resultado

Recién aquí entran los diagnósticos, y su papel es **entender lo que pasó**, no elegir el método:

- **El régimen de la proporción.** Chen y Lei (dic-2025) muestran que el caso binomial no se comporta como el gaussiano y que con proporciones y muestras pequeñas conviene la binomial directa. Estos datos están en ese régimen: 1.28% y ~3,136 ensayos por brazo.
- **La dependencia entre parámetro y precisión.** La contracción estándar supone que el valor verdadero de una variante es independiente de cuántas impresiones recibió. Chen (*Econometrica*, mar-2026) muestra que ese supuesto suele fallar porque el tamaño de muestra puede seleccionar sobre el parámetro. En estos datos las impresiones fueron una decisión de la plataforma, no un sorteo entre experimentos. **Hay que medirlo controlando por periodo y tipo de experimento**, para no confundir dependencia estructural con deriva temporal.
- **La calibración**, del paso 1.

Ninguno decide qué método se usa; los tres explican por qué el que ganó, ganó.

### Paso 7 — Heterogeneidad (opcional, y solo al final)

En los 1,589 experimentos que varían solo el titular, el texto como covariable con DR-learner o DML. **Solo si los pasos 0 a 6 están cerrados.**

### Inferencia

- **El clúster es el experimento**, no el brazo. El bootstrap remuestrea experimentos.
- La variación entre las $S$ particiones se reporta **por separado** de la incertidumbre muestral: son dos fuentes distintas.
- **Desarrollo en el exploratorio (3,380 experimentos tras exclusión); confirmación en el confirmatorio sin haberlo tocado antes.** Esa disciplina viene en el diseño del archivo y se respeta.

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
| **Kohavi y Thomke**, *HBR* sep–oct 2017 | El 10–20% de éxito en Google y Bing | ✓ |
| **Kohavi**, keynote KDD 2015 | El tercio/tercio/tercio de Microsoft, con texto literal | ✓ |
| Gelman y Carlin (2014) | Error de tipo M / razón de exageración | *pendiente* |
| Dimmery, Bakshy y Sekhon (**Facebook**, 2019) | Contracción para varios brazos, 17 experimentos internos | ✓ |
| Neufeld y coautores (**JMLR** 2024) | **Data thinning** | ✓ |
| Sudijono, Ejdemyr, Lal y Tingley (**Netflix**, dic-2024) | Decisión de lanzamiento como optimización, a nivel de programa | ✓ |
| Li (nov-2025) | Bayes empírico **local** | ✓ |
| Mudd y coautores (**Meta**, nov-2025) | Maldición del ganador; evalúa MSE, sesgo y cobertura | ✓ |
| **Chen y Lei (dic-2025)** | Contracción **binomial directa**, sin gaussiano | ✓ |
| **Chen (*Econometrica* 94(2), mar-2026)** | `close`: relaja la independencia parámetro-precisión | ✓ |
| **Neufeld, Perry y Witten (abr-2026)** | Revisión de inferencia condicionada a la selección | ✓ |
| **Spotify (sep-2026)** | La objeción operativa a la previa | ✓ |
| Robertson y coautores (*Nature Human Behaviour*, 2023) | Usan el archivo para la pregunta de **contenido** | ✓ |
| Efron y Morris (1977); DerSimonian-Laird; Paule-Mandel; Capen, Clapp y Campbell (1971) | Bayes empírico clásico, dispersión, origen del término | *pendientes* |

**La posición, sin inflarla:** los métodos están publicados y en producción. Este proyecto no inventa ninguno. Elige entre ellos con evidencia, sobre datos que cualquiera puede descargar, en un problema donde hoy solo hay evidencia privada y dos posiciones encontradas.

**Antes de implementar:** leer la revisión de Neufeld, Perry y Witten (abr-2026). Existe precisamente para no elegir a ciegas entre estas opciones.

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
