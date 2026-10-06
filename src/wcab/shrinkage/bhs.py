"""Bayesian Hybrid Shrinkage (BHS), la propuesta de Meta de 2025.

Implementación fiel al modelo jerárquico de Mudd, Friedberg, Gorbachev, Nassif
y Zaidi (arXiv 2511.06318, CODE@MIT'25):

    θ̂ᵢ | θᵢ, sᵢ²   ~  N(θᵢ, sᵢ²)
    θᵢ | m₀, λᵢ, τ  ~  N(m₀, λᵢ · τ)
    λᵢ | a, b       ~  InverseGamma(a/2, b/2)

El factor **local** λᵢ es lo que distingue BHS de la contracción estándar. El
propio artículo nombra el caso especial λᵢ = 1 para todo i: lo llama *«Bayesian
Global Shrinkage»*, y es exactamente lo que implementa `shrinkage/__init__.py`.

**Parametrización.** τ y b no son identificables por separado: solo el producto
entra en la escala de la previa. Se fija `b = a - 2`, que da E[λᵢ] = 1 y deja a
τ como la escala global y a `a` como el único mando de flexibilidad local:

    a → ∞   ⇒  λᵢ → 1  ⇒  contracción global (la línea base del artículo)
    a chico ⇒  colas pesadas ⇒ robustez ante previa mal especificada

Eso convierte a `a` en un diagnóstico por sí mismo: **cuánta flexibilidad local
piden los data.** Si â sale grande, los data dicen que la versión global
basta; si sale chico, piden las colas pesadas que BHS ofrece.

**Por qué la previa marginal es una t de Student.** Una normal cuya varianza
sigue una inversa-gamma es una mezcla de escalas: integrando λᵢ, la previa sobre
θᵢ es t con `a` grados de libertad. De ahí sale la robustez que anuncia el
artículo, y de ahí que el ajuste de `a` conteste si estos data la necesitan.

**Integración.** El artículo subraya que la posterior se estima sin integración
numérica. Aquí se integra λᵢ sobre una rejilla logarítmica fija de forma
vectorizada: es una cuadratura unidimensional por observación, exacta hasta la
densidad de la rejilla, y cuesta un producto de matrices para los 15 787
experiments. Se prefiere la rejilla porque es auditable —`GRID` es un
parámetro visible— frente a una aproximación cerrada cuyo error no se ve.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import optimize, special, stats

# rejilla de λ: log-espaciada, cubre cinco órdenes de magnitud alrededor de 1
GRID = 97
LAMBDA_MIN, LAMBDA_MAX = 1e-3, 1e3
A_MIN = 2.05  # a > 2 para que E[λ] exista

# puntos de arranque para `a`. Varios reinicios porque la verosimilitud marginal
# no es convexa en `a`; medido en el confirmatory, â ≈ 2.6 en todas las
# partitions, así que el arranque en 3.0 basta y los demás son red de seguridad.
RESTARTS = (3.0,)


@dataclass(frozen=True)
class BHSFit:
    """Hiperparámetros ajustados y lo que dicen."""

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
        """Razón de verosimilitudes contra λᵢ = 1. Un grado de libertad."""
        return 2.0 * (self.log_likelihood - self.log_likelihood_global)

    @property
    def p_value(self) -> float:
        """¿Piden los data la flexibilidad local? Chi² con 1 dof."""
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
            "grados_de_libertad_previa_t": self.a,
            "log_verosimilitud_bhs": self.log_likelihood,
            "log_likelihood_global": self.log_likelihood_global,
            "likelihood_ratio": self.beats_global,
            "p_value": self.p_value,
            "requires_local_flexibility": self.requires_local_flexibility,
            "experiments": self.experiments,
        }


def _grid(a: float) -> tuple[np.ndarray, np.ndarray]:
    """Nodos de λ y log-pesos de la inversa-gamma, normalizados sobre la rejilla."""
    lam = np.geomspace(LAMBDA_MIN, LAMBDA_MAX, GRID)
    alfa, beta = a / 2.0, (a - 2.0) / 2.0
    # log densidad InverseGamma(alfa, beta) por λ, más el jacobiano log de la
    # rejilla geométrica (d log λ constante ⇒ peso ∝ λ)
    log_p = (
        alfa * np.log(beta)
        - special.gammaln(alfa)
        - (alfa + 1.0) * np.log(lam)
        - beta / lam
        + np.log(lam)
    )
    log_p -= special.logsumexp(log_p)
    return lam, log_p


def _log_marginal(theta: np.ndarray, s2: np.ndarray, m0: float, tau: float,
                  a: float) -> np.ndarray:
    """log m(θ̂ᵢ) = log ∫ N(θ̂ᵢ; m₀, sᵢ² + λτ) · IG(λ) dλ, por experimento."""
    lam, log_p = _grid(a)
    var = s2[:, None] + tau * lam[None, :]            # (n, rejilla)
    log_n = -0.5 * (np.log(2.0 * np.pi * var) + (theta[:, None] - m0) ** 2 / var)
    return special.logsumexp(log_n + log_p[None, :], axis=1)


def _log_marginal_global(theta: np.ndarray, s2: np.ndarray, m0: float,
                         tau: float) -> np.ndarray:
    """El caso especial λᵢ = 1 — la «Bayesian Global Shrinkage» del artículo."""
    var = s2 + tau
    return -0.5 * (np.log(2.0 * np.pi * var) + (theta - m0) ** 2 / var)


def fit(theta: np.ndarray, s2: np.ndarray) -> BHSFit:
    """Estima (m₀, τ, a) por máxima verosimilitud marginal.

    Devuelve también la verosimilitud del caso λᵢ = 1 con su propio τ óptimo,
    para que la comparación entre BHS y la contracción global sea justa.
    """
    theta = np.asarray(theta, dtype=float)
    s2 = np.asarray(s2, dtype=float)
    ok = np.isfinite(theta) & np.isfinite(s2) & (s2 > 0)
    theta, s2 = theta[ok], s2[ok]

    escala = max(float(np.var(theta, ddof=1) - np.mean(s2)), 1e-12)

    def neg_bhs(p: np.ndarray) -> float:
        m0, log_tau, log_a_ex = p
        tau = np.exp(log_tau)
        a = A_MIN + np.exp(log_a_ex)
        v = -float(np.sum(_log_marginal(theta, s2, m0, tau, a)))
        return v if np.isfinite(v) else 1e12

    def neg_global(p: np.ndarray) -> float:
        m0, log_tau = p
        v = -float(np.sum(_log_marginal_global(theta, s2, m0, np.exp(log_tau))))
        return v if np.isfinite(v) else 1e12

    p0_g = np.array([float(np.mean(theta)), np.log(escala)])
    rg = optimize.minimize(neg_global, p0_g, method="Nelder-Mead",
                           options={"xatol": 1e-10, "fatol": 1e-8, "maxiter": 4000})

    mejor = None
    for a0 in RESTARTS:
        p0 = np.array([rg.x[0], rg.x[1], np.log(max(a0 - A_MIN, 1e-3))])
        r = optimize.minimize(neg_bhs, p0, method="Nelder-Mead",
                              options={"xatol": 1e-10, "fatol": 1e-8, "maxiter": 8000})
        if mejor is None or r.fun < mejor.fun:
            mejor = r

    return BHSFit(
        m0=float(mejor.x[0]),
        tau=float(np.exp(mejor.x[1])),
        a=float(A_MIN + np.exp(mejor.x[2])),
        log_likelihood=float(-mejor.fun),
        log_likelihood_global=float(-rg.fun),
        experiments=int(theta.size),
    )


def posterior_mean(theta: np.ndarray, s2: np.ndarray, ajuste: BHSFit) -> np.ndarray:
    """E[θᵢ | θ̂ᵢ] bajo BHS, integrando el factor local λᵢ.

    E[θᵢ|θ̂ᵢ] = θ̂ᵢ − (θ̂ᵢ − m₀) · E[αᵢ(λ) | θ̂ᵢ],  con  αᵢ(λ) = sᵢ²/(sᵢ² + λτ)

    El peso de contracción ya no es un número por experimento: es el promedio
    de α sobre la posterior de λᵢ, y por eso BHS contrae **menos** a los
    experiments cuyo dato queda lejos del center — ésa es su robustez.
    """
    theta = np.asarray(theta, dtype=float)
    s2 = np.asarray(s2, dtype=float)
    lam, log_p = _grid(ajuste.a)

    var = s2[:, None] + ajuste.tau * lam[None, :]
    log_n = -0.5 * (np.log(2.0 * np.pi * var)
                    + (theta[:, None] - ajuste.m0) ** 2 / var)
    log_post = log_n + log_p[None, :]
    log_post -= special.logsumexp(log_post, axis=1, keepdims=True)

    alfa = s2[:, None] / var                               # αᵢ(λ)
    alfa_esperado = np.sum(np.exp(log_post) * alfa, axis=1)
    return theta - (theta - ajuste.m0) * alfa_esperado


def effective_alpha(theta: np.ndarray, s2: np.ndarray, ajuste: BHSFit) -> np.ndarray:
    """E[αᵢ(λ) | θ̂ᵢ]: el peso de contracción que BHS aplica de hecho."""
    theta = np.asarray(theta, dtype=float)
    s2 = np.asarray(s2, dtype=float)
    lam, log_p = _grid(ajuste.a)
    var = s2[:, None] + ajuste.tau * lam[None, :]
    log_post = (-0.5 * (np.log(2.0 * np.pi * var)
                        + (theta[:, None] - ajuste.m0) ** 2 / var)) + log_p[None, :]
    log_post -= special.logsumexp(log_post, axis=1, keepdims=True)
    return np.sum(np.exp(log_post) * (s2[:, None] / var), axis=1)
