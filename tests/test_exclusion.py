"""The exclusion is the rule easiest to violate silently, so it is tested.

If it lets through an experiment from the failure window, something that was not
randomised is analysed as though it had been, and nothing in the results reveals
it.
"""

import pandas as pd
import pytest

from wcab import exclusion


def _data(dates, experiments=None):
    n = len(dates)
    return pd.DataFrame(
        {
            "created_at": dates,
            "clickability_test_id": experiments or list(range(n)),
            "impressions": [100] * n,
        }
    )


def test_removes_the_whole_window():
    """The boundaries matter: 1 June is inside, 1 February is already outside."""
    df = _data(
        [
            "2013-05-31 23:00:00",   # outside, retained
            "2013-06-01 00:00:00",   # first excluded day
            "2013-09-15 12:00:00",   # middle of the window
            "2014-01-31 23:59:00",   # last excluded instant
            "2014-02-01 00:00:00",   # outside again, retained
        ]
    )
    out, res = exclusion.apply(df)
    assert list(out["clickability_test_id"]) == [0, 4]
    assert res.excluded_experiments == 3
    assert res.experiments_before == 5


def test_retains_everything_when_nothing_falls_in_the_window():
    df = _data(["2014-06-01", "2015-01-01", "2013-02-01"])
    out, res = exclusion.apply(df)
    assert len(out) == 3
    assert res.excluded_experiments == 0
    assert res.retained_fraction == 1.0


def test_invalid_date_is_excluded():
    """Where there is doubt about when it was created, it is not used."""
    df = _data(["2015-01-01", "not a date", None])
    out, res = exclusion.apply(df)
    assert len(out) == 1
    assert res.excluded_experiments == 2


def test_counts_experiments_not_arms():
    """Several arms of the same experiment count as one experiment."""
    df = _data(
        ["2013-09-01"] * 3 + ["2015-01-01"] * 2,
        experiments=["A", "A", "A", "B", "B"],
    )
    out, res = exclusion.apply(df)
    assert res.experiments_before == 2
    assert res.experiments_after == 1
    assert res.arms_before == 5
    assert res.arms_after == 2


def test_the_result_is_always_returned():
    """The exclusion cannot be applied without receiving the count of what went."""
    df = _data(["2013-09-01", "2015-01-01"])
    output = exclusion.apply(df)
    assert isinstance(output, tuple) and len(output) == 2
    _, res = output
    assert "exclusion" in str(res)


@pytest.mark.parametrize("tz", [None, "UTC"])
def test_tolerates_time_zones(tz):
    f = pd.to_datetime(pd.Series(["2013-09-01", "2015-01-01"]), utc=tz == "UTC")
    df = pd.DataFrame(
        {"created_at": f, "clickability_test_id": [1, 2], "impressions": [10, 10]}
    )
    out, _ = exclusion.apply(df)
    assert list(out["clickability_test_id"]) == [2]
