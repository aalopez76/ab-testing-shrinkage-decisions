"""How far variants genuinely differ: estimating tau-squared.

Shrinkage weighs two quantities: each measurement's noise (`v`) and the **real**
dispersion between an experiment's variants (tau^2). The first is calculated; the
second is not observed and must be estimated.

Here lies the problem that forces a pooled estimate: with 2 to 14 arms per
experiment, estimating tau^2 **within** each experiment means using a noisy
figure to decide how far to trust noisy figures. The solution comes from
meta-analysis, which has faced the same difficulty since the 1980s when combining
many clinical studies: **a single dispersion is estimated from all experiments
together.**

Two classical estimators, both built on Cochran's Q:

- **DerSimonian and Laird (1986):** closed form. It solves for how much real
  dispersion is needed to explain Q's excess over its degrees of freedom.
- **Paule and Mandel (1982):** finds the tau^2 at which Q, computed with weights
  that already include that dispersion, equals exactly its expectation. It has no
  closed form and is solved by bisection.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

MAX_ITER = 200
TOL = 1e-12


def _per_experiment(panel: pd.DataFrame, variance_factor: float = 1.0):
    """Iterate (theta, v) per experiment, skipping the uninformative ones."""
    for _, blk in panel.groupby("experiment_id", sort=False):
        if len(blk) < 2:
            continue
        theta = blk["theta_hat"].to_numpy(dtype=float)
        v = blk["v"].to_numpy(dtype=float) * variance_factor
        if not np.all(np.isfinite(v)) or np.any(v <= 0):
            continue
        yield theta, v


def dersimonian_laird(panel: pd.DataFrame, variance_factor: float = 1.0) -> float:
    """Pooled tau^2, closed form. Never negative.

    Numerator and denominator are accumulated across all experiments before
    dividing, so that small experiments do not drag the average as they would if
    tau^2 were estimated within each one and then averaged.
    """
    excess = 0.0
    denom = 0.0
    for theta, v in _per_experiment(panel, variance_factor):
        w = 1.0 / v
        sw = w.sum()
        pbar = float((w * theta).sum() / sw)
        Q = float((w * (theta - pbar) ** 2).sum())
        excess += Q - (len(theta) - 1)
        denom += sw - (w**2).sum() / sw
    if denom <= 0:
        return 0.0
    return max(0.0, excess / denom)


def _total_q(panel: pd.DataFrame, tau2: float, variance_factor: float) -> tuple[float, int]:
    """Accumulated Q with weights that already include tau^2, and its dof."""
    Q = 0.0
    dof = 0
    for theta, v in _per_experiment(panel, variance_factor):
        w = 1.0 / (v + tau2)
        sw = w.sum()
        pbar = float((w * theta).sum() / sw)
        Q += float((w * (theta - pbar) ** 2).sum())
        dof += len(theta) - 1
    return Q, dof


def paule_mandel(
    panel: pd.DataFrame,
    variance_factor: float = 1.0,
    upper: float | None = None,
) -> float:
    """Pooled tau^2 by the Paule and Mandel method.

    It seeks the tau^2 at which Q equals its degrees of freedom. Q decreases
    monotonically in tau^2, so bisection is safe. If Q(0) already fails to exceed
    the degrees of freedom there is no excess to explain and tau^2 is zero.
    """
    Q0, dof = _total_q(panel, 0.0, variance_factor)
    if dof == 0:
        return 0.0
    if Q0 <= dof:
        return 0.0

    if upper is None:
        # the observed variance of all rates is a generous upper bound
        upper = float(np.nanvar(panel["theta_hat"].to_numpy(dtype=float))) * 10 + 1e-9

    lo, hi = 0.0, upper
    Qhi, _ = _total_q(panel, hi, variance_factor)
    expansions = 0
    while Qhi > dof and expansions < 40:
        hi *= 2.0
        Qhi, _ = _total_q(panel, hi, variance_factor)
        expansions += 1

    for _ in range(MAX_ITER):
        mid = 0.5 * (lo + hi)
        Q, _ = _total_q(panel, mid, variance_factor)
        if abs(Q - dof) < TOL or (hi - lo) < TOL:
            return mid
        if Q > dof:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


METHODS = {
    "paule-mandel": paule_mandel,
    "dersimonian-laird": dersimonian_laird,
}


def estimate(panel: pd.DataFrame, method: str = "paule-mandel", variance_factor: float = 1.0) -> float:
    if method not in METHODS:
        raise ValueError(f"unknown method: {method!r}; use one of {list(METHODS)}")
    return float(METHODS[method](panel, variance_factor=variance_factor))
