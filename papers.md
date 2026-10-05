# Referencias

Los trabajos que se revisaron durante el desarrollo de este proyecto, con la referencia exacta y qué aportó cada uno. Se marcan por separado los que **sostienen una decisión de método** y los que se consultaron para encuadrar el problema o se descartaron con su razón.

---

## 1. Los datos

**Matias, J. N., Munger, K., Aubin Le Quéré, M. y Ebersole, C.** (2021). *The Upworthy Research Archive, a time series of 32,487 experiments in U.S. media*. **Scientific Data** 8, 195.
DOI: [10.1038/s41597-021-00934-7](https://doi.org/10.1038/s41597-021-00934-7) · Datos: [osf.io/jd64p](https://osf.io/jd64p/)

> El archivo que usa el proyecto. Aporta la aleatorización real, los experimentos A/A y la partición exploratorio/confirmatorio que permite congelar el método.

**Matias, J. N., Munger, K., Aubin Le Quéré, M. y Ebersole, C.** (2024). *Author Correction: The Upworthy Research Archive, a time series of 32,487 experiments in U.S. media*. **Scientific Data** 11.
DOI: [10.1038/s41597-024-03575-8](https://doi.org/10.1038/s41597-024-03575-8)

> La corrección que documenta el fallo de caché de Cloudflare del 25 de junio de 2013. Afecta a ~22% de las pruebas y desaconseja usarlas para inferencia causal. **Los CSV públicos no traen la columna que las identifica**, así que el proyecto reconstruyó la ventana afectada desde cero.

---

## 2. El origen del método

**Stein, C.** (1956). *Inadmissibility of the usual estimator for the mean of a multivariate normal distribution*. En **Proceedings of the Third Berkeley Symposium on Mathematical Statistics and Probability**, vol. 1, pp. 197–206. University of California Press.

> La demostración de que el estimador por máxima verosimilitud es inadmisible en tres o más dimensiones. El resultado del que nace toda la familia.

**James, W. y Stein, C.** (1961). *Estimation with quadratic loss*. En **Proceedings of the Fourth Berkeley Symposium on Mathematical Statistics and Probability**, vol. 1, pp. 361–379. University of California Press.

> El estimador explícito. Stein había anunciado la inadmisibilidad en 1956 con una prueba no constructiva; aquí aparece la forma cerrada.

**Robbins, H.** (1956). *An empirical Bayes approach to statistics*. En **Proceedings of the Third Berkeley Symposium on Mathematical Statistics and Probability**, vol. 1, pp. 157–163. University of California Press.

> Quien le dio el nombre de «Bayes empírico» al enfoque: estimar la previa de los propios datos en lugar de postularla.

**Efron, B. y Morris, C.** (1975). *Data analysis using Stein's estimator and its generalizations*. **Journal of the American Statistical Association** 70(350), 311–319.
DOI: [10.1080/01621459.1975.10479864](https://doi.org/10.1080/01621459.1975.10479864)

> Quienes lo convirtieron en una herramienta aplicable y lo difundieron fuera de la estadística matemática.

---

## 3. Los estimadores que implementa el proyecto

**Cochran, W. G.** (1954). *The combination of estimates from different experiments*. **Biometrics** 10(1), 101–129.
DOI: [10.2307/3001666](https://doi.org/10.2307/3001666)

> La *Q* que el proyecto usa para auditar el modelo de ruido contra los experimentos A/A. **Resultado: Q/gl = 1.940 en el exploratorio y 1.927 en el confirmatorio; el modelo binomial subestima el ruido cerca del doble.**

**DerSimonian, R. y Laird, N.** (1986). *Meta-analysis in clinical trials*. **Controlled Clinical Trials** 7(3), 177–188.
DOI: [10.1016/0197-2456(86)90046-2](https://doi.org/10.1016/0197-2456(86)90046-2)

> Estimador de momentos de la dispersión entre estudios, en forma cerrada. Implementado en `src/wcab/shrinkage/dispersion.py`.

**Paule, R. C. y Mandel, J.** (1982). *Consensus values and weighting factors*. **Journal of Research of the National Bureau of Standards** 87(5), 377–385.
DOI: [10.6028/jres.087.022](https://doi.org/10.6028/jres.087.022)

> Estimador iterativo de la dispersión, por bisección sobre *Q*. Es el que usa el proyecto por defecto.

**Neufeld, A., Dharamshi, A., Gao, L. L. y Witten, D.** (2024). *Data thinning for convolution-closed distributions*. **Journal of Machine Learning Research** 25(57), 1–35.
[jmlr.org/papers/v25/23-0446.html](https://jmlr.org/papers/v25/23-0446.html)

> **La pieza que hace posible la evaluación.** Permite partir los conteos de un brazo en mitades **marginalmente independientes** que suman la observación original — de forma hipergeométrica para la binomial, y de manera exacta, no aproximada. Sin esto no hay forma de medir fuera de muestra sin datos extra.
>
> **No confundir con *data fission*** (Leiner, Duan, Tibshirani y Ramdas), que para la binomial no produce partes independientes.

**Mudd, R., Friedberg, R., Gorbachev, I., Nassif, H. y Zaidi, A.** (2025). *Breaking the Winner's Curse with Bayesian Hybrid Shrinkage*. Meta Platforms. Presentado en **Conference on Digital Experimentation @ MIT (CODE@MIT'25)**.
arXiv: [2511.06318](https://arxiv.org/abs/2511.06318)

> La variante más reciente, implementada en `src/wcab/shrinkage/bhs.py`. Añade factores de contracción **locales** por experimento mediante una previa inversa-gamma sobre la escala, lo que equivale a una previa t de Student.
>
> El propio artículo nombra su caso base: con λᵢ = 1 para todo i se reduce a lo que llaman *«Bayesian Global Shrinkage»*, que es la contracción estándar.
>
> **Es una ponencia de congreso, no un sistema de producción documentado.**

---

## 4. El marco de la decisión

**Schultzberg, M. y Frånberg, M.** (2026). *Bayesian Inference Procedures for A/B Testing: An Overview*. Experimentation Platform team, Confidence, Spotify.
arXiv: [2608.12949](https://arxiv.org/abs/2608.12949) (13 de agosto de 2026)

> **El marco del que cuelga todo el proyecto.** Organiza las configuraciones bayesianas en tres niveles según la fuerza de su control de error, y establece que el Bayes empírico es el único camino al tercero.
>
> Dos frases que el proyecto usa directamente. La del cierre: *«las tasas de error, la exactitud de estimación y el arrepentimiento son riesgos distintos, y el método apropiado se sigue de los riesgos que un programa de experimentación necesita controlar, no al revés»*.
>
> Y la del abstract, que enuncia el bloqueo que el proyecto resuelve: *«los corpus seleccionados por el ganador, los programas agrupados y las métricas heterogéneas pueden impedir la calibración **independientemente del tamaño del corpus**»*. Demuestran además que *«recoger más datos de la misma fuente sesgada no ayuda»*. La respuesta del proyecto es la partición en tres tercios.

**Gu, J. y Koenker, R.** (2023). *Invidious Comparisons: Ranking and Selection as Compound Decisions*. **Econometrica** 91(1), 1–41.
DOI: [10.3982/ECTA19304](https://doi.org/10.3982/ECTA19304)

> Que la función de pérdida cambia cuál es el orden óptimo. Dos resultados que el proyecto usa:
>
> - Con **varianza homogénea**, la media posterior, la probabilidad de cola y la expectativa de cola **dan el mismo orden**. Es el caso degenerado en el que cae la decisión 1 del proyecto, y explica por qué contraer no puede cambiar qué variante se despliega.
> - Bajo restricción de capacidad, la media posterior **favorece a los de menor varianza** y la probabilidad de cola **prefiere a los de mayor varianza**. Explica por qué la regla de cola pierde cuando el criterio es la ganancia realizada.

**Chen, J.** (2026). *Empirical Bayes When Estimation Precision Predicts Parameters*. **Econometrica** 94(2).
arXiv: [2212.14444](https://arxiv.org/abs/2212.14444)

> Que el supuesto de independencia previa puede fallar, y que cuando falla **el cribado basado en estimaciones contraídas puede ser peor que con las crudas**. Es el diagnóstico que explica el resultado principal del proyecto.
>
> **Medido aquí:** la correlación entre precisión y resultado es −0.119 cruda, −0.087 dentro de cada semana y −0.113 dentro de cada tipo de experimento. Sobrevive al control.
>
> Su implementación de referencia, `close`, está en R; el proyecto es Python. **Costo operativo declarado, no omisión**: el diagnóstico sí se corrió.

**Coey, D. y Hung, K.** (2022, rev. 2025). *Empirical Bayes Selection for Value Maximization*. Meta Platforms.
arXiv: [2210.03905](https://arxiv.org/abs/2210.03905) · Código: [github.com/facebookresearch/eb-selection](https://github.com/facebookresearch/eb-selection)

> **El antecedente más cercano: misma pregunta, mismo archivo.** Demuestran cotas de arrepentimiento y su tesis es que *«seleccionar las mejores unidades es fundamentalmente más fácil que estimar sus valores»* — que es, en teoría, el resultado que este proyecto mide en datos reales.
>
> Su montaje impone dos condiciones, descritas en su apéndice B: filtran los pares con menos de 1 000 impresiones o 100 clics *«para asegurar que las aproximaciones de normalidad sean razonables»* —lo que conserva el **6.9%** de las variantes—, y reducen cada experimento a **una pareja arbitraria** (el brazo con más impresiones contra el de segundas más), de modo que **su montaje no contiene la maldición del ganador**. Además evalúan contra una verdad simulada desde una previa ajustada.

---

## 5. El problema, en otros campos

**Capen, E. C., Clapp, R. V. y Campbell, W. M.** (1971). *Competitive bidding in high-risk situations*. **Journal of Petroleum Technology** 23(6), 641–653.
DOI: [10.2118/2993-PA](https://doi.org/10.2118/2993-PA)

> El origen del término. Tres ingenieros de Atlantic Richfield documentaron que las compañías ganadoras de las subastas de arrendamiento marítimo obtenían rendimientos inesperadamente bajos «año tras año».

**Forde, A., Hemani, G. y Ferguson, J.** (2023). *Review and further developments in statistical corrections for Winner's Curse in genetic association studies*. **PLoS Genetics** 19(9), e1010546.
DOI: [10.1371/journal.pgen.1010546](https://doi.org/10.1371/journal.pgen.1010546)

> **La distinción que justifica partir el problema en cuatro decisiones.** Separan el **sesgo de ranking**, que nace de ordenar un millón de variantes, del **sesgo de selección**, que nace de usar un umbral de significancia — atribuyéndola a Dudbridge y Newcombe. Son dos mecanismos distintos, y nada garantiza que una misma corrección arregle los dos.
>
> Es el campo que más ha trabajado la corrección; publican además el paquete de R `winnerscurse`.

**Gelman, A. y Carlin, J.** (2014). *Beyond power calculations: assessing Type S (sign) and Type M (magnitude) errors*. **Perspectives on Psychological Science** 9(6), 641–651.
DOI: [10.1177/1745691614551642](https://doi.org/10.1177/1745691614551642)

> La razón de exageración, que es lo que hace que la gravedad del problema **dependa de la potencia del propio experimento**: con 80% de potencia la exageración ronda el 13%; con 50%, el 40%; con 20%, supera el 130%.

---

## 6. La práctica en la industria

**Deng, A.** (2015). *Objective Bayesian Two Sample Hypothesis Testing for Online Controlled Experiments*. En **Proceedings of the 24th International Conference on World Wide Web (WWW '15 Companion)**, pp. 923–928.
DOI: [10.1145/2740908.2742563](https://doi.org/10.1145/2740908.2742563)

> Previas estimadas del histórico de experimentos en Bing. Es el antecedente de que la contracción esté **en producción** en Microsoft, no solo en artículos.

**Dimmery, D., Bakshy, E. y Sekhon, J.** (2019). *Shrinkage Estimators in Online Experiments*. En **Proceedings of the 25th ACM SIGKDD Conference (KDD '19)**.
arXiv: [1904.12918](https://arxiv.org/abs/1904.12918)

> Contracción en experimentos en línea con muchos brazos, sobre 17 experimentos internos de Facebook. El antecedente directo del trabajo posterior de Meta.

**Abadie, A., Agarwal, A., Imbens, G., Jia, S., McQueen, J., Stepaniants, S. y Torres, S.** (2023, rev. 2026). *Estimating the Value of Evidence-Based Decision Making*.
arXiv: [2306.13681](https://arxiv.org/abs/2306.13681)

> Bayes empírico paramétrico y no paramétrico evaluando **la calidad de la decisión** y no solo el error de estimación. Su conclusión: *«las reglas de decisión basadas en significancia estadística pueden dejar valor sin realizar y, en algunos casos, generar valor esperado negativo»*.

**Sudijono, T., Ejdemyr, S., Lal, A. y Tingley, M.** (2024). *Optimizing Returns from Experimentation Programs*. Netflix.
arXiv: [2412.05508](https://arxiv.org/abs/2412.05508)

> Optimización a nivel de **programa**: qué experimentos correr y cuándo lanzar. **Descartado por alcance**, no por calidad: no trata qué elegir dentro de una cartera ya dada, que es la decisión 2 de este proyecto.

**Schultzberg, M. et al.** (2026). *Why Spotify Is Not Using Bayesian A/B Testing*. Spotify Engineering (septiembre de 2026).
[engineering.atspotify.com](https://engineering.atspotify.com/2026/9/why-spotify-is-not-using-bayesian-a-b-testing)

> El contrapeso operativo, y lo que vuelve necesario el procedimiento de este proyecto. Reconocen que *«cualquier Bayes con una previa informativa centrada en cero reduce el sesgo de la maldición del ganador, y una previa empírica bien calibrada puede a menudo contrarrestarlo por completo»*, pero advierten que *«una previa mal especificada empeoró la precisión y la detección… activamente peor que las pruebas secuenciales de referencia»*.
>
> **No contradicen a Meta sobre si el método funciona**: discrepan sobre si una organización puede mantener el corpus calibrado.

**Kohavi, R. y Thomke, S.** (2017). *The Surprising Power of Online Experiments*. **Harvard Business Review**, septiembre–octubre de 2017.

> La fuente correcta de la cifra de que solo un 10–20% de los experimentos produce resultados positivos en Google y Bing. **No** proviene del keynote de KDD 2015, cuyo 10–20% se refiere a la asignación de tráfico.

---

## 7. Consultados y descartados, con su razón

**Chen, Y. y Lei, L.** (2025). *Compound Estimation for Binomials*.
arXiv: [2512.25042](https://arxiv.org/abs/2512.25042) (31 de diciembre de 2025)

> Tratan la binomial directamente en lugar de aproximarla por una normal, lo que importa para proporciones pequeñas y muestras chicas.
>
> **Descartado por diagnóstico, no por supuesto:** en estos datos n·p tiene mediana 40 y solo el 0.1% de las variantes cae por debajo de 10, así que la aproximación gaussiana no es la fuente del problema. La comprobación está en `scripts/06_donde_falla.py`.

**Leiner, J., Duan, B., Tibshirani, R. y Ramdas, A.** *Data fission: splitting a single data point*. **JASA**.
arXiv: [2112.11079](https://arxiv.org/abs/2112.11079)

> Revisado y **descartado por corrección**: para la binomial no produce partes independientes, que es justo lo que el proyecto necesita. Se usa *data thinning* en su lugar. La prueba que documenta la diferencia está en `tests/test_thinning.py`.

---

## Nota sobre el uso de estas referencias

Cada cifra que este proyecto atribuye a un trabajo publicado se verificó contra el texto original, no contra resúmenes ni citas de segunda mano. En dos casos la verificación corrigió afirmaciones que ya estaban escritas en los documentos del proyecto: la fuente real del 10–20% de experimentos exitosos, y el hecho de que Coey y Hung usan **este mismo archivo**, lo que obligó a retirar una afirmación de novedad que no se sostenía.

Las referencias anteriores a 1990 se citan por su edición original; las de arXiv indican la versión revisada cuando existe.
