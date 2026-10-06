"""Step 1: establish whether the noise is correctly measured.

All shrinkage depends on `v`, the variance of each arm's rate. For a proportion
there is a closed form — p(1-p)/n — but that formula assumes an arm's impressions
are independent, and in online experimentation they rarely are: the same visitor
may see several, and there are time-of-day and traffic-source effects.

A/A experiments provide the yardstick. If no public field varies between an
experiment's arms, the true difference is zero by construction, so **all** of the
observed dispersion should correspond to the calculated noise. Cochran's Q should
then average k-1.

If it is larger, `v` is underestimated by a **design factor** that must be
corrected before use. This is precisely Spotify's warning: a poorly calibrated
prior decides worse than not correcting at all.

What this module does **not** do is settle the explanation. Excess dispersion may
arise from clustered impressions or from variation in fields the public archive
does not include. **These are not distinguishable with these data**, and both are
declared.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd
from scipy import stats


@dataclass(frozen=True)
class Calibration:
    """The verdict on `v`."""

    experiments: int
    arms: int
    degrees_of_freedom: int
    total_q: float
    q_over_dof: float            # 1.0 means the formula describes these data well
    median_q_over_dof: float
    fraction_p_005: float        # should be around 0.05
    design_factor: float         # the multiplier that corrects v
    passed: bool

    def to_dict(self) -> dict:
        return {k: (round(v, 6) if isinstance(v, float) else v)
                for k, v in asdict(self).items()}

    def __str__(self) -> str:
        status = "PASSED" if self.passed else "REJECTED"
        return (
            f"noise calibration: {status}\n"
            f"  Q/dof = {self.q_over_dof:.3f} (should be ~1.00) over "
            f"{self.experiments:,} A/A experiments\n"
            f"  median per experiment = {self.median_q_over_dof:.3f}\n"
            f"  fraction with p<0.05 = {self.fraction_p_005:.3f} "
            f"(should be ~0.05)\n"
            f"  design factor = {self.design_factor:.3f}  "
            f"-> corrected v = v x {self.design_factor:.3f}"
        )


def cochran_q(panel: pd.DataFrame) -> pd.DataFrame:
    """Cochran's Q per experiment, under the hypothesis of a common rate.

    The noise is computed from the experiment's pooled rate rather than from each
    arm's own rate: under the null all arms share the same rate, and using each
    arm's rate would put its own noise into the denominator.
    """
    rows = []
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
        rows.append({"experiment_id": eid, "arms": k, "dof": k - 1, "Q": Q})
    return pd.DataFrame(rows)


def calibrate(panel: pd.DataFrame, tolerance: float = 0.15) -> Calibration:
    """Test the noise model against the A/A experiments.

    `tolerance` is how far Q/dof may stray from 1 before the calibration is judged
    unsound. The value 0.15 is deliberately generous: what matters is detecting a
    large bias, not a third-decimal deviation.
    """
    aa = panel.loc[panel["is_aa"]]
    if aa.empty:
        raise ValueError("no A/A experiments in the panel: calibration is impossible")

    q = cochran_q(aa)
    if q.empty:
        raise ValueError("no A/A experiment is usable for Cochran's Q")

    ratio = float(q["Q"].sum() / q["dof"].sum())
    p = stats.chi2.sf(q["Q"].to_numpy(), q["dof"].to_numpy())

    return Calibration(
        experiments=int(len(q)),
        arms=int(q["arms"].sum()),
        degrees_of_freedom=int(q["dof"].sum()),
        total_q=float(q["Q"].sum()),
        q_over_dof=ratio,
        median_q_over_dof=float((q["Q"] / q["dof"]).median()),
        fraction_p_005=float((p < 0.05).mean()),
        design_factor=ratio,
        passed=abs(ratio - 1.0) <= tolerance,
    )


def correct(v: pd.Series | np.ndarray, factor: float) -> np.ndarray:
    """Apply the design factor to the variance.

    This is exposed as a separate function, rather than folded into the panel, so
    that the comparison between naive `v` and corrected `v` remains explicit in
    the analysis.
    """
    if factor <= 0:
        raise ValueError(f"invalid design factor: {factor}")
    return np.asarray(v, dtype=float) * factor
