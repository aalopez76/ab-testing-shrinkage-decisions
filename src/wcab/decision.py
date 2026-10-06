"""Step 5: compare decisions, not estimates.

This is where the project's criterion is settled: **methods are judged by the
decisions they produce, not by whether they satisfy their own assumptions.**

Each rule selects one variant per experiment using the estimation half, and what
that variant delivered is measured on the evaluation half — which played no part
in selecting it. Three metrics:

- **value**: the realised rate of the selected variant.
- **regret**: how much was lost against the best available variant, also measured
  on the evaluation half.
- **inflation**: what the selected variant promised at selection time minus what
  it delivered. This is the project's principal estimand.

The benchmark to beat is `random`: selecting a variant at random. A correction
that cannot beat that is of no use. And `raw` — selecting the measured maximum —
is the practice the project puts to the test.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

RAW = "raw"
RANDOM = "random"


@dataclass(frozen=True)
class Result:
    """A rule's performance, with what is needed to report it."""

    rule: str
    experiments: int
    value: float               # mean realised rate of the selected variants
    regret: float              # how much was left on the table
    inflation: float           # promised - delivered
    per_experiment: pd.DataFrame

    def summary(self) -> dict:
        return {
            "rule": self.rule,
            "experiments": self.experiments,
            "value": float(self.value),
            "regret": float(self.regret),
            "inflation": float(self.inflation),
            "fraction_worse_than_oracle": float(
                (self.per_experiment["regret"] > 0).mean()
            ),
        }


def _choose(priority: np.ndarray) -> int:
    """Index of the maximum. Ties resolve to the first, which is deterministic."""
    return int(np.argmax(priority))


def evaluate(
    estimation: pd.DataFrame,
    evaluation: pd.DataFrame,
    priority: pd.Series | np.ndarray | None = None,
    rule: str = RAW,
    seed: int = 0,
) -> Result:
    """Apply a rule and measure what it delivered.

    `priority` is the criterion by which variants are ranked within each
    experiment, computed on the **estimation** half. If it is None and the rule is
    `random`, priorities are drawn at random; if it is None in any other case,
    `theta_hat` is used.

    The two halves must arrive aligned row by row, which is what `thinning.split`
    guarantees.
    """
    if len(estimation) != len(evaluation):
        raise ValueError("the two halves are not aligned")

    rng = np.random.default_rng(seed)
    if rule == RANDOM:
        prio = rng.random(len(estimation))
    elif priority is None:
        prio = estimation["theta_hat"].to_numpy(dtype=float)
    else:
        prio = np.asarray(priority, dtype=float)

    exp = estimation["experiment_id"].to_numpy()
    theta_est = estimation["theta_hat"].to_numpy(dtype=float)
    theta_eval = evaluation["theta_hat"].to_numpy(dtype=float)

    rows = []
    order = np.argsort(exp, kind="stable")
    exp_ord = exp[order]
    cuts = np.flatnonzero(np.r_[True, exp_ord[1:] != exp_ord[:-1]])
    bounds = np.r_[cuts, len(exp_ord)]

    for a, b in zip(bounds[:-1], bounds[1:]):
        idx = order[a:b]
        if len(idx) < 2:
            continue
        chosen = idx[_choose(prio[idx])]
        best_possible = float(theta_eval[idx].max())
        rows.append(
            {
                "experiment_id": exp_ord[a],
                "arms": len(idx),
                "promised": float(theta_est[chosen]),
                "delivered": float(theta_eval[chosen]),
                "best_possible": best_possible,
                "regret": best_possible - float(theta_eval[chosen]),
                "inflation": float(theta_est[chosen]) - float(theta_eval[chosen]),
            }
        )

    per_exp = pd.DataFrame(rows)
    return Result(
        rule=rule,
        experiments=len(per_exp),
        value=float(per_exp["delivered"].mean()),
        regret=float(per_exp["regret"].mean()),
        inflation=float(per_exp["inflation"].mean()),
        per_experiment=per_exp,
    )


def compare(results: list[Result], reference: str = RAW) -> pd.DataFrame:
    """Comparison table, with the difference in value against a reference rule."""
    base = next((r for r in results if r.rule == reference), None)
    rows = []
    for r in results:
        row = r.summary()
        if base is not None:
            row["value_minus_" + reference] = r.value - base.value
        rows.append(row)
    return pd.DataFrame(rows)


def where_it_fails(
    a: Result, b: Result, name_a: str = "A", name_b: str = "B"
) -> dict:
    """In which experiments rule `a` selects worse than rule `b`.

    The non-optional part of the project: shrinkage improves the aggregate while
    harming specific cases. Which ones, and what they have in common, is the
    question.
    """
    j = a.per_experiment.merge(
        b.per_experiment, on="experiment_id", suffixes=("_a", "_b")
    )
    worse = j["delivered_a"] < j["delivered_b"]
    out = {
        "comparison": f"{name_a} against {name_b}",
        "experiments": int(len(j)),
        "fraction_worse": float(worse.mean()),
        "fraction_better": float((j["delivered_a"] > j["delivered_b"]).mean()),
        "fraction_equal": float((j["delivered_a"] == j["delivered_b"]).mean()),
    }
    if worse.any():
        out["profile_of_the_worst"] = {
            "mean_arms": float(j.loc[worse, "arms_a"].mean()),
            "mean_arms_rest": float(j.loc[~worse, "arms_a"].mean()),
            "mean_loss": float(
                (j.loc[worse, "delivered_b"] - j.loc[worse, "delivered_a"]).mean()
            ),
        }
    return out
