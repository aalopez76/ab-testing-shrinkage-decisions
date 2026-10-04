"""Fase E: la decisión ENTRE experimentos, que es donde sí se puede mejorar.

La fase D encontró que la contracción no puede cambiar qué brazo se elige
**dentro** de un experimento: con α casi uniforme y un destino común, θ̃ es una
transformación monótona de θ̂ y conserva el orden. No es un fallo del método —
es que, con brazos balanceados, no hay un problema de selección que mejorar.

La condición que hace real el problema de selección tiene nombre en la
literatura: **precisión heterogénea** (Gu y Koenker, *Invidious Comparisons:
Ranking and Selection as Compound Decisions*, 2020-21). Y en este archivo:

    dentro de un experimento   razón n_max/n_min ≈ 1.04   → homogénea
    entre experimentos         razón p99/p01 ≈ 7.1        → heterogénea

Así que el nivel correcto es el de arriba, y resulta ser el que la industria
plantea: Meta habla de *«los experimentos seleccionados para lanzamiento»* y
Netflix de *cuándo lanzar*. Decisiones entre experimentos, no dentro de uno.

**La decisión que se modela.** Un equipo corre muchos experimentos y no puede
desplegar todos: hay presupuesto, o no quiere saturar a los usuarios. ¿Cuáles
de los ganadores vale la pena desplegar? Se eligen con la mitad de estimación y
se mide lo que rindieron en la de evaluación.

**Y la regla correcta tampoco es el máximo de la media contraída.** La
literatura reporta que, bajo precisión heterogénea, las reglas de *probabilidad
de cola posterior* superan a las de media posterior — porque combinan θ̂ con su
precisión de forma **no monótona**, y entonces sí reordenan.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats


@dataclass(frozen=True)
class Cartera:
    """Una fila por experimento: la ganancia estimada y la realizada."""

    tabla: pd.DataFrame

    def __len__(self) -> int:
        return len(self.tabla)


def construir_tres(
    eleccion: pd.DataFrame, estimacion: pd.DataFrame, evaluacion: pd.DataFrame
) -> Cartera:
    """Resume cada experimento separando elegir, estimar y evaluar.

    El brazo se elige con `eleccion`; su ventaja se estima con `estimacion`,
    que no participó en elegirlo; y se mide con `evaluacion`, que no participó
    en nada. Así δ̂ es la ventaja de un brazo **ya fijado** —una estimación
    insesgada— y no el máximo de un experimento, que es un estadístico
    seleccionado al que la contracción no se le puede aplicar directamente.
    """
    n = len(eleccion)
    if not (len(estimacion) == len(evaluacion) == n):
        raise ValueError("los tres tercios no están alineados")

    exp = eleccion["experimento_id"].to_numpy()
    th_e = eleccion["theta_hat"].to_numpy(dtype=float)
    th_a = estimacion["theta_hat"].to_numpy(dtype=float)
    th_b = evaluacion["theta_hat"].to_numpy(dtype=float)
    v_a = estimacion["v"].to_numpy(dtype=float)

    orden = np.argsort(exp, kind="stable")
    e_ord = exp[orden]
    cortes = np.flatnonzero(np.r_[True, e_ord[1:] != e_ord[:-1]])
    limites = np.r_[cortes, len(e_ord)]

    filas = []
    for a, b in zip(limites[:-1], limites[1:]):
        idx = orden[a:b]
        k = len(idx)
        if k < 2:
            continue
        elegido = idx[int(np.argmax(th_e[idx]))]          # elige con A1
        # ventaja frente al promedio de los NO elegidos, estimada en A2
        otros = idx[idx != elegido]
        delta_est = float(th_a[elegido] - th_a[otros].mean())
        delta_real = float(th_b[elegido] - th_b[otros].mean())
        v_delta = float(v_a[elegido] + v_a[otros].sum() / len(otros) ** 2)
        filas.append(
            {
                "experimento_id": e_ord[a],
                "brazos": k,
                "impresiones": float(estimacion["impresiones"].to_numpy()[idx].sum()),
                "delta_estimado": delta_est,
                "delta_realizado": delta_real,
                "v": max(v_delta, 1e-18),
                "theta_elegido_b": float(th_b[elegido]),
                "media_b": float(th_b[otros].mean()),
            }
        )
    return Cartera(pd.DataFrame(filas))


def construir(estimacion: pd.DataFrame, evaluacion: pd.DataFrame) -> Cartera:
    """Resume cada experimento en su ganancia por elegir el mejor brazo.

    La cantidad de interés es el **beneficio de haber corrido el experimento**:
    cuánto mejor es el brazo elegido frente a elegir uno al azar, que es el
    promedio del experimento.

        δ̂ = θ̂(elegido en A) − media de θ̂ en A        (lo prometido)
        δ  = θ(elegido)  en B − media de θ en B       (lo entregado)

    `v` de δ̂ se aproxima como v(elegido) + Σv/k², **ignorando el efecto de la
    selección** — que es justamente lo que el proyecto mide, así que meterlo
    aquí sería circular. Se declara la aproximación y se usa solo como escala
    para la contracción, no como intervalo de confianza.
    """
    if len(estimacion) != len(evaluacion):
        raise ValueError("las mitades no están alineadas")

    exp = estimacion["experimento_id"].to_numpy()
    th_a = estimacion["theta_hat"].to_numpy(dtype=float)
    th_b = evaluacion["theta_hat"].to_numpy(dtype=float)
    v_a = estimacion["v"].to_numpy(dtype=float)

    orden = np.argsort(exp, kind="stable")
    e_ord = exp[orden]
    cortes = np.flatnonzero(np.r_[True, e_ord[1:] != e_ord[:-1]])
    limites = np.r_[cortes, len(e_ord)]

    filas = []
    for a, b in zip(limites[:-1], limites[1:]):
        idx = orden[a:b]
        k = len(idx)
        if k < 2:
            continue
        elegido = idx[int(np.argmax(th_a[idx]))]
        media_a = float(th_a[idx].mean())
        media_b = float(th_b[idx].mean())
        v_sel = float(v_a[elegido] + v_a[idx].sum() / k**2)
        filas.append(
            {
                "experimento_id": e_ord[a],
                "brazos": k,
                "impresiones": float(estimacion["impresiones"].to_numpy()[idx].sum()),
                "delta_estimado": float(th_a[elegido]) - media_a,
                "delta_realizado": float(th_b[elegido]) - media_b,
                "v": max(v_sel, 1e-18),
                "theta_elegido_b": float(th_b[elegido]),
                "media_b": media_b,
            }
        )
    return Cartera(pd.DataFrame(filas))


# ---------------------------------------------------------------------------
# Las reglas de priorización
# ---------------------------------------------------------------------------

def prioridad_cruda(c: Cartera) -> np.ndarray:
    """Ordenar por la ganancia estimada. La práctica que se pone a prueba."""
    return c.tabla["delta_estimado"].to_numpy(dtype=float)


def contraer_cartera(c: Cartera, tau2: float | None = None) -> tuple[np.ndarray, float]:
    """Contracción entre experimentos: cada δ̂ hacia el promedio de todos.

    Aquí la precisión **sí** varía entre experimentos, así que α varía con ella
    y la transformación ya no es monótona en δ̂: dos experimentos con la misma
    ganancia estimada y distinta precisión se ordenan distinto. Por eso esta
    contracción puede reordenar y la de la fase D no podía.
    """
    d = c.tabla["delta_estimado"].to_numpy(dtype=float)
    v = c.tabla["v"].to_numpy(dtype=float)
    if tau2 is None:
        # momento de orden dos: var observada menos el ruido medio, acotado a 0
        tau2 = max(float(np.var(d, ddof=1) - v.mean()), 0.0)
    alpha = v / (v + tau2) if tau2 > 0 else np.ones_like(v)
    centro = float(np.average(d, weights=1.0 / v))
    return (1.0 - alpha) * d + alpha * centro, float(tau2)


def prioridad_cola(c: Cartera, tau2: float | None = None, umbral: float = 0.0) -> np.ndarray:
    """Probabilidad posterior de que la ganancia real supere un umbral.

    La regla que la literatura señala como superior bajo precisión heterogénea.
    Con previa normal(centro, τ²) y verosimilitud normal(δ̂, v), la posterior de
    cada experimento es normal con media la contraída y varianza v·τ²/(v+τ²);
    la probabilidad de cola es entonces inmediata.

    **No es monótona en δ̂**: a igual ganancia estimada, el experimento más
    preciso recibe mayor probabilidad. Eso es lo que la distingue de ordenar por
    la media contraída, que sí es monótona en δ̂ a precisión fija.
    """
    media, t2 = contraer_cartera(c, tau2)
    v = c.tabla["v"].to_numpy(dtype=float)
    var_post = v * t2 / (v + t2) if t2 > 0 else np.zeros_like(v)
    sd = np.sqrt(np.maximum(var_post, 1e-24))
    return stats.norm.sf(umbral, loc=media, scale=sd)


# ---------------------------------------------------------------------------
# La evaluación: curva por presupuesto
# ---------------------------------------------------------------------------

def valor_por_presupuesto(
    c: Cartera, prioridad: np.ndarray, presupuestos: tuple[float, ...]
) -> dict[float, float]:
    """Ganancia realizada media de los experimentos elegidos, por presupuesto.

    `presupuesto` es la fracción de experimentos que se puede desplegar. Se
    ordena por la prioridad —calculada en la mitad de estimación— y se mide lo
    que rindieron en la de evaluación.
    """
    realizado = c.tabla["delta_realizado"].to_numpy(dtype=float)
    orden = np.argsort(-np.asarray(prioridad, dtype=float), kind="stable")
    n = len(orden)
    out = {}
    for b in presupuestos:
        k = max(1, int(round(b * n)))
        out[b] = float(realizado[orden[:k]].mean())
    return out


def oraculo(c: Cartera, presupuestos: tuple[float, ...]) -> dict[float, float]:
    """El techo: ordenar por la ganancia REALIZADA. No se puede alcanzar."""
    return valor_por_presupuesto(c, c.tabla["delta_realizado"].to_numpy(), presupuestos)
