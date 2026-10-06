"""El panel canónico: la única puerta a los data.

Se construye una vez desde `data/raw/`, con la exclusión aplicada, y se guarda
en `data/derived/`. Todo lo demás lo lee desde aquí. Un script que lea
`data/raw/` directamente está mal: ver `.claude/rules/data.md`.

Columnas:
    experiment_id  arm_id  impressions  clicks  theta_hat  v
    date  week  varies_headline  varies_image  is_aa  sample

`v` es la varianza binomial de la rate, y **está subestimada**: la auditoría
previa midió Q/dof = 1.927 sobre los experiments A/A, es decir casi el doble de
la dispersión que predice. Por eso `v` se expone tal cual (ingenua) y la
corrección por factor de diseño se aplica explícitamente en `shrinkage/`, donde
se puede compare una contra otra. No se corrige en silencio aquí.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from . import exclusion

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
DERIVED = ROOT / "data" / "derived"

FILES = {
    "exploratory": "upworthy-exploratory.csv",
    "confirmatory": "upworthy-confirmatory.csv",
}

#: Campos del CSV que describen qué se le mostró al visitante. Si ninguno varía
#: entre los arms de un experimento, es una prueba A/A de hecho.
VARIANT_FIELDS = ["headline", "eyecatcher_id", "lede", "excerpt"]

COLUMNS = [
    "experiment_id", "arm_id", "impressions", "clicks", "theta_hat", "v",
    "date", "week", "varies_headline", "varies_image", "is_aa", "sample",
]


def _read_raw(sample: str) -> pd.DataFrame:
    if sample not in FILES:
        raise ValueError(f"sample desconocida: {sample!r}; use {list(FILES)}")
    ruta = RAW / FILES[sample]
    if not ruta.exists():
        raise FileNotFoundError(
            f"No está {ruta}. Córrase antes `scripts/00_descargar.py`."
        )
    return pd.read_csv(ruta, low_memory=False)


def build(sample: str = "exploratory") -> tuple[pd.DataFrame, exclusion.ExclusionResult]:
    """Construye el panel canónico de una sample, con la exclusión aplicada."""
    crudo = _read_raw(sample)
    crudo = crudo.loc[crudo["impressions"] > 0].copy()

    data, res = exclusion.apply(crudo)

    g = data.groupby("clickability_test_id")
    distintos = g[VARIANT_FIELDS].nunique()
    tamano = g.size().rename("k")

    varia = distintos.join(tamano)
    # Un experimento es A/A de hecho si tiene >=2 arms y ningún campo varía.
    is_aa = (varia["k"] >= 2) & (varia[VARIANT_FIELDS].max(axis=1) <= 1)

    date = pd.to_datetime(data["created_at"], errors="coerce")
    theta = data["clicks"] / data["impressions"]

    panel = pd.DataFrame(
        {
            "experiment_id": data["clickability_test_id"].astype(str),
            "arm_id": data.index.astype(str),
            "impressions": data["impressions"].astype("int64"),
            "clicks": data["clicks"].astype("int64"),
            "theta_hat": theta.astype("float64"),
            "v": (theta * (1 - theta) / data["impressions"]).astype("float64"),
            "date": date,
            "week": date.dt.to_period("W").astype(str),
            "varies_headline": data["clickability_test_id"]
            .map(distintos["headline"]).gt(1).fillna(False),
            "varies_image": data["clickability_test_id"]
            .map(distintos["eyecatcher_id"]).gt(1).fillna(False),
            "is_aa": data["clickability_test_id"].map(is_aa).fillna(False),
            "sample": sample,
        }
    )[COLUMNS].reset_index(drop=True)

    return panel, res


def derived_path(sample: str) -> Path:
    return DERIVED / f"panel-{sample}.parquet"


def save(panel: pd.DataFrame, sample: str) -> Path:
    DERIVED.mkdir(parents=True, exist_ok=True)
    destino = derived_path(sample)
    panel.to_parquet(destino, index=False)
    return destino


def load(sample: str = "exploratory") -> pd.DataFrame:
    """Lee el panel ya construido; lo construye y guarda si no existe."""
    destino = derived_path(sample)
    if destino.exists():
        return pd.read_parquet(destino)
    panel, _ = build(sample)
    save(panel, sample)
    return panel


def summary(panel: pd.DataFrame) -> dict:
    """Las metrics de escala que los documentos citan. Una sola fuente."""
    por_exp = panel.groupby("experiment_id")
    k = por_exp.size()
    return {
        "arms": int(len(panel)),
        "experiments": int(panel["experiment_id"].nunique()),
        "impressions": int(panel["impressions"].sum()),
        "clicks": int(panel["clicks"].sum()),
        "global_rate": float(panel["clicks"].sum() / panel["impressions"].sum()),
        "brazos_por_experimento_min": int(k.min()),
        "brazos_por_experimento_max": int(k.max()),
        "brazos_por_experimento_media": float(k.mean()),
        "impresiones_por_brazo_mediana": float(panel["impressions"].median()),
        "semanas": int(panel["week"].nunique()),
        "experimentos_aa": int(
            panel.loc[panel["is_aa"], "experiment_id"].nunique()
        ),
        "experimentos_solo_titular": int(
            panel.loc[panel["varies_headline"] & ~panel["varies_image"],
                      "experiment_id"].nunique()
        ),
        "error_estandar_brazo_tipico": float(np.sqrt(panel["v"].mean())),
    }
