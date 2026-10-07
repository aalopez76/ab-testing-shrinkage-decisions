"""The panel is the single gateway to the data, so its contract is tested.

These assertions are about the **archive**, not about the software: that the
exclusion window is empty, that enough A/A experiments survive to calibrate
against, that rates and variances agree. They cannot run without the real CSV
files, which are not redistributed here, so they skip where the data are absent
— on CI, for instance.

The software itself is covered without the archive: `tests/test_pipeline.py`
walks the same chain over a synthetic one.
"""

import pandas as pd
import pytest

from wcab import panel

needs_archive = pytest.mark.skipif(
    not panel.derived_path("exploratory").exists()
    and not (panel.RAW / panel.FILES["exploratory"]).exists(),
    reason="the Upworthy archive is not present; run scripts/00_download.py",
)

pytestmark = needs_archive


@pytest.fixture(scope="module")
def p():
    return panel.load("exploratory")


def test_it_has_the_contracted_columns(p):
    assert list(p.columns) == panel.COLUMNS


def test_the_exclusion_has_been_applied(p):
    """No arm in the panel may fall inside the failure window."""
    f = pd.to_datetime(p["date"])
    inside = (f >= pd.Timestamp("2013-06-01")) & (f < pd.Timestamp("2014-02-01"))
    assert not inside.any()
    assert p["date"].notna().all()


def test_no_empty_arms(p):
    assert (p["impressions"] > 0).all()
    assert (p["clicks"] >= 0).all()
    assert (p["clicks"] <= p["impressions"]).all()


def test_theta_and_v_are_coherent(p):
    expected = p["clicks"] / p["impressions"]
    assert (p["theta_hat"] - expected).abs().max() < 1e-12
    v = p["theta_hat"] * (1 - p["theta_hat"]) / p["impressions"]
    assert (p["v"] - v).abs().max() < 1e-15
    assert (p["v"] >= 0).all()


def test_aa_experiments_vary_in_no_field(p):
    """An experiment marked A/A cannot carry any recorded variation."""
    aa = p.loc[p["is_aa"]]
    assert not aa["varies_headline"].any()
    assert not aa["varies_image"].any()


def test_there_are_enough_aa_experiments_to_calibrate(p):
    """Without A/A experiments, step 1 of the plan cannot be run.

    The threshold is 100 experiments: with 2 to 14 arms each, that gives hundreds
    of degrees of freedom for Cochran's Q, which is ample. It is not set higher so
    as not to encode an expectation in the test in place of a requirement.
    """
    assert p.loc[p["is_aa"], "experiment_id"].nunique() >= 100


def test_the_summary_carries_the_figures_the_documents_cite(p):
    r = panel.summary(p)
    for key in (
        "arms", "experiments", "impressions", "global_rate",
        "arms_per_experiment_max", "median_impressions_per_arm",
        "weeks", "aa_experiments",
    ):
        assert key in r
    assert 2 <= r["arms_per_experiment_min"]
    assert 0 < r["global_rate"] < 1
