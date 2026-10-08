"""Calibration decides whether `v` is usable, so it is tested against known truth."""

import numpy as np
import pandas as pd
import pytest

from wcab.diagnostics import noise


def _panel(n_exp, k, n_per_arm, p, excess_factor=1.0, seed=0):
    """Generate a synthetic A/A panel.

    `excess_factor` > 1 inflates the true variance without moving the mean,
    simulating clustered impressions: that is what makes it possible to check
    that calibration detects the excess rather than merely assuming it.
    """
    rng = np.random.default_rng(seed)
    rows = []
    for e in range(n_exp):
        for b in range(k):
            if excess_factor == 1.0:
                clicks = rng.binomial(n_per_arm, p)
            else:
                # beta-binomial: same mean, variance inflated by the factor
                rho = (excess_factor - 1.0) / (n_per_arm - 1.0)
                a = p * (1 - rho) / rho
                bb = (1 - p) * (1 - rho) / rho
                clicks = rng.binomial(n_per_arm, rng.beta(a, bb))
            rows.append((f"e{e}", f"e{e}b{b}", n_per_arm, clicks))
    d = pd.DataFrame(rows, columns=["experiment_id", "arm_id", "impressions", "clicks"])
    d["theta_hat"] = d.clicks / d.impressions
    d["v"] = d.theta_hat * (1 - d.theta_hat) / d.impressions
    d["is_aa"] = True
    return d


def test_it_passes_when_the_noise_is_purely_binomial():
    """With no excess, Q/dof should sit near 1 and calibration should pass."""
    cal = noise.calibrate(_panel(400, 4, 3000, 0.013))
    assert 0.85 < cal.q_over_dof < 1.15, cal
    assert cal.passed
    assert cal.fraction_p_005 < 0.12


def test_it_detects_a_known_amount_of_overdispersion():
    """With the variance inflated twofold, calibration must reject and measure it."""
    cal = noise.calibrate(_panel(400, 4, 3000, 0.013, excess_factor=2.0, seed=7))
    assert not cal.passed
    assert 1.6 < cal.q_over_dof < 2.5, cal
    assert cal.design_factor == cal.q_over_dof


def test_correcting_scales_the_variance():
    v = pd.Series([1e-6, 4e-6])
    out = noise.correct(v, 1.9)
    assert np.allclose(out, [1.9e-6, 7.6e-6])


def test_correcting_rejects_invalid_factors():
    with pytest.raises(ValueError):
        noise.correct(pd.Series([1e-6]), 0.0)
