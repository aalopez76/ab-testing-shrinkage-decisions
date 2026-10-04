# El problema

Hay una decisión que se repite, con la misma forma, en sectores que no tienen nada que ver entre sí: **se miden varios candidatos, se elige el que midió mejor, y luego el elegido rinde menos de lo que prometió.**

Pasa porque el que midió mejor lo hizo por dos razones a la vez —porque es bueno y porque le favoreció el azar— y el azar no se repite. El nombre se lo pusieron tres ingenieros de petróleo en 1971: estudiando las subastas de arrendamiento marítimo, documentaron que las compañías obtenían rendimientos inesperadamente bajos «año tras año», y llamaron a eso **la maldición del ganador**.

Desde entonces el mismo problema aparece documentado en:

| Sector | Qué se elige | Cómo se manifiesta |
|---|---|---|
| **Subastas** | La puja ganadora | La ganadora paga de más por un bien de valor incierto |
| **Genética** | Las variantes más significativas entre un millón | Los efectos de las variantes seleccionadas están exagerados frente a su valor real |
| **Ensayos clínicos** | La dosis con mayor efecto observado | Estimaciones demasiado optimistas para la dosis elegida, más error de tipo I inflado |
| **Educación** | Los docentes mejor evaluados | Se contraen las evaluaciones hacia la media, con peso creciente en la imprecisión |
| **Gestión de inversión** | Los gestores con mejor desempeño | Se contrata y despide en los momentos equivocados, extrapolando rendimientos |
| **Comercio digital** | La variante ganadora de una prueba A/B | **El caso de este proyecto** |

Es el mismo problema estadístico con seis nombres distintos. Y en todos, la corrección propuesta es la misma familia: **contraer las estimaciones hacia la media del grupo**, con un peso que crece con la imprecisión de cada medición.

## El caso que resuelve este proyecto

El comercio digital y los sectores que operan como él —medios, suscripción, marketplaces— tienen que decidir continuamente qué desplegar: un anuncio, un descuento, una promoción, un titular, un orden de resultados.

Hay varios métodos para esa decisión, y conviene distinguirlos en dos ejes, porque confundirlos lleva a comparar cosas que no compiten.

**Cómo se asigna** (el diseño):

| Método | Para qué sirve |
|---|---|
| **Pruebas A/B** | Comparar versiones completas repartiendo usuarios al azar |
| **Bandidos multibrazo** | Mucho tráfico y muchas variantes: mueve el tráfico hacia la que va ganando |
| **Intercalado** | Sistemas de ranking: mezcla dos algoritmos dentro de la misma búsqueda |
| **Conmutación** (*switchback*) | Marketplaces: aleatoriza región y franja horaria en lugar de usuarios |
| **Cuasiexperimentales** | Cuando no se puede aleatorizar y solo hay datos de comportamiento |

**Cómo se analiza lo recogido** (la inferencia):

| Método | Para qué sirve |
|---|---|
| **Frecuentista de horizonte fijo** | Lo dominante: muestra fija, lectura al final |
| **Secuencial de grupo** | Permite mirar antes sin inflar el error |
| **Bayesiano** | Previa explícita, posterior interpretable |
| **Bayes empírico post-hoc** | La previa se **estima del histórico**. Aquí entran la contracción y sus variantes |

Las pruebas A/B son el estándar del primer eje, por tres razones concretas: establecen causalidad porque el reparto es al azar; son sencillas de iterar, porque comparar versiones completas no exige rediseñar el sistema; y escalan, porque las plataformas ya tienen el tráfico que el método necesita.

**La corrección de la maldición del ganador vive en el segundo eje.** Se monta encima de una prueba A/B ya corrida, no la sustituye.

## Por qué cuesta decidir mal

La corrección no es gratis. Es infraestructura —un trimestre de ingeniería— y cambia cómo se reporta cada resultado al negocio. Y equivocarse tiene costo en las dos direcciones: si funciona y no se usa, se dejan mejoras sobre la mesa; **si se usa donde no corresponde, se decide peor que no corrigiendo nada.**

Lo que vuelve esto difícil es que **no es una decisión, son cuatro**, y la literatura las trata como si fueran la misma:

1. **¿Qué variante despliego?** — ordenar candidatos dentro de un experimento.
2. **¿Qué experimentos priorizo?** — ordenar con presupuesto limitado.
3. **¿Lanzo esto o no?** — comparar contra un umbral absoluto.
4. **¿Qué cifra le reporto al negocio?** — la estimación misma.

Esa distinción no es mía. La genética ya la nombra: separan el **sesgo de ranking**, que nace de ordenar un millón de variantes, del **sesgo de selección**, que nace de usar un umbral. Son dos mecanismos distintos, y nada garantiza que una corrección arregle los dos.

**Este proyecto mide las cuatro, por separado, y encuentra cuatro respuestas distintas.**

---

# Cómo lo resolví

## Los datos: lo que reproducen es el procedimiento, no el dato

Los datos ideales serían los del propio equipo. Nadie los publica. Así que el proyecto **analiza con datos reales un escenario hipotético, pero muy parecido al que enfrentan hoy los sectores industriales digitales.**

Lo que reproducen no es el dato, **es el bucle**: una organización que lanza varias versiones de una propuesta, reparte el tráfico al azar entre ellas, mide una tasa de conversión y despliega la ganadora. Y es la estructura de ese bucle —no el sector, ni la métrica, ni el año— la que determina si la corrección funciona.

Son el **Upworthy Research Archive** ([Matias, Munger, Aubin Le Quéré y Ebersole, *Scientific Data* 8:195, 2021](https://www.nature.com/articles/s41597-021-00934-7)): un medio digital estadounidense que probaba titulares de forma sistemática antes de publicar.

| | Exploratorio | Confirmatorio |
|---|---|---|
| Experimentos tras exclusión | 3 380 | **15 787** |
| Variantes | 16 629 | **77 446** |
| Impresiones | 58.8 millones | **273.5 millones** |
| Clics | 749 878 | **3 492 259** |
| Variantes por experimento | 2 a 14 (mediana 5) | 2 a 20 (mediana 5) |
| Tasa de clic | 1.28% | 1.28% |

Sirven porque reúnen las seis condiciones que el problema exige, y que casi ningún archivo público reúne juntas:

| Condición | Por qué es imprescindible | Qué aporta |
|---|---|---|
| Aleatorización real | Sin ella el efecto de selección se confunde con sesgo de asignación | 19 167 experimentos aleatorizados |
| Varias variantes | La maldición vive en el **máximo** sobre candidatos | mediana 5, hasta 20 |
| Muchos experimentos | Para estimar la dispersión entre ellos | 15 787, muy por encima de los 200 que la literatura fija como mínimo |
| Experimentos A/A | Vara **independiente** para auditar el ruido | 1 279 |
| Partición previa | Para congelar el método y confirmarlo | incluida por los autores |
| Precisión heterogénea | Para que el peso de contracción pueda variar | impresiones p99/p01 = 7.1 |

Y lo que no tienen: un solo medio, métrica de clic, 2013–2015, datos agregados sin nivel de persona. **Transfiere el procedimiento y sus umbrales; los números concretos, no.**

## Dos problemas de los datos, resueltos antes de medir nada

**La aleatorización falló durante meses y el archivo público no lo marca.** Los autores publicaron en 2024 que una mala configuración de caché, el 25 de junio de 2013, hizo que durante meses se mostrara una sola variante. Afecta a ~22% de las pruebas. Los CSV no traen la columna que las identifica, así que se verificó desde cero con una prueba sobre las impresiones por variante:

| Mes | Experimentos con reparto anómalo |
|---|---|
| jun-2013 | 22.3% |
| dic-2013 | **86.4%** |
| ene-2014 | 11.0% |
| feb-2014 en adelante | 0.0% a 0.9% |

Se excluye esa ventana: **6 956 de 22 743 experimentos fuera (30.6%)**.

**Y el modelo de ruido no describe estos datos.** Los experimentos A/A —donde nada varía entre variantes— dan una vara independiente: la diferencia verdadera es cero por construcción, así que la dispersión observada debería igualar la calculada. No lo hace: la *Q* de Cochran vale **1.940** veces sus grados de libertad en el exploratorio y **1.927** en el confirmatorio. El modelo binomial subestima el ruido cerca del doble, y **replica en las dos muestras**.

![Izquierda: el fallo de aleatorización mes a mes, verificado desde cero porque los CSV no lo marcan. Derecha: la Q de Cochran sobre los experimentos A/A, donde la diferencia verdadera es cero por construcción.](reports/figures/02_comprobaciones_iniciales.png)

*Izquierda: el fallo de aleatorización mes a mes, verificado desde cero porque los CSV no lo marcan. Derecha: la Q de Cochran sobre los experimentos A/A, donde la diferencia verdadera es cero por construcción.*


## El estado del arte, aplicado

| Qué | Para qué, aquí |
|---|---|
| **Contracción de Bayes empírico** | La corrección a evaluar. Dispersión estimada en conjunto con los métodos del meta-análisis |
| **Bayesian Hybrid Shrinkage** (Meta, 2025) | La variante más reciente: factores de contracción **locales** por experimento. Implementada en `src/wcab/shrinkage/bhs.py` |
| **Probabilidad de cola posterior** | La regla alternativa cuando el criterio no es el valor realizado |
| **Data thinning** (*JMLR* 2024) | Partir los conteos de forma hipergeométrica para evaluar fuera de muestra sin datos extra |
| **Diagnóstico de precisión-parámetro** | Comprobar si se sostiene el supuesto central de la corrección |
| **Régimen n·p** | Decidir si corresponde la versión gaussiana o la binomial directa |

Dos decisiones de método que vale la pena explicitar.

**Por qué hubo que partir en tres tercios y no en dos.** La ventaja del ganador, δ = máximo − media, es un estadístico **ya seleccionado**, y el Bayes empírico supone una estimación que no lo sea. Con dos mitades, la dispersión entre experimentos se estimaba en **cero**: la calibración colapsaba. La solución fue partir en tres —uno elige el brazo, otro estima su ventaja, otro evalúa—, de modo que el δ estimado es la ventaja de un brazo **ya fijado**. La dispersión pasó de 0 a 1.787e-05 y la corrección volvió a funcionar.

Esto importa más allá de este proyecto, porque es un bloqueo que la literatura enuncia y deja abierto: los corpus seleccionados por el ganador **impiden la calibración independientemente del tamaño del corpus**, y recoger más datos de la misma fuente sesgada no ayuda. Correcto — y la respuesta no es recoger más, es **partir los conteos que ya se tienen** para que la selección y la estimación ocurran en mitades independientes.

**Y cómo se sabe si BHS hacía falta.** El modelo de BHS se reparametrizó con `b = a − 2`, lo que deja a `a` como único mando: con `a` grande reproduce exactamente la contracción estándar —el caso que el propio artículo llama *Bayesian Global Shrinkage*—, y con `a` chico da las colas pesadas. Así que **ajustar `a` es preguntarle a los datos cuánta flexibilidad local necesitan.** Validado en tres casos construidos, incluido el decisivo: con una previa normal, el método responde «aquí no hago falta» (razón de verosimilitudes 0.67, p = 0.41).

---

# Lo que encontré

El método se congeló el 3 de octubre de 2026 —con fecha, commit de git y criterio de éxito declarado— y entonces se corrió la muestra confirmatoria **una sola vez**.

## La maldición del ganador es real y grande

| | Exploratorio | Confirmatorio |
|---|---|---|
| Inflación de la variante ganadora | 0.236 pp | **0.237 pp** |

La variante desplegada promete 1.792% y entrega 1.553%: una **sobreestimación del 15.4% relativo**, medida sobre lo que esa variante realmente rinde. Y es un efecto de **selección**, no de medición: elegir una variante al azar da una inflación cien veces menor.

![La variante elegida promete más de lo que entrega. Elegir al azar no produce brecha: la maldición es un efecto de selección.](reports/figures/01_maldicion_del_ganador.png)

*La variante elegida promete más de lo que entrega. Elegir al azar no produce brecha: la maldición es un efecto de selección.*



![La misma corrección sobre cuatro decisiones distintas. Cada panel está en sus propias unidades a propósito: normalizarlas a un eje común sería disfrazar cantidades distintas de comparables.](reports/figures/03_cuatro_decisiones.png)

*La misma corrección sobre cuatro decisiones distintas. Cada panel está en sus propias unidades a propósito: normalizarlas a un eje común sería disfrazar cantidades distintas de comparables.*

## Las cuatro decisiones, cuatro respuestas

| La decisión | ¿Ayuda contraer? | La cifra |
|---|---|---|
| **1. Qué variante despliego** | **No, y no puede** | 99.8% de decisiones idénticas |
| **2. Qué experimentos priorizo** | **No, levemente peor** | −0.0556 pp, IC 95% [−0.0619, −0.0493], pierde en 40/40 |
| **3. Lanzo o no** | **Sí, y crece con la exigencia** | +1.73 a +2.91 pp de acierto, gana en 20/20 |
| **4. La cifra que reporto** | **Sí** | −24.0% estándar, **−28.1%** con BHS |

**La decisión 1 no puede mejorarse, y eso se demuestra.** La contracción es un promedio ponderado entre el dato y un centro común. Si el peso y el centro son iguales para las variantes de un experimento, es una función monótona creciente del estimador y **conserva el orden**. Medido: el peso varía **0.009** entre variantes del mismo experimento, porque reciben tráfico parejo por diseño —la razón entre la más y la menos expuesta tiene mediana 1.040. Con variantes balanceadas no había un problema de selección que mejorar.

**La decisión 2 empeora, y se sabe por qué.** Al 10% de presupuesto la corrección cambia el 23.4% de la selección: descarta experimentos con peso 0.689 y 4 000 impresiones, y añade otros con peso 0.318 y 7 151. Descarta los imprecisos y añade los precisos, que es lo que la teoría dice que hace. Pero **los que descarta tenían más ganancia real** (0.647 contra 0.510 pp), porque el supuesto de independencia previa falla: la correlación entre impresiones y tasa es −0.119 cruda, **−0.087 dentro de cada semana** (66 semanas) y **−0.113 dentro de cada tipo de experimento**. Sobrevive al control.

![El mecanismo del daño: la corrección descarta los experimentos imprecisos, y en este corpus los imprecisos tienen mejor resultado real porque la precisión y el resultado están correlacionados.](reports/figures/05_donde_falla.png)

*El mecanismo del daño: la corrección descarta los experimentos imprecisos, y en este corpus los imprecisos tienen mejor resultado real porque la precisión y el resultado están correlacionados.*


**La decisión 3 sí mejora, y la razón es la asimetría que separa ordenar de comparar.** Ordenar es invariante a una transformación monótona, así que contraer no puede cambiar el argmax. Comparar contra un **umbral absoluto** no lo es: contraer cambia el valor, así que cambia si cruza la línea.

| Umbral de lanzamiento | Acierto cruda | Acierto contraída | Mejora | Gana en |
|---|---|---|---|---|
| > 0.2 pp | 62.60% | 62.61% | +0.01 pp | 45% |
| > 0.4 pp | 68.69% | 70.42% | **+1.73 pp** | **100%** |
| > 0.6 pp | 76.72% | 79.62% | **+2.91 pp** | **100%** |
| > 0.8 pp | 83.83% | 86.68% | **+2.85 pp** | **100%** |

Con umbral exigente la regla cruda lanza el 14.2% y la verdad es 14.2%: **acierta la tasa y se equivoca en los individuos.** La contraída lanza el 3.2% y acierta más, porque la mayoría genuinamente no cruza un umbral alto, y contraer lo dice bien.

![Donde la corrección sí gana. La ventaja crece con la exigencia del umbral, y a partir de 0.4 pp gana en las 20 particiones.](reports/figures/04_decision_de_lanzar.png)

*Donde la corrección sí gana. La ventaja crece con la exigencia del umbral, y a partir de 0.4 pp gana en las 20 particiones.*


## La variante más reciente estima mejor y tampoco cambia el orden

Los datos piden la flexibilidad local de BHS sin ambigüedad:

```
a ajustado = 2.65  [2.52, 2.79] en 12 particiones
razón de verosimilitudes contra la versión estándar = 961   (1 grado de libertad)
```

Una previa t con 2.65 grados de libertad: colas casi tan pesadas como el modelo admite. Y **coincide con la asimetría de +1.19** medida antes por una vía independiente.

BHS cumple lo que promete: **estima mejor que la versión estándar** (−28.1% contra −23.9%). Pero la diferencia en la decisión de orden es **+0.0092 pp y gana en el 0% de las particiones**.


![La variante de 2025 estima mejor que la estándar y deja el orden donde estaba. Los datos piden su flexibilidad local sin ambigüedad, pero esa flexibilidad corrige otro supuesto.](reports/figures/06_bhs.png)

*La variante de 2025 estima mejor que la estándar y deja el orden donde estaba. Los datos piden su flexibilidad local sin ambigüedad, pero esa flexibilidad corrige otro supuesto.*

**El motivo ya estaba medido.** BHS corrige la **forma** de la previa, con colas pesadas. Lo que falla aquí es la **independencia previa**. Hacer la previa más flexible no hace que la precisión sea independiente del parámetro: son dos supuestos distintos, y BHS solo toca uno.

## Y el resultado favorable más citado vale en su régimen

El trabajo empírico más cercano sobre este mismo archivo filtra las variantes con menos de 1 000 impresiones o 100 clics, «para asegurar que las aproximaciones de normalidad sean razonables». **Ese filtro conserva el 6.9%.** Medido dentro y fuera:

| Al 5% de presupuesto | Su régimen | Archivo completo |
|---|---|---|
| Experimentos | 1 277 | 15 787 |
| Ganancia, contraída − cruda | +0.0148 pp | −0.0556 pp |
| IC 95% | [−0.0153, +0.0448] | [−0.0619, −0.0493] |
| ¿Se distingue de cero? | **No** | **Sí** |

En el régimen que conservan, contraer es **neutro** para el orden —el intervalo cruza el cero—, que es lo que su teorema predice. Fuera de él degrada la selección de forma medible. **No es un cambio de signo: es un límite de validez.**

---

# Recomendaciones

Para un equipo que está evaluando adoptar la corrección:

* **La variante ganadora sobreestima un 15.4% relativo, y eso sí se corrige.** **Adóptala para lo que reportas al negocio y para decidir si lanzas.** Reduce el error un 24% y mejora el acierto de la decisión de lanzamiento hasta 2.9 puntos, ganando en todas las particiones evaluadas.

* **No la justifiques como una mejora de qué variante eliges.** **Mide la razón de impresiones entre tu variante más y menos expuesta.** Si está cerca de 1, hay una razón algebraica para que no reordene — es una línea de código y evita un trimestre mal vendido.

* **Antes de usarla para priorizar entre experimentos, mide la correlación entre precisión y resultado.** **Si es negativa, te hará escoger peor.** Aquí vale −0.12 y sobrevive al control. Tres líneas de código, y es el diagnóstico de mayor rendimiento.

* **Audita tu modelo de ruido contra experimentos A/A antes que nada.** **Si tu plataforma no corre A/A, empieza por ahí**, porque sin una vara independiente no puedes saber si la varianza —el insumo del que todo depende— está bien medida. Aquí estaba subestimada al doble.

* **Si tu ventaja estimada viene de un máximo, no la contraigas directamente.** **Parte los conteos en tres**: uno elige, otro estima, otro evalúa. Con dos la dispersión se estima en cero y la corrección deja de funcionar, por una razón que no se ve hasta que pasa.

* **Comprueba tu régimen antes de apoyarte en un resultado publicado.** **Los resultados favorables más citados se obtuvieron en condiciones filtradas que pueden no ser las tuyas.**

---

# Supuestos y advertencias

* **El modelo de ruido se rechaza y las dos explicaciones posibles no son distinguibles.** *Q*/gl ≈ 1.93. Puede ser que las impresiones no sean independientes, o que variaran campos que el archivo no publica. Ambas quedan declaradas.

* **La exclusión del 30.6% se verificó, no se heredó.** Los CSV no marcan las pruebas afectadas, así que la ventana se determinó con una prueba propia. Ante la duda sobre cuándo se creó un experimento, se excluye.

* **Apliqué un factor de varianza al nivel equivocado y fabriqué un resultado falso.** Reporté primero que contraer **perjudica** el orden en 0.27 pp. Usé el factor de diseño 1.94, medido para comparaciones entre variantes, sobre la ganancia entre experimentos. Lo detecté con una referencia que no usa la varianza —una covarianza que estima la dispersión directamente— y que da ~1.09 para ese nivel. **El factor de diseño no transfiere entre niveles.**

* **Escribí una interpretación antes de ver los números y los números la contradijeron.** Afirmé que el peso de contracción era ~0.95 en todos los casos; medido, iba de 0.413 a 1.000.

* **Un primer titular no sobrevivió a su propio intervalo de confianza.** Leí «el signo cambia entre regímenes»; con 40 particiones e intervalo, el régimen filtrado no se distingue de cero. Queda el límite de validez, que es menos vistoso y es lo que los datos aguantan.

* **La previa normal está mal especificada por construcción.** La asimetría de la ganancia es +1.19 cuando la normal supone 0, porque es la ventaja de una variante ya seleccionada. Por eso el orden por media posterior no alcanza su óptimo teórico, y por eso se implementó BHS.

* **Un solo medio, una sola métrica, 2013–2015, datos agregados.** Ninguna cifra de este documento debe usarse como expectativa para otra plataforma. **Transfiere el procedimiento, no los números.**

* **Lo que no se implementó, con su razón.** La contracción binomial directa queda fuera **por diagnóstico**: n·p mediana = 40 y 0.1% de variantes bajo 10, así que la aproximación gaussiana no es el problema aquí. La implementación de referencia de Chen está en R y este proyecto es Python: **costo operativo declarado**, no omisión — su diagnóstico sí se corrió, y es el que explica el resultado principal.

---

# Sobre qué se apoya todo esto

Cada pieza del procedimiento tiene una fuente, y vale decir cuál sostiene qué.

**El marco de la decisión.** Que las tasas de error, la exactitud de estimación y el arrepentimiento son **riesgos distintos**, y que el método apropiado se sigue de los riesgos que un programa necesita controlar, es de [Schultzberg y Frånberg (Spotify, ago-2026)](https://arxiv.org/abs/2608.12949). Su jerarquía de tres niveles organiza las configuraciones bayesianas por la fuerza de su control de error y establece que el Bayes empírico es el único camino al tercero. Este proyecto mide en un corpus real las cuatro ramas que ellos comparan en simulación — y resuelve con partición en tres tercios el bloqueo de los corpus seleccionados por el ganador, que ellos enuncian y demuestran.

**Los métodos.**

| Pieza | Fuente |
|---|---|
| La contracción misma | Stein (1956), James y Stein (1961); Robbins le dio el nombre, Efron y Morris la desarrollaron en los setenta |
| Dispersión estimada en conjunto | DerSimonian y Laird; Paule y Mandel |
| Auditar el ruido con A/A | *Q* de Cochran (1954) |
| Evaluación fuera de muestra | *Data thinning*, [Neufeld, Dharamshi, Gao y Witten (*JMLR* 2024)](https://jmlr.org/papers/v25/23-0446.html) |
| Factores locales por experimento | *Bayesian Hybrid Shrinkage*, [Mudd, Friedberg, Gorbachev, Nassif y Zaidi (Meta, 2025)](https://arxiv.org/abs/2511.06318) |
| Regla de probabilidad de cola, y que la función de pérdida cambia el orden óptimo | [Gu y Koenker (*Econometrica*, 2023)](https://www.econometricsociety.org/publications/econometrica/2023/01/01/invidious-comparisons-ranking-and-selection-as-compound-decisions) |
| Que la independencia previa puede fallar y empeorar el cribado | [Chen (*Econometrica* 94(2), 2026)](https://arxiv.org/abs/2212.14444) |
| El régimen donde la aproximación gaussiana flaquea | Chen y Lei (dic-2025) |
| Que seleccionar es más fácil que estimar | [Coey y Hung (Meta)](https://arxiv.org/abs/2210.03905) |
| Ranking y umbral como sesgos distintos | La literatura de genética los separa: sesgo de ranking y sesgo de selección |
| Los datos | [Matias, Munger, Aubin Le Quéré y Ebersole (*Scientific Data*, 2021)](https://www.nature.com/articles/s41597-021-00934-7) |

**Y el problema de fondo**, documentado en subastas desde 1971, en genética, en ensayos clínicos de dosis, en evaluación docente y en selección de gestores de inversión. Es el mismo problema con seis nombres; lo que cambia es qué se elige y cuánto cuesta equivocarse.
