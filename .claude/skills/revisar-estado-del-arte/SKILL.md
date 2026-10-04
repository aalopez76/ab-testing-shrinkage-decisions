---
name: revisar-estado-del-arte
description: Comprueba en la web si apareció trabajo nuevo que cambie el posicionamiento del proyecto, y si las afirmaciones sobre lo que ya está hecho siguen siendo ciertas. Usar antes de congelar el método, antes de publicar, y si pasaron más de dos meses desde la última revisión. También cuando se vaya a afirmar que algo no está hecho.
---

# Revisar el estado del arte

Este proyecto se posiciona dentro de una discusión viva: **siete de las nueve referencias del README son de los últimos catorce meses.** Un posicionamiento escrito hace tres meses puede estar desactualizado, y durante el planteamiento **tres afirmaciones de hueco se cayeron al revisarlas**. Esta skill existe para que eso se descubra a tiempo y no en una entrevista.

## Cuándo usarla

- **Antes de congelar el método.** Si apareció un método mejor, es el momento de saberlo.
- **Antes de publicar.**
- Si pasaron más de **dos meses** desde la última revisión.
- **Siempre que se vaya a afirmar que algo no está hecho.** Esa clase de afirmación es la más frágil que existe y es la que ya falló tres veces.

## Procedimiento

### 1. Reconfirmar lo que el README ya afirma

Para cada entrada de la tabla de literatura del README, comprobar:

- **La fecha de aparición**, no la de la versión que se leyó. Caso conocido: el artículo de Meta tiene dos registros en arXiv (nov-2025 y mar-2026) y la prioridad es el primero.
- **Si cambió de estado**: un borrador puede haberse publicado. Caso conocido: Chen pasó de documento de trabajo (2023) a *Econometrica* 94(2) en marzo de 2026, lo que cambia su peso.
- **Si lo que se le atribuye sigue siendo lo que dice.**

### 2. Buscar lo nuevo

Búsquedas en los ejes del proyecto, en modo extendido:

- maldición del ganador en experimentación · *winner's curse A/B testing*
- Bayes empírico para selección · contracción local · *local empirical Bayes*
- contracción para binomiales / proporciones pequeñas
- inferencia condicionada a la selección · *data thinning*
- calidad de **decisión** frente a calidad de estimación en experimentación

Y revisar si hay **respuesta pública a la objeción de Spotify** (sep-2026), que es el eje del posicionamiento: si alguien ya la arbitró con datos públicos, el proyecto tiene que decirlo.

### 3. Comprobar lo que el proyecto declara no hecho

Tomar cada afirmación del tipo «nadie ha…» o «no está hecho» y buscarla activamente **en contra**. Si se encuentra algo:

- **No se defiende la afirmación: se corrige el documento.**
- Y se degrada, si corresponde, de titular a paso. Ver `.claude/rules/evidencia.md` §3.

### 4. Juzgar el impacto

| Hallazgo | Qué hacer |
|---|---|
| Un método nuevo mejor que los dos elegidos | Decirlo. **No añadirlo sin decidirlo explícitamente** — la regla de dos métodos sigue en pie |
| Alguien ya respondió la pregunta del proyecto | Reencuadrar: el proyecto pasa a reproducir o contrastar, y se dice |
| Cambió la fecha o el estado de una referencia | Corregir README, artículo y la tabla de literatura |
| Nada relevante | **Decirlo en una línea.** No inflar el reporte |

### 5. Reportar

Qué se buscó, qué se encontró, qué cambia y qué documentos hay que tocar. Si el posicionamiento sigue en pie, decirlo y anotar la fecha de la revisión en `HANDOFF.md`.

## Lo que esta skill no hace

- No reescribe los documentos por su cuenta: reporta y espera instrucción.
- No añade métodos al plan.
- No busca justificaciones para lo que el proyecto ya afirma. **Busca lo contrario**, que es para lo que sirve.
