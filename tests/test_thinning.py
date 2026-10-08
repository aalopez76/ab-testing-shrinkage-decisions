"""The project's critical test.

If the split is wrong, **every** figure is wrong and nothing in the results
reveals it: the measured inflation comes out biased while the numbers look
perfectly ordinary. This is the only module with that property.

The property to defend is the **marginal independence** of the two halves. That
is exactly what distinguishes *data thinning* (valid for the binomial) from
*data fission* (which for the binomial does not yield independent parts), and it
is the confusion that very nearly made its way into this project's design.

A hook in `.claude/hooks/test_critico.py` runs this file whenever the split is
edited.
"""

import numpy as np
import pandas as pd
import pytest

from wcab import thinning

N_SIM = 30_000
TRUE_P = 0.013          # the archive's real rate, about 1.3%
N_PER_ARM = 3_000       # the real median of impressions per arm


@pytest.fixture(scope="module")
def halves():
    """Many realisations of X ~ Binomial(n, p), each one split in two."""
    rng = np.random.default_rng(20261003)
    x = rng.binomial(N_PER_ARM, TRUE_P, size=N_SIM)
    n = np.full(N_SIM, N_PER_ARM, dtype=np.int64)
    n_a, c_a, n_b, c_b = thinning.split_counts(n, x, 0.5, rng)
    return {"x": x, "n_a": n_a, "c_a": c_a, "n_b": n_b, "c_b": c_b}


# --------------------------------------------------------------------------
# 1. Exactness: the split neither invents nor loses anything
# --------------------------------------------------------------------------

def test_the_halves_sum_to_the_original(halves):
    m = halves
    assert np.array_equal(m["c_a"] + m["c_b"], m["x"])
    assert np.array_equal(m["n_a"] + m["n_b"], np.full(N_SIM, N_PER_ARM))


def test_neither_half_is_left_empty(halves):
    assert (halves["n_a"] >= 1).all()
    assert (halves["n_b"] >= 1).all()


def test_clicks_never_exceed_impressions(halves):
    m = halves
    assert (m["c_a"] <= m["n_a"]).all() and (m["c_a"] >= 0).all()
    assert (m["c_b"] <= m["n_b"]).all() and (m["c_b"] >= 0).all()


# --------------------------------------------------------------------------
# 2. Unbiasedness: each half estimates the true rate
# --------------------------------------------------------------------------

def test_each_half_is_unbiased(halves):
    m = halves
    for side in ("a", "b"):
        rate = (m[f"c_{side}"] / m[f"n_{side}"]).mean()
        error = abs(rate - TRUE_P)
        # four standard errors of the mean over N_SIM observations
        bound = 4 * np.sqrt(TRUE_P * (1 - TRUE_P) / (N_PER_ARM / 2) / N_SIM)
        assert error < bound, f"half {side}: {rate:.6f} vs {TRUE_P}"


def test_each_halfs_variance_is_the_correct_binomial(halves):
    """If a half were Binomial(n_a, p), its variance must be n_a * p * (1-p)."""
    m = halves
    for side in ("a", "b"):
        expected = (N_PER_ARM / 2) * TRUE_P * (1 - TRUE_P)
        observed = m[f"c_{side}"].var(ddof=1)
        assert 0.9 < observed / expected < 1.1, (
            f"half {side}: variance {observed:.1f} vs expected {expected:.1f}"
        )


# --------------------------------------------------------------------------
# 3. THE CRITICAL TEST: marginal independence
# --------------------------------------------------------------------------

def test_the_two_halves_are_independent(halves):
    """The heart of the project.

    The rates of the two halves must be uncorrelated. Were they linked, selecting
    the maximum in half A would mechanically drag half B along with it and the
    measured inflation would come out biased, with nothing to reveal it.
    """
    m = halves
    theta_a = m["c_a"] / m["n_a"]
    theta_b = m["c_b"] / m["n_b"]
    r = float(np.corrcoef(theta_a, theta_b)[0, 1])
    bound = 4 / np.sqrt(N_SIM)         # four standard errors of a null correlation
    assert abs(r) < bound, (
        f"correlation between halves = {r:+.4f}, should be about 0 (bound {bound:.4f}). "
        "A strongly negative value would mean the split is conditioning wrongly: "
        "that would be the behaviour of data fission, not of data thinning."
    )


def test_contrast_the_naive_split_is_correlated():
    """Documents why the implementation is what it is.

    A "naive" split in the style of *data fission* divides the RATE rather than
    the counts: theta_A = theta + Z, theta_B = theta - Z. Its correlation is

        corr(theta+Z, theta-Z) = (Var theta - Var Z) / (Var theta + Var Z)

    which is zero only at the exact point Var Z = Var theta, and negative as soon
    as the noise dominates. In other words, **independence would depend on
    getting the noise variance right**, which is precisely the quantity this
    project does not know — hence splitting the counts rather than the rate.

    Here Var Z is about 25 times Var theta, where the anticorrelation is
    unambiguous.
    """
    rng = np.random.default_rng(1)
    theta = rng.binomial(N_PER_ARM, TRUE_P, size=20_000) / N_PER_ARM
    sd_theta = np.sqrt(TRUE_P * (1 - TRUE_P) / N_PER_ARM)
    noise = rng.normal(0, 5 * sd_theta, size=20_000)

    r = float(np.corrcoef(theta + noise, theta - noise)[0, 1])
    expected = (sd_theta**2 - (5 * sd_theta) ** 2) / (
        sd_theta**2 + (5 * sd_theta) ** 2
    )
    assert r < -0.8, f"the naive shortcut should anticorrelate: r={r:+.3f}"
    assert abs(r - expected) < 0.05, (
        f"the observed correlation ({r:+.3f}) should follow the algebra "
        f"({expected:+.3f})"
    )


# --------------------------------------------------------------------------
# 4. The panel-level interface
# --------------------------------------------------------------------------

def _minimal_panel(n=(3000, 3000, 5000), c=(40, 35, 70)):
    d = pd.DataFrame(
        {
            "experiment_id": ["e1", "e1", "e2"],
            "arm_id": ["a", "b", "c"],
            "impressions": n,
            "clicks": c,
            "is_aa": [False, False, False],
        }
    )
    d["theta_hat"] = d.clicks / d.impressions
    d["v"] = d.theta_hat * (1 - d.theta_hat) / d.impressions
    return d


def test_split_preserves_the_panel_and_recomputes():
    p = _minimal_panel()
    out = thinning.split(p, fraction=0.5, seed=3)
    assert thinning.check_sum(p, out)
    for half in (out.estimation, out.evaluation):
        assert list(half.columns) == list(p.columns)
        assert np.allclose(half["theta_hat"], half["clicks"] / half["impressions"])
        v = half["theta_hat"] * (1 - half["theta_hat"]) / half["impressions"]
        assert np.allclose(half["v"], v)
    # descriptive columns are carried over unchanged
    assert list(out.estimation["experiment_id"]) == list(p["experiment_id"])


def test_the_seed_makes_the_split_reproducible():
    p = _minimal_panel()
    a = thinning.split(p, seed=42).estimation["clicks"].tolist()
    b = thinning.split(p, seed=42).estimation["clicks"].tolist()
    c = thinning.split(p, seed=43).estimation["clicks"].tolist()
    assert a == b
    assert a != c


@pytest.mark.parametrize("fraction", [0.0, 1.0, -0.1, 1.5])
def test_rejects_invalid_fractions(fraction):
    with pytest.raises(ValueError):
        thinning.split(_minimal_panel(), fraction=fraction)


def test_rejects_impossible_data():
    with pytest.raises(ValueError):
        thinning.split_counts([100], [200], 0.5, np.random.default_rng(0))
    with pytest.raises(ValueError):
        thinning.split_counts([1], [0], 0.5, np.random.default_rng(0))


# --------------------------------------------------------------------------
# The three-way shares. Exposed so the published numbers can be reported
# against the split that produced them, which makes two things testable: that
# the default still reproduces the equal thirds every figure was computed on,
# and that a requested allocation is the one actually delivered.
# --------------------------------------------------------------------------

def _panel_for_shares(rows: int = 600, seed: int = 11) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n = rng.integers(400, 4000, size=rows)
    return pd.DataFrame({
        "experiment_id": [f"e{i // 3:04d}" for i in range(rows)],
        "arm_id": [f"a{i:05d}" for i in range(rows)],
        "impressions": n,
        "clicks": rng.binomial(n, 0.02),
    })


def test_the_default_shares_are_equal_thirds():
    """Every published figure uses this path; it must not have moved."""
    p = _panel_for_shares()
    parts = thinning.split_three_way(p, seed=3)
    explicit = thinning.split_three_way(p, seed=3, shares=(1 / 3, 1 / 3, 1 / 3))
    for a, b in zip(parts, explicit):
        assert a["clicks"].equals(b["clicks"])
        assert a["impressions"].equals(b["impressions"])


def test_the_three_parts_still_reconstruct_the_original():
    """Thinning splits counts; it does not create or destroy them."""
    p = _panel_for_shares()
    for shares in [(1 / 3, 1 / 3, 1 / 3), (0.25, 0.25, 0.50), (0.5, 0.25, 0.25)]:
        a, b, c = thinning.split_three_way(p, seed=5, shares=shares)
        total = (a["clicks"].to_numpy() + b["clicks"].to_numpy()
                 + c["clicks"].to_numpy())
        assert (total == p["clicks"].to_numpy()).all()
        total = (a["impressions"].to_numpy() + b["impressions"].to_numpy()
                 + c["impressions"].to_numpy())
        assert (total == p["impressions"].to_numpy()).all()


def test_the_requested_allocation_is_the_one_delivered():
    """A second fraction conditional on the first is easy to get wrong."""
    p = _panel_for_shares(rows=3000)
    total = p["impressions"].sum()
    for shares in [(0.25, 0.25, 0.50), (0.5, 0.25, 0.25), (0.2, 0.4, 0.4)]:
        parts = thinning.split_three_way(p, seed=9, shares=shares)
        realised = [part["impressions"].sum() / total for part in parts]
        for asked, got in zip(shares, realised):
            assert abs(asked - got) < 0.01, f"asked {shares}, got {realised}"


@pytest.mark.parametrize("bad", [(0.5, 0.5, 0.5), (0.5, 0.5, 0.0), (1.0, 0.0, 0.0)])
def test_shares_that_do_not_form_a_split_are_rejected(bad):
    with pytest.raises(ValueError):
        thinning.split_three_way(_panel_for_shares(rows=60), shares=bad)
