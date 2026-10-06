"""Step 0: establish that the draw was in fact a draw.

If random assignment worked, impressions should be distributed approximately
uniformly across an experiment's arms. A systematic imbalance — *sample ratio
mismatch* — indicates that assignment was not random, and analysing those
experiments contaminates everything downstream.

It is used to reproduce, month by month, the Cloudflare failure the archive's
team reported in June 2024, so that the exclusion rests on evidence gathered here
rather than on the archive's own flag, which in any case is absent from the
public 2020-2021 CSV files.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

THRESHOLD = 1e-3


def per_experiment(data: pd.DataFrame) -> pd.DataFrame:
    """Chi-squared of impressions per arm against uniform assignment.

    Expects the columns `experiment_id`, `impressions` and `date`. Returns one row
    per experiment with the statistic, its p-value and whether it is imbalanced.
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


def by_month(srm: pd.DataFrame, minimum: int = 30) -> pd.DataFrame:
    """Fraction of experiments with severe imbalance, by month.

    `minimum` discards months with few experiments, where the fraction is
    too noisy to read.
    """
    s = srm.dropna(subset=["date"]).copy()
    s["month"] = pd.to_datetime(s["date"]).dt.to_period("M").astype(str)
    t = s.groupby("month").agg(
        experiments=("desbalance", "size"),
        imbalance_fraction=("desbalance", "mean"),
    )
    return t.loc[t["experiments"] >= minimum].reset_index()


def summary(srm: pd.DataFrame) -> dict:
    """The figures the document cites, from a single source."""
    return {
        "experiments_evaluated": int(len(srm)),
        "p_threshold": THRESHOLD,
        "global_imbalance_fraction": float(srm["desbalance"].mean()),
    }
