"""Shrinkage: pulling each measurement towards what the others say.

The form is a weighted average between what each variant reports and the centre
of its experiment, with a weight comparing the measurement's noise against the
real dispersion between variants:

    theta_tilde = (1 - alpha) * theta_hat + alpha * centre,   alpha = v / (v + tau^2)

If noise dominates, more weight goes to the centre; if real differences dominate,
more weight goes to each measurement. This is parametric empirical Bayes
(Efron and Morris, JASA 1975).

**The interface is a single function** — `shrink` — so that the decision harness
does not know which method it is evaluating. "Two methods x global/local" is then
a loop rather than code copied four times, and the comparison is fair by
construction.

The project's axes enter as arguments:

- **which method**: `tau2_method` selects the dispersion estimator.
- **towards what**: `tau2` is computed outside, over all experiments (global) or
  over a neighbourhood (local).
- **with what noise**: `variance_factor` applies the design factor from step 1.
  The project compares naive `v` (1.0) against corrected `v`.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import dispersion

CENTERS = ("weighted", "simple")


@dataclass(frozen=True)
class ShrinkageResult:
    """The result, with its inputs exposed so that they can be reported."""

    theta_tilde: pd.Series
    alpha: pd.Series
    tau2: float
    variance_factor: float
    tau2_method: str
    center: str

    def summary(self) -> dict:
        return {
            "tau2": float(self.tau2),
            "tau": float(np.sqrt(self.tau2)),
            "variance_factor": float(self.variance_factor),
            "tau2_method": self.tau2_method,
            "center": self.center,
            "alpha_mean": float(self.alpha.mean()),
            "alpha_median": float(self.alpha.median()),
            "alpha_min": float(self.alpha.min()),
            "alpha_max": float(self.alpha.max()),
        }


def pooled_variance(panel: pd.DataFrame, minimum: int = 1) -> pd.Series:
    """Each arm's variance computed from its experiment's POOLED rate.

    The panel carries `v` computed from each arm's own rate — p(1-p)/n — and that
    fails for two reasons, both of which matter:

    1. **It is zero when an arm recorded no clicks.** After splitting into halves
       this happens frequently (rates around 1.3% and roughly 1,500 impressions
       per half), and a zero variance breaks the 1/v weights.
    2. **It correlates `v` with `theta_hat`**, because both are computed from the
       same counts. In other words, the estimator itself would induce the
       dependence between parameter and precision that Chen (*Econometrica*,
       2026) warns about. Using the pooled rate avoids this.

    Under the shrinkage model the arms of an experiment share a similar rate, so
    their pooled rate is the best available scale for the variance. This is
    standard practice in meta-analysis of proportions.

    Experiments with no clicks at all are left with NaN variance: they carry no
    information and are discarded upstream.
    """
    g = panel.groupby("experiment_id")
    clicks = g["clicks"].transform("sum").to_numpy(dtype=float)
    impressions = g["impressions"].transform("sum").to_numpy(dtype=float)
    n = panel["impressions"].to_numpy(dtype=float)

    with np.errstate(divide="ignore", invalid="ignore"):
        p = np.where(impressions > 0, clicks / impressions, np.nan)
        v = p * (1.0 - p) / n
    v = np.where((clicks >= minimum) & (clicks < impressions), v, np.nan)
    return pd.Series(v, index=panel.index, name="v_pooled")


def usable_mask(panel: pd.DataFrame) -> np.ndarray:
    """Which rows are usable for shrinkage, as a positional mask.

    This is exposed separately from `prepare` because the two halves of a split
    must be filtered with the **same mask** to stay aligned row by row. Were each
    half filtered independently, different arms would be compared and nothing
    would reveal it.

    It discards arms whose pooled variance cannot be computed — no clicks, or all
    of the experiment's clicks — and experiments left with fewer than two arms,
    which cannot be compared.
    """
    v = pooled_variance(panel).to_numpy()
    ok = np.isfinite(v) & (v > 0)
    count = (
        pd.Series(ok, index=panel.index)
        .groupby(panel["experiment_id"].to_numpy())
        .transform("sum")
        .to_numpy()
    )
    return ok & (count >= 2)


def prepare(panel: pd.DataFrame, mask: np.ndarray | None = None) -> pd.DataFrame:
    """Return the panel ready for shrinkage: pooled `v`, unusable rows removed."""
    m = usable_mask(panel) if mask is None else np.asarray(mask, dtype=bool)
    out = panel.loc[m].copy()
    out["v"] = pooled_variance(out)
    return out.reset_index(drop=True)


def _center_per_experiment(
    panel: pd.DataFrame, v: np.ndarray, center: str
) -> np.ndarray:
    """The point shrunk towards: the centre of the arm's own experiment."""
    if center == "simple":
        means = panel.groupby("experiment_id")["theta_hat"].transform("mean")
        return means.to_numpy(dtype=float)
    if center == "weighted":
        w = 1.0 / v
        tmp = pd.DataFrame(
            {
                "experiment_id": panel["experiment_id"].to_numpy(),
                "wt": w * panel["theta_hat"].to_numpy(dtype=float),
                "w": w,
            }
        )
        sums = tmp.groupby("experiment_id")[["wt", "w"]].transform("sum")
        return (sums["wt"] / sums["w"]).to_numpy(dtype=float)
    raise ValueError(f"unknown center: {center!r}; use one of {CENTERS}")


def shrink(
    panel: pd.DataFrame,
    tau2: float | pd.Series | None = None,
    *,
    variance_factor: float = 1.0,
    tau2_method: str = "paule-mandel",
    center: str = "weighted",
) -> ShrinkageResult:
    """Shrink the panel's rates towards the centre of their experiment.

    `tau2` may be a scalar (the same dispersion for every row: the global case) or
    a series aligned to the panel (one dispersion per row: the local case). If it
    is not supplied, it is estimated over the whole panel, which is the global
    case.
    """
    v = panel["v"].to_numpy(dtype=float) * variance_factor
    if np.any(v <= 0) or not np.all(np.isfinite(v)):
        raise ValueError("the panel contains non-positive or non-finite variances")

    if tau2 is None:
        tau2 = dispersion.estimate(panel, method=tau2_method, variance_factor=variance_factor)

    t2 = (
        np.full(len(panel), float(tau2))
        if np.isscalar(tau2)
        else np.asarray(tau2, dtype=float)
    )
    if t2.shape[0] != len(panel):
        raise ValueError("the tau2 series is not aligned with the panel")

    alpha = v / (v + t2)
    center_values = _center_per_experiment(panel, v, center)
    theta = panel["theta_hat"].to_numpy(dtype=float)

    return ShrinkageResult(
        theta_tilde=pd.Series((1.0 - alpha) * theta + alpha * center_values,
                              index=panel.index, name="theta_tilde"),
        alpha=pd.Series(alpha, index=panel.index, name="alpha"),
        tau2=float(np.mean(t2)),
        variance_factor=variance_factor,
        tau2_method=tau2_method,
        center=center,
    )
