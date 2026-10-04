"""Paso 5: comparar decisiones, no estimaciones.

Aquí se juega el criterio del proyecto: **los métodos se juzgan por las
decisiones que producen, no por si cumplen sus propios supuestos.**

Cada regla elige una variante por experimento usando la mitad de estimación, y
se mide lo que esa variante rindió en la mitad de evaluación — que no participó
en elegirla. Las tres métricas:

- **valor**: la tasa realizada de la variante elegida.
- **arrepentimiento**: cuánto se perdió frente a la mejor variante disponible,
  medida también en la mitad de evaluación.
- **inflación**: lo que la variante elegida prometió al elegirla menos lo que
  entregó. Es el estimando principal del proyecto.

La referencia que hay que batir es `azar`: elegir una variante al azar. Si una
corrección no le gana a eso, no sirve para nada. Y `crudo` —elegir el máximo
medido— es la práctica que el proyecto pone a prueba.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Resultado:
    """El rendimiento de una regla, con lo necesario para reportarlo."""

    regla: str
    experimentos: int
    valor: float               # tasa realizada media de lo elegido
    arrepentimiento: float     # cuánto se dejó en la mesa
    inflacion: float           # prometido − entregado
    por_experimento: pd.DataFrame

    def resumen(self) -> dict:
        return {
            "regla": self.regla,
            "experimentos": self.experimentos,
            "valor": float(self.valor),
            "arrepentimiento": float(self.arrepentimiento),
            "inflacion": float(self.inflacion),
            "fraccion_peor_que_oraculo": float(
                (self.por_experimento["arrepentimiento"] > 0).mean()
            ),
        }


def _elegir(prioridad: np.ndarray) -> int:
    """Índice del máximo. Empates al primero, que es determinista."""
    return int(np.argmax(prioridad))


def evaluar(
    estimacion: pd.DataFrame,
    evaluacion: pd.DataFrame,
    prioridad: pd.Series | np.ndarray | None = None,
    regla: str = "crudo",
    semilla: int = 0,
) -> Resultado:
    """Aplica una regla y mide lo que rindió.

    `prioridad` es el criterio con el que se ordena dentro de cada experimento,
    calculado sobre la mitad de **estimación**. Si es None y la regla es
    `azar`, se sortea; si es None en cualquier otro caso, se usa `theta_hat`.

    Las dos mitades deben venir alineadas fila a fila, que es lo que garantiza
    `thinning.partir`.
    """
    if len(estimacion) != len(evaluacion):
        raise ValueError("las mitades no están alineadas")

    rng = np.random.default_rng(semilla)
    if regla == "azar":
        prio = rng.random(len(estimacion))
    elif prioridad is None:
        prio = estimacion["theta_hat"].to_numpy(dtype=float)
    else:
        prio = np.asarray(prioridad, dtype=float)

    exp = estimacion["experimento_id"].to_numpy()
    theta_est = estimacion["theta_hat"].to_numpy(dtype=float)
    theta_eval = evaluacion["theta_hat"].to_numpy(dtype=float)

    filas = []
    inicio = 0
    orden = np.argsort(exp, kind="stable")
    exp_ord = exp[orden]
    cortes = np.flatnonzero(np.r_[True, exp_ord[1:] != exp_ord[:-1]])
    limites = np.r_[cortes, len(exp_ord)]

    for a, b in zip(limites[:-1], limites[1:]):
        idx = orden[a:b]
        if len(idx) < 2:
            continue
        elegido = idx[_elegir(prio[idx])]
        mejor_posible = float(theta_eval[idx].max())
        filas.append(
            {
                "experimento_id": exp_ord[a],
                "brazos": len(idx),
                "prometido": float(theta_est[elegido]),
                "entregado": float(theta_eval[elegido]),
                "mejor_posible": mejor_posible,
                "arrepentimiento": mejor_posible - float(theta_eval[elegido]),
                "inflacion": float(theta_est[elegido]) - float(theta_eval[elegido]),
            }
        )
        inicio = b

    por_exp = pd.DataFrame(filas)
    return Resultado(
        regla=regla,
        experimentos=len(por_exp),
        valor=float(por_exp["entregado"].mean()),
        arrepentimiento=float(por_exp["arrepentimiento"].mean()),
        inflacion=float(por_exp["inflacion"].mean()),
        por_experimento=por_exp,
    )


def comparar(resultados: list[Resultado], referencia: str = "crudo") -> pd.DataFrame:
    """Tabla comparativa, con la diferencia de valor contra una referencia."""
    base = next((r for r in resultados if r.regla == referencia), None)
    filas = []
    for r in resultados:
        fila = r.resumen()
        if base is not None:
            fila["valor_menos_" + referencia] = r.valor - base.valor
        filas.append(fila)
    return pd.DataFrame(filas)


def donde_falla(
    a: Resultado, b: Resultado, nombre_a: str = "A", nombre_b: str = "B"
) -> dict:
    """En qué experimentos la regla `a` elige peor que la regla `b`.

    La parte no opcional del proyecto: contraer mejora el conjunto y perjudica
    casos concretos. Interesa cuáles y qué tienen en común.
    """
    j = a.por_experimento.merge(
        b.por_experimento, on="experimento_id", suffixes=("_a", "_b")
    )
    peor = j["entregado_a"] < j["entregado_b"]
    out = {
        "comparacion": f"{nombre_a} contra {nombre_b}",
        "experimentos": int(len(j)),
        "fraccion_peor": float(peor.mean()),
        "fraccion_mejor": float((j["entregado_a"] > j["entregado_b"]).mean()),
        "fraccion_igual": float((j["entregado_a"] == j["entregado_b"]).mean()),
    }
    if peor.any():
        out["perfil_de_los_peores"] = {
            "brazos_media": float(j.loc[peor, "brazos_a"].mean()),
            "brazos_media_resto": float(j.loc[~peor, "brazos_a"].mean()),
            "perdida_media": float(
                (j.loc[peor, "entregado_b"] - j.loc[peor, "entregado_a"]).mean()
            ),
        }
    return out
