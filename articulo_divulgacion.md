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

Y la mayoría no encuentra una mejora. Las cifras las publicaron quienes dirigieron esas plataformas:

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

### Primero: comprobar que el sorteo fue un sorteo

Antes de estimar nada hay que verificar que la asignación aleatoria funcionó. Es una comprobación que parece burocrática y en este caso no lo es.

En junio de 2024, el equipo que mantiene el archivo publicó una advertencia: una mala configuración de la caché de Cloudflare, el 25 de junio de 2013, provocó que durante meses se mostrara **una sola variante** a los visitantes hasta que la caché expiraba. Afecta a cerca del 22% de las pruebas, y sus responsables **desaconsejan expresamente usarlas para inferencia causal**. Añadieron una columna que las marca.

Los archivos públicos, descargados, son de 2020 y 2021 y no traen esa columna. Así que la verificación se hizo desde cero, con una prueba de bondad de ajuste de las impresiones por variante contra una asignación uniforme. El resultado reproduce el fallo documentado mes a mes:

```
feb–may 2013   2–5%     línea base esperada
jun 2013      21.8%     comienza (el fallo fue el día 25)
jul–dic 2013  56–88%    ventana del fallo
ene 2014      15.1%     se corrige a mitad de mes
feb 2014+     0.0–0.5%  tasa nominal: el resto del archivo está limpio
```

Se excluyen los experimentos creados entre junio de 2013 y enero de 2014. Queda cerca del 78% del archivo, y el periodo conservado **es** limpio: corre a la tasa que se esperaría por puro azar.

### Segundo: comprobar que el ruido está bien medido

Toda contracción depende de una cantidad: cuánta suerte trae la medición de cada variante. Para una proporción esa cantidad tiene fórmula cerrada, pero conviene comprobar que la fórmula describe **estos** datos.

Ahí entran los 295 experimentos sin variación. Si no hay diferencia real entre variantes, toda la dispersión observada debe corresponder exactamente a la suerte calculada. Si resulta mayor, el modelo subestima el ruido — que es precisamente el escenario de mala calibración que Spotify advierte.

Es una comprobación barata que rara vez se hace, y la diferencia entre aplicar una fórmula y saber si sus insumos valen. **Si falla, se reporta antes de seguir.**

### Tercero: contraer, de dos maneras y hacia dos sitios

La contracción es un promedio ponderado entre lo que dice cada variante y lo que dice el conjunto, con un peso que depende de una comparación: **cuánta suerte trae la medición, frente a cuánto difieren realmente las variantes entre sí.** Si la suerte domina, se le hace más caso al conjunto; si las diferencias reales dominan, a cada medición.

El problema práctico está en el segundo término: cuánto difieren realmente las variantes no se observa, hay que estimarlo. Y con 2 a 14 variantes por experimento, estimarlo dentro de cada experimento es usar un dato ruidoso para decidir cuánto confiar en datos ruidosos. La salida viene del meta-análisis, que enfrenta lo mismo desde los años ochenta: **se estima una sola dispersión con todos los experimentos juntos** (DerSimonian y Laird; Paule y Mandel).

Sobre esa base se cruzan los dos ejes del trabajo:

- **Qué método**: la contracción estándar contra una alternativa.
- **Hacia dónde**: el promedio de **todos** los experimentos, o el de **los parecidos** — los de semanas cercanas o titulares similares. Es el contraste de Li y el aporte de Meta, y con 68 semanas consecutivas se puede medir.

El ancho del vecindario es un parámetro que la fórmula no resuelve: se declara de antemano y se reporta cómo cambia el resultado al moverlo. Elegirlo mirando los datos de evaluación convertiría la validación en un ajuste.

### Cuarto: medir sin hacer trampa

Para saber cuánto se infló la ganadora hace falta medirla en datos que no participaron en elegirla. El archivo tiene una muestra de reserva, y parecería el lugar natural. **No lo es**: la documentación oficial confirma que la reserva son experimentos *distintos*, no más datos de los mismos.

La solución es un resultado reciente. De las impresiones de cada variante se toma una parte para elegir y el resto para evaluar, repartiendo los clics de forma hipergeométrica. Para la familia de distribuciones a la que pertenece la binomial, eso produce **dos partes independientes** que suman la observación original; es exacto, no una aproximación. Se llama **data thinning** (Neufeld y coautores, JMLR 2024).

Conviene señalar una confusión fácil, porque casi se cuela aquí: existe una técnica hermana, *data fission*, que para la binomial **no** sirve — produce componentes que no son independientes, y la independencia es justo lo que se necesita.

Con eso, la cantidad principal queda definida sin ambigüedad: **la diferencia entre lo que la variante elegida prometió en la mitad que la eligió, y lo que entregó en la mitad que no participó.**

### Quinto: comparar decisiones, no estimaciones

Se comparan las reglas eligiendo con una mitad y evaluando en la otra: elegir al azar —la referencia que hay que ganar—, elegir el máximo sin corregir, y elegir el máximo con cada corrección, global y local.

Y se miden tres cosas: lo que rindió la variante elegida, cuánto se perdió frente a la mejor variante disponible, y cómo cambia todo si solo se puede desplegar en una fracción de los experimentos.

Con el criterio declarado de antemano: **gana el método que decide mejor fuera de muestra.** No el que reduce el error de estimación — eso ya está medido por los trabajos citados. **Si ninguna corrección mejora la decisión, el resultado de este trabajo será que no la mejora**, y eso le daría la razón a Spotify sobre estos datos.

### Sexto: explicar el resultado

Recién aquí entran los diagnósticos, y su papel es entender lo que pasó:

- **El régimen de la proporción.** Chen y Lei muestran que el caso binomial no se comporta como el gaussiano, y que con proporciones y muestras pequeñas conviene trabajar la binomial directamente. Estos datos están en ese régimen.
- **La dependencia entre parámetro y precisión.** La contracción estándar supone que el valor verdadero de una variante es independiente de cuántas impresiones recibió. Chen (*Econometrica*, 2026) muestra que ese supuesto suele fallar, porque el tamaño de muestra puede seleccionar sobre el parámetro. En estos datos las impresiones no se repartieron al azar entre experimentos: fueron una decisión de la plataforma. Medirlo es directo, y hay que hacerlo con cuidado de no confundirlo con efectos de periodo.
- **La calibración**, del paso 2.

Ninguno de los tres decide qué método se usa: todos sirven para explicar por qué el que ganó, ganó.

### Y lo que no es opcional: dónde falla

La contracción mejora el conjunto y, en casos concretos, perjudica. Interesa en qué fracción de experimentos la corrección elige peor que no corregir, y qué caracteriza a esos experimentos. Omitirlo sería contar la mitad — y sería darle la razón a Spotify sin haberla medido.

## Lo que queda fuera

Este trabajo no estima qué tipo de titular funciona mejor: eso ya lo respondieron Robertson y coautores en *Nature Human Behaviour* (2023) con este mismo archivo. No propone ningún método nuevo: todos están publicados y la tabla de la sección de actualidad dice quién los desarrolló. Y no trata el caso en que las opciones están **ordenadas** —dosis, precios, niveles de descuento—, donde cada opción puede pedirle información prestada a sus vecinas inmediatas; ese es el tema del trabajo hermano.

Lo que aporta es una elección de método justificada con evidencia, sobre datos que cualquiera puede descargar, en un problema donde hoy solo hay evidencia privada y dos posiciones encontradas.

---

*Los datos, el código y las cifras de este artículo se reproducen desde el repositorio. Las referencias con enlace fueron verificadas. Las citas a Gelman y Carlin (2014), Capen, Clapp y Campbell (1971), Efron y Morris (1977), DerSimonian y Laird, y Paule y Mandel están pendientes de verificación bibliográfica directa antes de la publicación final.*
