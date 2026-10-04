# Regla: cómo se eligen y se juzgan los métodos

## El criterio

> **Los métodos se juzgan por las decisiones que producen, no por si cumplen sus propios supuestos.**

Un método con supuestos impecables puede ser la elección equivocada si optimiza lo que no se paga —el error de estimación cuando lo que cuesta es la decisión. Y uno con un supuesto violado puede decidir mejor de todos modos: **la robustez se mide, no se deduce.**

## El orden: medir → explicar → descartar

| Paso | Qué hace | Qué NO hace |
|---|---|---|
| **Medir** | Qué método elige mejor, fuera de muestra | — |
| **Explicar** | Los diagnósticos entienden el resultado | **No filtran candidatos de entrada** |
| **Descartar** | Con la razón nombrada | No se descarta sin decir por qué |

Los diagnósticos —calibración del ruido, régimen de la proporción, dependencia entre parámetro y precisión— van **después** de la comparación. Usarlos como filtro previo invertiría el criterio.

## Las razones de descarte, nombradas

No todas son del dato, y confundirlas sería impreciso:

| Razón | Cómo se lee |
|---|---|
| **No responde la pregunta** | Fuera por alcance. El trabajo de Netflix optimiza a nivel de programa, no la elección dentro de un experimento |
| **La naturaleza del dato** | Proporciones de 1.5% con ~3 000 ensayos: el territorio de Chen y Lei |
| **Costo operativo** | Una implementación de referencia en otro lenguaje es un costo real. **Se declara, no se omite** |
| **No sobrevive la comparación** | Pierde fuera de muestra. El descarte más limpio |
| **No es un método** | La posición de Spotify es una restricción operativa, no un competidor |

## Dos métodos, no más

Se implementan **la contracción estándar** —lo que usa la industria, la referencia a batir o confirmar— y **una** alternativa. El eje global contra local se cruza encima: seis configuraciones contando las dos referencias (azar y sin corregir).

**Más de dos no se termina**, y un proyecto sin terminar no demuestra nada. Añadir un tercero exige decirlo y justificarlo.

## La congelación del método

El archivo trae tres muestras disjuntas. **El exploratorio (4 873 experimentos) es para desarrollar; el confirmatorio (22 743) se usa una sola vez, con el método ya fijado.** Mirarlo antes destruye lo único que lo hace valioso, y no se puede deshacer.

Eso está **impuesto por un hook**, no por buena voluntad: `.claude/hooks/freeze_guard.py` bloquea cualquier comando que toque el confirmatorio mientras no exista `reports/results/METODO_CONGELADO.json`. El guardián **falla cerrado**: si no logra ubicar la raíz del proyecto, bloquea.

Para congelar, ese archivo debe contener:

```json
{
  "fecha": "...",
  "commit": "...",
  "criterio": "valor fuera de muestra de la variante elegida",
  "metodos": ["estandar", "..."],
  "vecindario": {"tipo": "...", "ancho": ...},
  "particiones": ...,
  "bootstrap": ...
}
```

Escribirlo es un acto deliberado, con el commit de git que prueba qué código existía en ese momento. **No se escribe «para desbloquear»**: se escribe cuando el método está decidido.

## El ancho del vecindario

Se **declara de antemano** y se reporta la sensibilidad al moverlo. **Nunca se elige mirando los datos de evaluación** — hacerlo convertiría la validación en un ajuste y invalidaría todo lo demás.

## El resultado negativo es un resultado

Si ninguna corrección mejora la decisión, **eso es lo que se reporta**, y le daría la razón a Spotify sobre estos datos. No se buscan configuraciones hasta que alguna gane.

Y la sección de **dónde falla** no es opcional: en qué fracción de experimentos la corrección elige peor que no corregir, y qué caracteriza a esos casos.
