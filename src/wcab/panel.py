"""El panel canónico: la única puerta a los datos.

Se construye una vez desde `data/raw/`, con la exclusión aplicada, y se guarda
en `data/derived/`. Todo lo demás lo lee desde aquí. Un script que lea
`data/raw/` directamente está mal: ver `.claude/rules/datos.md`.

Columnas:
    experimento_id  brazo_id  impresiones  clics  theta_hat  v
    fecha  semana  varia_titular  varia_imagen  es_aa  muestra

`v` es la varianza binomial de la tasa, y **está subestimada**: la auditoría
previa midió Q/gl = 1.927 sobre los experimentos A/A, es decir casi el doble de
la dispersión que predice. Por eso `v` se expone tal cual (ingenua) y la
corrección por factor de diseño se aplica explícitamente en `shrinkage/`, donde
se puede comparar una contra otra. No se corrige en silencio aquí.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from . import exclusion

RAIZ = Path(__file__).resolve().parents[2]
CRUDO = RAIZ / "data" / "raw"
DERIVADO = RAIZ / "data" / "derived"

ARCHIVOS = {
    "exploratorio": "upworthy-exploratory.csv",
    "confirmatorio": "upworthy-confirmatory.csv",
}

#: Campos del CSV que describen qué se le mostró al visitante. Si ninguno varía
#: entre los brazos de un experimento, es una prueba A/A de hecho.
CAMPOS_VARIANTE = ["headline", "eyecatcher_id", "lede", "excerpt"]

COLUMNAS = [
    "experimento_id", "brazo_id", "impresiones", "clics", "theta_hat", "v",
    "fecha", "semana", "varia_titular", "varia_imagen", "es_aa", "muestra",
]


def _leer_crudo(muestra: str) -> pd.DataFrame:
    if muestra not in ARCHIVOS:
        raise ValueError(f"muestra desconocida: {muestra!r}; use {list(ARCHIVOS)}")
    ruta = CRUDO / ARCHIVOS[muestra]
    if not ruta.exists():
        raise FileNotFoundError(
            f"No está {ruta}. Córrase antes `scripts/00_descargar.py`."
        )
    return pd.read_csv(ruta, low_memory=False)


def construir(muestra: str = "exploratorio") -> tuple[pd.DataFrame, exclusion.ResultadoExclusion]:
    """Construye el panel canónico de una muestra, con la exclusión aplicada."""
    crudo = _leer_crudo(muestra)
    crudo = crudo.loc[crudo["impressions"] > 0].copy()

    datos, res = exclusion.aplicar(crudo)

    g = datos.groupby("clickability_test_id")
    distintos = g[CAMPOS_VARIANTE].nunique()
    tamano = g.size().rename("k")

    varia = distintos.join(tamano)
    # Un experimento es A/A de hecho si tiene >=2 brazos y ningún campo varía.
    es_aa = (varia["k"] >= 2) & (varia[CAMPOS_VARIANTE].max(axis=1) <= 1)

    fecha = pd.to_datetime(datos["created_at"], errors="coerce")
    theta = datos["clicks"] / datos["impressions"]

    panel = pd.DataFrame(
        {
            "experimento_id": datos["clickability_test_id"].astype(str),
            "brazo_id": datos.index.astype(str),
            "impresiones": datos["impressions"].astype("int64"),
            "clics": datos["clicks"].astype("int64"),
            "theta_hat": theta.astype("float64"),
            "v": (theta * (1 - theta) / datos["impressions"]).astype("float64"),
            "fecha": fecha,
            "semana": fecha.dt.to_period("W").astype(str),
            "varia_titular": datos["clickability_test_id"]
            .map(distintos["headline"]).gt(1).fillna(False),
            "varia_imagen": datos["clickability_test_id"]
            .map(distintos["eyecatcher_id"]).gt(1).fillna(False),
            "es_aa": datos["clickability_test_id"].map(es_aa).fillna(False),
            "muestra": muestra,
        }
    )[COLUMNAS].reset_index(drop=True)

    return panel, res


def ruta_derivada(muestra: str) -> Path:
    return DERIVADO / f"panel-{muestra}.parquet"


def guardar(panel: pd.DataFrame, muestra: str) -> Path:
    DERIVADO.mkdir(parents=True, exist_ok=True)
    destino = ruta_derivada(muestra)
    panel.to_parquet(destino, index=False)
    return destino


def cargar(muestra: str = "exploratorio") -> pd.DataFrame:
    """Lee el panel ya construido; lo construye y guarda si no existe."""
    destino = ruta_derivada(muestra)
    if destino.exists():
        return pd.read_parquet(destino)
    panel, _ = construir(muestra)
    guardar(panel, muestra)
    return panel


def resumen(panel: pd.DataFrame) -> dict:
    """Las cifras de escala que los documentos citan. Una sola fuente."""
    por_exp = panel.groupby("experimento_id")
    k = por_exp.size()
    return {
        "brazos": int(len(panel)),
        "experimentos": int(panel["experimento_id"].nunique()),
        "impresiones": int(panel["impresiones"].sum()),
        "clics": int(panel["clics"].sum()),
        "tasa_global": float(panel["clics"].sum() / panel["impresiones"].sum()),
        "brazos_por_experimento_min": int(k.min()),
        "brazos_por_experimento_max": int(k.max()),
        "brazos_por_experimento_media": float(k.mean()),
        "impresiones_por_brazo_mediana": float(panel["impresiones"].median()),
        "semanas": int(panel["semana"].nunique()),
        "experimentos_aa": int(
            panel.loc[panel["es_aa"], "experimento_id"].nunique()
        ),
        "experimentos_solo_titular": int(
            panel.loc[panel["varia_titular"] & ~panel["varia_imagen"],
                      "experimento_id"].nunique()
        ),
        "error_estandar_brazo_tipico": float(np.sqrt(panel["v"].mean())),
    }
