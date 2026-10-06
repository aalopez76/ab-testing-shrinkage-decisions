"""The exclusion rule. It lives here and nowhere else.

The Upworthy archive has a documented randomisation failure: a Cloudflare caching
misconfiguration on 25 June 2013 meant that a single variant was shown for months
until the cache expired. It affects approximately 22% of the tests, and the
archive's maintainers advise against using them for causal inference.

The public OSF files date from 2020-2021 and **carry no column marking them**, so
the exclusion is derived from the creation date. It was verified independently,
month by month (see `diagnostics/srm.py`).
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

#: Excluded window: from the start of June 2013 to the end of January 2014.
#: Closed on the left, open on the right.
WINDOW_START = pd.Timestamp("2013-06-01")
WINDOW_END = pd.Timestamp("2014-02-01")


@dataclass(frozen=True)
class ExclusionResult:
    """What was excluded, so that it can be reported."""

    arms_before: int
    arms_after: int
    experiments_before: int
    experiments_after: int

    @property
    def excluded_arms(self) -> int:
        return self.arms_before - self.arms_after

    @property
    def excluded_experiments(self) -> int:
        return self.experiments_before - self.experiments_after

    @property
    def retained_fraction(self) -> float:
        if self.experiments_before == 0:
            return 0.0
        return self.experiments_after / self.experiments_before

    def __str__(self) -> str:
        return (
            f"exclusion {WINDOW_START.date()} to {WINDOW_END.date()}: "
            f"{self.excluded_experiments:,} of {self.experiments_before:,} "
            f"experiments removed ({1 - self.retained_fraction:.1%}); "
            f"{self.experiments_after:,} remain "
            f"({self.retained_fraction:.1%})"
        )


def in_failure_window(dates: pd.Series) -> pd.Series:
    """True for rows created within the failure window.

    Dates that cannot be parsed return True and are therefore excluded: where
    there is doubt about when an experiment was created, it is not used for
    inference.
    """
    f = pd.to_datetime(dates, errors="coerce", utc=False)
    if getattr(f.dtype, "tz", None) is not None:
        f = f.dt.tz_localize(None)
    inside = (f >= WINDOW_START) & (f < WINDOW_END)
    return inside | f.isna()


def apply(
    df: pd.DataFrame,
    date_col: str = "created_at",
    experiment_col: str = "clickability_test_id",
) -> tuple[pd.DataFrame, ExclusionResult]:
    """Remove the rows in the failure window and report how many were removed.

    This always returns the pair (data, result) so that a caller cannot apply the
    exclusion without having the count of what was dropped to hand.
    """
    arms_before = len(df)
    experiments_before = df[experiment_col].nunique()

    keep = ~in_failure_window(df[date_col])
    out = df.loc[keep].copy()

    return out, ExclusionResult(
        arms_before=arms_before,
        arms_after=len(out),
        experiments_before=experiments_before,
        experiments_after=out[experiment_col].nunique(),
    )
