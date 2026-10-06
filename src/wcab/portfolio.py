"""Phase E: the decision BETWEEN experiments, which is where improvement is possible.

Phase D found that shrinkage cannot change which arm is selected **within** an
experiment: with a near-uniform alpha and a common target, theta-tilde is a
monotone transformation of theta-hat and preserves the ordering. This is not a
failure of the method — with balanced arms there is no selection problem to
improve upon.

The condition that makes the selection problem real has a name in the
literature: **heterogeneous precision** (Gu and Koenker, *Invidious Comparisons:
Ranking and Selection as Compound Decisions*, Econometrica 2023). In this
archive:

    within an experiment    ratio n_max/n_min ~ 1.04   -> homogeneous
    between experiments     ratio p99/p01 ~ 7.1        -> heterogeneous

So the relevant level is the upper one, which happens to be the level the
industry poses: Meta writes about *"experiments selected for launch"* and
Netflix about *when to ship*. Decisions between experiments, not within one.

**The decision being modelled.** A team runs many experiments and cannot deploy
all of them: there is a budget, or a reluctance to saturate users. Which of the
winners are worth deploying? They are selected using the estimation split and
scored on what they delivered in the evaluation split.

**And the right rule is not the maximum of the shrunken mean either.** The
literature reports that under heterogeneous precision, *posterior tail
probability* rules outperform posterior-mean rules, because they combine
theta-hat with its precision **non-monotonically** and therefore do reorder.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats


@dataclass(frozen=True)
class Portfolio:
    """One row per experiment: the estimated gain and the realised one."""

    table: pd.DataFrame

    def __len__(self) -> int:
        return len(self.table)


def build_three_way(
    selection: pd.DataFrame, estimation: pd.DataFrame, evaluation: pd.DataFrame
) -> Portfolio:
    """Summarise each experiment, separating selection, estimation and evaluation.

    The arm is selected using `selection`; its advantage is estimated on
    `estimation`, which played no part in selecting it; and it is scored on
    `evaluation`, which played no part in either. The estimated delta is
    therefore the advantage of an **already-fixed** arm — an unbiased estimate —
    rather than the maximum of an experiment, which is a selected statistic to
    which shrinkage cannot be applied directly.
    """
    n = len(selection)
    if not (len(estimation) == len(evaluation) == n):
        raise ValueError("the three splits are not aligned")

    exp = selection["experiment_id"].to_numpy()
    th_e = selection["theta_hat"].to_numpy(dtype=float)
    th_a = estimation["theta_hat"].to_numpy(dtype=float)
    th_b = evaluation["theta_hat"].to_numpy(dtype=float)
    v_a = estimation["v"].to_numpy(dtype=float)

    order = np.argsort(exp, kind="stable")
    e_ord = exp[order]
    cuts = np.flatnonzero(np.r_[True, e_ord[1:] != e_ord[:-1]])
    bounds = np.r_[cuts, len(e_ord)]

    rows = []
    for a, b in zip(bounds[:-1], bounds[1:]):
        idx = order[a:b]
        k = len(idx)
        if k < 2:
            continue
        chosen = idx[int(np.argmax(th_e[idx]))]          # selected on the first split
        # advantage over the mean of the NOT-selected arms, estimated on the second
        others = idx[idx != chosen]
        delta_est = float(th_a[chosen] - th_a[others].mean())
        delta_real = float(th_b[chosen] - th_b[others].mean())
        v_delta = float(v_a[chosen] + v_a[others].sum() / len(others) ** 2)
        rows.append(
            {
                "experiment_id": e_ord[a],
                "arms": k,
                "impressions": float(estimation["impressions"].to_numpy()[idx].sum()),
                "delta_estimated": delta_est,
                "delta_realized": delta_real,
                "v": max(v_delta, 1e-18),
                "theta_chosen_b": float(th_b[chosen]),
                "mean_b": float(th_b[others].mean()),
            }
        )
    return Portfolio(pd.DataFrame(rows))


def build(estimation: pd.DataFrame, evaluation: pd.DataFrame) -> Portfolio:
    """Summarise each experiment by the gain from selecting the best arm.

    The quantity of interest is the **benefit of having run the experiment**:
    how much better the selected arm is than picking one at random, which is the
    experiment's mean.

        delta_hat = theta_hat(chosen on A) - mean of theta_hat on A   (promised)
        delta     = theta(chosen) on B     - mean of theta on B       (delivered)

    The variance of the estimated delta is approximated as v(chosen) + sum(v)/k^2,
    **ignoring the effect of selection** — which is precisely what this project
    measures, so including it here would be circular. The approximation is
    declared and used only as a scale for shrinkage, never as a confidence
    interval.
    """
    if len(estimation) != len(evaluation):
        raise ValueError("the two splits are not aligned")

    exp = estimation["experiment_id"].to_numpy()
    th_a = estimation["theta_hat"].to_numpy(dtype=float)
    th_b = evaluation["theta_hat"].to_numpy(dtype=float)
    v_a = estimation["v"].to_numpy(dtype=float)

    order = np.argsort(exp, kind="stable")
    e_ord = exp[order]
    cuts = np.flatnonzero(np.r_[True, e_ord[1:] != e_ord[:-1]])
    bounds = np.r_[cuts, len(e_ord)]

    rows = []
    for a, b in zip(bounds[:-1], bounds[1:]):
        idx = order[a:b]
        k = len(idx)
        if k < 2:
            continue
        chosen = idx[int(np.argmax(th_a[idx]))]
        mean_a = float(th_a[idx].mean())
        mean_b = float(th_b[idx].mean())
        v_sel = float(v_a[chosen] + v_a[idx].sum() / k**2)
        rows.append(
            {
                "experiment_id": e_ord[a],
                "arms": k,
                "impressions": float(estimation["impressions"].to_numpy()[idx].sum()),
                "delta_estimated": float(th_a[chosen]) - mean_a,
                "delta_realized": float(th_b[chosen]) - mean_b,
                "v": max(v_sel, 1e-18),
                "theta_chosen_b": float(th_b[chosen]),
                "mean_b": mean_b,
            }
        )
    return Portfolio(pd.DataFrame(rows))


# ---------------------------------------------------------------------------
# The prioritisation rules
# ---------------------------------------------------------------------------

def raw_priority(c: Portfolio) -> np.ndarray:
    """Rank by the estimated gain. The practice being put to the test."""
    return c.table["delta_estimated"].to_numpy(dtype=float)


def shrink_portfolio(c: Portfolio, tau2: float | None = None) -> tuple[np.ndarray, float]:
    """Shrinkage between experiments: each estimated delta towards the overall mean.

    Here precision **does** vary between experiments, so alpha varies with it and
    the transformation is no longer monotone in the estimated delta: two
    experiments with the same estimated gain but different precision are ranked
    differently. This is why shrinkage at this level can reorder while the
    within-experiment shrinkage of phase D could not.
    """
    d = c.table["delta_estimated"].to_numpy(dtype=float)
    v = c.table["v"].to_numpy(dtype=float)
    if tau2 is None:
        # second moment: observed variance minus mean noise, floored at zero
        tau2 = max(float(np.var(d, ddof=1) - v.mean()), 0.0)
    alpha = v / (v + tau2) if tau2 > 0 else np.ones_like(v)
    center = float(np.average(d, weights=1.0 / v))
    return (1.0 - alpha) * d + alpha * center, float(tau2)


def tail_priority(c: Portfolio, tau2: float | None = None, threshold: float = 0.0) -> np.ndarray:
    """Posterior probability that the true gain exceeds a threshold.

    The rule the literature identifies as superior under heterogeneous precision.
    With a normal(center, tau^2) prior and a normal(delta_hat, v) likelihood, each
    experiment's posterior is normal with the shrunken value as its mean and
    variance v*tau^2/(v+tau^2); the tail probability follows immediately.

    **It is not monotone in the estimated delta**: at equal estimated gain, the
    more precise experiment receives the higher probability. That is what
    distinguishes it from ranking by the shrunken mean, which is monotone in the
    estimated delta at fixed precision.
    """
    mean, t2 = shrink_portfolio(c, tau2)
    v = c.table["v"].to_numpy(dtype=float)
    var_post = v * t2 / (v + t2) if t2 > 0 else np.zeros_like(v)
    sd = np.sqrt(np.maximum(var_post, 1e-24))
    return stats.norm.sf(threshold, loc=mean, scale=sd)


# ---------------------------------------------------------------------------
# The evaluation: curve by budget
# ---------------------------------------------------------------------------

def value_by_budget(
    c: Portfolio, priority: np.ndarray, budgets: tuple[float, ...]
) -> dict[float, float]:
    """Mean realised gain of the selected experiments, by budget.

    `budget` is the fraction of experiments that can be deployed. Experiments are
    ranked by `priority` — computed on the estimation split — and scored on what
    they delivered in the evaluation split.
    """
    realized = c.table["delta_realized"].to_numpy(dtype=float)
    order = np.argsort(-np.asarray(priority, dtype=float), kind="stable")
    n = len(order)
    out = {}
    for b in budgets:
        k = max(1, int(round(b * n)))
        out[b] = float(realized[order[:k]].mean())
    return out


def oracle(c: Portfolio, budgets: tuple[float, ...]) -> dict[float, float]:
    """The ceiling: ranking by the REALISED gain. Unattainable in practice."""
    return value_by_budget(c, c.table["delta_realized"].to_numpy(), budgets)
