"""The portfolio level: alignment, the shrinkage limits, and policy value.

The alignment tests matter most. Length-equal but order-different splits produce
plausible numbers and announce nothing, so the guard that rejects them is itself
worth testing.
"""

import numpy as np
import pandas as pd
import pytest

from wcab import portfolio


def _split(n_experiments=8, arms=3, offset=0.0, seed=0):
    """Three aligned frames, as thinning.split_three_way returns them."""
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n_experiments):
        base = 0.012 + 0.001 * i
        for a in range(arms):
            theta = base + 0.0005 * a + offset + rng.normal(0, 1e-5)
            rows.append(
                {
                    "experiment_id": f"e{i}",
                    "arm_id": f"e{i}a{a}",
                    "impressions": 3000.0,
                    "theta_hat": theta,
                    "v": theta * (1 - theta) / 3000.0,
                }
            )
    return pd.DataFrame(rows)


def _portfolio(n_experiments=8, seed=0):
    sel = _split(n_experiments, seed=seed)
    est = _split(n_experiments, offset=1e-4, seed=seed + 1)
    ev = _split(n_experiments, offset=2e-4, seed=seed + 2)
    return portfolio.build_three_way(sel, est, ev)


# --------------------------------------------------------------------------
# Alignment: the corruption that does not announce itself
# --------------------------------------------------------------------------

def test_rejects_splits_of_equal_length_in_a_different_order():
    """The whole point of the guard: same rows, wrong order, same length."""
    sel = _split()
    est = _split(offset=1e-4)
    ev = _split(offset=2e-4).iloc[::-1].reset_index(drop=True)

    with pytest.raises(ValueError, match="misaligned"):
        portfolio.build_three_way(sel, est, ev)


def test_rejects_splits_holding_different_experiments():
    sel = _split(n_experiments=8)
    est = _split(n_experiments=8, offset=1e-4)
    ev = _split(n_experiments=8, offset=2e-4)
    ev.loc[0, "experiment_id"] = "someone_else"

    with pytest.raises(ValueError, match="misaligned"):
        portfolio.build_three_way(sel, est, ev)


def test_rejects_splits_of_different_length():
    sel = _split(n_experiments=8)
    est = _split(n_experiments=8, offset=1e-4)
    with pytest.raises(ValueError, match="rows"):
        portfolio.build_three_way(sel, est, est.iloc[:-1])


def test_accepts_aligned_splits():
    c = portfolio.build_three_way(
        _split(), _split(offset=1e-4), _split(offset=2e-4)
    )
    assert len(c) == 8
    assert set(c.table.columns) >= {
        "experiment_id", "arms", "delta_estimated", "delta_realized", "v"
    }


# --------------------------------------------------------------------------
# The shrinkage limits. Both directions, because it is easy to state backwards.
# --------------------------------------------------------------------------

def test_tau2_zero_sends_everything_to_the_weighted_centre():
    """alpha = v/(v + tau^2), so tau^2 = 0 gives alpha = 1: maximum shrinkage.

    Stating this the other way round is a natural slip, which is why it is
    pinned here.
    """
    c = _portfolio()
    shrunk, tau2 = portfolio.shrink_portfolio(c, tau2=0.0)

    d = c.table["delta_estimated"].to_numpy()
    v = c.table["v"].to_numpy()
    centre = np.average(d, weights=1.0 / v)

    assert tau2 == 0.0
    assert np.allclose(shrunk, centre)
    assert shrunk.std() == pytest.approx(0.0, abs=1e-15)


def test_a_large_tau2_returns_the_raw_estimates():
    c = _portfolio()
    shrunk, _ = portfolio.shrink_portfolio(c, tau2=1e6)
    assert np.allclose(shrunk, c.table["delta_estimated"].to_numpy(), atol=1e-12)


def test_shrinkage_preserves_the_ordering_when_precision_is_equal():
    """The project's central conceptual claim, pinned as a test.

    With v identical across experiments, alpha is identical too, so shrinkage is
    a monotone transformation of the estimate and cannot reorder anything.
    """
    c = _portfolio()
    c.table["v"] = 4e-7                       # one precision for everybody
    shrunk, _ = portfolio.shrink_portfolio(c, tau2=5e-7)

    raw_order = np.argsort(c.table["delta_estimated"].to_numpy())
    assert list(np.argsort(shrunk)) == list(raw_order)


def test_tail_priority_is_not_monotone_in_the_estimate():
    """What separates the tail rule from ranking by the shrunken mean.

    At equal estimated gain, the more precise experiment must receive the higher
    tail probability — so the rule depends on precision as well as on the point
    estimate.
    """
    c = _portfolio(n_experiments=2)
    c.table.loc[:, "delta_estimated"] = 0.002      # identical estimates
    c.table.loc[0, "v"] = 1e-8                     # precise
    c.table.loc[1, "v"] = 1e-6                     # imprecise

    priority = portfolio.tail_priority(c, tau2=1e-6)
    assert priority[0] > priority[1]


# --------------------------------------------------------------------------
# Threshold-adjusted value
# --------------------------------------------------------------------------

def test_value_is_zero_when_nothing_clears_the_threshold():
    c = _portfolio()
    out = portfolio.threshold_adjusted_value(
        c, c.table["delta_estimated"].to_numpy(), threshold=1.0
    )
    assert out["value"] == 0.0
    assert out["ship_rate"] == 0.0


def test_value_sums_only_what_was_shipped_net_of_the_threshold():
    c = _portfolio(n_experiments=4)
    c.table.loc[:, "delta_estimated"] = [0.010, 0.001, 0.008, 0.002]
    c.table.loc[:, "delta_realized"] = [0.006, 0.009, 0.004, 0.001]
    u = 0.005

    out = portfolio.threshold_adjusted_value(
        c, c.table["delta_estimated"].to_numpy(), u
    )

    # experiments 0 and 2 are shipped; their realised gains net of u are
    # 0.001 and -0.001, averaged over ALL four experiments
    assert out["value"] == pytest.approx(0.0)
    assert out["ship_rate"] == pytest.approx(0.5)
    assert out["value_per_shipped"] == pytest.approx(0.0)


def test_the_threshold_is_read_in_the_units_of_delta():
    """A stray factor of 100 here would give plausible and wrong numbers.

    Thresholds are proportions, like delta_estimated. Passing 0.4 where 0.004
    was meant must change the answer, not be silently absorbed.
    """
    c = _portfolio(n_experiments=4)
    c.table.loc[:, "delta_estimated"] = [0.010, 0.001, 0.008, 0.002]
    c.table.loc[:, "delta_realized"] = [0.010, 0.001, 0.008, 0.002]

    as_proportion = portfolio.threshold_adjusted_value(
        c, c.table["delta_estimated"].to_numpy(), 0.004
    )
    as_percentage_points = portfolio.threshold_adjusted_value(
        c, c.table["delta_estimated"].to_numpy(), 0.4
    )

    assert as_proportion["ship_rate"] == pytest.approx(0.5)
    assert as_percentage_points["ship_rate"] == 0.0


def test_rejects_a_priority_of_the_wrong_length():
    c = _portfolio()
    with pytest.raises(ValueError, match="entries"):
        portfolio.threshold_adjusted_value(c, np.zeros(3), 0.004)
