"""Cuánto difieren realmente las variantes: la estimación de τ².

La contracción pesa dos cantidades: el ruido de cada medición (`v`) y la
dispersión **real** entre las variantes de un experimento (τ²). La primera se
calcula; la segunda no se observa y hay que estimarla.

Y aquí está el problema que obliga a estimarla en conjunto: con 2 a 14 brazos
por experimento, estimar τ² **dentro** de cada experimento es usar un dato
ruidoso para decidir cuánto confiar en datos ruidosos. La salida viene del
meta-análisis, que enfrenta lo mismo desde los años ochenta al combinar muchos
estudios clínicos: **se estima una sola dispersión con todos los experimentos
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


def _por_experimento(panel: pd.DataFrame, factor_v: float = 1.0):
    """Itera (theta, v) por experimento, descartando los no informativos."""
    for _, blk in panel.groupby("experimento_id", sort=False):
        if len(blk) < 2:
            continue
        theta = blk["theta_hat"].to_numpy(dtype=float)
        v = blk["v"].to_numpy(dtype=float) * factor_v
        if not np.all(np.isfinite(v)) or np.any(v <= 0):
            continue
        yield theta, v


def dersimonian_laird(panel: pd.DataFrame, factor_v: float = 1.0) -> float:
    """τ² en conjunto, forma cerrada. Nunca negativo.

    Se acumulan numerador y denominador sobre todos los experimentos antes de
    dividir: así los experimentos chicos no arrastran el promedio como lo
    harían si se estimara τ² en cada uno y luego se promediara.
    """
    exceso = 0.0
    denom = 0.0
    for theta, v in _por_experimento(panel, factor_v):
        w = 1.0 / v
        sw = w.sum()
        pbar = float((w * theta).sum() / sw)
        Q = float((w * (theta - pbar) ** 2).sum())
        exceso += Q - (len(theta) - 1)
        denom += sw - (w**2).sum() / sw
    if denom <= 0:
        return 0.0
    return max(0.0, exceso / denom)


def _Q_total(panel: pd.DataFrame, tau2: float, factor_v: float) -> tuple[float, int]:
    """Q acumulada con pesos que ya incluyen τ², y sus grados de libertad."""
    Q = 0.0
    gl = 0
    for theta, v in _por_experimento(panel, factor_v):
        w = 1.0 / (v + tau2)
        sw = w.sum()
        pbar = float((w * theta).sum() / sw)
        Q += float((w * (theta - pbar) ** 2).sum())
        gl += len(theta) - 1
    return Q, gl


def paule_mandel(
    panel: pd.DataFrame,
    factor_v: float = 1.0,
    tope: float | None = None,
) -> float:
    """τ² en conjunto por el método de Paule y Mandel.

    Busca el τ² que iguala Q a sus grados de libertad. Q decrece de forma
    monótona en τ², así que la bisección es segura. Si Q(0) ya no supera los
    grados de libertad, no hay exceso que explicar y τ² = 0.
    """
    Q0, gl = _Q_total(panel, 0.0, factor_v)
    if gl == 0:
        return 0.0
    if Q0 <= gl:
        return 0.0

    if tope is None:
        # la varianza observada de todas las tasas es una cota superior holgada
        tope = float(np.nanvar(panel["theta_hat"].to_numpy(dtype=float))) * 10 + 1e-9

    lo, hi = 0.0, tope
    Qhi, _ = _Q_total(panel, hi, factor_v)
    expansiones = 0
    while Qhi > gl and expansiones < 40:
        hi *= 2.0
        Qhi, _ = _Q_total(panel, hi, factor_v)
        expansiones += 1

    for _ in range(MAX_ITER):
        medio = 0.5 * (lo + hi)
        Q, _ = _Q_total(panel, medio, factor_v)
        if abs(Q - gl) < TOL or (hi - lo) < TOL:
            return medio
        if Q > gl:
            lo = medio
        else:
            hi = medio
    return 0.5 * (lo + hi)


METODOS = {
    "paule-mandel": paule_mandel,
    "dersimonian-laird": dersimonian_laird,
}


def estimar(panel: pd.DataFrame, metodo: str = "paule-mandel", factor_v: float = 1.0) -> float:
    if metodo not in METODOS:
        raise ValueError(f"método desconocido: {metodo!r}; use {list(METODOS)}")
    return float(METODOS[metodo](panel, factor_v=factor_v))
