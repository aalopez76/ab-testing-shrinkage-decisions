"""The canonical panel: the single gateway to the data.

It is built once from `data/raw/`, with the exclusion applied, and stored in
`data/derived/`. Everything else reads it from here. A script that reads
`data/raw/` directly is doing it wrong.

Columns:
    experiment_id  arm_id  impressions  clicks  theta_hat  v
    date  week  varies_headline  varies_image  is_aa  sample

`v` is the binomial variance of the rate, and it is **underestimated**: the audit
measured Q/dof = 1.927 over the A/A-like experiments, close to twice the dispersion the
formula predicts. For that reason `v` is exposed as it is (naive) and the design
factor correction is applied explicitly in `shrinkage/`, where the two can be
compared. Nothing is corrected silently here.
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

#: CSV fields describing what was shown to the visitor. If none of them varies
#: between an experiment's arms, it is an A/A test in effect.
VARIANT_FIELDS = ["headline", "eyecatcher_id", "lede", "excerpt"]

COLUMNS = [
    "experiment_id", "arm_id", "impressions", "clicks", "theta_hat", "v",
    "date", "week", "varies_headline", "varies_image", "is_aa", "sample",
]


def _read_raw(sample: str) -> pd.DataFrame:
    if sample not in FILES:
        raise ValueError(f"unknown sample: {sample!r}; use one of {list(FILES)}")
    path = RAW / FILES[sample]
    if not path.exists():
        raise FileNotFoundError(
            f"{path} is missing. Run `scripts/00_download.py` first."
        )
    return pd.read_csv(path, low_memory=False)


def build(sample: str = "exploratory") -> tuple[pd.DataFrame, exclusion.ExclusionResult]:
    """Build a sample's canonical panel, with the exclusion applied."""
    raw = _read_raw(sample)
    raw = raw.loc[raw["impressions"] > 0].copy()

    data, res = exclusion.apply(raw)

    g = data.groupby("clickability_test_id")
    distinct = g[VARIANT_FIELDS].nunique()
    size = g.size().rename("k")

    varies = distinct.join(size)
    # An experiment is A/A in effect if it has >=2 arms and no field varies.
    is_aa = (varies["k"] >= 2) & (varies[VARIANT_FIELDS].max(axis=1) <= 1)

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
            .map(distinct["headline"]).gt(1).fillna(False),
            "varies_image": data["clickability_test_id"]
            .map(distinct["eyecatcher_id"]).gt(1).fillna(False),
            "is_aa": data["clickability_test_id"].map(is_aa).fillna(False),
            "sample": sample,
        }
    )[COLUMNS].reset_index(drop=True)

    return panel, res


def derived_path(sample: str) -> Path:
    return DERIVED / f"panel-{sample}.parquet"


def save(panel: pd.DataFrame, sample: str) -> Path:
    DERIVED.mkdir(parents=True, exist_ok=True)
    target = derived_path(sample)
    panel.to_parquet(target, index=False)
    return target


def load(sample: str = "exploratory") -> pd.DataFrame:
    """Read the panel if it has been built; build and store it otherwise."""
    target = derived_path(sample)
    if target.exists():
        return pd.read_parquet(target)
    panel, _ = build(sample)
    save(panel, sample)
    return panel


def summary(panel: pd.DataFrame) -> dict:
    """The scale figures the documents cite. A single source for all of them."""
    per_exp = panel.groupby("experiment_id")
    k = per_exp.size()
    return {
        "arms": int(len(panel)),
        "experiments": int(panel["experiment_id"].nunique()),
        "impressions": int(panel["impressions"].sum()),
        "clicks": int(panel["clicks"].sum()),
        "global_rate": float(panel["clicks"].sum() / panel["impressions"].sum()),
        "arms_per_experiment_min": int(k.min()),
        "arms_per_experiment_max": int(k.max()),
        "arms_per_experiment_mean": float(k.mean()),
        "median_impressions_per_arm": float(panel["impressions"].median()),
        "weeks": int(panel["week"].nunique()),
        "aa_experiments": int(
            panel.loc[panel["is_aa"], "experiment_id"].nunique()
        ),
        "headline_only_experiments": int(
            panel.loc[panel["varies_headline"] & ~panel["varies_image"],
                      "experiment_id"].nunique()
        ),
        "typical_arm_standard_error": float(np.sqrt(panel["v"].mean())),
    }
