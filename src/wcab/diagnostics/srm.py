"""Paso 0: comprobar que el sorteo fue un sorteo.

Si la asignación aleatoria funcionó, las impressions deberían repartirse entre
los arms de un experimento de forma aproximadamente uniforme. Un desbalance
sistemático —*sample ratio mismatch*— indica que la asignación no fue aleatoria,
y analizar esos experiments contamina todo lo que venga después.

Se usa para reproducir month a month el fallo de Cloudflare que el equipo del
archivo reportó en junio de 2024, y así justificar la exclusión con evidencia
propia en lugar de confiar en la marca del archivo (que además no viene en los
CSV públicos de 2020-2021).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

THRESHOLD = 1e-3


def per_experiment(data: pd.DataFrame) -> pd.DataFrame:
    """χ² de impressions por brazo contra asignación uniforme, por experimento.

    Espera columnas `experiment_id`, `impressions` y `date`. Devuelve una fila
    por experimento con el estadístico, su p-value y si desbalancea.
    """
    filas = []
    for eid, blk in data.groupby("experiment_id", sort=False):
        obs = blk["impressions"].to_numpy(dtype=float)
        if len(obs) < 2 or obs.sum() <= 0:
            continue
        esperado = np.full(len(obs), obs.mean())
        chi2 = float(((obs - esperado) ** 2 / esperado).sum())
        dof = len(obs) - 1
        p = float(stats.chi2.sf(chi2, dof))
        filas.append(
            {
                "experiment_id": eid,
                "arms": len(obs),
                "impressions": float(obs.sum()),
                "chi2": chi2,
                "dof": dof,
                "p": p,
                "desbalance": p < THRESHOLD,
                "date": blk["date"].iloc[0],
            }
        )
    return pd.DataFrame(filas)


def by_month(srm: pd.DataFrame, minimo: int = 30) -> pd.DataFrame:
    """Fracción de experiments con desbalance severo, por month.

    `minimo` descarta los meses con pocos experiments, donde la fracción es
    demasiado ruidosa para leerse.
    """
    s = srm.dropna(subset=["date"]).copy()
    s["month"] = pd.to_datetime(s["date"]).dt.to_period("M").astype(str)
    t = s.groupby("month").agg(
        experiments=("desbalance", "size"),
        imbalance_fraction=("desbalance", "mean"),
    )
    return t.loc[t["experiments"] >= minimo].reset_index()


def summary(srm: pd.DataFrame) -> dict:
    """Las metrics que el documento cita, en una sola fuente."""
    return {
        "experiments_evaluated": int(len(srm)),
        "p_threshold": THRESHOLD,
        "global_imbalance_fraction": float(srm["desbalance"].mean()),
    }
