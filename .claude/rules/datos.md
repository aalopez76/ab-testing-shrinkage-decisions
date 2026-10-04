# Regla: el dato y su defecto

## La exclusión, en un solo lugar

**Se excluyen los experimentos creados entre el 1 de junio de 2013 y el 31 de enero de 2014.** Sin excepción, en todo análisis.

Y vive en **una sola función**: `src/wcab/exclusion.py`. El panel canónico la aplica al construirse y registra cuántos experimentos eliminó. **Ningún script debe llegar a los datos por otro camino** — `src/wcab/panel.py` es la única puerta, y los CSV crudos de `data/raw/` no se leen directamente desde `scripts/`.

## Por qué

Una mala configuración de la caché de Cloudflare el 25 de junio de 2013 hizo que durante meses se mostrara una sola variante hasta que expiraba la caché. El equipo del archivo lo reportó en junio de 2024, marcó ~22% de las pruebas y **desaconseja usarlas para inferencia causal**.

Verificado de forma independiente con χ² de impresiones por brazo contra asignación uniforme (p < 0.001):

```
feb–may 2013   2–5%     línea base
jun 2013      21.8%     arranca
jul–dic 2013  56–88%    ventana del fallo
ene 2014      15.1%     lo arreglan a mitad de mes
feb 2014+     0.0–0.5%  tasa nominal
```

Los CSV del OSF en `data/raw/` son de 2020–2021 y **no traen la columna de marca**: la exclusión se deriva por fecha.

## El panel canónico

Una tabla a nivel de brazo, construida una vez y guardada en `data/derived/`. Todo lo demás la lee:

```
experimento_id · brazo_id · impresiones · clics · theta_hat · v
semana · varia_titular · varia_imagen · es_AA · muestra
```

`es_AA` marca los ~840 experimentos sin variación registrada entre brazos — la vara de medir del paso 1.

## Qué está prohibido

- Analizar el archivo completo «para comparar» sin etiquetar esa salida como no causal.
- Mover las fechas de corte sin volver a correr el diagnóstico y actualizar la tabla.
- Leer `data/raw/` desde un script sin pasar por `panel.py`.
- Editar a mano cualquier cosa bajo `data/` — está denegado en los permisos.

## La muestra confirmatoria

No se toca hasta congelar el método. Está en `.claude/rules/metodo.md` y lo impone un hook.
