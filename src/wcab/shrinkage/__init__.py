"""Contracción: acercar cada medición a lo que dicen las demás.

La forma es un promedio ponderado entre lo que dice cada variante y el centro
de su experimento, con un peso que compara el ruido de la medición contra la
dispersión real entre variantes:

    θ̃ = (1 − α)·θ̂ + α·centro        α = v / (v + τ²)

Si el ruido domina, se le hace más caso al centro; si las diferencias reales
dominan, a cada medición. Es Bayes empírico paramétrico (Efron y Morris;
*pendiente de verificación*).

**La interfaz es una sola función** —`contraer`— para que el arnés de decisión
no sepa qué método está evaluando. Así «dos métodos × global/local» es un bucle
y no código copiado cuatro veces, y la comparación queda justa por
construcción.

Los dos ejes del proyecto entran como argumentos:

- **qué método**: `metodo_tau2` elige el estimador de la dispersión.
- **hacia dónde**: `tau2` se calcula fuera, sobre todos los experimentos
  (global) o sobre un vecindario (local). Ver `neighborhood.py`.
- **con qué ruido**: `factor_v` aplica el factor de diseño del paso 1. El
  proyecto compara `v` ingenuo (1.0) contra `v` corregido.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import dispersion

CENTROS = ("ponderado", "simple")


@dataclass(frozen=True)
class Contraccion:
    """El resultado, con los insumos a la vista para poder reportarlos."""

    theta_tilde: pd.Series
    alpha: pd.Series
    tau2: float
    factor_v: float
    metodo_tau2: str
    centro: str

    def resumen(self) -> dict:
        return {
            "tau2": float(self.tau2),
            "raiz_tau2": float(np.sqrt(self.tau2)),
            "factor_v": float(self.factor_v),
            "metodo_tau2": self.metodo_tau2,
            "centro": self.centro,
            "alpha_media": float(self.alpha.mean()),
            "alpha_mediana": float(self.alpha.median()),
            "alpha_min": float(self.alpha.min()),
            "alpha_max": float(self.alpha.max()),
        }


def varianza_agrupada(panel: pd.DataFrame, minimo: int = 1) -> pd.Series:
    """Varianza de cada brazo calculada con la tasa AGRUPADA de su experimento.

    El panel trae `v` con la tasa de cada brazo —p̂(1−p̂)/n— y eso falla por dos
    motivos, los dos importantes:

    1. **Da cero cuando el brazo no tuvo clics.** Al partir en mitades eso pasa
       con frecuencia (tasas de ~1.3% y ~1 500 impresiones por mitad), y una
       varianza cero rompe los pesos 1/v.
    2. **Correlaciona `v` con `θ̂`**, porque los dos se calculan del mismo
       conteo. Es decir: el propio estimador induce la dependencia entre
       parámetro y precisión que advierte Chen (*Econometrica*, 2026). Usar la
       tasa agrupada la evita.

    Bajo el modelo de contracción los brazos de un experimento comparten una
    tasa parecida, así que su tasa agrupada es la mejor escala disponible para
    la varianza. Es la práctica estándar en meta-análisis de proporciones.

    Los experimentos sin ningún clic quedan con varianza NaN: no aportan
    información y se descartan aguas arriba.
    """
    g = panel.groupby("experimento_id")
    clics = g["clics"].transform("sum").to_numpy(dtype=float)
    impres = g["impresiones"].transform("sum").to_numpy(dtype=float)
    n = panel["impresiones"].to_numpy(dtype=float)

    with np.errstate(divide="ignore", invalid="ignore"):
        p = np.where(impres > 0, clics / impres, np.nan)
        v = p * (1.0 - p) / n
    v = np.where((clics >= minimo) & (clics < impres), v, np.nan)
    return pd.Series(v, index=panel.index, name="v_agrupada")


def mascara_utilizable(panel: pd.DataFrame) -> np.ndarray:
    """Qué filas sirven para contraer, como máscara posicional.

    Se expone aparte de `preparar` porque las dos mitades de una partición
    tienen que filtrarse **con la misma máscara** para seguir alineadas fila a
    fila. Si cada mitad se filtrara por su cuenta, se compararían brazos
    distintos y nada lo delataría.

    Descarta los brazos cuya varianza agrupada no se puede calcular —ningún
    clic o todos los clics en el experimento— y los experimentos que quedan con
    menos de dos brazos, que no se pueden comparar.
    """
    v = varianza_agrupada(panel).to_numpy()
    ok = np.isfinite(v) & (v > 0)
    cuenta = (
        pd.Series(ok, index=panel.index)
        .groupby(panel["experimento_id"].to_numpy())
        .transform("sum")
        .to_numpy()
    )
    return ok & (cuenta >= 2)


def preparar(panel: pd.DataFrame, mascara: np.ndarray | None = None) -> pd.DataFrame:
    """Deja el panel listo para contraer: `v` agrupada y sin filas inservibles."""
    m = mascara_utilizable(panel) if mascara is None else np.asarray(mascara, dtype=bool)
    out = panel.loc[m].copy()
    out["v"] = varianza_agrupada(out)
    return out.reset_index(drop=True)


def _centro_por_experimento(
    panel: pd.DataFrame, v: np.ndarray, centro: str
) -> np.ndarray:
    """El punto hacia el que se contrae: el centro del propio experimento."""
    if centro == "simple":
        medias = panel.groupby("experimento_id")["theta_hat"].transform("mean")
        return medias.to_numpy(dtype=float)
    if centro == "ponderado":
        w = 1.0 / v
        tmp = pd.DataFrame(
            {
                "experimento_id": panel["experimento_id"].to_numpy(),
                "wt": w * panel["theta_hat"].to_numpy(dtype=float),
                "w": w,
            }
        )
        sumas = tmp.groupby("experimento_id")[["wt", "w"]].transform("sum")
        return (sumas["wt"] / sumas["w"]).to_numpy(dtype=float)
    raise ValueError(f"centro desconocido: {centro!r}; use {CENTROS}")


def contraer(
    panel: pd.DataFrame,
    tau2: float | pd.Series | None = None,
    *,
    factor_v: float = 1.0,
    metodo_tau2: str = "paule-mandel",
    centro: str = "ponderado",
) -> Contraccion:
    """Contrae las tasas del panel hacia el centro de su experimento.

    `tau2` puede ser un número (misma dispersión para todos: el caso global) o
    una serie alineada al panel (una dispersión por fila: el caso local). Si no
    se pasa, se estima sobre el panel entero, que es el caso global.
    """
    v = panel["v"].to_numpy(dtype=float) * factor_v
    if np.any(v <= 0) or not np.all(np.isfinite(v)):
        raise ValueError("hay varianzas no positivas o no finitas en el panel")

    if tau2 is None:
        tau2 = dispersion.estimar(panel, metodo=metodo_tau2, factor_v=factor_v)

    t2 = (
        np.full(len(panel), float(tau2))
        if np.isscalar(tau2)
        else np.asarray(tau2, dtype=float)
    )
    if t2.shape[0] != len(panel):
        raise ValueError("la serie de tau2 no está alineada con el panel")

    alpha = v / (v + t2)
    centro_vals = _centro_por_experimento(panel, v, centro)
    theta = panel["theta_hat"].to_numpy(dtype=float)

    return Contraccion(
        theta_tilde=pd.Series((1.0 - alpha) * theta + alpha * centro_vals,
                              index=panel.index, name="theta_tilde"),
        alpha=pd.Series(alpha, index=panel.index, name="alpha"),
        tau2=float(np.mean(t2)),
        factor_v=factor_v,
        metodo_tau2=metodo_tau2,
        centro=centro,
    )
