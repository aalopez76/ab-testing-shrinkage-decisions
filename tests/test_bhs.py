"""BHS: that it reproduces its own base case, and that it can say "not needed".

The third test is the one that matters. If the fit always called for local
flexibility, the result on real data would mean nothing: one must first establish
that the method discriminates.
"""

import numpy as np
import pytest

from wcab.shrinkage import bhs


@pytest.fixture
def data():
    rng = np.random.default_rng(0)
    n = 3000
    s2 = rng.gamma(4, 1e-6, n)
    return rng, n, s2


def test_large_a_reproduces_global_shrinkage(data):
    """The paper calls lambda_i = 1 "Bayesian Global Shrinkage". BHS must yield it."""
    rng, n, s2 = data
    m0, tau = 0.0, 2e-5
    theta = rng.normal(m0, np.sqrt(tau), n) + rng.normal(0, np.sqrt(s2))

    fitted = bhs.BHSFit(m0=m0, tau=tau, a=5_000.0, log_likelihood=0.0,
                        log_likelihood_global=0.0, experiments=n)
    by_bhs = bhs.posterior_mean(theta, s2, fitted)

    alpha = s2 / (s2 + tau)
    global_ = (1.0 - alpha) * theta + alpha * m0

    # theta is on the scale of sqrt(2e-5) ~ 4.5e-3, so a 1e-5 tolerance is 0.2%
    assert np.max(np.abs(by_bhs - global_)) < 1e-5
    assert np.max(np.abs(bhs.effective_alpha(theta, s2, fitted) - alpha)) < 1e-3


def test_recovers_the_degrees_of_freedom_of_a_t_prior(data):
    """Given a hand-built t prior with 3 dof, the fitted a should land near 3."""
    rng, n, s2 = data
    m0, tau, dof = 0.0, 2e-5, 3.0
    theta = m0 + np.sqrt(tau) * rng.standard_t(dof, n) + rng.normal(0, np.sqrt(s2))

    r = bhs.fit(theta, s2)
    assert 2.0 < r.a < 6.0
    assert r.requires_local_flexibility


def test_with_a_normal_prior_it_does_NOT_require_local_flexibility(data):
    """The decisive test: the method must be able to say it is not needed."""
    rng, n, s2 = data
    m0, tau = 0.0, 2e-5
    theta = rng.normal(m0, np.sqrt(tau), n) + rng.normal(0, np.sqrt(s2))

    r = bhs.fit(theta, s2)
    assert not r.requires_local_flexibility, (
        f"local flexibility was requested for a normal prior: a={r.a:.1f}, "
        f"likelihood ratio={r.beats_global:.1f}"
    )


def test_the_effective_weight_stays_in_the_valid_interval(data):
    rng, n, s2 = data
    theta = rng.normal(0.0, 4e-3, n)
    fitted = bhs.BHSFit(m0=0.0, tau=2e-5, a=3.0, log_likelihood=0.0,
                        log_likelihood_global=0.0, experiments=n)
    alpha = bhs.effective_alpha(theta, s2, fitted)
    assert np.all(alpha > 0.0) and np.all(alpha < 1.0)


def test_it_shrinks_observations_far_from_the_centre_less(data):
    """The robustness of BHS: heavy tails mean less shrinkage far from the centre."""
    _, _, _ = data
    s2 = np.full(5, 1e-5)
    theta = np.array([0.0, 2e-3, 5e-3, 1e-2, 5e-2])
    fitted = bhs.BHSFit(m0=0.0, tau=1e-5, a=2.5, log_likelihood=0.0,
                        log_likelihood_global=0.0, experiments=5)
    alpha = bhs.effective_alpha(theta, s2, fitted)
    assert np.all(np.diff(alpha) < 0), f"the weight does not decrease with distance: {alpha}"
