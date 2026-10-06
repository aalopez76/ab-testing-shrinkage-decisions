# Contexto del proyecto

Las organizaciones que deciden con experimentos —comercio digital, medios, marketplaces, salud, investigación— proponen varias versiones de una misma propuesta (anuncios, descuentos, titulares, dosis), miden cuál rinde mejor y despliegan la ganadora. **Sin embargo, la versión seleccionada por haber rendido mejor tiende después a rendir menos de lo que se esperaba.**

Es un problema conocido y se le llama **la maldición del ganador**. Ocurre porque la propuesta elegida debe su ventaja a dos cosas: por un lado a ser la de mejor rendimiento y, por otro, a un factor de suerte —ruido— que no se repite al desplegar. Su magnitud depende de la potencia del experimento: con una potencia del 80%, que es el estándar de la industria, la exageración ronda el 13%; con 20%, supera el 130%.

La corrección que la industria propone es la **contracción de Bayes empírico**: acercar el resultado del ganador a la media del grupo, en una proporción que crece con la imprecisión de la medición. Microsoft y Netflix la usan en producción, Meta publicó en 2025 una variante —*Bayesian Hybrid Shrinkage*— y **Spotify publicó por qué no la adopta**, advirtiendo que una previa mal calibrada resulta activamente peor que no corregir. Adoptarla cambia cómo se reporta cada resultado al negocio.

**La pregunta que este proyecto resuelve es si conviene adoptarla, y para qué exactamente.

Los resultados y recomendaciones se organizan sobre esas cuatro decisiones:

- **Qué variante desplegar** — ordenar candidatos dentro de un experimento.
- **Qué experimentos priorizar** — ordenar con presupuesto limitado.
- **Si lanzar o no** — comparar contra un umbral absoluto.
- **Qué cifra reportar al negocio** — la estimación misma.


---

# Los datos y las comprobaciones iniciales

**Upworthy Research Archive** ([Matias y coautores, *Scientific Data* 8:195, 2021](https://www.nature.com/articles/s41597-021-00934-7)): son pruebas A/B reales de titulares e imágenes de un medio digital estadounidense. **Lo que estos datos reproducen no es el dato de ninguna empresa concreta, es el procedimiento** —lanzar varias versiones, repartir los usuarios al azar, medir una tasa de conversión y desplegar la ganadora—, que es el mismo bucle que corre una tienda que prueba incentivos o un laboratorio que prueba dosis.


El archivo resulta de interés porque reúne tres condiciones: **aleatorización real** (lo que evita confundir el efecto de selección con sesgo de asignación), **muchas variantes por experimento** (la maldición vive en el máximo sobre candidatos, y con solo dos apenas hay de dónde seleccionar) y una **partición exploratorio/confirmatorio incluida**, que permite congelar el método y confirmarlo sin contaminación. 

| | Exploratorio | Confirmatorio |
|---|---|---|
| Experimentos tras exclusión | 3 380 | **15 787** |
| Variantes | 16 629 | **77 446** |
| Impresiones | 58.8 millones | **273.5 millones** |
| Clics | 749 878 | **3 492 259** |
| Variantes por experimento | 2 a 14 (mediana 5) | 2 a 20 (mediana 5) |
| Tasa de clic | 1.28% | 1.28% |



## Comprobación 1: la aleatorización 

Se excluye una ventana de **6 956 de 22 743 experimentos fuera (30.6%)**, debido a que por una mala configuración de caché, el 25 de junio de 2013, hizo que durante meses se mostrara una sola variante, afectando a ~22% de las pruebas. **Los archivos públicos no traen la columna que las identifica**, así que se verificó desde cero con una prueba de bondad de ajuste sobre las impresiones por variante, que reproduce el fallo mes a mes: 22.3% en junio de 2013, **86.4% en diciembre**, 11.0% en enero de 2014 y entre 0.0% y 0.9% después. 

El periodo conservado corre a la tasa de anomalía que se esperaría por azar.

## Comprobación 2: Modelo de ruido (subestimación al doble)

Toda contracción depende de la varianza de cada medición, y los experimentos A/A —donde nada varía entre variantes— dan una vara independiente: la diferencia verdadera es cero por construcción, así que la dispersión observada debería igualar la calculada. No lo hace. La *Q* de Cochran vale **1.940** veces sus grados de libertad en el exploratorio y **1.927** en el confirmatorio, y **replica en las dos muestras**.

![Las dos comprobaciones iniciales](reports/figures/02_comprobaciones_iniciales.png)

## Cómo se mide fuera de muestra

Para saber cuánto se infló el ganador hay que medirlo donde no participó en ser elegido. Se parten los conteos de cada variante de forma **hipergeométrica**, lo que para la familia a la que pertenece la binomial produce partes **marginalmente independientes** que suman la observación original; es exacto, no aproximado. Se llama *data thinning*.

La partición es en **tres tercios** y no en dos: uno elige la variante, otro estima su ventaja, otro evalúa. Con dos mitades la dispersión entre experimentos se estima en cero, porque la ventaja del ganador es un estadístico ya seleccionado y el método supone una estimación que no lo sea.

---

# Resumen ejecutivo

Con el método congelado, se corrió la muestra confirmatoria **una sola vez**. Replicó al tercer decimal sobre una muestra 4.7 veces mayor que nunca se tocó durante el desarrollo.

**La maldición del ganador es real y grande:** la variante desplegada promete 1.792% y entrega 1.553%, una **sobreestimación del 15.4% relativo**. Y es un efecto de selección, no de medición: elegir una variante al azar da una inflación cien veces menor.

**La corrección no arregla lo que la mayoría supone que arregla.** Medida sobre las cuatro decisiones consideradas, por separado, se obtiene:

| La decisión | ¿Ayuda contraer? | La cifra |
|---|---|---|
| **1. Qué variante despliego** | **No, y no puede** | 99.8% de decisiones idénticas |
| **2. Qué experimentos priorizo** | **No, levemente peor** | −0.056 pp, IC 95% [−0.062, −0.049], pierde en 40/40 |
| **3. Lanzo o no** | **Sí, y crece con la exigencia** | +1.73 a +2.91 pp de acierto, gana en 20/20 |
| **4. La cifra que reporto** | **Sí** | −24.0% de error, −28.1% con la variante de Meta |

![Las cuatro decisiones](reports/figures/03_cuatro_decisiones.png)

Lo que se lleva un responsable de experimentación: **la corrección sirve para dejar de prometer de más y para decidir si una mejora merece desplegarse; no sirve para elegir mejor entre candidatos.** Y la diferencia no es un matiz, es un trimestre de ingeniería bien o mal invertido.

---

# Hallazgos en detalle

## 1. Qué variante desplegar: no puede mejorarse, y está demostrado 

* **No es que no ayude, es que no puede.** La contracción es un promedio ponderado entre el dato y un centro común, así que si el peso y el centro son iguales para las variantes de un mismo experimento, es una función monótona creciente del estimador y **conserva el orden**.

* **Y en estos datos el peso es prácticamente el mismo:** varía 0.009 entre variantes del mismo experimento, porque reciben tráfico parejo por diseño —la razón entre la más y la menos expuesta tiene mediana 1.040—. El 99.8% de las decisiones resultan idénticas.

* **Es el caso degenerado que la literatura ya describe.** Con varianza homogénea, la media posterior, la probabilidad de cola y la expectativa de cola dan el mismo orden. Con variantes balanceadas no había un problema de selección que mejorar.

* **Consecuencia práctica:** un equipo cuyas variantes reciben tráfico parejo puede descartar el proyecto entero midiendo una razón de impresiones. 

## 2. Qué experimentos priorizar: empeora, y se sabe por qué

* **Reordena de verdad pero elige peor.** Al 10% de presupuesto la corrección cambia el 23.0% de la selección, y la ganancia realizada cae 0.056 pp, perdiendo en las 40 particiones evaluadas con un intervalo que no toca el cero.

* **El mecanismo es visible:** descarta experimentos con peso de contracción 0.689 y 4 000 impresiones, y añade otros con peso 0.318 y 7 151. Es decir, **descarta los imprecisos y añade los precisos**, que es exactamente lo que la teoría dice que hace bajo restricción de capacidad.

* **Pero los que descarta tenían más ganancia real** (0.647 contra 0.510 pp), porque el supuesto de independencia previa falla: la correlación entre impresiones y resultado es −0.119 cruda, **−0.087 dentro de cada semana** y **−0.113 dentro de cada tipo de experimento**. Sobrevive al control por periodo y por tipo.

* **Consecuencia práctica:** El signo predice si la corrección va a ayudar o a perjudicar antes de implementarla.

![Dónde falla](reports/figures/05_donde_falla.png)

## 3. Si lanzar o no: aquí sí gana, y la ventaja crece

* **La razón es una asimetría que la literatura de A/B testing no suele separar.** Ordenar es invariante a una transformación monótona, así que contraer no puede cambiar el argmax. **Comparar contra un umbral absoluto no lo es**: contraer cambia el valor, así que cambia si cruza la línea.

* **Y la mejora crece con la exigencia del umbral**, ganando en las 20 particiones a partir de 0.4 puntos:

| Umbral | Acierto sin corregir | Acierto contraída | Mejora | Gana en |
|---|---|---|---|---|
| > 0.2 pp | 62.60% | 62.61% | +0.01 pp | 45% |
| > 0.4 pp | 68.69% | 70.42% | **+1.73 pp** | **100%** |
| > 0.6 pp | 76.72% | 79.62% | **+2.91 pp** | **100%** |
| > 0.8 pp | 83.83% | 86.68% | **+2.85 pp** | **100%** |

* **Con umbral exigente la regla sin corregir lanza el 14.2% y la verdad es 14.2%:** acierta la tasa y se equivoca en los individuos. La contraída lanza el 3.2% y acierta más, porque la mayoría de los experimentos genuinamente no cruza un umbral alto y contraer lo dice bien.

* **Esta es la decisión que un equipo toma con más frecuencia**, y es donde la corrección paga.

![La decisión de lanzar](reports/figures/04_decision_de_lanzar.png)

## 4. La cifra reportada: mejora, y la variante más reciente mejora más

* **La corrección estándar reduce el error de estimación un 24.0%**, replicado en las dos muestras. Es lo que evita prometer al negocio mejoras que no llegan.

* **Se implementó además BHS**, la variante que Meta publicó en 2025 con factores de contracción locales por experimento. Los datos piden esa flexibilidad sin ambigüedad: el parámetro ajustado es **a = 2.65** con una **razón de verosimilitudes de 961** contra la versión estándar.

* **BHS cumple lo que promete y estima mejor: −28.1% de error.** Pero no cambia el orden: la diferencia en la decisión 2 es +0.009 pp y gana en el 0% de las particiones.

* **El motivo estaba ya medido.** BHS corrige la **forma** de la previa con colas pesadas; lo que falla en estos datos es la **independencia previa**. Hacer la previa más flexible no hace que la precisión sea independiente del parámetro: son dos supuestos distintos, y BHS solo toca uno.

![BHS](reports/figures/06_bhs.png)

---

# Recomendaciones

Para un equipo de experimentación que está evaluando adoptar la corrección:

* **La variante ganadora sobreestima un 15.4% relativo y eso sí se corrige.** **Conviene adoptarla para lo que se reporta al negocio y para decidir si una mejora merece desplegarse**, porque reduce el error un 24% y mejora el acierto de la decisión de lanzamiento hasta 2.9 puntos, ganando en todas las particiones evaluadas.

* **Las variantes de una prueba A/B suelen recibir tráfico parejo por diseño.** **Entonces no conviene justificar la corrección como una mejora de qué variante se elige**: basta medir la razón de impresiones entre la más y la menos expuesta, y si está cerca de 1 hay una razón algebraica para que no reordene.

* **El supuesto central de la corrección es que el valor verdadero no dependa de la precisión con que se midió.** **Antes de usarla para priorizar entre experimentos conviene medir esa correlación, porque si es negativa hará escoger peor.** Aquí vale −0.12 y sobrevive al control.

* **La varianza es el insumo del que depende todo el método, y aquí estaba subestimada al doble.** **Conviene auditarla contra experimentos A/A antes que nada, y si la plataforma no los corre, empezar por ahí**, porque sin una vara independiente no hay forma de saber si está bien medida.

* **La ventaja de un ganador es un estadístico ya seleccionado y el método supone una estimación que no lo sea.** **Si se va a contraer, conviene partir los conteos en tres** —uno elige, otro estima, otro evalúa—, porque con dos la dispersión se estima en cero y la corrección deja de funcionar.

---

# Supuestos y advertencias

* **El modelo de ruido no describe estos datos, y las dos explicaciones posibles no son distinguibles.** La *Q* de Cochran vale ~1.93 veces sus grados de libertad en las dos muestras. Puede deberse a que las impresiones no sean independientes, o a que variaran campos que el archivo no publica. Ambas quedan declaradas, y el factor medido se aplica a la varianza de cada variante.

* **El factor de diseño se aplica únicamente al nivel en que se midió.** El 1.94 corresponde a comparaciones entre variantes dentro de un experimento. Para la ventaja entre experimentos se usa un factor estimado por una vía independiente —una covarianza que no emplea la varianza en absoluto—, que da ~1.09. **Un factor de diseño no transfiere entre niveles**, y suponer que sí invertiría la conclusión.

* **La previa normal está mal especificada por construcción.** La ventaja del ganador es la de una variante ya seleccionada, de modo que su distribución está corrida (asimetría +1.19) cuando la normal supone cero. Es la razón de implementar BHS, y también la razón de que el orden por media posterior no alcance su óptimo teórico.

* **La evaluación mide predicción sobre una partición reservada, no rendimiento tras un despliegue real.** El procedimiento es exacto para la binomial, pero lo que contrasta es la capacidad de anticipar la mitad reservada del mismo experimento. Un despliegue a toda la base introduce efectos —saturación, estacionalidad, interferencia entre usuarios— que estos datos no permiten observar.

* **Un solo medio, una sola métrica, 2013–2015, y datos agregados sin nivel de persona.** No hay segmentos ni características de usuario. **Transfiere el procedimiento y sus umbrales; los números concretos, no.** Ninguna cifra de este documento debe usarse como expectativa para otra plataforma.

* **Dos métodos quedaron fuera con su razón.** La contracción binomial directa, **por diagnóstico**: n·p tiene mediana 40 y solo el 0.1% de las variantes cae por debajo de 10, así que la aproximación gaussiana no es la fuente del problema aquí. Y la implementación de referencia de Chen, **por costo operativo declarado**: está en R y este proyecto es Python; su diagnóstico sí se corrió, y es el que explica el resultado principal.
