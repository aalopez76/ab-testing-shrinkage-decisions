"""Uncertainty about the effect, kept apart from noise in the split.

The project evaluates every rule over repeated thinning splits of the same
archive. Averaging those splits and dividing their standard deviation by the
square root of their count produces an interval — but **not** the interval it
appears to be. It measures how much the answer moves when the random split
moves, which shrinks towards zero as more seeds are added. Sampling uncertainty
about the effect does not shrink by splitting the same data again.

The natural resampling unit is the **experiment**, which makes this a cluster
bootstrap: arms within an experiment are dependent, experiments are treated as
the exchangeable units, and whole clusters are drawn with replacement.

Two things this implementation must get right, both of which fail silently:

1. **Each resampled copy receives a fresh `experiment_id`.** Drawing experiment
   14 three times and keeping its original id would let `groupby` merge the
   three copies back into one, quietly undoing the resampling.
2. **Everything is recomputed inside each replicate** — selection, thinning,
   dispersion, shrinkage, ranking and the statistic. Resampling a table of
   already-computed differences would omit the estimator's own contribution to
   the uncertainty.

**The published point estimate is the statistic on the original data**, never the
mean of the replicates. The bootstrap estimates the sampling distribution; it
does not replace the estimator. The bootstrap mean is returned only as a bias
diagnostic.

**Scope.** Experiments are the resampling units, so dependence *across* them —
shared time periods, editorial context — is not modelled. The archive is a time
series, and nothing here is a block bootstrap.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd

#: Statistic signature: (panel, seed) -> scalar, or -> dict of scalars. The seed
#: drives the thinning, so the same panel under different seeds gives the Monte
#: Carlo spread.
#:
#: **Return several quantities from one call whenever they will be compared.**
#: Computing `shrunk` and `raw` in separate bootstrap passes and subtracting the
#: results ignores the correlation between them and inflates the variance of the
#: difference; the rules are being applied to the same resampled experiments, so
#: the comparison is paired. Returning a dict keeps the pairing, and costs one
#: portfolio build instead of several.
Statistic = Callable[[pd.DataFrame, int], "float | dict[str, float]"]


@dataclass(frozen=True)
class BootstrapResult:
    """What the bootstrap says, with the two uncertainties kept apart."""

    point_estimate: float          # statistic on the ORIGINAL data
    percentile_interval: tuple[float, float]
    basic_interval: tuple[float, float]
    bootstrap_se: float
    mc_variability: float          # sd across thinning seeds, reported apart
    bootstrap_mean: float          # diagnostic only: bias is mean - point
    replicates: int
    seeds_per_replicate: int

    @property
    def bias(self) -> float:
        """Bootstrap estimate of bias. Large values make the mean suspect."""
        return self.bootstrap_mean - self.point_estimate

    @property
    def intervals_agree(self) -> bool:
        """Whether percentile and basic tell the same story.

        A material gap signals non-negligible asymmetry or displacement of the
        bootstrap distribution relative to the observed estimate. It does not by
        itself establish that the distribution is biased.
        """
        width = max(
            self.percentile_interval[1] - self.percentile_interval[0], 1e-300
        )
        gap = max(
            abs(self.percentile_interval[0] - self.basic_interval[0]),
            abs(self.percentile_interval[1] - self.basic_interval[1]),
        )
        return gap / width < 0.10

    def to_dict(self) -> dict:
        return {
            "point_estimate": self.point_estimate,
            "percentile_interval": list(self.percentile_interval),
            "basic_interval": list(self.basic_interval),
            "bootstrap_se": self.bootstrap_se,
            "mc_variability": self.mc_variability,
            "bootstrap_mean": self.bootstrap_mean,
            "bias": self.bias,
            "intervals_agree": self.intervals_agree,
            "replicates": self.replicates,
            "seeds_per_replicate": self.seeds_per_replicate,
        }


class ClusterIndex:
    """Row positions of each experiment, worked out once and drawn from many times.

    Resampling by `groupby` and `concat` rebuilds the grouping on every replicate
    and glues thousands of small frames back together — on this archive that cost
    4.8 s per draw, six times the statistic it exists to serve. Precomputing the
    row ranges turns a draw into one `take`, and the whole bootstrap from hours
    into minutes.
    """

    def __init__(self, panel: pd.DataFrame) -> None:
        ids = panel["experiment_id"].to_numpy()
        order = np.argsort(ids, kind="stable")
        _, first, counts = np.unique(ids[order], return_index=True, return_counts=True)

        self.panel = panel
        self._order = order
        self._first = first
        self._counts = counts
        self.clusters = len(counts)

    def draw(self, rng: np.random.Generator) -> pd.DataFrame:
        """One bootstrap sample: whole experiments, with replacement, relabelled.

        The relabelling is the part that matters. Without it, a cluster drawn
        twice would be reunited by the next `groupby("experiment_id")` and the
        replicate would silently hold fewer, larger experiments than intended.
        """
        drawn = rng.integers(0, self.clusters, size=self.clusters)
        counts = self._counts[drawn]

        rows = np.concatenate(
            [self._order[f:f + c] for f, c in zip(self._first[drawn], counts)]
        )
        out = self.panel.take(rows).reset_index(drop=True)
        out["experiment_id"] = np.repeat(
            [f"b{i:06d}" for i in range(self.clusters)], counts
        )
        return out


def resample_experiments(
    panel: pd.DataFrame, rng: np.random.Generator
) -> pd.DataFrame:
    """Draw whole experiments with replacement, relabelling every copy.

    Convenience wrapper: builds the index and draws once. Inside a bootstrap loop
    use `ClusterIndex` directly, so the grouping is computed a single time.
    """
    return ClusterIndex(panel).draw(rng)


def _as_dict(value) -> dict[str, float]:
    return value if isinstance(value, dict) else {"value": float(value)}


def _average_over_seeds(
    panel: pd.DataFrame, statistic: Statistic, seeds: int, base_seed: int
) -> tuple[dict[str, float], dict[str, float]]:
    """Mean and spread of each returned quantity across `seeds` thinning draws."""
    draws = [_as_dict(statistic(panel, base_seed + s)) for s in range(seeds)]
    keys = list(draws[0])
    mean, spread = {}, {}
    for k in keys:
        v = np.asarray(
            [d[k] for d in draws if np.isfinite(d.get(k, np.nan))], dtype=float
        )
        if v.size == 0:
            mean[k], spread[k] = float("nan"), float("nan")
        else:
            mean[k] = float(v.mean())
            spread[k] = float(v.std(ddof=1)) if v.size > 1 else 0.0
    return mean, spread


def cluster_bootstrap(
    panel: pd.DataFrame,
    statistic: Statistic,
    replicates: int = 300,
    seeds_per_replicate: int = 3,
    seed: int = 0,
    level: float = 0.95,
) -> BootstrapResult | dict[str, BootstrapResult]:
    """Cluster bootstrap over experiments, averaging thinning noise within each.

    `statistic` takes `(panel, seed)` and returns either a scalar or a dict of
    scalars. It must recompute everything it depends on, because that is what
    carries the estimator's own uncertainty into the interval.

    A scalar statistic returns one `BootstrapResult`; a dict statistic returns
    one per key, **all computed from the same replicates**, which keeps paired
    comparisons paired.
    """
    if not 0.0 < level < 1.0:
        raise ValueError(f"level outside (0,1): {level}")
    if replicates < 2:
        raise ValueError(f"need at least 2 replicates, got {replicates}")

    rng = np.random.default_rng(seed)
    returns_scalar = not isinstance(statistic(panel, seed), dict)

    point, mc = _average_over_seeds(
        panel, statistic, seeds_per_replicate, base_seed=seed
    )

    index = ClusterIndex(panel)          # grouped once, drawn from B times
    draws: dict[str, list[float]] = {k: [] for k in point}
    for b in range(replicates):
        sample = index.draw(rng)
        value, _ = _average_over_seeds(
            sample, statistic, seeds_per_replicate, base_seed=seed + 1_000 * (b + 1)
        )
        for k in draws:
            if np.isfinite(value.get(k, np.nan)):
                draws[k].append(value[k])

    alpha = (1.0 - level) / 2.0
    results: dict[str, BootstrapResult] = {}
    for k, values in draws.items():
        d = np.asarray(values, dtype=float)
        if d.size < 2:
            raise RuntimeError(
                f"only {d.size} usable bootstrap replicates for {k!r}; "
                "cannot form an interval"
            )
        lo_pct, hi_pct = np.quantile(d, [alpha, 1.0 - alpha])
        # basic (reverse percentile): reflects the replicates about the observed
        # estimate. From the SAME draws, so it costs nothing.
        results[k] = BootstrapResult(
            point_estimate=point[k],
            percentile_interval=(float(lo_pct), float(hi_pct)),
            basic_interval=(float(2.0 * point[k] - hi_pct),
                            float(2.0 * point[k] - lo_pct)),
            bootstrap_se=float(d.std(ddof=1)),
            mc_variability=mc[k],
            bootstrap_mean=float(d.mean()),
            replicates=int(d.size),
            seeds_per_replicate=int(seeds_per_replicate),
        )

    return results["value"] if returns_scalar else results
