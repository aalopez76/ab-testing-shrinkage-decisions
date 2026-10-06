> **Archived.** Written in Spanish before the final methodological revision, and
> retained for provenance. It predates the four-decision framing, the BHS
> extension and the cluster-bootstrap intervals, so its conclusions do not match
> the current `README.md`. Superseded, not corrected.

# Pruebas A/B: el problema oculto

*La variante que gana un experimento casi siempre promete más de lo que entrega. Hay varias formas de corregirlo, publicadas en los últimos catorce meses, y no está claro cuál conviene. Esto es el trabajo de averiguarlo.*

---

El comercio electrónico decide qué recomendación mostrar. Las plataformas de transporte y reparto deciden qué promoción enviar. La banca decide qué oferta de crédito presentar, el sector farmacéutico qué presentación llevar al mercado, la industria automotriz y el comercio minorista qué versión de su campaña emitir.

En todos esos casos el problema es el mismo —entre varias opciones, cuál desplegar— y el camino para resolverlo también: se prueban las opciones en paralelo sobre grupos asignados al azar, se mide cuál rinde mejor, y se despliega esa.

Según el sector, ese procedimiento tiene nombres distintos. Las plataformas digitales corren **experimentos en línea**, conocidos como **pruebas A/B**. El comercio minorista, la banca y la agricultura corren **experimentos de campo**. El sector farmacéutico corre **ensayos clínicos**. Son tres tradiciones separadas con el mismo esqueleto estadístico, y su diseño es sólido: la asignación aleatoria garantiza que la comparación mida el efecto de la opción y no una diferencia previa entre los grupos. Sobre eso no hay discusión.

Pero queda algo que el diseño no resuelve. Lo que se mide en cada variante es **el efecto real más ruido**: la parte sistemática que se repetiría si se volviera a correr el experimento, y la parte que depende de a quién le tocó qué. A esa segunda parte la llamaremos, en todo este artículo, **suerte** — es ruido de muestreo, nada más.

Y entonces: **de la ventaja que mostró la variante ganadora, ¿cuánto es efecto real y cuánto es suerte?**

## Antecedentes

Las organizaciones que deciden así no corren un experimento: corren muchos en paralelo. Cada ajuste de un sistema de recomendación, cada rediseño, cada campaña pasa por una prueba antes de desplegarse. En las plataformas grandes eso significa **miles de experimentos concurrentes**, según describe el equipo de experimentación de Meta Platforms.

Y la mayoría no encuentra una mejora:

| Organización | Resultado | Fuente |
|---|---|---|
| Google y Bing | **10%–20%** de los experimentos producen resultados positivos | Kohavi y Thomke, *Harvard Business Review*, sep–oct 2017 ✓ |
| Microsoft | **un tercio** positivo y significativo · **un tercio** plano · **un tercio** negativo y significativo | Kohavi, keynote KDD 2015 ✓ (texto literal) |

Del keynote de KDD conviene citar la frase exacta, porque es más fuerte que su paráfrasis: *«la mayoría de los experimentos muestran que las funcionalidades no logran mover las métricas que fueron diseñadas para mejorar»*. Y sobre Bing añade, sin dar número: *«la tasa de éxito es menor»*.

Vale detenerse en el último renglón, porque es contraintuitivo: **una de cada tres ideas que un equipo consideró lo bastante buena para probarla deteriora precisamente aquello que buscaba mejorar.** Y si solo una de cada cinco funciona, encontrarla importa mucho.

El camino habitual para encontrarla es quedarse con la variante que mostró el mejor resultado medido.

## El fallo no es disciplinario

Ahí está el problema: **quedarse con el mejor resultado medido no es lo mismo que quedarse con la mejor variante.** Y la razón no tiene que ver con el rigor de quien analiza. Es cuantificable.

Cuando un experimento tiene **poca potencia estadística** —pocos usuarios en relación con el tamaño del efecto que busca detectar—, la medición de cada variante viene con mucha suerte encima. En ese régimen ocurre algo que no es evidente a primera vista:

> La única forma de que un efecto real pero pequeño destaque en una muestra chica es que **la suerte lo haya empujado por encima de su valor verdadero**.

Eso tiene nombre y tiene fórmula. Gelman y Carlin (2014) lo llaman **error de tipo M**, o **razón de exageración**: el factor por el cual un efecto que pasó el umbral de significancia queda, en promedio, exagerado. Y dan la magnitud: **cuando la potencia cae por debajo de 0.5, la razón de exageración se dispara.** Por debajo de 0.1 aparece además el error de tipo S, y la estimación significativa tiende a tener **el signo equivocado**.

Dicho de otra manera: en una prueba sub-potenciada, **el solo hecho de que una variante destaque garantiza que su medición está inflada**. No es un error de cálculo ni un sesgo del analista. Es la consecuencia inevitable de elegir el máximo entre cantidades ruidosas.

Probablemente ya lo has vivido. Un producto con cinco estrellas y siete reseñas frente a otro con 4.3 y dos mil. El de cinco gana la comparación, se compra, y decepciona — mientras el de 4.3 habría cumplido. El de siete reseñas no es mejor: es el que tuvo la suerte suficiente para parecerlo, porque con siete opiniones basta con que las primeras salgan bien. Con dos mil ya no hay espacio para esa suerte. **Elegir la variante con el mejor resultado medido es exactamente eso, a escala industrial.**

El término para el fenómeno viene de otro campo: en 1971, tres ingenieros petroleros —Capen, Clapp y Campbell— lo bautizaron **maldición del ganador** al explicar por qué las compañías perdían dinero «año tras año» en subastas de concesiones, donde ganar significaba haber sido quien más sobreestimó el yacimiento.

El costo es concreto y cualquiera que haya trabajado con métricas lo reconoce. El equipo de producto reporta una mejora de varios puntos en conversión, se despliega a todos los usuarios, y el indicador no se mueve. Nadie hizo nada mal; la mejora nunca fue de ese tamaño. Repetido durante suficiente tiempo, el efecto secundario es peor que el error: **la organización deja de creerle a sus propios experimentos**, que era justamente el sistema que debía resolver las discusiones.

## Actualidad: hay herramientas, y son muy nuevas

Esto no es una curiosidad académica. Es un problema que la industria y la estadística trabajan activamente, y la producción reciente es densa — lo que importa, porque significa que un equipo que quiera corregirlo hoy tiene que elegir entre varias opciones.

La herramienta común a todas se llama **Bayes empírico**, y en una frase dice: *cuando se estiman muchas cantidades parecidas y cada estimación trae ruido, conviene acercar cada una a lo que dicen las demás.* A ese acercamiento se le llama **contracción** (*shrinkage*). Quien quiera el porqué en versión accesible, el lugar clásico es Efron y Morris, «Stein's paradox in statistics», *Scientific American*, 1977.

Sobre esa base:

| Cuándo | Quién | Qué aporta |
|---|---|---|
| abr 2019 | Dimmery, Bakshy y Sekhon (**Facebook**) | Contracción de Bayes empírico para experimentos de varios brazos, sobre 17 experimentos internos |
| 2024 | Neufeld y coautores (**JMLR**) | **Data thinning**: partir una observación en dos partes independientes |
| dic 2024 | Sudijono, Ejdemyr, Lal y Tingley (**Netflix**) | Reencuadran el asunto como optimización: qué experimentos correr y cuándo lanzar |
| **dic 2025** | **Chen y Lei** | Contracción **directa para binomiales**, sin aproximación gaussiana, pensada para proporciones y muestras pequeñas |
| nov 2025 | Li | La contracción se vuelve **local**: vecindarios en lugar del promedio global |
| nov 2025 | Mudd y coautores (**Meta**) | La maldición del ganador de frente, con contracción local por experimento |
| **mar 2026** | **Chen**, *Econometrica* 94(2) | `close`: relaja el supuesto de que el parámetro es independiente de la precisión de su medición |
| **abr 2026** | **Neufeld, Perry y Witten** | Revisión de la inferencia condicionada a la selección, con «inferencia sobre un ganador» como caso central |
| sep 2026 | **Spotify** | **Dice que no**: la previa es difícil de calibrar y **mal calibrada puede empeorar** las cosas |

Siete de esas nueve entradas son de los últimos catorce meses. Y la última merece detalle, porque es la que convierte esto en una decisión y no en una receta: el equipo de ingeniería de Spotify explicó [por qué no adopta pruebas A/B bayesianas](https://engineering.atspotify.com/2026/9/why-spotify-is-not-using-bayesian-a-b-testing). Reconocen que una previa informativa reduce el sesgo, pero advierten que mantenerla **bien calibrada** a través de métricas y programas es extremadamente exigente, y que **una previa mal calibrada puede empeorar la precisión** frente a lo que ya tenían. Falla, dicen, cuando el historial mezcla distribuciones de efecto distintas, cuando esas distribuciones cambian con el tiempo y cuando no hay suficiente historia experimental.

## El problema, dicho con precisión

Un equipo que hoy quiera dejar de desplegar variantes sobreestimadas se encuentra con esto: **métodos publicados en el último año y medio, con supuestos distintos, y dos empresas de referencia diciendo cosas opuestas sobre si conviene usarlos.** Meta y Netflix invierten en la infraestructura; Spotify la rechaza por escrito. Las dos posiciones son razonadas y no pueden ser ambas correctas para todos.

Así que el problema de este trabajo no es inventar una corrección. Es responder, con evidencia:

> **¿Cuál de las correcciones disponibles lleva a mejores decisiones de despliegue, cuánto mejora, y en qué condiciones conviene no usar ninguna?**

## Por qué importa resolverlo bien

Tres razones, en orden de peso.

**Porque el costo de elegir mal no es simétrico.** Si la corrección funciona y no se usa, se dejan mejoras sobre la mesa. Pero si se usa mal —el escenario que Spotify describe— **se decide peor que no corrigiendo nada**. No es una herramienta que se pueda adoptar por si acaso: equivocarse tiene un costo propio.

**Porque quien decida hoy no tiene en qué apoyarse.** Toda la evidencia publicada está medida sobre datos internos: diecisiete experimentos de Facebook, el historial de Netflix, los experimentos de Meta. Nadie fuera de esas empresas puede reproducirla, cuestionarla ni comprobar si aplica a su caso. Un equipo que lea los dos lados y quiera decidir se queda con una discusión de autoridad.

**Porque la confianza en el sistema es lo que está en juego.** Una plataforma de experimentación existe para que las decisiones dejen de depender de quién argumenta mejor. Si entrega mejoras que no se materializan, pierde esa función — y recuperarla cuesta más que haberla cuidado.

Este trabajo no va a cerrar la discusión. Aporta **un dato público, reproducible y verificable** donde hoy solo hay evidencia privada, y dice con claridad dónde funciona y dónde no.

## Cómo se aborda

El criterio es uno y se declara antes de mirar nada:

> **Los métodos se juzgan por las decisiones que producen, no por si cumplen sus propios supuestos.**

Eso importa porque la alternativa es tentadora y está mal. Un método con supuestos impecables puede ser la elección equivocada si optimiza lo que no se paga —por ejemplo, el error de estimación cuando lo que cuesta es la decisión. Y un método con un supuesto violado puede decidir mejor de todos modos: la robustez es un hecho que se mide, no algo que se deduzca.

De ahí sale el orden de trabajo:

**1. Medir.** Qué método elige mejor la variante, evaluado en información que no participó en elegirla.

**2. Explicar.** Los diagnósticos vienen después y sirven para entender el resultado, no para filtrar candidatos de entrada. Si la versión estándar pierde, interesa saber por qué: puede ser el régimen de proporciones pequeñas que señalan Chen y Lei, o la dependencia entre el parámetro y la precisión de su medición que trata Chen, o la calibración que preocupa a Spotify.

**3. Descartar, con la razón nombrada.** Y las razones no son todas del dato. Un método puede quedar fuera por **alcance** —el trabajo de Netflix optimiza a nivel de programa, no la elección dentro de un experimento—, por **la naturaleza del dato**, por **costo operativo** —una implementación de referencia en otro lenguaje es un costo real que hay que declarar, no omitir— o simplemente porque **no sobrevive la comparación**. Nombrar bien el motivo es parte del trabajo: un descarte por alcance se lee distinto de uno por rendimiento.

Se implementan **dos** métodos, no todos: la contracción estándar, porque es lo que usa la industria y es la referencia que hay que batir o confirmar, y **una** alternativa. Más de dos no se termina, y un proyecto sin terminar no demuestra nada.

## Los datos

El **Upworthy Research Archive**, publicado por Matias, Munger, Aubin Le Quere y Ebersole en *Scientific Data* (2021) y disponible en [OSF](https://osf.io/jd64p/).

Upworthy fue un medio digital que entre 2013 y 2015 probaba titulares e imágenes **como operación diaria**: para cada historia escribía varias versiones, las mostraba al azar a distintos visitantes y registraba impresiones y clics. No es un experimento diseñado para investigar: es trabajo comercial real que quedó archivado.

Abriendo los archivos —no copiando la documentación— la escala es:

```
MUESTRA EXPLORATORIA, tras la exclusión (cifras de reports/results/01_panel.json)
  3,380 experimentos | 16,629 brazos | 58.8M impresiones
  2 a 14 brazos por experimento (media 4.92)
  mediana de 3,136 impresiones por brazo | tasa de clic 1.28%
  68 semanas | 295 experimentos A/A | 1,589 varían solo el titular

La exclusión deja fuera 1,493 de 4,873 experimentos (30.6%);
se conserva el 69.4%.
```

Las cifras del confirmatorio se producirán al correrlo, **una sola vez, con el método ya congelado**.

> **Nota de la fase A.** Varias cifras de las versiones anteriores de este documento estaban mal: citaban los totales **antes** de la exclusión y una definición laxa de A/A. Las de arriba salen del código. Es el motivo por el que existe la regla de que ninguna cifra entra a un documento sin un script que la produzca.

Tres razones para elegir estos datos. **Son aleatorizados**, así que el efecto está identificado por diseño y no hay supuestos de identificación que defender: todo el esfuerzo va a la estimación y a la decisión, que es lo que está en cuestión. **Son públicos**, que es la carencia del estado del arte. Y **el régimen es exactamente el del problema**: con 3,136 impresiones por variante y una tasa base de 1.28%, el error estándar de cada medición ronda **0.23 puntos porcentuales** mientras la dispersión observada entre variantes del mismo experimento es de 0.35 — de donde se sigue que **una parte sustancial de la variación aparente entre variantes es suerte**. Poca potencia, de fábrica, 27 616 veces, justo donde Gelman y Carlin advierten que la exageración se dispara.

Hay además 295 experimentos donde **nada cambiaba entre variantes**: comparaciones de algo contra sí mismo. Ahí la diferencia real es cero por construcción, así que toda la dispersión observada **es** suerte. Son una vara de medir independiente para el modelo de ruido, y aparecerán en el paso 2.

## El recorrido

Seis pasos. El detalle de cada uno —notación, estimadores, inferencia— está en el `README.md` del repositorio; aquí va lo que cambia el resultado.

**Comprobar que el sorteo fue un sorteo.** El equipo del archivo advirtió en junio de 2024 que una mala configuración de la caché de Cloudflare, el 25 de junio de 2013, hizo que durante meses se mostrara una sola variante. Afecta a ~22% de las pruebas y desaconsejan usarlas para inferencia causal. Los CSV públicos no traen la columna que las marca, así que se verificó desde cero con una prueba de bondad de ajuste de las impresiones por brazo. Reproduce el fallo mes a mes —22.3% en junio de 2013, 86.4% en diciembre, 11.0% en enero de 2014, y entre 0.0% y 0.9% después— y se excluye esa ventana. Queda el 69.4% del archivo, y el periodo conservado corre a la tasa que se esperaría por azar.

**Comprobar que el ruido está bien medido.** Toda contracción depende de la varianza de cada medición, y aquí hay una vara independiente: los experimentos donde **nada varía entre brazos**. Ahí la diferencia verdadera es cero por construcción, así que la dispersión observada debería igualar la calculada. No lo hace: la *Q* de Cochran vale **1.94 veces** sus grados de libertad en el exploratorio y 1.93 en el confirmatorio. El modelo binomial subestima el ruido cerca del doble. Dos explicaciones —impresiones no independientes, o variación en campos que el archivo no publica— que **no son distinguibles** con estos datos, y las dos se declaran.

**Contraer.** Un promedio ponderado entre lo que dice cada medición y el centro de su grupo, con un peso que compara el ruido contra la dispersión real. Esa dispersión no se observa y, con 2 a 14 brazos por experimento, estimarla dentro de cada uno sería usar un dato ruidoso para decidir cuánto confiar en datos ruidosos. Se estima **en conjunto**, con los métodos que el meta-análisis desarrolló para combinar muchos estudios.

**Medir sin hacer trampa.** Para saber cuánto se infló el ganador hay que medirlo donde no participó en ser elegido. La muestra de reserva del archivo no sirve —son experimentos *distintos*, comprobado en la documentación— así que se parte cada brazo: de sus impresiones, una parte elige y el resto evalúa, repartiendo los clics de forma hipergeométrica. Para la familia a la que pertenece la binomial eso produce **dos partes independientes** que suman la observación original; es exacto. Se llama *data thinning* (Neufeld y coautores, *JMLR* 2024), y no es *data fission*, que para la binomial no da partes independientes.

Y hubo que partir en **tres** tercios —uno elige, otro estima, otro evalúa— porque con dos la dispersión se estimaba en cero: el máximo de un experimento ya es un estadístico seleccionado, y el Bayes empírico supone una estimación que no lo sea.

**Comparar decisiones, no estimaciones.** Cuatro reglas: al azar, el máximo sin corregir, el máximo contraído y la probabilidad de cola posterior. Todas eligen con un tercio y se miden en otro. Con el criterio declarado antes de mirar: **gana la que decide mejor fuera de muestra**, no la que reduce el error.

**Y después explicar.** Los diagnósticos van al final, para entender el resultado y no para filtrar candidatos de entrada.

## El resultado

El método se congeló el 3 de octubre de 2026 —con el commit de git que lo respalda— y entonces se corrió la muestra confirmatoria, **una sola vez**. Lo que sigue son las dos muestras, lado a lado.

### Primero: la maldición del ganador es real y está medida

| | Exploratorio | Confirmatorio |
|---|---|---|
| Experimentos | 3 380 | 15 787 |
| **Inflación de la variante ganadora** | **0.236 pp** | **0.237 pp** |

Sobre una tasa base de 1.28%, eso es una **sobreestimación del 18% relativo**: la variante que un equipo desplegaría promete casi un 20% más de lo que entrega.

Y es un efecto de **selección**, no de medición: elegir una variante al azar da una inflación cien veces menor. Si no se selecciona, no hay maldición.

### Y ahora la pregunta del proyecto

| | Exploratorio | Confirmatorio |
|---|---|---|
| Error cuadrático medio, cruda → contraída | **-24.0%** | **-24.0%** |
| Correlación de orden con lo realizado | +0.3608 → +0.3662 | +0.3601 → +0.3656 |
| Ganancia realizada al 5% de presupuesto | 1.073 → 1.029 pp | 1.086 → 1.033 pp |

> **La contracción reduce el error de estimación un 24% y deja la decisión donde estaba.**

Idéntico en las dos muestras, con la segunda 4.7 veces más grande y jamás tocada durante el desarrollo.

La curva completa por presupuesto, en el confirmatorio (puntos porcentuales de ganancia realizada):

```
regla             5%       10%       25%       50%
azar          0.259    0.261    0.261    0.261
cruda         1.086    0.859    0.602    0.427
contraída     1.033    0.829    0.592    0.427
cola          0.862    0.731    0.556    0.421
oráculo       1.776    1.436    1.006    0.678
```

## Por qué, en los dos niveles

**Dentro de un experimento no puede cambiar la decisión, y eso se demuestra.** La contracción es θ̃ = (1−α)·θ̂ + α·centro. Si α y el centro son iguales para los brazos de un experimento, es una función monótona creciente de θ̂ y **conserva el orden**. Medido: α varía 0.009 entre los brazos de un mismo experimento, porque reciben tráfico parejo por diseño (razón de impresiones 1.04).

No es un fallo del método: es que **con brazos balanceados no había un problema de selección que mejorar**. Y es un caso que la literatura ya describe — Gu y Koenker (*Econometrica*, 2023) señalan que con varianza homogénea la media posterior, la probabilidad de cola y la expectativa de cola **dan el mismo orden**.

**Entre experimentos sí reordena, y ahí queda en empate.** La precisión varía 7 veces en impresiones y 2.6 en error estándar, así que α varía de verdad (media 0.43, desviación 0.17) y la contracción cambia el 23.4% de la selección. Pero la ganancia realizada no mejora.

## Dónde falla, y es la parte que lo explica

Con un presupuesto del 10%, estos son los experimentos que la contracción cambia:

| | Descarta | Añade |
|---|---|---|
| Ganancia realizada | **0.643 pp** | 0.530 pp |
| α | 0.695 | 0.320 |
| Impresiones | 4,161 | 7,283 |

**Contraer descarta los experimentos imprecisos y añade los precisos.** Eso es exactamente lo que la teoría dice que hace —bajo restricción de capacidad, la media posterior favorece a los de menor varianza— y en este corpus los que descarta tenían **más** ganancia real.

¿Por qué sale mal el canje? Porque **la independencia previa falla.** La contracción supone que el valor verdadero de un experimento es independiente de la precisión con que se midió. Medido:

```
correlación entre impresiones y tasa    cruda       -0.140
                                        por semana  -0.098
                                        por tipo    -0.138
```

**Sobrevive al control** por periodo y por tipo de experimento. En estos datos los experimentos con menos impresiones tienen tasas **más altas**, así que despreciar a los imprecisos —justo lo que hace la contracción— empuja sistemáticamente hacia los peores.

Es el modo de falla que la literatura documenta: los métodos que dependen de la independencia previa pueden dar peores medias posteriores, y **el cribado basado en ellas puede ser peor que con las estimaciones crudas**. Chen lo publicó en *Econometrica* en marzo de 2026; aquí está medido.

## Los métodos que quedaron fuera, con su razón

| Método | Por qué no | Tipo de descarte |
|---|---|---|
| Contracción binomial directa (Chen y Lei, dic-2025) | n·p mediana = 40 y **0%** de brazos bajo n·p < 10: la aproximación gaussiana no es el problema aquí | **Diagnóstico** |
| Optimización a nivel de programa (Netflix, dic-2024) | Optimiza qué experimentos correr y cuándo lanzar, no qué elegir dentro de una cartera dada | **Alcance** |
| `close` (Chen, *Econometrica*, mar-2026) | Implementación de referencia en R; el proyecto es Python. **Su diagnóstico sí se corrió**, y es el que explica el resultado | **Costo operativo** |
| Probabilidad de cola posterior | Pierde en los dos criterios, también en potencia. Consistente con que prefiera a los de **mayor** varianza, mal negocio cuando lo que se paga es la ganancia realizada | **No sobrevive la comparación** |

## Dos errores propios, por si sirven más que el resultado

**El factor de diseño no transfiere entre niveles.** El paso 1 midió que el modelo de ruido binomial subestima la dispersión un 94% (Q/gl = 1.94 en el exploratorio, 1.93 en el confirmatorio — replica). Apliqué ese factor a δ entre experimentos y **fabriqué un resultado falso**: que contraer *perjudica* la decisión en 0.27 puntos. Lo detecté con una referencia que no usa la varianza en absoluto —Cov(δ̂, δ realizado) estima Var(δ) directamente— y que da un factor de ~1.09 para δ. Con α correcto el perjuicio desaparece y queda el empate.

**Y τ² se estimaba en cero.** Porque δ = máximo − media **ya es un estadístico seleccionado**, y el Bayes empírico supone una estimación que no lo sea. Se resolvió partiendo en tres tercios: uno elige, otro estima, otro evalúa.

## Qué se lleva un equipo de experimentación

> **La contracción de Bayes empírico corrige la cifra que le reportas al negocio, no cuál variante lanzas.**

Tres consecuencias prácticas:

1. **Si tus experimentos están balanceados, no esperes que corrija la elección.** No puede: hay una razón algebraica, no un problema de implementación.
2. **Sí corrige la promesa.** Un 24% menos de error, y eso es lo que evita prometer mejoras que no llegan.
3. **Antes de adoptarla, comprueba la independencia previa.** Aquí falla, y por eso el canje que hace sale mal. Es una correlación que se mide en tres líneas.

Y una advertencia sobre el alcance: esto es **un corpus, de un medio digital, entre 2013 y 2015**, y no cierra la discusión entre quienes adoptan la corrección y quienes la rechazan.

## Quién llegó antes, y qué queda por medir

**Coey y Hung** (Meta), en *Empirical Bayes Selection for Value Maximization*, hacen esta misma pregunta —Bayes empírico para **seleccionar**, no para estimar—, con cotas de arrepentimiento demostradas, **sobre este mismo archivo**, y publicaron su código. Su tesis, en el abstract: *«seleccionar las mejores unidades es fundamentalmente más fácil que estimar sus valores»*.

La pregunta no es mía y el teorema tampoco. Lo que encontré al buscar es que **su montaje impone dos condiciones**, descritas en su apéndice:

> *«Filtramos los pares artículo-paquete con menos de 1 000 impresiones o 100 clics, para asegurar que las aproximaciones de normalidad sean razonables.»*
>
> *«Consideramos **arbitrariamente** el de más impresiones como grupo de control y el de segundas más impresiones como tratamiento, **omitiendo cualquier otro paquete** de ese artículo.»*

La segunda importa más de lo que parece: elegir «el de más impresiones» **no es seleccionar por resultado**, así que su montaje —por construcción— no contiene la maldición del ganador. Y evalúan contra una verdad **simulada** desde una previa ajustada, no contra resultados reales.

La primera condición conserva el **6.9%** de los brazos del archivo. Así que la pregunta es verificable: **¿su conclusión vale fuera de ese 6.9%?**

| Al 5% de presupuesto | Su régimen | Archivo completo |
|---|---|---|
| Experimentos | 1,277 | 15,787 |
| n·p mediana | 131 | 40 |
| Error cuadrático medio | -32.8% | -23.9% |
| **Ganancia, contraída − cruda** | **+0.0148 pp** | **-0.0556 pp** |
| IC 95% | [-0.0153, +0.0448] | [-0.0619, -0.0493] |
| Contraer gana en | 55% de las particiones | 0% |
| ¿Se distingue de cero? | **No** | **Sí** |

**En el régimen que ellos conservan, contraer es neutro para la decisión** —el intervalo cruza el cero y gana en la mitad de las particiones—, que es lo que su teorema predice: si seleccionar ya es fácil, mejorar el estimador no cambia la selección.

**Fuera de él, en el 93% del archivo que su filtro descarta, degrada la selección de forma medible**: pierde en las 40 particiones, y el intervalo no toca el cero.

No es un cambio de signo —y conviene no venderlo así—, es un **límite de validez**. Y tiene el mecanismo ya medido detrás: la independencia previa falla (−0.14, sobrevive al control), y el régimen de pocas impresiones es justo donde la precisión varía más, así que es ahí donde despreciar a los imprecisos hace más daño.

Lo que aporta este trabajo, entonces, no es la pregunta ni la teoría. Es **medirla donde sus autores no la midieron**: contra resultados reales reservados en lugar de simulados, conservando el máximo sobre 2 a 20 brazos —donde vive la maldición— y sin filtrar el régimen incómodo, sino diagnosticándolo.

## Lo que queda fuera

Este trabajo no estima qué tipo de titular funciona mejor: eso ya lo respondieron Robertson y coautores en *Nature Human Behaviour* (2023) con este mismo archivo. No propone ningún método nuevo: todos están publicados y la tabla de la sección de actualidad dice quién los desarrolló. Y no trata el caso en que las opciones están **ordenadas** —dosis, precios, niveles de descuento—, donde cada opción puede pedirle información prestada a sus vecinas inmediatas; ese es el tema del trabajo hermano.

Lo que aporta es una elección de método justificada con evidencia, sobre datos que cualquiera puede descargar, en un problema donde hoy solo hay evidencia privada y dos posiciones encontradas.

---

*Los datos, el código y las cifras de este artículo se reproducen desde el repositorio. Las referencias con enlace fueron verificadas. Las citas a Gelman y Carlin (2014), Capen, Clapp y Campbell (1971), Efron y Morris (1977), DerSimonian y Laird, y Paule y Mandel están pendientes de verificación bibliográfica directa antes de la publicación final.*
