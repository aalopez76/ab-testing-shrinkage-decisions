"""Paso 1: comprobar que el ruido está bien medido.

Toda la contracción depende de `v`, la varianza de la rate de cada brazo. Para
una proporción hay fórmula cerrada —p(1-p)/n— pero esa fórmula supone que las
impressions de un brazo son independientes, y en experimentación en línea rara
vez lo son: un mismo visitante puede ver varias, hay efectos de hora y de
fuente de tráfico.

Los experiments A/A dan la vara de measure. Si entre los arms de un
experimento no varía ningún campo público, la diferencia verdadera es cero por
construcción, así que **toda** la dispersión observada debería corresponder al
ruido calculado. La Q de Cochran debería valer en promedio k-1.

Si vale más, `v` está subestimado por un **factor de diseño** y hay que
corregirlo antes de usarlo. Ésa es, exactamente, la advertencia de Spotify:
una previa mal calibrada decide peor que no correct.

Lo que este módulo **no** hace es decidir la explicación. Un exceso de
dispersión puede venir de impressions agrupadas o de variación en campos que el
archivo público no incluye. **No son distinguibles con estos data**, y las dos
se declaran.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd
from scipy import stats


@dataclass(frozen=True)
class Calibration:
    """El veredicto sobre `v`."""

    experiments: int
    arms: int
    degrees_of_freedom: int
    total_q: float
    q_over_dof: float            # 1.0 = la fórmula describe bien estos data
    median_q_over_dof: float
    fraction_p_005: float        # debería ser ~0.05
    design_factor: float         # por cuánto multiplicar v para corregirlo
    passed: bool

    def to_dict(self) -> dict:
        return {k: (round(v, 6) if isinstance(v, float) else v)
                for k, v in asdict(self).items()}

    def __str__(self) -> str:
        estado = "APROBADA" if self.passed else "RECHAZADA"
        return (
            f"calibración del ruido: {estado}\n"
            f"  Q/dof = {self.q_over_dof:.3f} (debería ser ~1.00) sobre "
            f"{self.experiments:,} experiments A/A\n"
            f"  mediana por experimento = {self.median_q_over_dof:.3f}\n"
            f"  fracción con p<0.05 = {self.fraction_p_005:.3f} "
            f"(debería ser ~0.05)\n"
            f"  factor de diseño = {self.design_factor:.3f}  "
            f"→ v corregido = v × {self.design_factor:.3f}"
        )


def cochran_q(panel: pd.DataFrame) -> pd.DataFrame:
    """Q de Cochran por experimento, bajo la hipótesis de una rate común.

    El ruido se calcula con la rate agrupada del experimento, no con la de cada
    brazo: bajo la hipótesis nula todos los arms comparten la misma rate, y
    usar la de cada brazo metería el propio ruido en el denominador.
    """
    filas = []
    for eid, blk in panel.groupby("experiment_id", sort=False):
        n = blk["impressions"].to_numpy(dtype=float)
        c = blk["clicks"].to_numpy(dtype=float)
        k = len(n)
        if k < 2 or c.sum() == 0 or c.sum() == n.sum():
            continue
        p_pool = c.sum() / n.sum()
        v = p_pool * (1.0 - p_pool) / n
        w = 1.0 / v
        theta = c / n
        pbar = float(np.sum(w * theta) / np.sum(w))
        Q = float(np.sum(w * (theta - pbar) ** 2))
        filas.append({"experiment_id": eid, "arms": k, "dof": k - 1, "Q": Q})
    return pd.DataFrame(filas)


def calibrate(panel: pd.DataFrame, tolerance: float = 0.15) -> Calibration:
    """Contrasta el modelo de ruido contra los experiments A/A.

    `tolerance` es cuánto puede alejarse Q/dof de 1 para dar la calibración por
    buena. 0.15 es holgado a propósito: lo que interesa detectar es un sesgo
    grande, no una desviación de tercer decimal.
    """
    aa = panel.loc[panel["is_aa"]]
    if aa.empty:
        raise ValueError("No hay experiments A/A en el panel: no se puede calibrate.")

    q = cochran_q(aa)
    if q.empty:
        raise ValueError("Ningún experimento A/A es utilizable para la Q de Cochran.")

    razon = float(q["Q"].sum() / q["dof"].sum())
    p = stats.chi2.sf(q["Q"].to_numpy(), q["dof"].to_numpy())

    return Calibration(
        experiments=int(len(q)),
        arms=int(q["arms"].sum()),
        degrees_of_freedom=int(q["dof"].sum()),
        total_q=float(q["Q"].sum()),
        q_over_dof=razon,
        median_q_over_dof=float((q["Q"] / q["dof"]).median()),
        fraction_p_005=float((p < 0.05).mean()),
        design_factor=razon,
        passed=abs(razon - 1.0) <= tolerance,
    )


def correct(v: pd.Series | np.ndarray, factor: float) -> np.ndarray:
    """Aplica el factor de diseño a la varianza.

    Se expone como función aparte, y no se mete en el panel, para que la
    comparación entre `v` ingenuo y `v` corregido sea explícita en el análisis.
    Ver `.claude/rules/method.md`.
    """
    if factor <= 0:
        raise ValueError(f"factor de diseño inválido: {factor}")
    return np.asarray(v, dtype=float) * factor
