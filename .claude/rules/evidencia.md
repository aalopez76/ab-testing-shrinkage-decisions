# Regla: toda afirmación necesita respaldo

Sostiene el marco del proyecto: demostración de oficio, no descubrimiento. Vale para el README, el artículo, el HANDOFF, los comentarios del código y cualquier texto que salga del repositorio.

## 1. Cifras

**Ninguna cifra entra a un documento si no la produce un script del repositorio.**

El rastro es mecánico: cada script de `scripts/` escribe su JSON en `reports/results/`, y toda cifra de un documento debe poder señalarse como *«script → archivo → clave»*.

- Nada de redondear de memoria, copiar de una sesión anterior o reusar un número de la conversación.
- Si una cifra cambia porque cambió el código, se actualiza el documento en el mismo commit.
- Las cifras de escala del dato —experimentos, brazos, impresiones— también cuentan.

## 2. Referencias

**Ninguna referencia se escribe sin haberla verificado.**

- Las verificadas llevan ✓ en el README; las demás dicen *pendiente de verificar*, y **no se escriben en ningún entregable** hasta comprobarlas.
- Verificar significa abrir la fuente y confirmar autores, año, título y la afirmación que se le atribuye. No basta recordarla.
- **Verificar también la prioridad.** El artículo de Meta tiene dos registros en arXiv: noviembre de 2025 y marzo de 2026. Citar el segundo como la aparición sería inexacto.
- Si no se pudo verificar, se dice. No se cita.

## 3. El guardarraíl contra convertir un hallazgo en tesis

Este es el modo de falla propio de este proyecto, y ya ocurrió tres veces durante su planteamiento.

> **Si un hallazgo parece lo bastante importante para ser el titular, ésa es la señal de degradarlo a paso.**

El proyecto **no tiene tesis**. Todo hallazgo entra como una comprobación dentro del paso donde apareció, con su cita y su número. La diferencia es de peso, no de contenido:

| Como tesis | Como paso |
|---|---|
| «Descubrí que el campo descansa sobre un supuesto falso» | «Comprobé los supuestos del método; uno no se sostiene aquí, y lo reporto con su cautela» |
| Necesita defenderse. Si la premisa cae, se derrumba el proyecto | **No puede fallar**: si el hallazgo resulta confundido, «lo comprobé y era confusión» sigue siendo un buen paso |

Si un hallazgo resulta falso o confundido, **se reporta igual** y el paso sigue siendo válido.

## 4. Alcance de lo que se afirma

- **No se reclama originalidad.** Los métodos están publicados; la tabla de literatura del README dice quién los desarrolló.
- No se presenta un método publicado como propio ni se deriva nada nuevo.
- **Lo que se puede concluir está acotado:** «en 27 616 experimentos públicos de este tipo, juzgando por la decisión, el método X eligió mejor». **No** «Meta se equivoca» — datos distintos y pregunta distinta.
- Donde el resultado sea negativo, ambiguo o peor que la referencia simple, **se reporta igual**.

## 5. Límites

Los límites declarados en el README se repiten en cualquier entregable derivado. No se publica un resultado sin sus límites al lado.
