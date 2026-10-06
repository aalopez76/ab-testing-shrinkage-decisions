"""Cuánto difieren realmente las variantes: la estimación de τ².

La contracción pesa dos cantidades: el ruido de cada medición (`v`) y la
dispersión **real** entre las variantes de un experimento (τ²). La primera se
calcula; la segunda no se observa y hay que estimarla.

Y aquí está el problema que obliga a estimarla en conjunto: con 2 a 14 arms
por experimento, estimate τ² **dentro** de cada experimento es usar un dato
ruidoso para decidir cuánto confiar en data ruidosos. La output viene del
meta-análisis, que enfrenta lo mismo desde los años ochenta al combinar muchos
estudios clínicos: **se estima una sola dispersión con todos los experiments
juntos.**

Dos estimadores clásicos, ambos sobre la Q de Cochran:

- **DerSimonian y Laird (1986):** forma cerrada. Despeja cuánta dispersión real
  hace falta para explicar el exceso de Q sobre sus grados de libertad.
- **Paule y Mandel (1982):** busca el τ² que hace que Q, con los pesos que ya
  incluyen esa dispersión, valga exactamente lo esperado. No tiene solución
  cerrada; se resuelve por bisección.

*Referencias pendientes de verificación bibliográfica directa.*
"""

from __future__ import annotations

import numpy as np
import pandas as pd

MAX_ITER = 200
TOL = 1e-12


def _per_experiment(panel: pd.DataFrame, variance_factor: float = 1.0):
    """Itera (theta, v) por experimento, descartando los no informativos."""
    for _, blk in panel.groupby("experiment_id", sort=False):
        if len(blk) < 2:
            continue
        theta = blk["theta_hat"].to_numpy(dtype=float)
        v = blk["v"].to_numpy(dtype=float) * variance_factor
        if not np.all(np.isfinite(v)) or np.any(v <= 0):
            continue
        yield theta, v


def dersimonian_laird(panel: pd.DataFrame, variance_factor: float = 1.0) -> float:
    """τ² en conjunto, forma cerrada. Nunca negativo.

    Se acumulan numerador y denominador sobre todos los experiments antes de
    dividir: así los experiments chicos no arrastran el promedio como lo
    harían si se estimara τ² en cada uno y luego se promediara.
    """
    exceso = 0.0
    denom = 0.0
    for theta, v in _per_experiment(panel, variance_factor):
        w = 1.0 / v
        sw = w.sum()
        pbar = float((w * theta).sum() / sw)
        Q = float((w * (theta - pbar) ** 2).sum())
        exceso += Q - (len(theta) - 1)
        denom += sw - (w**2).sum() / sw
    if denom <= 0:
        return 0.0
    return max(0.0, exceso / denom)


def _total_q(panel: pd.DataFrame, tau2: float, variance_factor: float) -> tuple[float, int]:
    """Q acumulada con pesos que ya incluyen τ², y sus grados de libertad."""
    Q = 0.0
    dof = 0
    for theta, v in _per_experiment(panel, variance_factor):
        w = 1.0 / (v + tau2)
        sw = w.sum()
        pbar = float((w * theta).sum() / sw)
        Q += float((w * (theta - pbar) ** 2).sum())
        dof += len(theta) - 1
    return Q, dof


def paule_mandel(
    panel: pd.DataFrame,
    variance_factor: float = 1.0,
    tope: float | None = None,
) -> float:
    """τ² en conjunto por el método de Paule y Mandel.

    Busca el τ² que iguala Q a sus grados de libertad. Q decrece de forma
    monótona en τ², así que la bisección es segura. Si Q(0) ya no supera los
    grados de libertad, no hay exceso que explicar y τ² = 0.
    """
    Q0, dof = _total_q(panel, 0.0, variance_factor)
    if dof == 0:
        return 0.0
    if Q0 <= dof:
        return 0.0

    if tope is None:
        # la varianza observada de todas las tasas es una cota superior holgada
        tope = float(np.nanvar(panel["theta_hat"].to_numpy(dtype=float))) * 10 + 1e-9

    lo, hi = 0.0, tope
    Qhi, _ = _total_q(panel, hi, variance_factor)
    expansiones = 0
    while Qhi > dof and expansiones < 40:
        hi *= 2.0
        Qhi, _ = _total_q(panel, hi, variance_factor)
        expansiones += 1

    for _ in range(MAX_ITER):
        medio = 0.5 * (lo + hi)
        Q, _ = _total_q(panel, medio, variance_factor)
        if abs(Q - dof) < TOL or (hi - lo) < TOL:
            return medio
        if Q > dof:
            lo = medio
        else:
            hi = medio
    return 0.5 * (lo + hi)


METHODS = {
    "paule-mandel": paule_mandel,
    "dersimonian-laird": dersimonian_laird,
}


def estimate(panel: pd.DataFrame, method: str = "paule-mandel", variance_factor: float = 1.0) -> float:
    if method not in METHODS:
        raise ValueError(f"método desconocido: {method!r}; use {list(METHODS)}")
    return float(METHODS[method](panel, variance_factor=variance_factor))
