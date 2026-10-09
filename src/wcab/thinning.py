"""Step 4: split each arm into two independent halves.

Measuring how far the selected variant was inflated requires evaluating it on
data that played no part in selecting it. The archive's held-out sample does not
serve this purpose — it contains *different* experiments — so each arm is split
instead.

**The result that makes this valid.** If X ~ Binomial(n, p) and one draws
X_A | X ~ Hypergeometric(n, X, m) with X_B = X - X_A, then

    X_A ~ Binomial(m, p),   X_B ~ Binomial(n-m, p),   X_A independent of X_B

The independence is **marginal**, not conditional: given X the two halves sum to
a constant and are therefore linked, but because X is itself random the joint
pair reproduces exactly the law that would have arisen from splitting the trials
in advance. This is *data thinning* for convolution-closed distributions
(Neufeld et al., *JMLR* 2024).

**It is not *data fission*** (Leiner, Duan, Tibshirani and Ramdas). For the
binomial that technique yields components that are **not** independent, and
independence is precisely what is needed here. The confusion is easy to make and
very nearly made its way into this project's design; `tests/test_thinning.py`
exists so that it cannot happen again.

Were the split incorrect, **every** figure in the project would be wrong and
nothing in the results would reveal it. This is the only module with that
property, which is why a hook runs its test whenever it is edited.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Partition:
    """The two halves of a panel, together with the fraction used."""

    estimation: pd.DataFrame   # half A: used to select
    evaluation: pd.DataFrame   # half B: used to score; played no part in selecting
    fraction: float
    seed: int


def split_counts(
    n: np.ndarray,
    c: np.ndarray,
    fraction: float,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Split (n, c) into two independent halves.

    Returns (n_a, c_a, n_b, c_b). `n_a` is the nearest integer to
    `fraction * n`, clipped to [1, n-1] so that neither half can be empty: an arm
    with an empty half carries no information and would break the ratios
    downstream.
    """
    if not 0.0 < fraction < 1.0:
        raise ValueError(f"fraction outside (0,1): {fraction}")

    n = np.asarray(n, dtype=np.int64)
    c = np.asarray(c, dtype=np.int64)
    if np.any(c < 0) or np.any(c > n):
        raise ValueError("clicks out of range: 0 <= c <= n must hold")
    if np.any(n < 2):
        raise ValueError("an arm with fewer than 2 impressions cannot be split")

    n_a = np.clip(np.rint(fraction * n).astype(np.int64), 1, n - 1)
    n_b = n - n_a

    # Hypergeometric: out of n impressions carrying c clicks, how many clicks fall
    # in the n_a that make up half A. `nbad` is the impressions without a click.
    c_a = rng.hypergeometric(ngood=c, nbad=n - c, nsample=n_a)
    c_b = c - c_a

    return n_a, c_a, n_b, c_b


def split(
    panel: pd.DataFrame,
    fraction: float = 0.5,
    seed: int = 0,
) -> Partition:
    """Split a canonical panel into an estimation half and an evaluation half.

    Each half keeps the panel's columns, with `impressions`, `clicks`,
    `theta_hat` and `v` recomputed for its own size. Descriptive columns —
    experiment, week, is_aa — are carried over unchanged.
    """
    rng = np.random.default_rng(seed)
    n_a, c_a, n_b, c_b = split_counts(
        panel["impressions"].to_numpy(), panel["clicks"].to_numpy(), fraction, rng
    )

    def _half(n_m: np.ndarray, c_m: np.ndarray) -> pd.DataFrame:
        out = panel.copy()
        out["impressions"] = n_m
        out["clicks"] = c_m
        theta = c_m / n_m
        out["theta_hat"] = theta
        out["v"] = theta * (1.0 - theta) / n_m
        return out.reset_index(drop=True)

    return Partition(
        estimation=_half(n_a, c_a),
        evaluation=_half(n_b, c_b),
        fraction=fraction,
        seed=seed,
    )


def check_sum(panel: pd.DataFrame, p: Partition) -> bool:
    """The split neither invents nor loses data: the halves sum to the original."""
    n_ok = np.array_equal(
        p.estimation["impressions"] + p.evaluation["impressions"],
        panel["impressions"].to_numpy(),
    )
    c_ok = np.array_equal(
        p.estimation["clicks"] + p.evaluation["clicks"], panel["clicks"].to_numpy()
    )
    return bool(n_ok and c_ok)


def split_three_way(
    panel: pd.DataFrame,
    seed: int = 0,
    shares: tuple[float, float, float] = (1 / 3, 1 / 3, 1 / 3),
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split into three independent parts: select, estimate, evaluate.

    This is necessary because a **selected** statistic — the maximum of an
    experiment — does not behave like an ordinary noisy estimate: its
    distribution is shifted and its variance is not the naive one, so empirical
    Bayes machinery applied to it produces meaningless results (in practice, a
    tau^2 estimated as zero).

    The remedy is to separate the roles:

        A1  selects the arm        (and nothing else)
        A2  estimates its advantage (having played no part in selecting it)
        B   scores what it delivered (having played no part in either)

    The estimated delta then ceases to be a maximum and becomes the advantage of
    an **already-fixed** arm, which is an unbiased estimate and to which shrinkage
    can properly be applied.

    `shares` are the proportions going to (select, estimate, evaluate) and
    default to equal thirds, which is what every published figure uses. They are
    exposed because the split fraction governs a real tradeoff rather than a
    detail: in data thinning it decides how much information goes to the task
    being performed as against the task of evaluating it, and its best value is
    problem-dependent (Neufeld et al., JMLR 2024). The published estimates are
    reported against this choice in `scripts/12_split_sensitivity.py`.

    Implemented as two successive binary splits, so the second fraction is
    conditional on what the first left behind.
    """
    total = sum(shares)
    if not np.isclose(total, 1.0) or any(s <= 0 for s in shares):
        raise ValueError(f"shares must be positive and sum to 1, got {shares}")

    select, estimate, evaluate = shares
    first = split(panel, fraction=select + estimate, seed=seed)
    second = split(first.estimation, fraction=select / (select + estimate),
                   seed=seed + 10_000)
    return second.estimation, second.evaluation, first.evaluation
