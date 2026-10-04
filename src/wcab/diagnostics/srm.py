"""Paso 0: comprobar que el sorteo fue un sorteo.

Si la asignación aleatoria funcionó, las impresiones deberían repartirse entre
los brazos de un experimento de forma aproximadamente uniforme. Un desbalance
sistemático —*sample ratio mismatch*— indica que la asignación no fue aleatoria,
y analizar esos experimentos contamina todo lo que venga después.

Se usa para reproducir mes a mes el fallo de Cloudflare que el equipo del
archivo reportó en junio de 2024, y así justificar la exclusión con evidencia
propia en lugar de confiar en la marca del archivo (que además no viene en los
CSV públicos de 2020-2021).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

UMBRAL = 1e-3


def por_experimento(datos: pd.DataFrame) -> pd.DataFrame:
    """χ² de impresiones por brazo contra asignación uniforme, por experimento.

    Espera columnas `experimento_id`, `impresiones` y `fecha`. Devuelve una fila
    por experimento con el estadístico, su p-valor y si desbalancea.
    """
    filas = []
    for eid, blk in datos.groupby("experimento_id", sort=False):
        obs = blk["impresiones"].to_numpy(dtype=float)
        if len(obs) < 2 or obs.sum() <= 0:
            continue
        esperado = np.full(len(obs), obs.mean())
        chi2 = float(((obs - esperado) ** 2 / esperado).sum())
        gl = len(obs) - 1
        p = float(stats.chi2.sf(chi2, gl))
        filas.append(
            {
                "experimento_id": eid,
                "brazos": len(obs),
                "impresiones": float(obs.sum()),
                "chi2": chi2,
                "gl": gl,
                "p": p,
                "desbalance": p < UMBRAL,
                "fecha": blk["fecha"].iloc[0],
            }
        )
    return pd.DataFrame(filas)


def por_mes(srm: pd.DataFrame, minimo: int = 30) -> pd.DataFrame:
    """Fracción de experimentos con desbalance severo, por mes.

    `minimo` descarta los meses con pocos experimentos, donde la fracción es
    demasiado ruidosa para leerse.
    """
    s = srm.dropna(subset=["fecha"]).copy()
    s["mes"] = pd.to_datetime(s["fecha"]).dt.to_period("M").astype(str)
    t = s.groupby("mes").agg(
        experimentos=("desbalance", "size"),
        fraccion_desbalance=("desbalance", "mean"),
    )
    return t.loc[t["experimentos"] >= minimo].reset_index()


def resumen(srm: pd.DataFrame) -> dict:
    """Las cifras que el documento cita, en una sola fuente."""
    return {
        "experimentos_evaluados": int(len(srm)),
        "umbral_p": UMBRAL,
        "fraccion_desbalance_global": float(srm["desbalance"].mean()),
    }
