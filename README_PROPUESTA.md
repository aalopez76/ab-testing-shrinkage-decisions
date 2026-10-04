# Contexto del proyecto

El comercio digital y los sectores que operan como él —medios, suscripción, marketplaces— tienen que decidir continuamente qué desplegar: un anuncio, un descuento, una promoción, un titular, un orden de resultados. Hay varios métodos para tomar esa decisión, y cada uno sirve para una forma distinta de problema:

| Método | Para qué sirve |
|---|---|
| **Pruebas A/B** | Comparar versiones completas cuando se puede repartir usuarios al azar |
| **Bandidos multibrazo** (*Thompson sampling*) | Muchas variantes y mucho tráfico: mueve el tráfico hacia la que va ganando, sin esperar a cerrar la prueba |
| **Intercalado** (*interleaving*) | Sistemas de ranking: mezcla los resultados de dos algoritmos dentro de la misma búsqueda del mismo usuario |
| **Pruebas de conmutación** (*switchback*) | Marketplaces y sistemas con oferta compartida: aleatoriza región y franja horaria en lugar de usuarios |
| **Métodos cuasiexperimentales** (diferencias en diferencias, control sintético, experimentos geográficos) | Cuando no se puede aleatorizar y solo hay datos de comportamiento |

Aunque existen todos esos, **las pruebas A/B son el estándar de la industria**, por tres razones concretas: establecen causalidad —no correlación— porque el reparto es al azar; son sencillas de iterar, porque comparar dos versiones completas no exige rediseñar el sistema; y escalan, porque las plataformas digitales ya tienen el volumen de tráfico que el método necesita. Por eso son el procedimiento con el que la industria digital decide hoy qué desplegar.

El funcionamiento es simple: se lanzan varias versiones de una propuesta, se mide cuál rinde mejor —en atracción de clientes, retención, gasto, tasa de clics, lo que el negocio persiga— y se despliega la ganadora.

## El problema

**La variante ganadora casi nunca rinde lo que prometió.** Parte de su ventaja era mérito y parte fue suerte —ruido—, y la suerte no se repite al desplegar. Es un fenómeno conocido: se le llama **la maldición del ganador**, y aparece siempre que se elige el máximo de varias mediciones ruidosas.

## La corrección que se propone, y quién hace qué

La corrección es la **contracción de Bayes empírico**: no creerse del todo el resultado del ganador y acercarlo al promedio del grupo, en una proporción que depende de cuánto ruido tiene la medición.

No es una técnica nueva ni de nadie en particular. Charles Stein la demostró en **1956**, James y Stein publicaron el estimador explícito en 1961, Herbert Robbins le dio el nombre de «Bayes empírico» y Efron y Morris la desarrollaron en los setenta. **Tiene setenta años.**

Lo que es reciente —y lo que crea la decisión— es que los equipos de experimentación de las grandes plataformas están publicando activamente sobre llevarla a producción, **y no coinciden**:

| Quién | Qué publicó | Postura |
|---|---|---|
| **Meta** — [Coey y Hung](https://arxiv.org/abs/2210.03905) | *Empirical Bayes Selection for Value Maximization*: usar la contracción para **seleccionar**, con cotas de arrepentimiento demostradas y código público | A favor, con teoría |
| **Meta** — [Mudd, Friedberg, Gorbachev, Nassif y Zaidi](https://arxiv.org/abs/2511.06318) | *Bayesian Hybrid Shrinkage* (BHS): añade factores de contracción **locales por experimento** para reducir la sensibilidad a la elección de previa | A favor, propuesta de 2025 |
| **Amazon, MIT y Stanford** — [Abadie, Agarwal, Imbens, Jia, McQueen, Stepaniants y Torres](https://arxiv.org/abs/2306.13681) | *Estimating the Value of Evidence-Based Decision Making*: las reglas de decisión basadas en significancia «pueden dejar valor sin realizar y, en algunos casos, generar valor esperado negativo» | A favor de corregir la regla de decisión |
| **Spotify** — [ingeniería](https://engineering.atspotify.com/2026/9/why-spotify-is-not-using-bayesian-a-b-testing) | *Why Spotify Is Not Using Bayesian A/B Testing*: las ventajas atribuidas «solo se sostienen bajo configuraciones específicas y exigentes» que rara vez vienen por defecto | **En contra, por escrito** |

**Dos cosas que conviene no exagerar, y que este documento no exagera.** Primero: BHS es una propuesta presentada a congreso en 2025, no un sistema de producción documentado — el artículo describe cómo se *implementaría* sobre la infraestructura existente, no que esté desplegado. Segundo: **este proyecto no implementa BHS.** BHS añade factores locales por experimento; aquí se evalúa la versión estándar, con un único peso estimado en conjunto. Es deliberado: antes de añadir la capa local de Meta hay que saber si la versión básica aporta algo, y eso es lo que aún no estaba medido en datos públicos.

## La decisión, y por qué cuesta

Un equipo que hoy quiera corregir la maldición del ganador tiene tres opciones, y ninguna buena:

1. **Adivinar.**
2. **Seguir a la plataforma más grande** y suponer que su caso es el suyo.
3. **Invertir el trimestre** en construirla para averiguarlo.

Y equivocarse no es gratis en ninguna dirección: adoptar la corrección es infraestructura y cambia cómo se reporta cada resultado al negocio, mientras que **hay un régimen en el que corregir decide peor que no corregir nada**.

## Lo que entrega este proyecto

**La cuarta opción:** cuatro comprobaciones que un equipo corre sobre su propio histórico en un día, con el umbral y la consecuencia de cada una, y que devuelven la respuesta para su caso antes de comprometer el trimestre.

No es un «depende». Dos de las cuatro dan respuestas duras, y una de ellas es un **no algebraico** que ninguna cantidad de datos puede revertir.

Esto importa porque adoptar el método implica **dos cosas distintas que suelen confundirse**:

1. **El número que se reporta** al negocio — la mejora que prometes.
2. **La variante que se elige** desplegar — la decisión.

Si se adopta esperando decidir mejor y solo arregla el número, el trimestre se gastó en lo que no era.

## Qué representan los datos

Este proyecto **analiza con datos reales un escenario hipotético, pero muy parecido al que enfrentan hoy los sectores industriales digitales.** La distinción merece precisión, porque es de lo que depende que el resultado sirva.

No son los datos de ninguna empresa que esté tomando esta decisión hoy, y no pretenden serlo. Lo que reproducen no es el dato, **es el procedimiento**: una organización que lanza varias versiones de una propuesta, reparte el tráfico al azar entre ellas, mide una tasa de conversión y despliega la ganadora. Ese es el mismo bucle que corre hoy un equipo de comercio digital.

Y es la estructura de ese bucle —no el sector, ni la métrica, ni el año— la que determina si la corrección funciona. Por eso **lo que transfiere es el procedimiento y sus umbrales; los números concretos, no.**

Resultados y recomendaciones sobre cuatro áreas:

- **Calibración del ruido:** ¿está bien medida la varianza de la que depende todo el método?
- **Capacidad de reordenar:** ¿puede la corrección cambiar siquiera la decisión, dado el diseño del experimento?
- **Independencia previa:** ¿el supuesto central del método se sostiene en estos datos?
- **Régimen de la aproximación:** ¿qué versión del método corresponde?

El código de ingesta, construcción del panel y los diagnósticos está en [`src/wcab/`](src/wcab/). Los scripts reproducibles que generan cada cifra citada, en [`scripts/`](scripts/). Las cifras crudas que respaldan este documento, en [`reports/results/`](reports/results/).

**Lo que este proyecto no tiene, y no voy a inventar:** no hay SQL —el procesamiento es Python sobre CSV planos— ni panel interactivo. Las secciones del informe que pedirían un diagrama entidad-relación o un dashboard no aplican y se marcan como tales.

---

# Estructura de los datos y comprobaciones iniciales

Los datos son el **Upworthy Research Archive** ([Matias, Munger, Aubin Le Quéré y Ebersole, *Scientific Data* 8:195, 2021](https://www.nature.com/articles/s41597-021-00934-7)), descargable de [OSF](https://osf.io/jd64p/) con licencia abierta. Upworthy era un medio digital estadounidense que probaba titulares de forma sistemática antes de publicar: a cada visitante le mostraba una variante distinta del mismo artículo y medía los clics.

Dos archivos planos, sin estructura relacional:

| | `upworthy-exploratory.csv` | `upworthy-confirmatory.csv` |
|---|---|---|
| Filas (variantes) | 31 580 | 149 187 |
| Experimentos tras exclusión | 3 380 | **15 787** |
| Variantes tras exclusión | 16 629 | **77 446** |
| Impresiones | 58 769 384 | **273 495 317** |
| Clics | 749 878 | **3 492 259** |
| Tasa de clic | 1.28% | 1.28% |
| Variantes por experimento | 2 a 14 (mediana 5) | 2 a 20 (mediana 5) |
| Rango de fechas | may-2013 a abr-2015 | may-2013 a abr-2015 |

Columnas relevantes: `clickability_test_id` (el experimento), `headline`, `excerpt`, `lede`, `eyecatcher_id` (la imagen), `impressions`, `clicks`, `created_at`, `test_week`.

El archivo **viene partido de fábrica** en una muestra exploratoria y una confirmatoria. Los autores lo diseñaron así para que un investigador pueda fijar su método en la primera y confirmarlo en la segunda. Este proyecto usa esa partición exactamente para eso.

## Por qué estos datos sirven, aunque no sean los datos ideales

Los datos ideales serían los del propio equipo: su plataforma, su métrica, su tráfico. **Nadie publica eso.** El argumento no es que estos sean los datos, sino que **tienen las seis características estructurales que el problema exige**:

| Lo que el problema exige | Por qué es imprescindible | Qué aporta este archivo |
|---|---|---|
| Aleatorización real | Sin ella, el efecto de selección se confunde con sesgo de asignación | 19 167 experimentos aleatorizados |
| Varias variantes por experimento | La maldición del ganador vive en el **máximo** sobre variantes | mediana 5, hasta 20 |
| Muchos experimentos | Para estimar la dispersión **entre** ellos, que es el denominador del método | 15 787 |
| Experimentos A/A | Vara **independiente** para auditar el modelo de ruido | 1 279 en el confirmatorio |
| Partición previa | Para congelar el método y confirmarlo sin contaminación | incluida por los autores |
| Precisión heterogénea | Para que el peso de contracción pueda variar | impresiones p99/p01 = 7.1 |

## Comprobaciones iniciales

**1. La aleatorización falló durante meses, y el archivo público no lo marca.**

En junio de 2024 los autores publicaron una corrección: una mala configuración de caché de Cloudflare, el 25 de junio de 2013, hizo que durante meses se mostrara una sola variante. Afecta a ~22% de las pruebas y desaconsejan usarlas para inferencia causal. **Los CSV públicos no traen la columna que las identifica.**

Se verificó desde cero con una prueba de bondad de ajuste sobre las impresiones por variante. Reproduce el fallo mes a mes:

| Mes | Experimentos con reparto anómalo |
|---|---|
| jun-2013 | 22.3% |
| dic-2013 | **86.4%** |
| ene-2014 | 11.0% |
| feb-2014 en adelante | 0.0% a 0.9% |

Se excluye la ventana del 2013-06-01 al 2014-02-01: **6 956 de 22 743 experimentos fuera (30.6%)**. El periodo conservado corre a la tasa de anomalía que se esperaría por azar.

**2. El modelo de ruido no describe estos datos.**

Toda contracción depende de la varianza de cada medición. El archivo ofrece una vara independiente: los experimentos donde **nada varía entre variantes**, donde la diferencia verdadera es cero por construcción. La dispersión observada debería igualar la calculada. No lo hace:

| | Exploratorio | Confirmatorio |
|---|---|---|
| Experimentos A/A | 295 | 1 279 |
| *Q* de Cochran / grados de libertad | **1.940** | **1.927** |
| Fracción con p < 0.05 (debería ser ~0.05) | 0.251 | 0.258 |

El modelo binomial subestima el ruido cerca del doble, y **replica en las dos muestras**. Dos explicaciones son compatibles con esto —impresiones no independientes, o variación en campos que el archivo no publica— y **no son distinguibles** con estos datos. Ambas quedan declaradas.

*No aplica: diagrama entidad-relación. Son dos archivos planos sin claves foráneas.*

---

# Resumen ejecutivo

## Lo esencial

**La contracción de Bayes empírico corrige la cifra que le reportas al negocio, no cuál variante lanzas.** Sobre 15 787 experimentos aleatorizados, con el método congelado antes de ver la muestra confirmatoria, reduce el error de estimación un **24.0%** y deja la decisión estadísticamente donde estaba.

Tres cosas que un responsable de experimentación debería llevarse:

1. **La maldición del ganador es real y grande.** La variante ganadora promete 1.551% y entrega 1.314%: una **sobreestimación del 18.5% relativo**. Si tu equipo reporta el resultado del ganador sin corregir, infla sistemáticamente lo que promete.

2. **Corregirla no mejora la elección, y en un caso ni puede.** Si tus variantes reciben tráfico parejo —como ocurre por diseño en la mayoría de las plataformas— la corrección es una transformación monótona del estimador y **conserva el orden**. Es una imposibilidad algebraica, no un problema de implementación.

3. **En el régimen equivocado, empeora la elección de forma medible.** Cuando se aplica a toda la cartera, la corrección pierde en las 40 particiones evaluadas (−0.0556 pp, IC 95% [−0.0619, −0.0493]). El motivo es diagnosticable en tres líneas de código, y el procedimiento lo detecta antes de adoptar nada.

| El resultado, replicado | Exploratorio (3 380 exp.) | Confirmatorio (15 787 exp.) |
|---|---|---|
| Inflación del ganador | 0.236 pp | **0.237 pp** |
| Error cuadrático medio | **−24.0%** | **−24.0%** |
| Correlación de orden con lo realizado | +0.3608 → +0.3662 | +0.3601 → +0.3656 |
| Ganancia realizada al 5% de presupuesto | 1.073 → 1.029 pp | 1.086 → 1.033 pp |

La muestra confirmatoria es **4.7 veces más grande y no se tocó durante el desarrollo**. El método se congeló en [`reports/results/METODO_CONGELADO.json`](reports/results/METODO_CONGELADO.json) con fecha, commit de git y criterio de éxito declarado, y se corrió **una sola vez**.

*Pendiente: figura con la curva de ganancia realizada por presupuesto para las cuatro reglas. Las cifras están en [`reports/results/07_resultado.json`](reports/results/07_resultado.json); el gráfico no está hecho.*

---

# Los cuatro diagnósticos en detalle

Cada uno decide algo concreto antes de gastar el trimestre, y cada uno viene de la literatura actual.

## 1. Calibración del ruido: ¿está bien medida tu varianza?

**Decide:** si la varianza está mal medida, el peso de contracción sale mal y todo lo que venga después es ruido. Esto se arregla primero o no se sigue.

* **El modelo de ruido se rechaza, y replica.** *Q*/gl = 1.940 en el exploratorio sobre 295 experimentos A/A y 1.927 en el confirmatorio sobre 1 279. El 25.8% de los A/A sale significativo cuando debería ser el 5%.

* **La consecuencia es cuantitativa, no retórica.** Con el factor mal aplicado, el peso de contracción medio salta de 0.43 a 0.87 y la conclusión se invierte. Lo comprobé a mi costa (ver *Supuestos y advertencias*).

* **El factor de diseño no transfiere entre niveles.** El 1.94 se midió para comparaciones **entre variantes** dentro de un experimento. Aplicado a la ganancia **entre experimentos** fabrica un resultado falso. La referencia correcta es una covarianza que no usa la varianza en absoluto —Cov(ganancia estimada, ganancia realizada) estima la dispersión verdadera— y da ~1.09 para ese nivel.

* **La vara independiente es lo que lo hace posible.** Sin experimentos A/A no hay forma de auditar el modelo de ruido con los propios datos. Si tu plataforma no corre A/A, esta comprobación no está disponible, y ése es en sí un hallazgo operativo.

## 2. Capacidad de reordenar: ¿puede la corrección cambiar la decisión?

**Decide:** si tus variantes están balanceadas, la corrección **no puede** cambiar qué eliges. No la adoptes esperando mejores decisiones.

* **La razón es algebraica.** La contracción es un promedio ponderado entre el dato y un centro común. Si el peso y el centro son iguales para las variantes de un experimento, es una función monótona creciente del estimador y conserva el argmax.

* **Y se cumple en los datos.** El peso varía **0.009** entre las variantes de un mismo experimento, porque reciben tráfico parejo por diseño: la razón entre la variante con más y con menos impresiones tiene mediana **1.040**. El 99.8% de las decisiones son idénticas con y sin corregir.

* **No es un fallo del método.** Con variantes balanceadas no había un problema de selección que mejorar. Gu y Koenker (*Econometrica*, 2023) ya lo describen: con varianza homogénea, la media posterior, la probabilidad de cola y la expectativa de cola **dan el mismo orden**.

* **Entre experimentos sí reordena, porque ahí la precisión es heterogénea.** El peso medio es 0.432 con desviación 0.168; las impresiones varían 7.1 veces entre el percentil 99 y el 1. La corrección cambia el **23.4%** de la selección a un presupuesto del 10%.

## 3. Independencia previa: ¿se sostiene el supuesto central?

**Decide:** si la precisión predice el valor verdadero, la corrección canjea mal y **escogerás peor**.

* **El supuesto falla en estos datos, y sobrevive al control.** La correlación entre impresiones y tasa de clic es −0.140 cruda (p = 3.1e−16), **−0.098 dentro de cada semana** (60 semanas) y **−0.138 dentro de cada tipo de experimento** (4 tipos). No es confusión por periodo ni por tipo.

* **El mecanismo del daño es visible.** A un presupuesto del 10%, la corrección descarta experimentos con peso 0.695 y 4 161 impresiones, y añade otros con peso 0.320 y 7 283. Es decir, **descarta los imprecisos y añade los precisos** — exactamente lo que la teoría dice que hace bajo restricción de capacidad.

* **Y en este corpus el canje sale mal.** Los experimentos que descarta tenían **0.643 pp** de ganancia realizada; los que añade, **0.530 pp**. Como los imprecisos aquí tienen tasas más altas, despreciarlos empuja sistemáticamente hacia los peores.

* **Es el modo de falla que la literatura documenta.** Chen (*Econometrica* 94(2), marzo 2026) demuestra que cuando la independencia previa falla, el cribado basado en estimaciones contraídas puede ser **peor** que con las crudas. Aquí está medido.

* **Y explica por qué la corrección no alcanza su óptimo teórico.** La asimetría de la ganancia estimada es **+1.19** cuando la previa normal supone 0, porque es la ventaja de una variante **ya seleccionada**. La previa está mal especificada por construcción.

## 4. Régimen de la aproximación: ¿qué versión del método corresponde?

**Decide:** si la aproximación gaussiana vale, o si hace falta la formulación binomial directa. Y también **qué tanto se puede confiar en la literatura existente** para tu caso.

* **Aquí la aproximación gaussiana vale.** La regla habitual pide n·p ≥ 10. La mediana es **40**, y **el 0% de las variantes** cae por debajo de 10 o de 5. Así que Chen y Lei (diciembre 2025), que trabajan la binomial directamente para proporciones y muestras pequeñas, queda descartado **por diagnóstico y no por supuesto**.

* **Y aquí está la parte que importa para interpretar la literatura.** Coey y Hung (Meta), en *Empirical Bayes Selection for Value Maximization*, hacen esta misma pregunta sobre este mismo archivo, con cotas de arrepentimiento demostradas y código público. Su tesis: *«seleccionar las mejores unidades es fundamentalmente más fácil que estimar sus valores»*. Pero su montaje, descrito en su apéndice, impone dos condiciones:

  > *«Filtramos los pares artículo-paquete con menos de 1 000 impresiones o 100 clics, para asegurar que las aproximaciones de normalidad sean razonables.»*
  >
  > *«Consideramos arbitrariamente el de más impresiones como grupo de control y el de segundas más impresiones como tratamiento, omitiendo cualquier otro paquete.»*

* **Ese filtro conserva el 6.9% de las variantes.** Y «el de más impresiones» no es una selección por resultado, así que su montaje —por construcción— **no contiene la maldición del ganador**. Además evalúan contra una verdad simulada desde una previa ajustada, no contra resultados reales.

* **Medido dentro y fuera de su filtro, con 40 particiones y presupuesto del 5%:**

| | Su régimen | Archivo completo |
|---|---|---|
| Experimentos | 1 277 | 15 787 |
| n·p mediana | 131 | 40 |
| Error cuadrático medio | −32.8% | −23.9% |
| **Ganancia, contraída − cruda** | **+0.0148 pp** | **−0.0556 pp** |
| IC 95% | [−0.0153, +0.0448] | [−0.0619, −0.0493] |
| Contraer gana en | 55% de las particiones | **0%** |
| ¿Se distingue de cero? | **No** | **Sí** |

* **La lectura, sin inflarla.** En el régimen que ellos conservan, contraer es **neutro** para la decisión: el intervalo cruza el cero, exactamente lo que su teorema predice. Fuera de él —el 93% del archivo— **degrada la selección de forma medible**. No es un cambio de signo, y conviene no venderlo así: es un **límite de validez**, con el mecanismo del diagnóstico 3 detrás.

---

# Recomendaciones

Para un equipo de experimentación que está evaluando adoptar la contracción de Bayes empírico:

* **La variante ganadora sobreestima un 18.5% relativo y eso sí se corrige.** **Adopta la corrección para lo que reportas al negocio.** Reduce el error de estimación un 24.0%, replicado en dos muestras independientes, y es lo que evita prometer mejoras que no llegan.

* **Tus variantes probablemente reciben tráfico parejo, y entonces la corrección no puede cambiar la elección.** **No la justifiques ante tu dirección como una mejora de la decisión.** Mide la razón de impresiones entre tu variante más y menos expuesta: si está cerca de 1, hay una razón algebraica para que no reordene. Es una línea de código y evita un trimestre mal vendido.

* **Antes de usarla para priorizar entre experimentos, mide la correlación entre precisión y resultado.** **Si es negativa, la corrección te hará escoger peor.** Aquí vale −0.14 y sobrevive al control por periodo y por tipo. Son tres líneas de código y es el diagnóstico con mayor rendimiento del procedimiento.

* **Comprueba en qué régimen estás antes de apoyarte en la literatura publicada.** **Los resultados favorables más citados se obtuvieron en condiciones filtradas que pueden no ser las tuyas.** El filtro de uno de los trabajos de referencia conserva el 6.9% de estos datos, y su conclusión no se sostiene fuera de él.

* **Evalúa la decisión, no la estimación.** **Si el criterio de éxito es el error cuadrático medio, vas a aprobar un método que no mejora lo que te importa.** Partir los conteos con *data thinning* (Neufeld, Dharamshi, Gao y Witten, *JMLR* 2024) permite medir la ganancia realizada fuera de muestra sin datos extra. Es el único cambio de instrumentación que este procedimiento requiere.

* **Si tu plataforma no corre experimentos A/A, empieza por ahí.** **Sin una vara independiente no puedes auditar tu modelo de ruido**, y el modelo de ruido es el insumo del que depende todo el método. Aquí los A/A revelaron que la varianza estaba subestimada al doble.

---

# Supuestos y advertencias

* **El modelo de ruido se rechaza y las dos explicaciones posibles no son distinguibles.** *Q*/gl ≈ 1.93. Puede ser que las impresiones no sean independientes, o que variaran campos que el archivo no publica. Ambas quedan declaradas; ninguna se elige por conveniencia.

* **La exclusión del 30.6% por fallo de aleatorización se verificó, no se heredó.** Los CSV públicos no marcan las pruebas afectadas, así que la ventana se determinó con una prueba estadística propia. Ante la duda sobre cuándo se creó un experimento, se excluye.

* **Apliqué un factor de varianza al nivel equivocado y fabriqué un resultado falso.** Reporté primero que contraer **perjudica** la decisión en 0.27 pp. Era mío: usé el factor de diseño 1.94, medido para comparaciones entre variantes, sobre la ganancia entre experimentos. Lo detecté con una referencia que no usa la varianza —una covarianza que estima la dispersión directamente— y que da ~1.09 para ese nivel. Con el peso correcto el perjuicio desaparece y queda el empate. **El factor de diseño no transfiere entre niveles.**

* **Escribí una interpretación antes de ver los números y los números la contradijeron.** Afirmé que el peso de contracción era ~0.95 en todos los casos; medido, iba de 0.413 a 1.000. Queda registrado en el historial de git.

* **El primer titular de la comparación con la literatura no sobrevivió a su propio intervalo de confianza.** Leí «el signo cambia entre regímenes»; con 40 particiones e intervalo, el régimen filtrado no se distingue de cero. Lo que queda es un límite de validez, que es menos vistoso y es lo que los datos aguantan.

* **La ganancia estimada es un estadístico seleccionado, y eso rompe el método si no se trata.** Con dos particiones la dispersión entre experimentos se estimaba en cero, porque la ventaja del máximo ya incorpora la selección. Se resolvió partiendo en tres tercios: uno elige, otro estima, otro evalúa.

* **La previa normal está mal especificada por construcción.** La asimetría de la ganancia es +1.19 cuando la normal supone 0, porque es la ventaja de una variante ya seleccionada. Por eso el orden por media posterior no alcanza su óptimo teórico.

* **Un solo medio, una sola métrica, 2013–2015, datos agregados.** No hay nivel de persona ni segmentos. **El procedimiento transfiere; los números no.** Ninguna cifra de este documento debe usarse como expectativa para otra plataforma.

* **Lo que no se implementó, con su razón.** `close` (la implementación de referencia de Chen) está en R y este proyecto es Python: costo operativo declarado, no omisión. Su **diagnóstico** sí se corrió, y es el que explica el resultado principal.
