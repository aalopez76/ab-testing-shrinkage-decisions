"""Check that every number the README states still matches the artefacts.

This answers a different question from the test suite. `pytest` asks whether the
software works; this asks whether the **published claims still correspond to the
files that back them**. Code can be correct while a document quietly drifts away
from it.

Each claim names where it appears, how to find it in `reports/results/`, and the
tolerance it is allowed. The tolerances are tight enough to catch a changed
analysis and loose enough to survive the last reported digit.

**This script and the README are updated in the same commit.** A number that
changes on purpose changes here too; one that changes by accident fails here
first.

It reads only versioned JSON, so it needs no data download and no recomputation,
which is why CI can run it.

Exit code is non-zero when any claim fails.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "reports" / "results"


@dataclass(frozen=True)
class Claim:
    """One number the README states, and where it comes from."""

    label: str
    source: str                      # file in reports/results/
    path: tuple[str | int, ...]      # keys to walk; ints index into lists
    expected: float
    tolerance: float
    scale: float = 1.0               # multiply the stored value before comparing

    def read(self) -> float:
        payload: Any = json.loads((RESULTS / self.source).read_text(encoding="utf-8"))
        for key in self.path:
            payload = payload[key]
        return float(payload) * self.scale


# --------------------------------------------------------------------------
# Stage 1 — pre-specified confirmatory analysis
# --------------------------------------------------------------------------

CLAIMS: list[Claim] = [
    # The estimand
    Claim("winner inflation, exploratory (pp)", "07_result.json",
          ("exploratory", "winner_inflation"), 0.236, 0.004, scale=100),
    Claim("winner inflation, confirmatory (pp)", "07_result.json",
          ("confirmatory", "winner_inflation"), 0.237, 0.004, scale=100),

    # Decision 4: the reported figure
    Claim("MSE change, exploratory (%)", "07_result.json",
          ("exploratory", "estimation", "relative_change"), -24.0, 0.4, scale=100),
    Claim("MSE change, confirmatory (%)", "07_result.json",
          ("confirmatory", "estimation", "relative_change"), -24.0, 0.4, scale=100),
    Claim("rank correlation, raw", "07_result.json",
          ("confirmatory", "estimation", "rho_raw"), 0.3601, 0.004),
    Claim("rank correlation, shrunk", "07_result.json",
          ("confirmatory", "estimation", "rho_shrunk"), 0.3656, 0.004),

    # Decision 2: prioritisation under a budget
    Claim("gain at 5%, raw (pp)", "07_result.json",
          ("confirmatory", "gain", "raw", "0.05"), 1.086, 0.015, scale=100),
    Claim("gain at 5%, shrunk (pp)", "07_result.json",
          ("confirmatory", "gain", "shrunk", "0.05"), 1.033, 0.015, scale=100),

    # Decision 2, with the interval the README now quotes. The bootstrap is a
    # Monte Carlo approximation, so these tolerances are wider than the
    # deterministic claims above: they must survive a rerun on a new seed, not
    # pin one run's digits. Endpoints moved by 0.0014 pp between B=1000 and
    # B=2000, which is what sets the scale.
    Claim("D2 difference, point (pp)", "08_regime.json",
          ("confirmatory", "full_archive", "difference", "point_estimate"),
          -0.0685, 0.004, scale=100),
    Claim("D2 difference, lower endpoint (pp)", "08_regime.json",
          ("confirmatory", "full_archive", "difference", "percentile_interval", 0),
          -0.092, 0.010, scale=100),
    Claim("D2 difference, upper endpoint (pp)", "08_regime.json",
          ("confirmatory", "full_archive", "difference", "percentile_interval", 1),
          -0.027, 0.010, scale=100),

    # Initial checks
    Claim("Cochran Q/dof, exploratory", "03_calibration.json",
          ("exploratory", "q_over_dof"), 1.940, 0.003),
    Claim("Cochran Q/dof, confirmatory", "03_calibration.json",
          ("confirmatory", "q_over_dof"), 1.927, 0.003),

    # Where it fails, and the mechanism it is consistent with
    Claim("selection changed (%)", "06_where_it_fails.json",
          ("confirmatory", "where_it_fails", "fraction_of_selection_changed"),
          23.0, 0.8, scale=100),
    Claim("discarded, realised gain (pp)", "06_where_it_fails.json",
          ("confirmatory", "where_it_fails", "discarded_delta_realized"),
          0.647, 0.02, scale=100),
    Claim("added, realised gain (pp)", "06_where_it_fails.json",
          ("confirmatory", "where_it_fails", "added_delta_realized"),
          0.510, 0.02, scale=100),
    Claim("discarded, shrinkage weight", "06_where_it_fails.json",
          ("confirmatory", "where_it_fails", "discarded_alpha"), 0.689, 0.015),
    Claim("added, shrinkage weight", "06_where_it_fails.json",
          ("confirmatory", "where_it_fails", "added_alpha"), 0.318, 0.015),
    Claim("precision-outcome, unadjusted", "06_where_it_fails.json",
          ("confirmatory", "precision_predicts_parameter", "correlation_raw"),
          -0.119, 0.005),
    Claim("precision-outcome, within week", "06_where_it_fails.json",
          ("confirmatory", "precision_predicts_parameter", "correlation_within_week"),
          -0.087, 0.005),
    Claim("precision-outcome, within type", "06_where_it_fails.json",
          ("confirmatory", "precision_predicts_parameter", "correlation_within_type"),
          -0.113, 0.005),
    Claim("median n*p", "06_where_it_fails.json",
          ("confirmatory", "proportion_regime", "median_n_times_p"), 40.0, 1.0),

    # Scale figures the document quotes
    Claim("experiments, confirmatory", "01_panel.json",
          ("confirmatory", "panel", "experiments"), 15787, 0),
    Claim("arms, confirmatory", "01_panel.json",
          ("confirmatory", "panel", "arms"), 77446, 0),
    Claim("experiments, exploratory", "01_panel.json",
          ("exploratory", "panel", "experiments"), 3380, 0),
    Claim("retained fraction, confirmatory", "01_panel.json",
          ("confirmatory", "exclusion", "retained_fraction"), 0.694, 0.002),

    # --------------------------------------------------------------------
    # Stage 2 — post-confirmatory exploratory extensions
    # --------------------------------------------------------------------
    Claim("BHS fitted a", "10_bhs.json",
          ("confirmatory", "a_mean"), 2.65, 0.08),
    Claim("BHS likelihood ratio", "10_bhs.json",
          ("confirmatory", "likelihood_ratio"), 961, 40),
    Claim("BHS MSE change (%)", "10_bhs.json",
          ("confirmatory", "mse_relative_change", "bhs"), -28.1, 0.6, scale=100),
    Claim("regime filter retains (%)", "08_regime.json",
          ("confirmatory", "filter", "fraction_of_arms_retained"), 6.9, 0.3, scale=100),

    # Decision 3, by realised policy value. The sign of the uncorrected rule at
    # the demanding threshold is the claim that matters, so its tolerance is
    # tight enough that a change of sign fails here.
    Claim("ship value at 0.8 pp, raw (pp)", "09_ship_decision.json",
          ("thresholds", "0.008", "value_raw", "point_estimate"),
          -0.00641, 0.0020, scale=100),
    Claim("ship value at 0.8 pp, shrunk (pp)", "09_ship_decision.json",
          ("thresholds", "0.008", "value_shrunk", "point_estimate"),
          0.01187, 0.0020, scale=100),
    Claim("ship difference at 0.8 pp (pp)", "09_ship_decision.json",
          ("thresholds", "0.008", "difference_shrunk_minus_raw", "point_estimate"),
          0.01828, 0.0025, scale=100),
    Claim("ship difference at 0.8 pp, lower endpoint (pp)",
          "09_ship_decision.json",
          ("thresholds", "0.008", "difference_shrunk_minus_raw",
           "percentile_interval", 0),
          0.0148, 0.0040, scale=100),
    Claim("ship difference at 0.6 pp (pp)", "09_ship_decision.json",
          ("thresholds", "0.006", "difference_shrunk_minus_raw", "point_estimate"),
          0.01475, 0.0025, scale=100),
    Claim("ship difference at 0.4 pp (pp)", "09_ship_decision.json",
          ("thresholds", "0.004", "difference_shrunk_minus_raw", "point_estimate"),
          0.00548, 0.0020, scale=100),
    Claim("ship rate at 0.8 pp, raw (%)", "09_ship_decision.json",
          ("thresholds", "0.008", "ship_rate_raw"), 14.2, 0.8, scale=100),
    Claim("ship rate at 0.8 pp, shrunk (%)", "09_ship_decision.json",
          ("thresholds", "0.008", "ship_rate_shrunk"), 3.1, 0.8, scale=100),
    Claim("should ship at 0.8 pp (%)", "09_ship_decision.json",
          ("thresholds", "0.008", "should_ship"), 14.2, 0.8, scale=100),

    # Split sensitivity. The point of these rows is the spread: they fail if a
    # future change quietly makes the published numbers look less dependent on
    # the split than they are.
    Claim("inflation at selection share 0.3 (pp)", "12_split_sensitivity.json",
          ("inflation_by_fraction", "0.3", "mean"), 0.3348, 0.012, scale=100),
    Claim("inflation at selection share 0.5 (pp)", "12_split_sensitivity.json",
          ("inflation_by_fraction", "0.5", "mean"), 0.2374, 0.008, scale=100),
    Claim("inflation at selection share 0.7 (pp)", "12_split_sensitivity.json",
          ("inflation_by_fraction", "0.7", "mean"), 0.1868, 0.008, scale=100),
    Claim("inflation at 0.3, relative to published (%)",
          "12_split_sensitivity.json",
          ("inflation_by_fraction", "0.3", "relative_to_published"),
          41.0, 4.0, scale=100),
    Claim("MSE change, equal thirds (%)", "12_split_sensitivity.json",
          ("between_by_shares", "equal thirds (published)",
           "mse_relative_change"), -24.1, 1.2, scale=100),
    Claim("MSE change, more to estimation (%)", "12_split_sensitivity.json",
          ("between_by_shares", "more to estimation", "mse_relative_change"),
          -11.4, 1.5, scale=100),
    Claim("gain difference, equal thirds (pp)", "12_split_sensitivity.json",
          ("between_by_shares", "equal thirds (published)", "gain_difference"),
          -0.0541, 0.012, scale=100),
    Claim("gain difference, more to estimation (pp)",
          "12_split_sensitivity.json",
          ("between_by_shares", "more to estimation", "gain_difference"),
          -0.0302, 0.012, scale=100),
]


def main() -> int:
    failures = []
    print(f"{'claim':42}{'README':>11}{'artefact':>11}")
    for claim in CLAIMS:
        try:
            actual = claim.read()
        except (KeyError, FileNotFoundError) as exc:
            failures.append((claim.label, f"not found: {exc}"))
            print(f"{claim.label:42}{claim.expected:11.4g}{'MISSING':>11}   FAIL")
            continue
        ok = abs(actual - claim.expected) <= claim.tolerance
        if not ok:
            failures.append((claim.label, f"{actual:.6g} against {claim.expected:.6g}"))
        print(f"{claim.label:42}{claim.expected:11.4g}{actual:11.4g}"
              f"   {'ok' if ok else 'FAIL'}")

    total = len(CLAIMS)
    passed = total - len(failures)
    print(f"\n{passed}/{total} reported numerical claims verified")
    if failures:
        print("\nfailed:")
        for label, detail in failures:
            print(f"  {label}: {detail}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
