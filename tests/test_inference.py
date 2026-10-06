"""The cluster bootstrap, and the two failures that would pass unnoticed.

The relabelling test is the important one. Without fresh ids, a cluster drawn
twice is reunited by the next groupby, the replicate quietly holds fewer and
larger experiments, and the interval comes out too narrow with nothing to show
for it.
"""

import numpy as np
import pandas as pd
import pytest

from wcab import inference


def _panel(n_experiments=40, arms=3, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n_experiments):
        base = rng.normal(0.013, 0.003)
        for a in range(arms):
            rows.append(
                {
                    "experiment_id": f"e{i}",
                    "arm_id": f"e{i}a{a}",
                    "theta_hat": max(base + rng.normal(0, 5e-4), 1e-4),
                }
            )
    return pd.DataFrame(rows)


def test_resampling_relabels_every_copy():
    """Each drawn cluster must become its own experiment.

    This is the defect that destroys a cluster bootstrap in silence: duplicate
    ids survive into the next groupby and the copies merge back together.
    """
    p = _panel(n_experiments=30)
    out = inference.resample_experiments(p, np.random.default_rng(0))

    # as many experiments out as in, even though some originals were drawn twice
    assert out["experiment_id"].nunique() == p["experiment_id"].nunique()
    # and the new labels share nothing with the old ones
    assert not set(out["experiment_id"]) & set(p["experiment_id"])
    # every block keeps its full set of arms
    assert out.groupby("experiment_id").size().unique().tolist() == [3]


def test_resampling_actually_draws_with_replacement():
    """With replacement, some originals appear more than once and others not at all."""
    p = _panel(n_experiments=60)
    out = inference.resample_experiments(p, np.random.default_rng(1))
    # arm_id still carries the original experiment, so duplicates are visible
    origins = out["arm_id"].str.split("a").str[0]
    counts = origins.value_counts()
    assert counts.max() > 3, "no cluster was drawn more than once"
    assert len(counts) < p["experiment_id"].nunique(), "every cluster was drawn"


def test_point_estimate_is_the_original_not_the_bootstrap_mean():
    """The bootstrap estimates the sampling distribution; it does not replace
    the estimator."""
    p = _panel()
    stat = lambda panel, seed: float(panel["theta_hat"].mean())

    r = inference.cluster_bootstrap(p, stat, replicates=50, seeds_per_replicate=1, seed=0)

    assert r.point_estimate == pytest.approx(p["theta_hat"].mean())
    # the bootstrap mean is close but is a separate, diagnostic quantity
    assert r.bootstrap_mean != r.point_estimate


def test_the_interval_covers_a_known_mean():
    p = _panel(n_experiments=80, seed=3)
    stat = lambda panel, seed: float(panel["theta_hat"].mean())

    r = inference.cluster_bootstrap(p, stat, replicates=300, seeds_per_replicate=1, seed=0)

    lo, hi = r.percentile_interval
    assert lo < r.point_estimate < hi
    assert r.bootstrap_se > 0


def test_monte_carlo_variability_is_reported_apart_from_the_interval():
    """A statistic that depends on the seed must show spread in mc_variability,
    not have it folded into the interval."""
    p = _panel()
    noisy = lambda panel, seed: float(
        panel["theta_hat"].mean() + np.random.default_rng(seed).normal(0, 1e-4)
    )

    r = inference.cluster_bootstrap(p, noisy, replicates=60, seeds_per_replicate=5, seed=0)

    assert r.mc_variability > 0
    steady = lambda panel, seed: float(panel["theta_hat"].mean())
    r2 = inference.cluster_bootstrap(p, steady, replicates=60, seeds_per_replicate=5, seed=0)
    assert r2.mc_variability == 0.0


def test_basic_and_percentile_agree_on_a_symmetric_statistic():
    p = _panel(n_experiments=80, seed=5)
    stat = lambda panel, seed: float(panel["theta_hat"].mean())

    r = inference.cluster_bootstrap(p, stat, replicates=400, seeds_per_replicate=1, seed=0)

    assert r.intervals_agree
    assert abs(r.bias) < r.bootstrap_se


def test_a_dict_statistic_keeps_comparisons_paired():
    """Two rules applied to the same replicates must be compared within them.

    Running separate bootstraps and subtracting ignores how strongly the two
    move together, which inflates the variance of the difference. Returning both
    from one call keeps the pairing — and the interval for the difference comes
    out much tighter than the independent-bootstrap arithmetic would suggest.
    """
    p = _panel(n_experiments=80, seed=7)

    def both(panel, seed):
        m = float(panel["theta_hat"].mean())
        return {"a": m, "b": m * 1.01, "difference": m * 0.01}

    r = inference.cluster_bootstrap(p, both, replicates=300, seeds_per_replicate=1, seed=0)

    assert set(r) == {"a", "b", "difference"}
    assert all(res.replicates == r["a"].replicates for res in r.values())

    # the paired difference is far better determined than treating a and b as
    # independent would imply
    independent_se = (r["a"].bootstrap_se**2 + r["b"].bootstrap_se**2) ** 0.5
    assert r["difference"].bootstrap_se < independent_se / 10


def test_a_scalar_statistic_still_returns_a_single_result():
    p = _panel(n_experiments=30)
    r = inference.cluster_bootstrap(
        p, lambda panel, seed: float(panel["theta_hat"].mean()),
        replicates=40, seeds_per_replicate=1, seed=0,
    )
    assert isinstance(r, inference.BootstrapResult)


def test_rejects_an_invalid_level():
    p = _panel(n_experiments=10)
    with pytest.raises(ValueError):
        inference.cluster_bootstrap(
            p, lambda panel, seed: 0.0, replicates=5, level=1.5
        )
