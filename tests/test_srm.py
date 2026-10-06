"""Sample ratio mismatch: the check that justified excluding 30.6% of the archive.

If this flagged balanced experiments, or missed unbalanced ones, the exclusion
window would rest on nothing.
"""

import numpy as np
import pandas as pd
import pytest

from wcab.diagnostics import srm


def _experiments(allocations, date="2014-06-01", prefix="e"):
    """One experiment per entry; each entry lists impressions per arm.

    `prefix` keeps ids distinct when two groups are concatenated. Without it the
    groupby merges experiments across groups — the same silent collision the
    cluster bootstrap guards against.
    """
    rows = []
    for i, impressions in enumerate(allocations):
        for n in impressions:
            rows.append(
                {
                    "experiment_id": f"{prefix}{i}",
                    "impressions": n,
                    "date": pd.Timestamp(date),
                }
            )
    return pd.DataFrame(rows)


def test_a_balanced_allocation_is_not_flagged():
    df = _experiments([[3000, 3000, 3000]] * 5)
    out = srm.per_experiment(df)
    assert not out["imbalanced"].any()


def test_a_severe_imbalance_is_flagged():
    """What the Cloudflare failure looked like: one arm served, the rest starved."""
    df = _experiments([[9000, 500, 500]] * 5)
    out = srm.per_experiment(df)
    assert out["imbalanced"].all()


def test_a_single_arm_experiment_is_skipped_rather_than_flagged():
    df = _experiments([[3000], [3000, 3000]])
    out = srm.per_experiment(df)
    assert len(out) == 1
    assert out["experiment_id"].iloc[0] == "e1"


def test_the_p_value_moves_the_right_way_with_the_imbalance():
    mild = srm.per_experiment(_experiments([[3100, 2900, 3000]]))
    severe = srm.per_experiment(_experiments([[9000, 500, 500]]))
    assert mild["p_value"].iloc[0] > severe["p_value"].iloc[0]


def test_by_month_discards_months_with_too_few_experiments():
    """A fraction computed over three experiments is too noisy to read."""
    many = _experiments([[9000, 500]] * 50, date="2013-12-15", prefix="m")
    few = _experiments([[9000, 500]] * 3, date="2014-07-15", prefix="f")
    out = srm.by_month(srm.per_experiment(pd.concat([many, few], ignore_index=True)),
                       minimum=30)
    assert list(out["month"]) == ["2013-12"]


def test_by_month_reports_the_imbalanced_fraction():
    balanced = _experiments([[3000, 3000]] * 30, date="2014-06-15", prefix="bal")
    broken = _experiments([[9000, 300]] * 30, date="2013-12-15", prefix="bro")
    out = srm.by_month(
        srm.per_experiment(pd.concat([balanced, broken], ignore_index=True)),
        minimum=10,
    )
    by_month = dict(zip(out["month"], out["imbalance_fraction"]))
    assert by_month["2013-12"] == pytest.approx(1.0)
    assert by_month["2014-06"] == pytest.approx(0.0)


def test_the_summary_carries_what_the_document_cites():
    out = srm.summary(srm.per_experiment(_experiments([[3000, 3000]] * 10)))
    assert "experiments_evaluated" in out
    assert 0.0 <= out["global_imbalance_fraction"] <= 1.0
