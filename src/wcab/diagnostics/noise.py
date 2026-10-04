"""Paso 1: comprobar que el ruido está bien medido.

Toda la contracción depende de `v`, la varianza de la tasa de cada brazo. Para
una proporción hay fórmula cerrada —p(1-p)/n— pero esa fórmula supone que las
impresiones de un brazo son independientes, y en experimentación en línea rara
vez lo son: un mismo visitante puede ver varias, hay efectos de hora y de
fuente de tráfico.

Los experimentos A/A dan la vara de medir. Si entre los brazos de un
experimento no varía ningún campo público, la diferencia verdadera es cero por
construcción, así que **toda** la dispersión observada debería corresponder al
ruido calculado. La Q de Cochran debería valer en promedio k-1.

Si vale más, `v` está subestimado por un **factor de diseño** y hay que
corregirlo antes de usarlo. Ésa es, exactamente, la advertencia de Spotify:
una previa mal calibrada decide peor que no corregir.

Lo que este módulo **no** hace es decidir la explicación. Un exceso de
dispersión puede venir de impresiones agrupadas o de variación en campos que el
archivo público no incluye. **No son distinguibles con estos datos**, y las dos
se declaran.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd
from scipy import stats


@dataclass(frozen=True)
class Calibracion:
    """El veredicto sobre `v`."""

    experimentos: int
    brazos: int
    grados_libertad: int
    Q_total: float
    razon_Q_gl: float            # 1.0 = la fórmula describe bien estos datos
    mediana_Q_gl: float
    fraccion_p_005: float        # debería ser ~0.05
    factor_diseno: float         # por cuánto multiplicar v para corregirlo
    aprobada: bool

    def to_dict(self) -> dict:
        return {k: (round(v, 6) if isinstance(v, float) else v)
                for k, v in asdict(self).items()}

    def __str__(self) -> str:
        estado = "APROBADA" if self.aprobada else "RECHAZADA"
        return (
            f"calibración del ruido: {estado}\n"
            f"  Q/gl = {self.razon_Q_gl:.3f} (debería ser ~1.00) sobre "
            f"{self.experimentos:,} experimentos A/A\n"
            f"  mediana por experimento = {self.mediana_Q_gl:.3f}\n"
            f"  fracción con p<0.05 = {self.fraccion_p_005:.3f} "
            f"(debería ser ~0.05)\n"
            f"  factor de diseño = {self.factor_diseno:.3f}  "
            f"→ v corregido = v × {self.factor_diseno:.3f}"
        )


def q_de_cochran(panel: pd.DataFrame) -> pd.DataFrame:
    """Q de Cochran por experimento, bajo la hipótesis de una tasa común.

    El ruido se calcula con la tasa agrupada del experimento, no con la de cada
    brazo: bajo la hipótesis nula todos los brazos comparten la misma tasa, y
    usar la de cada brazo metería el propio ruido en el denominador.
    """
    filas = []
    for eid, blk in panel.groupby("experimento_id", sort=False):
        n = blk["impresiones"].to_numpy(dtype=float)
        c = blk["clics"].to_numpy(dtype=float)
        k = len(n)
        if k < 2 or c.sum() == 0 or c.sum() == n.sum():
            continue
        p_pool = c.sum() / n.sum()
        v = p_pool * (1.0 - p_pool) / n
        w = 1.0 / v
        theta = c / n
        pbar = float(np.sum(w * theta) / np.sum(w))
        Q = float(np.sum(w * (theta - pbar) ** 2))
        filas.append({"experimento_id": eid, "brazos": k, "gl": k - 1, "Q": Q})
    return pd.DataFrame(filas)


def calibrar(panel: pd.DataFrame, tolerancia: float = 0.15) -> Calibracion:
    """Contrasta el modelo de ruido contra los experimentos A/A.

    `tolerancia` es cuánto puede alejarse Q/gl de 1 para dar la calibración por
    buena. 0.15 es holgado a propósito: lo que interesa detectar es un sesgo
    grande, no una desviación de tercer decimal.
    """
    aa = panel.loc[panel["es_aa"]]
    if aa.empty:
        raise ValueError("No hay experimentos A/A en el panel: no se puede calibrar.")

    q = q_de_cochran(aa)
    if q.empty:
        raise ValueError("Ningún experimento A/A es utilizable para la Q de Cochran.")

    razon = float(q["Q"].sum() / q["gl"].sum())
    p = stats.chi2.sf(q["Q"].to_numpy(), q["gl"].to_numpy())

    return Calibracion(
        experimentos=int(len(q)),
        brazos=int(q["brazos"].sum()),
        grados_libertad=int(q["gl"].sum()),
        Q_total=float(q["Q"].sum()),
        razon_Q_gl=razon,
        mediana_Q_gl=float((q["Q"] / q["gl"]).median()),
        fraccion_p_005=float((p < 0.05).mean()),
        factor_diseno=razon,
        aprobada=abs(razon - 1.0) <= tolerancia,
    )


def corregir(v: pd.Series | np.ndarray, factor: float) -> np.ndarray:
    """Aplica el factor de diseño a la varianza.

    Se expone como función aparte, y no se mete en el panel, para que la
    comparación entre `v` ingenuo y `v` corregido sea explícita en el análisis.
    Ver `.claude/rules/metodo.md`.
    """
    if factor <= 0:
        raise ValueError(f"factor de diseño inválido: {factor}")
    return np.asarray(v, dtype=float) * factor
