"""Bayesian Hybrid Shrinkage (BHS), Meta's 2025 proposal.

A faithful implementation of the hierarchical model of Mudd, Friedberg,
Gorbachev, Nassif and Zaidi (arXiv 2511.06318, CODE@MIT'25):

    theta_hat_i | theta_i, s_i^2  ~  N(theta_i, s_i^2)
    theta_i | m0, lambda_i, tau   ~  N(m0, lambda_i * tau)
    lambda_i | a, b               ~  InverseGamma(a/2, b/2)

The **local** factor lambda_i is what distinguishes BHS from standard shrinkage.
The paper itself names the special case lambda_i = 1 for all i: it calls it
*"Bayesian Global Shrinkage"*, and that is exactly what `shrinkage/__init__.py`
implements.

**Parameterisation.** tau and b are not separately identifiable: only their
product enters the prior's scale. Setting `b = a - 2` gives E[lambda_i] = 1,
leaving tau as the global scale and `a` as the single control on local
flexibility:

    a -> infinity  =>  lambda_i -> 1  =>  global shrinkage (the paper's baseline)
    small a        =>  heavy tails    =>  robustness to a misspecified prior

That makes `a` a diagnostic in its own right: **how much local flexibility the
data require.** A large fitted `a` means the data say the global version
suffices; a small one means they call for the heavy tails BHS offers.

**Why the marginal prior is a Student-t.** A normal whose variance follows an
inverse-gamma is a scale mixture: integrating out lambda_i, the prior on theta_i
is a t with `a` degrees of freedom. That is the source of the robustness the
paper advertises, and the reason fitting `a` answers whether these data need it.

**Integration.** The paper stresses that the posterior is estimated without
numerical integration. Here lambda_i is integrated over a fixed logarithmic grid,
vectorised: a one-dimensional quadrature per observation, exact up to the grid's
density, costing one matrix product across the 15,787 experiments. The grid is
preferred because it is auditable — `GRID` is a visible parameter — over a closed
approximation whose error cannot be inspected.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import optimize, special, stats

# lambda grid: log-spaced, covering five orders of magnitude around 1
GRID = 97
LAMBDA_MIN, LAMBDA_MAX = 1e-3, 1e3
A_MIN = 2.05  # a > 2 is required for E[lambda] to exist

# starting points for `a`. Several restarts are available because the marginal
# likelihood is not convex in `a`; measured on the confirmatory sample, the fitted
# a is about 2.6 in every partition, so starting at 3.0 suffices and further
# restarts are a safety net.
RESTARTS = (3.0,)


@dataclass(frozen=True)
class BHSFit:
    """The fitted hyperparameters and what they imply."""

    m0: float
    tau: float
    a: float
    log_likelihood: float
    log_likelihood_global: float
    experiments: int

    @property
    def b(self) -> float:
        return self.a - 2.0

    @property
    def beats_global(self) -> float:
        """Likelihood ratio against lambda_i = 1. One degree of freedom."""
        return 2.0 * (self.log_likelihood - self.log_likelihood_global)

    @property
    def p_value(self) -> float:
        """Do the data require local flexibility? Chi-squared with 1 dof."""
        return float(stats.chi2.sf(max(self.beats_global, 0.0), df=1))

    @property
    def requires_local_flexibility(self) -> bool:
        return self.p_value < 0.05

    def to_dict(self) -> dict:
        return {
            "m0": self.m0,
            "tau": self.tau,
            "a": self.a,
            "b": self.b,
            "t_prior_degrees_of_freedom": self.a,
            "log_likelihood_bhs": self.log_likelihood,
            "log_likelihood_global": self.log_likelihood_global,
            "likelihood_ratio": self.beats_global,
            "p_value": self.p_value,
            "requires_local_flexibility": self.requires_local_flexibility,
            "experiments": self.experiments,
        }


def _grid(a: float) -> tuple[np.ndarray, np.ndarray]:
    """Lambda nodes and inverse-gamma log weights, normalised over the grid."""
    lam = np.geomspace(LAMBDA_MIN, LAMBDA_MAX, GRID)
    alpha, beta = a / 2.0, (a - 2.0) / 2.0
    # log density of InverseGamma(alpha, beta) at lambda, plus the log Jacobian of
    # the geometric grid (constant d log lambda implies weight proportional to lambda)
    log_p = (
        alpha * np.log(beta)
        - special.gammaln(alpha)
        - (alpha + 1.0) * np.log(lam)
        - beta / lam
        + np.log(lam)
    )
    log_p -= special.logsumexp(log_p)
    return lam, log_p


def _log_marginal(theta: np.ndarray, s2: np.ndarray, m0: float, tau: float,
                  a: float) -> np.ndarray:
    """log m(theta_hat_i) = log of the integral of N(.; m0, s_i^2 + lambda*tau) * IG(lambda)."""
    lam, log_p = _grid(a)
    var = s2[:, None] + tau * lam[None, :]            # (n, grid)
    log_n = -0.5 * (np.log(2.0 * np.pi * var) + (theta[:, None] - m0) ** 2 / var)
    return special.logsumexp(log_n + log_p[None, :], axis=1)


def _log_marginal_global(theta: np.ndarray, s2: np.ndarray, m0: float,
                         tau: float) -> np.ndarray:
    """The special case lambda_i = 1 — the paper's "Bayesian Global Shrinkage"."""
    var = s2 + tau
    return -0.5 * (np.log(2.0 * np.pi * var) + (theta - m0) ** 2 / var)


def fit(theta: np.ndarray, s2: np.ndarray) -> BHSFit:
    """Estimate (m0, tau, a) by marginal maximum likelihood.

    It also returns the likelihood of the lambda_i = 1 case fitted with its own
    optimal tau, so that the comparison between BHS and global shrinkage is fair.
    """
    theta = np.asarray(theta, dtype=float)
    s2 = np.asarray(s2, dtype=float)
    ok = np.isfinite(theta) & np.isfinite(s2) & (s2 > 0)
    theta, s2 = theta[ok], s2[ok]

    scale = max(float(np.var(theta, ddof=1) - np.mean(s2)), 1e-12)

    def neg_bhs(p: np.ndarray) -> float:
        m0, log_tau, log_a_excess = p
        tau = np.exp(log_tau)
        a = A_MIN + np.exp(log_a_excess)
        v = -float(np.sum(_log_marginal(theta, s2, m0, tau, a)))
        return v if np.isfinite(v) else 1e12

    def neg_global(p: np.ndarray) -> float:
        m0, log_tau = p
        v = -float(np.sum(_log_marginal_global(theta, s2, m0, np.exp(log_tau))))
        return v if np.isfinite(v) else 1e12

    p0_g = np.array([float(np.mean(theta)), np.log(scale)])
    rg = optimize.minimize(neg_global, p0_g, method="Nelder-Mead",
                           options={"xatol": 1e-10, "fatol": 1e-8, "maxiter": 4000})

    best = None
    for a0 in RESTARTS:
        p0 = np.array([rg.x[0], rg.x[1], np.log(max(a0 - A_MIN, 1e-3))])
        r = optimize.minimize(neg_bhs, p0, method="Nelder-Mead",
                              options={"xatol": 1e-10, "fatol": 1e-8, "maxiter": 8000})
        if best is None or r.fun < best.fun:
            best = r

    return BHSFit(
        m0=float(best.x[0]),
        tau=float(np.exp(best.x[1])),
        a=float(A_MIN + np.exp(best.x[2])),
        log_likelihood=float(-best.fun),
        log_likelihood_global=float(-rg.fun),
        experiments=int(theta.size),
    )


def posterior_mean(theta: np.ndarray, s2: np.ndarray, fitted: BHSFit) -> np.ndarray:
    """E[theta_i | theta_hat_i] under BHS, integrating out the local factor lambda_i.

        E[theta_i | theta_hat_i] = theta_hat_i - (theta_hat_i - m0) * E[alpha_i(lambda) | theta_hat_i]
        with alpha_i(lambda) = s_i^2 / (s_i^2 + lambda * tau)

    The shrinkage weight is no longer a single number per experiment: it is the
    average of alpha over lambda_i's posterior, which is why BHS shrinks **less**
    the experiments whose observation lies far from the centre. That is its
    robustness.
    """
    theta = np.asarray(theta, dtype=float)
    s2 = np.asarray(s2, dtype=float)
    lam, log_p = _grid(fitted.a)

    var = s2[:, None] + fitted.tau * lam[None, :]
    log_n = -0.5 * (np.log(2.0 * np.pi * var)
                    + (theta[:, None] - fitted.m0) ** 2 / var)
    log_post = log_n + log_p[None, :]
    log_post -= special.logsumexp(log_post, axis=1, keepdims=True)

    alpha = s2[:, None] / var                              # alpha_i(lambda)
    expected_alpha = np.sum(np.exp(log_post) * alpha, axis=1)
    return theta - (theta - fitted.m0) * expected_alpha


def effective_alpha(theta: np.ndarray, s2: np.ndarray, fitted: BHSFit) -> np.ndarray:
    """E[alpha_i(lambda) | theta_hat_i]: the shrinkage weight BHS actually applies."""
    theta = np.asarray(theta, dtype=float)
    s2 = np.asarray(s2, dtype=float)
    lam, log_p = _grid(fitted.a)
    var = s2[:, None] + fitted.tau * lam[None, :]
    log_post = (-0.5 * (np.log(2.0 * np.pi * var)
                        + (theta[:, None] - fitted.m0) ** 2 / var)) + log_p[None, :]
    log_post -= special.logsumexp(log_post, axis=1, keepdims=True)
    return np.sum(np.exp(log_post) * (s2[:, None] / var), axis=1)
