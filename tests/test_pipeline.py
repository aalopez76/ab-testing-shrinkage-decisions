"""The core pipeline, end to end, on a synthetic archive.

Unit tests cover each module's contract; this covers their interaction. It
builds a small CSV in the shape the real archive has, then walks the whole
chain: raw file, exclusion, canonical panel, three-way split, portfolio,
decision value.

**What it does not cover**, deliberately, because pretending otherwise is how
the earlier translation defects survived a green suite: command-line flags,
printed output, and the JSON keys the figure generator reads. Ruff covers
undefined names, `test_figures_smoke.py` covers the artefact contract, and a
manual cold run covers the scripts themselves.
"""

import numpy as np
import pandas as pd
import pytest

from wcab import decision, exclusion, panel, portfolio, shrinkage, thinning


@pytest.fixture
def archive(tmp_path, monkeypatch):
    """A synthetic archive with the shape the real CSV files have.

    Includes experiments inside the failure window, so the exclusion has
    something to remove, and one genuine A/A experiment.
    """
    rng = np.random.default_rng(20261006)
    rows = []

    def experiment(eid, date, arms, headline_varies, rate=0.013):
        for a in range(arms):
            n = int(rng.integers(2500, 3500))
            theta = rate + (0.001 * a if headline_varies else 0.0)
            rows.append(
                {
                    "clickability_test_id": eid,
                    "created_at": date,
                    "headline": f"h{a}" if headline_varies else "h0",
                    "eyecatcher_id": "img0",
                    "lede": "l0",
                    "excerpt": "x0",
                    "impressions": n,
                    "clicks": int(rng.binomial(n, theta)),
                }
            )

    # kept: outside the failure window
    for i in range(60):
        experiment(f"keep{i}", "2014-06-15", arms=int(rng.integers(2, 6)),
                   headline_varies=True)
    # A/A: nothing varies between arms
    for i in range(20):
        experiment(f"aa{i}", "2014-07-10", arms=3, headline_varies=False)
    # dropped: inside the Cloudflare window
    for i in range(25):
        experiment(f"drop{i}", "2013-09-20", arms=3, headline_varies=True)

    raw = tmp_path / "raw"
    raw.mkdir()
    pd.DataFrame(rows).to_csv(raw / "upworthy-exploratory.csv", index=False)

    monkeypatch.setattr(panel, "RAW", raw)
    monkeypatch.setattr(panel, "DERIVED", tmp_path / "derived")
    return tmp_path


def test_the_chain_runs_from_a_raw_file_to_a_decision_value(archive):
    built, result = panel.build("exploratory")

    # exclusion removed the failure window and nothing else
    assert result.excluded_experiments == 25
    assert built["experiment_id"].nunique() == 80
    assert not exclusion.in_failure_window(built["date"]).any()

    # the panel honours its column contract
    assert list(built.columns) == panel.COLUMNS
    assert (built["clicks"] <= built["impressions"]).all()

    # A/A experiments are identified
    assert built.loc[built["is_aa"], "experiment_id"].nunique() == 20

    # three-way split, aligned and conserving the counts
    selection, estimation, evaluation = thinning.split_three_way(built, seed=0)
    assert list(selection["arm_id"]) == list(evaluation["arm_id"])

    mask = shrinkage.usable_mask(estimation)
    c = portfolio.build_three_way(
        selection.loc[mask].reset_index(drop=True),
        shrinkage.prepare(estimation, mask),
        evaluation.loc[mask].reset_index(drop=True),
    )
    assert len(c) > 0

    # the decision layer produces finite, comparable values
    shrunk, tau2 = portfolio.shrink_portfolio(c)
    assert tau2 >= 0
    budgets = (0.1, 0.5)
    raw_value = portfolio.value_by_budget(
        c, c.table["delta_estimated"].to_numpy(), budgets)
    shrunk_value = portfolio.value_by_budget(c, shrunk, budgets)
    assert all(np.isfinite(list(raw_value.values()) + list(shrunk_value.values())))

    # and the policy value is well formed
    policy = portfolio.threshold_adjusted_value(c, shrunk, threshold=0.001)
    assert 0.0 <= policy["ship_rate"] <= 1.0
    assert np.isfinite(policy["value"])


def test_the_winners_curse_appears_in_the_synthetic_archive(archive):
    """A sanity check on the estimand, not on its magnitude.

    Selecting the measured maximum must overstate; selecting at random must not.
    """
    built, _ = panel.build("exploratory")
    part = thinning.split(built, fraction=0.5, seed=0)
    mask = shrinkage.usable_mask(part.estimation)
    est = shrinkage.prepare(part.estimation, mask)
    ev = part.evaluation.loc[mask].reset_index(drop=True)

    chosen = decision.evaluate(est, ev, rule="raw")
    at_random = decision.evaluate(est, ev, rule="random", seed=1)

    assert chosen.inflation > 0
    assert abs(at_random.inflation) < chosen.inflation


def test_the_panel_round_trips_through_parquet(archive):
    """`load` must return what `build` produced, since everything reads it."""
    built, _ = panel.build("exploratory")
    panel.save(built, "exploratory")
    loaded = panel.load("exploratory")

    assert list(loaded.columns) == list(built.columns)
    assert len(loaded) == len(built)
    assert loaded["clicks"].sum() == built["clicks"].sum()
