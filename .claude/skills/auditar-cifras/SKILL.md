---
name: auditar-cifras
description: Verifica que cada cifra de README.md, articulo_divulgacion.md y HANDOFF.md se pueda rastrear hasta un script del repositorio y su JSON en reports/results/, y que cada referencia bibliográfica esté verificada. Usar antes de dar por terminada una sección, antes de publicar o editar cualquier afirmación, y siempre que se toque un script de scripts/ o un módulo de src/ que un documento describa.
---

# Auditar cifras y referencias

Hace cumplir `.claude/rules/evidencia.md`. Es una auditoría: **reporta, no corrige en silencio.**

## El rastro que se audita

El proyecto está construido para que el rastro sea mecánico:

```
scripts/NN_*.py   →   reports/results/NN_*.json   →   la cifra en el documento
```

Toda cifra de un documento debe poder señalarse como **script → archivo → clave**. Si no se puede, es un hallazgo.

## Procedimiento

### 1. Reunir las afirmaciones

Recorrer `README.md`, `articulo_divulgacion.md`, `HANDOFF.md` y cualquier `.md` del repositorio (excepto los de `.claude/`) y extraer:

- Toda cifra: porcentajes, conteos, impresiones, tamaños de muestra, errores estándar, valores de α, fechas de cobertura, palabras del entregable.
- Toda referencia bibliográfica, **con su fecha**.
- Toda afirmación comparativa («mejor que», «reduce el error en», «gana en N de M»).

### 2. Rastrear cada cifra

Leer los JSON de `reports/results/` y buscar la clave que produce cada cifra. Clasificar:

| Estado | Significado |
|---|---|
| **Respaldada** | Existe la clave y el valor coincide |
| **Desfasada** | Existe la clave y da otro valor |
| **Huérfana** | Ningún JSON la contiene |
| **No verificable** | El script existe pero no se pudo correr; decir por qué |

Para recomprobar un valor, correr el script con `./.venv/Scripts/python.exe`. Nunca el Python global — hay un hook que lo bloquea.

**Si el script lee la muestra confirmatoria y no existe `reports/results/METODO_CONGELADO.json`, no intentar forzarlo:** otro hook lo bloquea y con razón. Reportar la cifra como no verificable todavía.

### 3. Revisar las referencias

- ¿Está marcada ✓ (verificada) o *pendiente de verificar*?
- ¿Alguna marcada ✓ atribuye una afirmación que la fuente no hace?
- ¿Alguna **fecha** mal atribuida? Caso conocido: el artículo de Meta tiene dos registros en arXiv, noviembre de 2025 y marzo de 2026; citar el segundo como la aparición es inexacto.
- ¿Hay afirmaciones que **suenan** a literatura y no citan nada?

### 4. Revisar el encuadre

El marco es demostración de oficio, no descubrimiento. Marcar cualquier redacción que:

- Reclame originalidad o novedad, o presente un método publicado como propio.
- **Convierta un hallazgo en tesis** en lugar de dejarlo como paso — el modo de falla propio de este proyecto, descrito en `evidencia.md` §3.
- Concluya más de lo que los datos permiten: «el método X eligió mejor en estos 27 616 experimentos» es correcto; «Meta se equivoca» no lo es.
- Omita un resultado negativo, ambiguo o peor que la referencia simple.
- Publique un resultado sin sus límites al lado.

### 5. Reportar

Una tabla con una fila por hallazgo: ubicación (`archivo:línea`), afirmación, estado, y qué hace falta. Primero lo más grave.

**Si todo está respaldado, decirlo en una línea.** No inventar hallazgos para que la auditoría parezca productiva.

## Lo que esta skill no hace

- No corrige los documentos. Reporta y espera instrucción.
- No añade cifras nuevas ni corre análisis que no existan.
- No juzga si el análisis es correcto, solo si lo escrito está respaldado por lo que hay en el repositorio.
