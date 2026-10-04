"""Paso 4: partir cada brazo en dos mitades independientes.

Para medir cuánto se infló la variante elegida hace falta evaluarla en datos
que no participaron en elegirla. La muestra de reserva del archivo no sirve
—son experimentos *distintos*— así que se parte cada brazo.

**El resultado que lo hace válido.** Si X ~ Binomial(n, p) y se extrae
X_A | X ~ Hipergeométrica(n, X, m) con X_B = X − X_A, entonces

    X_A ~ Binomial(m, p)      X_B ~ Binomial(n−m, p)      X_A ⊥ X_B

La independencia es **marginal**, no condicional: dado X las dos mitades suman
una constante y por tanto están ligadas, pero como X es aleatorio el par
conjunto reproduce exactamente la ley de haber partido los ensayos de antemano.
Esto es *data thinning* para distribuciones cerradas bajo convolución (Neufeld
y coautores, *JMLR* 2024).

**No es *data fission*** (Leiner, Duan, Tibshirani y Ramdas). Para la binomial
esa técnica produce componentes que **no** son independientes, y la
independencia es justo lo que se necesita aquí. La confusión es fácil y casi se
cuela en el planteamiento de este proyecto; `tests/test_thinning.py` existe
para que no vuelva a pasar.

Si la partición estuviera mal, **todas** las cifras del proyecto quedarían mal
y nada en el resultado lo delataría. Es el único módulo con esa propiedad, y
por eso tiene un hook que corre su prueba al editarlo.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Particion:
    """Las dos mitades de un panel, con la fracción usada."""

    estimacion: pd.DataFrame   # mitad A: con ella se elige
    evaluacion: pd.DataFrame   # mitad B: con ella se mide, no participó en elegir
    fraccion: float
    semilla: int


def partir_conteos(
    n: np.ndarray,
    c: np.ndarray,
    fraccion: float,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Parte (n, c) en dos mitades independientes.

    Devuelve (n_a, c_a, n_b, c_b). `n_a` es el entero más cercano a
    `fraccion * n`, acotado a [1, n-1] para que ninguna mitad quede vacía:
    un brazo con una mitad vacía no aporta información y rompería las razones
    aguas abajo.
    """
    if not 0.0 < fraccion < 1.0:
        raise ValueError(f"fracción fuera de (0,1): {fraccion}")

    n = np.asarray(n, dtype=np.int64)
    c = np.asarray(c, dtype=np.int64)
    if np.any(c < 0) or np.any(c > n):
        raise ValueError("clics fuera de rango: debe cumplirse 0 <= c <= n")
    if np.any(n < 2):
        raise ValueError("un brazo con menos de 2 impresiones no se puede partir")

    n_a = np.clip(np.rint(fraccion * n).astype(np.int64), 1, n - 1)
    n_b = n - n_a

    # Hipergeométrica: de n impresiones con c clics, cuántos caen en las n_a
    # que forman la mitad A. `nbad` son las impresiones sin clic.
    c_a = rng.hypergeometric(ngood=c, nbad=n - c, nsample=n_a)
    c_b = c - c_a

    return n_a, c_a, n_b, c_b


def partir(
    panel: pd.DataFrame,
    fraccion: float = 0.5,
    semilla: int = 0,
) -> Particion:
    """Parte un panel canónico en mitad de estimación y mitad de evaluación.

    Cada mitad conserva las columnas del panel con `impresiones`, `clics`,
    `theta_hat` y `v` recalculados para su propio tamaño. Las columnas
    descriptivas —experimento, semana, es_aa— se arrastran sin cambios.
    """
    rng = np.random.default_rng(semilla)
    n_a, c_a, n_b, c_b = partir_conteos(
        panel["impresiones"].to_numpy(), panel["clics"].to_numpy(), fraccion, rng
    )

    def _mitad(n_m: np.ndarray, c_m: np.ndarray) -> pd.DataFrame:
        out = panel.copy()
        out["impresiones"] = n_m
        out["clics"] = c_m
        theta = c_m / n_m
        out["theta_hat"] = theta
        out["v"] = theta * (1.0 - theta) / n_m
        return out.reset_index(drop=True)

    return Particion(
        estimacion=_mitad(n_a, c_a),
        evaluacion=_mitad(n_b, c_b),
        fraccion=fraccion,
        semilla=semilla,
    )


def comprobar_suma(panel: pd.DataFrame, p: Particion) -> bool:
    """La partición no inventa ni pierde datos: las mitades suman el original."""
    n_ok = np.array_equal(
        p.estimacion["impresiones"] + p.evaluacion["impresiones"],
        panel["impresiones"].to_numpy(),
    )
    c_ok = np.array_equal(
        p.estimacion["clics"] + p.evaluacion["clics"], panel["clics"].to_numpy()
    )
    return bool(n_ok and c_ok)


def partir_tres(
    panel: pd.DataFrame,
    semilla: int = 0,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Parte en tres tercios independientes: elegir, estimar, evaluar.

    Hace falta porque un estadístico **seleccionado** —el máximo de un
    experimento— no se comporta como una estimación ruidosa cualquiera: su
    distribución está corrida y su varianza no es la ingenua, así que la
    maquinaria de Bayes empírico aplicada sobre él da resultados sin sentido
    (en la práctica, un τ² estimado en cero).

    La salida es separar los papeles:

        A1  elige el brazo         (y nada más)
        A2  estima su ventaja      (sin haber participado en elegirlo)
        B   mide lo que rindió     (sin haber participado en nada)

    Así δ̂ deja de ser un máximo y pasa a ser la ventaja de un brazo **ya
    fijado**, que sí es una estimación insesgada y a la que la contracción se
    puede aplicar como corresponde.
    """
    primero = partir(panel, fraccion=2.0 / 3.0, semilla=semilla)
    segundo = partir(primero.estimacion, fraccion=0.5, semilla=semilla + 10_000)
    return segundo.estimacion, segundo.evaluacion, primero.evaluacion
