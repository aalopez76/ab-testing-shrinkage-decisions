# Regla: el alcance es vinculante

La sección **«Alcance: qué queda fuera, explícitamente»** del `README.md` no es una aspiración: es un límite. Antes de añadir algo que no esté dentro, hay que decirlo y esperar confirmación.

## Fuera de alcance

- **DiD y control sintético.** Los datos son aleatorizados; no hay nada que identificar por tendencias paralelas.
- **Tratamiento continuo.** No hay dosis en estos datos y no se inventa una. Ese es el proyecto hermano `../dose-selection-phase2`.
- **Qué tipo de titular funciona mejor.** Ya lo contestó Robertson y coautores (2023) con este mismo archivo.
- **Derivar estimadores.** Se usan métodos publicados y se citan.
- **Un tercer método.** Dos, y el eje global contra local encima. Ver `.claude/rules/metodo.md`.
- **El paso 7 (heterogeneidad con el texto)** es opcional y solo si los pasos 0 a 6 están cerrados.

## El entregable, que es lo que le pone final al trabajo

**Un análisis escrito de 2 000 a 3 000 palabras**, con el repositorio como respaldo reproducible. La extensión es un **límite**, no una meta.

Terminado significa lo que dice la lista del README, y en particular:

- La tabla mes a mes del paso 0, reproducida **por el código del repo**.
- El veredicto sobre el ruido del paso 1, **sea cual sea**.
- Las tres cifras: inflación, frecuencia de cambio de decisión, valor fuera de muestra.
- **La sección de dónde falla, escrita.**
- Método congelado y confirmatorio corrido **una sola vez**.

## Documentos

**El README crece y nada más**, junto con el artículo de divulgación. Sin fases, enmiendas, bitácoras versionadas ni auto-auditorías.

El único documento de estado es `HANDOFF.md`, y es **corto: solo el estado actual**, no un historial. El contexto histórico vive en `../_bitacora-portafolio/`, que se escribió una vez y no crece.

Si parece necesario un documento de gobierno nuevo, es una señal de alarma, no una tarea. Lo que vive en `.claude/` es infraestructura del harness —permisos, reglas, hooks, skills—, no gobierno del proyecto: esa distinción es la que permite que exista.

## Terminar antes de ampliar

La lista «Terminado significa» es la puerta. **No se abre trabajo nuevo —ni el proyecto hermano— con ítems pendientes ahí.**

Y hay un orden de construcción en el README por fases A–G. La **fase D produce la primera cifra de punta a punta**; si ahí ya se ve que nada mejora la decisión, eso es el resultado y el proyecto se acorta, en lugar de descubrirlo después de construir seis configuraciones.
